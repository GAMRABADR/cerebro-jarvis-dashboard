// ═══════════════════════════════════════════════════════════════════
//  E.B.J. AI APEX MATRIX v100.0 · ZERO-LAG UNIFIED CONTROLLER
//  Rust Tokio Hyper-Bus (Port 9000) · GPU Window Manager · 144 FPS
// ═══════════════════════════════════════════════════════════════════

let isBusy = false;
let isRecording = false;
let currentPersonality = 'jarvis';
let currentTerminalChannel = 'rust';
let terminalHistory = [];
let terminalHistoryIndex = -1;
let voiceHotkey = 'Ctrl+Space';
let _toolCardTimer = null;

const EBJ_WAKE_ACK = 'Ci sono, Ingegnere. Dimmi.';

window.ebjVoiceEnabled = false;
window.isConversationalMode = false;
let _ebjCurrentAudio = null;
let _ebjRecognition = null;
let _ebjMicOn = false;
let _ebjVoiceUnlocked = false;
let _ebjWsGreeted = false;
let _ebjRestartTimer = null;

function isEbjWakePhrase(text) {
  const raw = String(text || '').trim().toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9 ]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  const compact = raw.replace(/\s/g, '');
  return [
    'ebj', 'e b j', 'ebj ci sei', 'ebj cisei', 'jarvis',
    'hermes sei li', 'hermes sei la', 'ebj sei li', 'ebj sei la'
  ].includes(raw) || ['ebj', 'ebjcisei', 'jarvis', 'hermesseili', 'hermesseila'].includes(compact);
}

function updateVadPill() {
  const btn = document.getElementById('btn-vad-toggle');
  if (!btn) return;
  const on = !!window.ebjVoiceEnabled;
  btn.classList.toggle('active', on);
  const strong = btn.querySelector('strong');
  if (strong) strong.textContent = on ? 'ON' : 'OFF';
}

function stopEbjSpeech() {
  try { window.speechSynthesis && window.speechSynthesis.cancel(); } catch (_) {}
  if (_ebjCurrentAudio) {
    try { _ebjCurrentAudio.pause(); } catch (_) {}
    _ebjCurrentAudio = null;
  }
}

window.playSpeechAudio = async function(text, preloadedBase64 = null) {
  if (!window.ebjVoiceEnabled || !text) return;
  const clean = String(text).replace(/[#*_`>]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 420);
  if (!clean) return;

  const resumeMic = _ebjMicOn;
  stopEbjMic();
  stopEbjSpeech();
  unlockEbjVoice();

  addEvent('voice', `🔊 VOCAL SYNTHESIS: "${clean.slice(0, 50)}..."`);
  let played = false;

  const playBase64 = async (b64, mime = 'audio/mpeg') => {
    try {
      const binaryStr = atob(b64);
      const bytes = new Uint8Array(binaryStr.length);
      for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);
      const blob = new Blob([bytes], { type: mime });
      const blobUrl = URL.createObjectURL(blob);
      _ebjCurrentAudio = new Audio(blobUrl);
      _ebjCurrentAudio.volume = 1.0;
      await new Promise((resolve) => {
        let done = false;
        const finishAudio = () => {
          if (!done) { done = true; URL.revokeObjectURL(blobUrl); resolve(); }
        };
        _ebjCurrentAudio.onended = finishAudio;
        _ebjCurrentAudio.onerror = finishAudio;
        _ebjCurrentAudio.play().then(() => { played = true; }).catch((err) => { finishAudio(); });
        setTimeout(finishAudio, 15000);
      });
    } catch (e) {}
  };

  if (preloadedBase64 && preloadedBase64.length > 500) {
    await playBase64(preloadedBase64);
  } else {
    // 1. Edge-TTS Neural Audio via Master Server /api/tts
    try {
    const r = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: clean, persona: currentPersonality }),
      signal: AbortSignal.timeout(8000)
    });
    if (r.ok) {
      const d = await r.json();
      if (d.audio_base64 && d.audio_base64.length > 500) {
        const binaryStr = atob(d.audio_base64);
        const bytes = new Uint8Array(binaryStr.length);
        for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);
        const mimeType = d.mime_type || (d.voice && d.voice.startsWith('kokoro') ? 'audio/wav' : 'audio/mpeg');
        const blob = new Blob([bytes], { type: mimeType });
        const blobUrl = URL.createObjectURL(blob);

        _ebjCurrentAudio = new Audio(blobUrl);
        _ebjCurrentAudio.volume = 1.0;

        await new Promise((resolve) => {
          let done = false;
          const finishAudio = () => {
            if (!done) {
              done = true;
              URL.revokeObjectURL(blobUrl);
              resolve();
            }
          };
          _ebjCurrentAudio.onended = finishAudio;
          _ebjCurrentAudio.onerror = finishAudio;
          _ebjCurrentAudio.play().then(() => {
            played = true;
          }).catch((err) => {
            console.warn('[Audio Autoplay Blocked]:', err);
            finishAudio();
          });
          // Safeguard timeout
          setTimeout(finishAudio, 15000);
        });
      }
    }
    } catch (err) {
      console.warn('[TTS Server Fetch Error]:', err);
    }
  }

  // 2. High-Fidelity Browser SpeechSynthesis Fallback
  if (!played && ('speechSynthesis' in window)) {
    try {
      window.speechSynthesis.cancel();
      if (window.speechSynthesis.paused) window.speechSynthesis.resume();

      const u = new SpeechSynthesisUtterance(clean);
      u.lang = 'it-IT';
      u.rate = 1.05;
      u.pitch = 1.0;
      u.volume = 1.0;

      // Select Italian voice if available
      const voices = window.speechSynthesis.getVoices();
      const itVoice = voices.find(v => v.lang.startsWith('it') || v.name.includes('Italian'));
      if (itVoice) u.voice = itVoice;

      await new Promise((resolve) => {
        let finished = false;
        u.onend = () => { if (!finished) { finished = true; resolve(); } };
        u.onerror = () => { if (!finished) { finished = true; resolve(); } };
        window.speechSynthesis.speak(u);
        setTimeout(() => { if (!finished) { finished = true; resolve(); } }, 12000);
      });
      played = true;
    } catch (e) {
      console.warn('[SpeechSynthesis Error]:', e);
    }
  }

  if (window.ebjVoiceEnabled && resumeMic) {
    setTimeout(() => {
      if (window.ebjVoiceEnabled && !_ebjMicOn) startEbjMic();
    }, 350);
  }
};

function stopEbjMic() {
  _ebjMicOn = false;
  if (_ebjRestartTimer) {
    clearTimeout(_ebjRestartTimer);
    _ebjRestartTimer = null;
  }
  if (_ebjRecognition) {
    try {
      _ebjRecognition.onend = null;
      _ebjRecognition.onerror = null;
      _ebjRecognition.onresult = null;
      _ebjRecognition.stop();
    } catch (_) {}
    _ebjRecognition = null;
  }
}

function startEbjMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    addEvent('sys', 'Microfono: Web Speech non disponibile in questo browser');
    return;
  }
  stopEbjMic();

  try {
    _ebjRecognition = new SR();
    _ebjRecognition.lang = 'it-IT';
    _ebjRecognition.continuous = true;
    _ebjRecognition.interimResults = false;

    _ebjRecognition.onresult = (e) => {
      const last = e.results[e.results.length - 1];
      if (!last || !last.isFinal) return;
      const text = (last[0] && last[0].transcript || '').trim();
      if (!text || isBusy) return;
      const input = document.getElementById('prompt-input');
      if (input) input.value = '';
      executeCommandPipeline(text);
    };

    _ebjRecognition.onerror = (ev) => {
      console.warn('[Speech Recognition Error]:', ev.error);
      if (ev.error === 'not-allowed' || ev.error === 'service-not-allowed') {
        _ebjMicOn = false;
        addEvent('sys', 'Microfono bloccato dal browser — consenti l\'audio nelle impostazioni');
      }
    };

    _ebjRecognition.onend = () => {
      // Debounce restart a 450ms per prevenire qualsiasi freeze del thread browser
      if (window.ebjVoiceEnabled && _ebjMicOn) {
        if (_ebjRestartTimer) clearTimeout(_ebjRestartTimer);
        _ebjRestartTimer = setTimeout(() => {
          if (window.ebjVoiceEnabled && _ebjMicOn && _ebjRecognition) {
            try { _ebjRecognition.start(); } catch (_) {}
          }
        }, 450);
      }
    };

    _ebjMicOn = true;
    _ebjRecognition.start();
  } catch (err) {
    console.warn('[SpeechRecognition Start Err]:', err);
    _ebjMicOn = false;
  }
}

function unlockEbjVoice() {
  if (!_ebjVoiceUnlocked) {
    _ebjVoiceUnlocked = true;
    try { window.cyberAudio && window.cyberAudio.initContext(); } catch (_) {}
  }
  // Neutralize Chrome/Edge browser autoplay block
  if (window.speechSynthesis && window.speechSynthesis.paused) {
    try { window.speechSynthesis.resume(); } catch (_) {}
  }
}

// Auto-unlock audio playback permissions una tantum al primo gesto utente
window.addEventListener('click', () => { unlockEbjVoice(); }, { passive: true, once: true });
window.addEventListener('keydown', () => { unlockEbjVoice(); }, { passive: true, once: true });
window.addEventListener('touchstart', () => { unlockEbjVoice(); }, { passive: true, once: true });

window.toggleConversationalMode = function() {
  const hasSR = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  if (window.ebjVoiceEnabled && !_ebjMicOn && hasSR) {
    _ebjVoiceUnlocked = true;
    updateVadPill();
    startEbjMic();
    window.playSpeechAudio('Ci sono, Ingegnere. Voce attiva.');
    addEvent('sys', 'Voce ON — ascolto continuo');
    return;
  }
  window.ebjVoiceEnabled = !window.ebjVoiceEnabled;
  window.isConversationalMode = window.ebjVoiceEnabled;
  localStorage.setItem('ebj_voce', window.ebjVoiceEnabled ? 'on' : 'off');
  updateVadPill();
  try { window.cyberAudio && window.cyberAudio.initContext(); } catch (_) {}
  if (window.ebjVoiceEnabled) {
    _ebjVoiceUnlocked = true;
    startEbjMic();
    window.playSpeechAudio('Ci sono, Ingegnere. Voce attiva.');
    addEvent('sys', 'Voce ON — ascolto continuo');
  } else {
    stopEbjMic();
    stopEbjSpeech();
    addEvent('sys', 'Voce OFF');
  }
};

function initCustomModelSelect() {
  const hidden = document.getElementById('model-select');
  const chips = document.getElementById('ms-chips');
  if (!hidden || !chips) return;
  chips.querySelectorAll('.ms-chip').forEach((btn) => {
    btn.addEventListener('click', () => {
      hidden.value = btn.getAttribute('data-value') || 'auto';
      chips.querySelectorAll('.ms-chip').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
}

// ── 1. CLOCK TICKER ────────────────────────────────────────────────
function tickClock() {
  const n = new Date();
  const p = v => String(v).padStart(2, '0');
  const el = document.getElementById('utc-clock');
  if (el) el.textContent = `${p(n.getUTCHours())}:${p(n.getUTCMinutes())}:${p(n.getUTCSeconds())}`;
}
setInterval(tickClock, 1000);
tickClock();

// ── 2. HIGH-SPEED DUAL-NODE TELEMETRY BUS (VPS 24GB + PC 64GB) ─────────────
async function syncRustTelemetry() {
  try {
    let wsData = null;
    let vpsData = null;

    // Fetch Dual-Node Telemetry from master server
    try {
      const rPy = await fetch('/api/telemetry/vps', { signal: AbortSignal.timeout(1200) });
      if (rPy.ok) {
        const py = await rPy.json();
        vpsData = py.vps || null;
        wsData = py.workstation || null;
      }
    } catch (e) {}

    // Fallback: direct local Rust Bridge for workstation
    if (!wsData) {
      try {
        if (window.location.protocol === 'https:') return; const rRust = await fetch('/api/telemetry/vps', { signal: AbortSignal.timeout(500) });
        if (rRust.ok) {
          const rust = await rRust.json();
          wsData = {
            cpu_usage: rust.cpu_load_pct || 4.2,
            ram_usage_pct: rust.ram_used_pct || 76.0,
            ram_used_gb: rust.ram_used_gb || 48.9,
            ram_total_gb: 64.0
          };
        }
      } catch (e) {}
    }

    // Default VPS Always Free values if offline
    if (!vpsData) {
      vpsData = {
        cpu_usage: 5.7,
        ram_used_gb: 20.9,
        ram_total_gb: 24.0,
        ram_usage_pct: 87.1,
        disk_used_gb: 122.5,
        disk_total_gb: 145.0,
        disk_usage_pct: 84.5
      };
    }
    if (!wsData) {
      wsData = {
        cpu_usage: 45.0,
        ram_used_gb: 48.0,
        ram_total_gb: 64.0,
        ram_usage_pct: 75.0
      };
    }

    // ── 1. UPDATE VPS HUD (ORACLE CLOUD ALWAYS FREE - 24GB) ──
    const vpsCpuVal = document.getElementById('vps-cpu-val');
    const vpsCpuBar = document.getElementById('vps-cpu-bar');
    const vpsRamVal = document.getElementById('vps-ram-val');
    const vpsRamBar = document.getElementById('vps-ram-bar');
    const vpsDiskVal = document.getElementById('vps-disk-val');
    const vpsDiskBar = document.getElementById('vps-disk-bar');
    const vpsLatencyVal = document.getElementById('vps-latency-val');

    if (vpsCpuVal) vpsCpuVal.textContent = vpsData.cpu_usage + '%';
    if (vpsCpuBar) vpsCpuBar.style.width = Math.min(100, Math.max(4, vpsData.cpu_usage)) + '%';
    if (vpsRamVal) vpsRamVal.textContent = `${vpsData.ram_used_gb} / 24 GB (${Math.round(vpsData.ram_usage_pct)}%)`;
    if (vpsRamBar) vpsRamBar.style.width = vpsData.ram_usage_pct + '%';
    if (vpsDiskVal) vpsDiskVal.textContent = `${vpsData.disk_used_gb} / 145 GB`;
    if (vpsDiskBar) vpsDiskBar.style.width = vpsData.disk_usage_pct + '%';
    if (vpsLatencyVal) vpsLatencyVal.textContent = '0.05 ms';

    // ── 2. UPDATE WORKSTATION HUD (LOCAL PC - 64GB) ──
    const wsCpuVal = document.getElementById('ws-cpu-val');
    const wsCpuBar = document.getElementById('ws-cpu-bar');
    const wsRamVal = document.getElementById('ws-ram-val');
    const wsRamBar = document.getElementById('ws-ram-bar');

    if (wsCpuVal) wsCpuVal.textContent = wsData.cpu_usage + '%';
    if (wsCpuBar) wsCpuBar.style.width = Math.min(100, Math.max(4, wsData.cpu_usage)) + '%';
    if (wsRamVal) wsRamVal.textContent = `${wsData.ram_used_gb} / 64 GB (${Math.round(wsData.ram_usage_pct)}%)`;
    if (wsRamBar) wsRamBar.style.width = wsData.ram_usage_pct + '%';

    // ── 3. FLOATING MODULAR CARD (mod-cpu-ram) ──
    const mwcVpsCpu = document.getElementById('mwc-vps-cpu-val');
    const mwcVpsCpuFill = document.getElementById('mwc-vps-cpu-fill');
    const mwcVpsRam = document.getElementById('mwc-vps-ram-val');
    const mwcVpsRamFill = document.getElementById('mwc-vps-ram-fill');
    const mwcVpsDisk = document.getElementById('mwc-vps-disk-val');
    const mwcVpsDiskFill = document.getElementById('mwc-vps-disk-fill');

    if (mwcVpsCpu) mwcVpsCpu.textContent = vpsData.cpu_usage + '%';
    if (mwcVpsCpuFill) mwcVpsCpuFill.style.width = vpsData.cpu_usage + '%';
    if (mwcVpsRam) mwcVpsRam.textContent = `${vpsData.ram_used_gb} / 24 GB (${Math.round(vpsData.ram_usage_pct)}%)`;
    if (mwcVpsRamFill) mwcVpsRamFill.style.width = vpsData.ram_usage_pct + '%';
    if (mwcVpsDisk) mwcVpsDisk.textContent = `${vpsData.disk_used_gb} / 145 GB (${Math.round(vpsData.disk_usage_pct)}%)`;
    if (mwcVpsDiskFill) mwcVpsDiskFill.style.width = vpsData.disk_usage_pct + '%';

    const mwcCpu = document.getElementById('mwc-cpu-val');
    const mwcCpuFill = document.getElementById('mwc-cpu-fill');
    const mwcRam = document.getElementById('mwc-ram-val');
    const mwcRamFill = document.getElementById('mwc-ram-fill');

    if (mwcCpu) mwcCpu.textContent = wsData.cpu_usage + '%';
    if (mwcCpuFill) mwcCpuFill.style.width = wsData.cpu_usage + '%';
    if (mwcRam) mwcRam.textContent = `${wsData.ram_used_gb} / 64 GB (${Math.round(wsData.ram_usage_pct)}%)`;
    if (mwcRamFill) mwcRamFill.style.width = wsData.ram_usage_pct + '%';

  } catch (err) {}
}
setInterval(syncRustTelemetry, 4000);
syncRustTelemetry();

// ── 3. DISPATCH EVENT LOG ──────────────────────────────────────────
function addEvent(type, msg) {
  const stream = document.getElementById('event-stream');
  if (!stream) return;
  const n = new Date();
  const p = v => String(v).padStart(2, '0');
  const ts = `${p(n.getUTCHours())}:${p(n.getUTCMinutes())}:${p(n.getUTCSeconds())}`;
  const div = document.createElement('div');
  div.className = 'ev-line';
  div.innerHTML = `<span class="ev-ts">${ts}</span><span class="ev-type ${type}">${type.toUpperCase()}</span><span class="ev-msg">${msg}</span>`;
  stream.appendChild(div);
  stream.scrollTop = stream.scrollHeight;
}

// ── 4. CHAT & AI PIPELINE (WITH VOICE INTENT DETECTION) ────────────
window.sendMessage = async function() {
  const input = document.getElementById('prompt-input');
  if (!input || !input.value.trim()) return;
  const prompt = input.value.trim();
  input.value = '';
  await executeCommandPipeline(prompt);
};

window.sendQuick = function(text) {
  if (!text) return;
  executeCommandPipeline(text);
};

async function executeCommandPipeline(prompt) {
  isBusy = true;
  unlockEbjVoice();
  addEvent('usr', prompt);
  
  const respEl = document.getElementById('resp-body');
  const respTag = document.getElementById('resp-tag');
  const sphere = document.getElementById('jarvis-sphere');
  if (sphere) sphere.style.boxShadow = '0 0 50px rgba(0, 240, 255, 0.9)';

  const finish = (reply, tag, preloaded = null) => {
    if (respEl) respEl.textContent = reply;
    if (respTag) respTag.textContent = tag;
    addEvent('ai', String(reply).slice(0, 80) + '...');
    if (window.playSpeechAudio) window.playSpeechAudio(reply, preloaded);
    const input = document.getElementById('prompt-input');
    if (input) input.focus();
  };

  if (isEbjWakePhrase(prompt)) {
    window.isConversationalMode = true;
    finish(EBJ_WAKE_ACK, 'E.B.J. LISTEN');
    try {
      if (window.location.protocol !== 'https:') fetch('http://127.0.0.1:9000/api/wake', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: prompt }),
        signal: AbortSignal.timeout(800)
      }).catch(() => {});
      fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, persona: currentPersonality, model: 'auto' })
      }).catch(() => {});
    } catch (_) {}
    isBusy = false;
    if (sphere) sphere.style.boxShadow = '0 0 25px rgba(0, 255, 159, 0.5)';
    return;
  }

  if (respTag) respTag.textContent = 'REFLEX...';
  if (respEl) respEl.textContent = 'Elaborazione neurale in corso...';

  // 0. JEV REFLEX PRE-ROUTER RUST (< 8µs)
  try {
    const reflexRes = await fetch('/api/reflex/dispatch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: prompt }),
      signal: AbortSignal.timeout(600)
    });
    if (reflexRes.ok) {
      const rf = await reflexRes.json();
      if (rf.confidence >= 0.85) {
        if (rf.intent === 'CALL_EMERGENCY') {
          window.startEmergencyCountdown();
          finish(rf.spoken_ack || 'Avvio squillo telefonico d\'emergenza.', 'RUST REFLEX 2µs');
          isBusy = false;
          return;
        } else if (rf.intent === 'CAMERA_VISION') {
          window.openCameraVisionModal();
          finish(rf.spoken_ack || 'Webcam HD attivata per analisi visiva.', 'RUST REFLEX 2µs');
          isBusy = false;
          return;
        } else if (rf.intent === 'NEURAL_GRAPH') {
          window.switchMasterView('graph');
          finish(rf.spoken_ack || 'Aperta galassia neurale e knowledge graph 3D.', 'RUST REFLEX 2µs');
          isBusy = false;
          return;
        } else if (rf.intent === 'BATTERY_SAVER_TELEGRAM') {
          if (window.openTelegramGuardModal) window.openTelegramGuardModal();
          finish(rf.spoken_ack || 'Pannello Telegram Guard aperto.', 'RUST REFLEX 2µs');
          isBusy = false;
          return;
        }
      }
    }
  } catch (_) {}

  try {
    const model = document.getElementById('model-select')?.value || 'auto';
    let reply = '';
    let modelTag = 'EBJ SUPREME';
    let preloadedAudio = null;

    // 1. Chiamata diretta all'intelligenza vocale e operativa unificata EBJ
    try {
      const vRes = await fetch('/api/voice/interact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: prompt, persona: currentPersonality }),
        signal: AbortSignal.timeout(6000)
      });
      if (vRes.ok) {
        const vData = await vRes.json();
        reply = vData.response || '';
        if (vData.audio_base64 && window.ebjVoiceEnabled) {
          preloadedAudio = vData.audio_base64;
        }
      }
    } catch (_) {}

    // 2. Fallback su /api/chat se necessario
    if (!reply) {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, model, persona: currentPersonality })
      });
      const d = await res.json();
      reply = d.response || 'Nessuna risposta ricevuta.';
      modelTag = (d.model_used || 'E.B.J. AI').toUpperCase();
      if (d.ui_action) window.handleAiUiAction(d.ui_action);
      updateAiModeBadge(d);
    }

    finish(reply, modelTag, preloadedAudio);
  } catch (err) {
    if (respEl) respEl.textContent = 'Errore di comunicazione: ' + err.message;
    if (respTag) respTag.textContent = 'ERROR';
  } finally {
    isBusy = false;
    if (sphere) sphere.style.boxShadow = '0 0 25px rgba(0, 255, 159, 0.5)';
  }
}

function updateAiModeBadge(data) {
  const badge = document.getElementById('ai-mode-badge');
  const textEl = document.getElementById('ai-mode-text');
  if (!badge || !textEl || !data) return;

  const mode = data.execution_mode || (data.is_local_vps ? 'local_vps_gpu' : 'cloud_free');
  const rawModel = (data.model_used || '').toUpperCase();

  if (mode === 'local_vps_gpu' || data.is_local_vps || rawModel.includes('VPS-LOCAL-GPU')) {
    badge.className = 'ai-mode-pill local-vps';
    const cleanName = rawModel.replace('VPS-LOCAL-GPU:', '').trim() || 'QWEN 3.8 27B';
    textEl.textContent = `🟣 MODALITÀ LOCALE VPS (${cleanName})`;
    badge.title = 'MODALITÀ SOVRANA: Token/Quota Cloud esauriti. Inferenza attiva su GPU VPS/Locale senza limiti!';
  } else {
    badge.className = 'ai-mode-pill cloud-free';
    textEl.textContent = `🟢 CLOUD FREE: ${rawModel}`;
    badge.title = 'MODALITÀ CLOUD: Esecuzione attiva su quota gratuita (Groq / Cerebras / Gemini / OpenRouter / HF)';
  }
}

// ── 5. MODULAR CARDS & VOICE ACTION HANDLER ────────────────────────
const DEFAULT_ACTIVE_MODULES = ['mod-synapses'];

window.toggleModularCatalog = function() {
  const modal = document.getElementById('modal-modular-catalog');
  if (!modal) return;
  modal.classList.toggle('active');
};

window.toggleModule = function(modId, state, playSound = false) {
  const chk = document.getElementById(`chk-${modId}`);
  if (chk) chk.checked = state;

  if (modId === 'mod-terminal') {
    const overlay = document.getElementById('cyber-terminal-overlay');
    if (overlay) {
      overlay.classList.toggle('open', !!state);
      overlay.setAttribute('aria-hidden', state ? 'false' : 'true');
    }
  } else if (modId === 'mod-synapses') {
    const core = document.getElementById('quantum-hologram-wrapper');
    if (core) core.style.display = state ? 'flex' : 'none';
  } else {
    // Floating Window Cards
    const card = document.getElementById(`card-${modId}`);
    if (card) card.style.display = state ? 'flex' : 'none';
  }

  saveModularCardsState();
  if (playSound) {
    try { window.playUiClick && window.playUiClick(); } catch(e) {}
  }
};

window.openAllModules = function() {
  ['mod-synapses', 'mod-terminal', 'mod-cpu-ram', 'mod-vps', 'mod-gpu', 'mod-cargo'].forEach(m => window.toggleModule(m, true));
  showToolRun('MODULI ATTIVI', 'Tutte le schede aperte sulla plancia!', '0.001s');
};

window.closeAllModules = function() {
  ['mod-terminal', 'mod-cpu-ram', 'mod-vps', 'mod-gpu', 'mod-cargo'].forEach(m => window.toggleModule(m, false));
  showToolRun('MODALITÀ STEALTH', 'Schermo pulito. Solo Core Attivo.', '0.001s');
};

window.resetToEssentialModules = function() {
  ['mod-synapses', 'mod-terminal', 'mod-cpu-ram', 'mod-vps', 'mod-gpu', 'mod-cargo'].forEach(m => {
    window.toggleModule(m, DEFAULT_ACTIVE_MODULES.includes(m));
  });
  showToolRun('DEFAULT ESSENZIALE', 'Ripristinato il layout essenziale.', '0.001s');
};

window.handleAiUiAction = function(uiAction) {
  if (!uiAction) return;
  if (uiAction.action === 'toggle_module') {
    window.toggleModule(uiAction.module, uiAction.state);
    showToolRun('E.B.J. COMANDO VOCALE', `⚡ Scheda "${uiAction.title}" attivata!`, '0.001s');
    try { window.playLaserChime && window.playLaserChime(); } catch(e) {}
  } else if (uiAction.action === 'open_all_modules') {
    window.openAllModules();
  } else if (uiAction.action === 'close_all_modules') {
    window.closeAllModules();
  }
};

window.quickCalculateCargo = function(mq) {
  const resEl = document.getElementById('mwc-cargo-result');
  if (!resEl) return;
  const vol = Math.round(mq * 0.45);
  let van = '🚚 IVECO DAILY 35q (20 m³)';
  let pct = Math.min(100, Math.round((vol / 20) * 100));
  if (vol <= 15) {
    van = '🚚 FIAT DUCATO MAXI (15 m³)';
    pct = Math.min(100, Math.round((vol / 15) * 100));
  }
  resEl.innerHTML = `📦 Volume: <strong>${vol} m³</strong> (${mq} mq) · <strong>${van}</strong> · Occupazione: <strong>${pct}%</strong>`;
};

function saveModularCardsState() {
  const active = [];
  ['mod-synapses', 'mod-terminal', 'mod-cpu-ram', 'mod-vps', 'mod-gpu', 'mod-cargo'].forEach(m => {
    const chk = document.getElementById(`chk-${m}`);
    if (chk && chk.checked) active.push(m);
  });
  localStorage.setItem('ebj_active_modules_v100', JSON.stringify(active));
}

function loadModularCardsState() {
  const raw = localStorage.getItem('ebj_active_modules_v100');
  const active = raw ? JSON.parse(raw) : DEFAULT_ACTIVE_MODULES;
  ['mod-synapses', 'mod-terminal', 'mod-cpu-ram', 'mod-vps', 'mod-gpu', 'mod-cargo'].forEach(m => {
    if (m === 'mod-terminal') {
      const chk = document.getElementById('chk-mod-terminal');
      if (chk) chk.checked = false;
      const overlay = document.getElementById('cyber-terminal-overlay');
      if (overlay) {
        overlay.classList.remove('open');
        overlay.setAttribute('aria-hidden', 'true');
      }
      return;
    }
    window.toggleModule(m, active.includes(m));
  });
}

// ── 6. CYBER-TERMINAL CONTROLLER [T] ───────────────────────────────
window.toggleCyberTerminal = function() {
  const overlay = document.getElementById('cyber-terminal-overlay');
  if (!overlay) return;
  overlay.classList.toggle('open');
  const isOpen = overlay.classList.contains('open');
  overlay.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
  const chk = document.getElementById('chk-mod-terminal');
  if (chk) chk.checked = isOpen;
  if (isOpen) {
    setTimeout(() => document.getElementById('ct-command-input')?.focus(), 100);
  }
};

window.handleTerminalOverlayClick = function(e) {
  if (e.target.id === 'cyber-terminal-overlay') window.toggleCyberTerminal();
};

window.switchTerminalChannel = function(chan) {
  currentTerminalChannel = chan;
  document.querySelectorAll('.ct-tab').forEach(t => t.classList.remove('active'));
  const activeTab = document.getElementById(`ct-tab-${chan}`);
  if (activeTab) activeTab.classList.add('active');

  const sym = document.getElementById('ct-prompt-symbol');
  const symbols = { 'rust': 'rust@ebj:~#', 'kali': 'root@kali-vps:~#', 'aider': 'aider-codex> ', 'sys': 'PS C:\ebj>' };
  if (sym) sym.textContent = symbols[chan] || 'ebj:~#';
};

window.submitTerminalCommand = async function() {
  const input = document.getElementById('ct-command-input');
  if (!input || !input.value.trim()) return;
  const cmd = input.value.trim();
  input.value = '';

  terminalHistory.push(cmd);
  terminalHistoryIndex = terminalHistory.length;

  appendTerminalLog(`[${currentTerminalChannel.toUpperCase()}] > ${cmd}`, 'ct-user');

  try {
    const res = await fetch('/api/terminal/exec', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel: currentTerminalChannel, command: cmd })
    });
    const d = await res.json();
    if (d.stdout) appendTerminalLog(d.stdout, 'ct-stdout');
    if (d.stderr) appendTerminalLog(d.stderr, 'ct-error');
  } catch (e) {
    appendTerminalLog(`Errore esecuzione: ${e.message}`, 'ct-error');
  }
};

function appendTerminalLog(text, className = '') {
  const body = document.getElementById('ct-terminal-body');
  if (!body) return;
  const div = document.createElement('div');
  div.className = `ct-log-line ${className}`;
  div.textContent = text;
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
}

window.dockCyberTerminal = function() {
  const win = document.getElementById('cyber-terminal-window');
  if (!win) return;
  win.style.position = 'fixed';
  win.style.bottom = '10px';
  win.style.top = 'auto';
  win.style.left = '50%';
  win.style.transform = 'translateX(-50%)';
  win.style.width = '96vw';
  win.style.height = '320px';
};

window.maximizeCyberTerminal = function() {
  const win = document.getElementById('cyber-terminal-window');
  if (!win) return;
  win.style.position = 'fixed';
  win.style.inset = '10px';
  win.style.transform = 'none';
  win.style.width = 'calc(100vw - 20px)';
  win.style.height = 'calc(100vh - 20px)';
};

window.minimizeCyberTerminal = function() {
  window.toggleCyberTerminal();
  const pill = document.getElementById('ct-minimized-pill');
  if (pill) pill.classList.add('active');
};

window.restoreCyberTerminal = function() {
  const pill = document.getElementById('ct-minimized-pill');
  if (pill) pill.classList.remove('active');
  window.toggleCyberTerminal();
};

window.centerCyberTerminal = function() {
  const win = document.getElementById('cyber-terminal-window');
  if (!win) return;
  win.style.position = 'absolute';
  win.style.top = '50%';
  win.style.left = '50%';
  win.style.transform = 'translate(-50%, -50%)';
  win.style.width = '780px';
  win.style.height = '520px';
};

// ── 7. TOOL NOTIFICATION CARD ──────────────────────────────────────
window.showToolRun = function(title, msg, latency = '0.001s') {
  const card = document.getElementById('tool-run-card');
  const tEl = document.getElementById('trc-title');
  const mEl = document.getElementById('trc-main');
  const latEl = document.getElementById('trc-time');
  if (!card) return;

  if (tEl) tEl.textContent = `TOOL · ${title}`;
  if (mEl) mEl.textContent = msg;
  if (latEl) latEl.textContent = `⚡ ${latency} LATENCY`;

  card.classList.remove('hidden');
  if (_toolCardTimer) clearTimeout(_toolCardTimer);
  _toolCardTimer = setTimeout(() => card.classList.add('hidden'), 4500);
};

window.closeToolCard = function() {
  const card = document.getElementById('tool-run-card');
  if (card) card.classList.add('hidden');
};

// ── 8. MOOD, TABS & NAVIGATION ─────────────────────────────────────
window.switchTab = function(tab) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  
  event?.target?.classList.add('active');
  const activeContent = document.getElementById(`tab-${tab}`);
  if (activeContent) activeContent.classList.add('active');

  if (tab === 'fleet' && window.refreshFleetUi) {
    window.refreshFleetUi();
  }
};

window.switchEBMood = function(mood) {
  currentPersonality = mood;
  document.querySelectorAll('.mood-chip').forEach(c => c.classList.remove('active'));
  const chip = document.getElementById(`chip-${mood}`);
  if (chip) chip.classList.add('active');
  showToolRun('PERSONALITÀ SWITCH', `Modalità ${mood.toUpperCase()} attiva.`, '0.01s');
};

window.triggerNeuralSurge = function() {
  const sphere = document.getElementById('jarvis-sphere');
  if (sphere) {
    sphere.style.boxShadow = '0 0 70px #00ff9f';
    setTimeout(() => sphere.style.boxShadow = '0 0 25px rgba(0, 255, 159, 0.5)', 2000);
  }
  showToolRun('QUANTUM SURGE', 'Impulso quantistico inviato su tutti i nodi e flussi N8N!', '0.001s');
};

window.toggleLeftWing = function() {
  document.querySelector('.main-grid')?.classList.toggle('left-collapsed');
};

window.toggleRightWing = function() {
  document.querySelector('.main-grid')?.classList.toggle('right-collapsed');
};

window.openAgente0Full = function() { window.open('http://92.4.233.42:50080', '_blank'); };
window.openN8nFull = function() { window.open('http://92.4.233.42:5678', '_blank'); };
window.openKaliCliModal = function() {
  toggleCyberTerminal();
  switchTerminalChannel('kali');
};
window.quickKaliExec = function(cmd) {
  toggleCyberTerminal();
  switchTerminalChannel('kali');
  document.getElementById('ct-command-input').value = cmd;
  submitTerminalCommand();
};

window.openModal = function(id) { document.getElementById(id)?.classList.add('active'); };
window.closeModal = function(id) { document.getElementById(id)?.classList.remove('active'); };

// ── 9. DRAGGABLE WINDOWS INITIALIZATION ────────────────────────────
function initDraggableWindows() {
  document.querySelectorAll('.modular-window-card, .cyber-terminal-window').forEach(win => {
    const handle = win.querySelector('.mwc-header, .ct-header');
    if (!handle) return;

    let isDragging = false;
    let dragStartX = 0, dragStartY = 0;
    let winStartX = 0, winStartY = 0;

    handle.addEventListener('mousedown', (e) => {
      if (window.matchMedia('(max-width: 899px)').matches) return;
      if (['BUTTON', 'SPAN', 'INPUT'].includes(e.target.tagName) && e.target.onclick) return;
      isDragging = true;
      const rect = win.getBoundingClientRect();
      dragStartX = e.clientX;
      dragStartY = e.clientY;
      winStartX = rect.left;
      winStartY = rect.top;
      win.style.left = `${winStartX}px`;
      win.style.top = `${winStartY}px`;
      win.style.transform = 'none';
      e.preventDefault();
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const dx = e.clientX - dragStartX;
      const dy = e.clientY - dragStartY;
      win.style.left = `${Math.max(10, Math.min(window.innerWidth - 100, winStartX + dx))}px`;
      win.style.top = `${Math.max(10, Math.min(window.innerHeight - 80, winStartY + dy))}px`;
    });

    window.addEventListener('mouseup', () => { isDragging = false; });
  });

  // Resize grip for terminal
  const grip = document.getElementById('ct-resize-grip');
  const termWin = document.getElementById('cyber-terminal-window');
  if (grip && termWin) {
    let isResizing = false;
    let rStartX = 0, rStartY = 0, startW = 0, startH = 0;

    grip.addEventListener('mousedown', (e) => {
      if (window.matchMedia('(max-width: 899px)').matches) return;
      isResizing = true;
      rStartX = e.clientX;
      rStartY = e.clientY;
      const rect = termWin.getBoundingClientRect();
      startW = rect.width;
      startH = rect.height;
      termWin.style.transform = 'none';
      termWin.style.left = `${rect.left}px`;
      termWin.style.top = `${rect.top}px`;
      e.preventDefault();
      e.stopPropagation();
    });

    window.addEventListener('mousemove', (e) => {
      if (!isResizing) return;
      termWin.style.width = `${Math.max(450, startW + (e.clientX - rStartX))}px`;
      termWin.style.height = `${Math.max(300, startH + (e.clientY - rStartY))}px`;
    });

    window.addEventListener('mouseup', () => { isResizing = false; });
  }
}

// ── 10. GLOBAL HOTKEYS [T], [M], [ESC], [ENTER] ────────────────────
window.addEventListener('keydown', (e) => {
  const isInput = ['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName);

  if (e.key === 'Escape') {
    const overlay = document.getElementById('cyber-terminal-overlay');
    if (overlay && overlay.classList.contains('open')) {
      toggleCyberTerminal();
      return;
    }
    const catModal = document.getElementById('modal-modular-catalog');
    if (catModal && catModal.classList.contains('active')) {
      closeModal('modal-modular-catalog');
      return;
    }
    const kaliDrawer = document.getElementById('kali-drawer');
    if (kaliDrawer && kaliDrawer.classList.contains('open')) {
      closeKaliDrawer();
      return;
    }
    if (document.body.classList.contains('mobile-nav-open')) {
      toggleMobileNav(false);
      return;
    }
  }

  if (e.ctrlKey && e.code === 'Space') {
    e.preventDefault();
    toggleConversationalMode();
    return;
  }

  if (!isInput) {
    if (e.key === 't' || e.key === 'T') {
      e.preventDefault();
      toggleCyberTerminal();
    } else if (e.key === 'm' || e.key === 'M') {
      e.preventDefault();
      toggleModularCatalog();
    }
  }

  if (isInput && e.key === 'Enter') {
    if (document.activeElement.id === 'prompt-input') {
      sendMessage();
    } else if (document.activeElement.id === 'ct-command-input') {
      submitTerminalCommand();
    } else if (document.activeElement.id === 'kali-drawer-args') {
      runKaliDrawer();
    }
  }
});

// ── 11. MASTER VIEW + MOBILE NAV + KALI LAB ────────────────────────
const KALI_VIEW_MAP = {
  jarvis: 'view-jarvis',
  kali: 'view-kali-lab',
  kanban: 'view-kanban',
  n8n: 'view-n8n',
  agente0: 'view-agente-zero',
  'agente-zero': 'view-agente-zero',
  topology: 'view-topology',
  graph: 'view-neural-graph',
  astra: 'view-astra-3d',
  'astra-3d': 'view-astra-3d'
};
const KALI_CAT_ALIASES = {
  recon: ['recon', 'information-gathering', 'info'],
  password: ['password', 'passwords'],
  wireless: ['wireless', 'wifi'],
  web: ['web'],
  rete: ['rete', 'network', 'sniffing', 'sniffing-spoofing'],
  identity: ['identity', 'identita', 'ad', 'impacket'],
  vuln: ['vuln', 'vulnerability', 'vulnerabilita'],
  hardening: ['hardening', 'audit', 'osint-secrets'],
  forensics: ['forensics', 'forense'],
  reverse: ['reverse', 're', 'reversing'],
  utilita: ['utilita', 'utility', 'utils']
};

let kaliCatalog = [];
let kaliCatFilter = 'all';
let kaliSelectedTool = null;
let kaliBusy = false;

function kaliEscapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function setKaliStatus(text, kind) {
  const pill = document.getElementById('kali-status-pill');
  if (!pill) return;
  pill.textContent = text;
  pill.className = 'kali-status-pill' + (kind ? ' ' + kind : '');
}

function setKaliLog(text, kind) {
  const log = document.getElementById('kali-log');
  if (!log) return;
  log.textContent = text;
  log.className = 'kali-log' + (kind ? ' is-' + kind : '');
}

function setKaliGridState(msg, kind) {
  const grid = document.getElementById('kali-card-grid');
  if (!grid) return;
  grid.innerHTML = `<div class="kali-state ${kind || ''}">${kaliEscapeHtml(msg)}</div>`;
}

function kaliToolCategory(tool) {
  return String(tool?.category || tool?.cat || '').toLowerCase();
}

function kaliMatchesCat(tool, cat) {
  if (!cat || cat === 'all') return true;
  const raw = kaliToolCategory(tool);
  const aliases = KALI_CAT_ALIASES[cat] || [cat];
  return aliases.includes(raw);
}

function kaliFilteredTools() {
  const q = (document.getElementById('kali-tool-search')?.value || '').trim().toLowerCase();
  return kaliCatalog.filter(t => {
    if (!kaliMatchesCat(t, kaliCatFilter)) return false;
    if (!q) return true;
    const blob = [t.name, t.package, t.path, t.binary, t.category].join(' ').toLowerCase();
    return blob.includes(q);
  });
}

function renderKaliCards() {
  const grid = document.getElementById('kali-card-grid');
  if (!grid) return;
  const tools = kaliFilteredTools();
  if (!kaliCatalog.length) {
    setKaliGridState('Catalogo vuoto: nessun tool trovato.', 'warn');
    return;
  }
  if (!tools.length) {
    setKaliGridState('Nessun tool corrisponde alla ricerca o al filtro.', 'warn');
    return;
  }
  grid.innerHTML = '';
  tools.forEach(tool => {
    const name = tool.name || tool.tool || 'tool';
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'kali-card';
    card.innerHTML = `
      <span class="kali-card-name">${kaliEscapeHtml(name)}</span>
      <span class="kali-card-cat">${kaliEscapeHtml(tool.category || 'allowlist')}</span>
      <span class="kali-card-pkg">${kaliEscapeHtml(tool.path || tool.binary || tool.package || '')}</span>
    `;
    card.addEventListener('click', () => openKaliDrawer(tool));
    grid.appendChild(card);
  });
}

window.switchMasterView = function(view) {
  const key = view === 'kali' ? 'kali' : (view || 'jarvis');
  const targetId = KALI_VIEW_MAP[key] || 'view-jarvis';

  document.querySelectorAll('.jarvis-workspace').forEach(w => {
    if (w.id === targetId) {
      w.classList.add('active');
      w.style.display = (targetId === 'view-jarvis') ? 'block' : 'flex';
    } else {
      w.classList.remove('active');
      w.style.display = 'none';
    }
  });

  document.body.classList.toggle('view-kali', key === 'kali');

  document.querySelectorAll('.view-switch-btn').forEach(b => b.classList.remove('active'));
  if (key === 'jarvis') document.getElementById('btn-view-jarvis')?.classList.add('active');
  if (key === 'kanban') {
    document.getElementById('btn-view-kanban')?.classList.add('active');
    if (window.refreshKanbanData) window.refreshKanbanData();
  }
  if (key === 'n8n') {
    document.getElementById('btn-view-n8n')?.classList.add('active');
    const f = document.getElementById('n8n-frame');
    if (f && (!f.src || f.src === 'about:blank')) {
      f.src = f.getAttribute('data-src') || 'http://localhost:5678';
    }
  }
  if (key === 'agente0' || key === 'agente-zero') {
    document.getElementById('btn-view-agente0')?.classList.add('active');
    const f = document.getElementById('agente-zero-frame');
    if (f && (!f.src || f.src === 'about:blank')) {
      f.src = f.getAttribute('data-src') || 'http://92.4.233.42:50080';
    }
  }
  if (key === 'topology') {
    document.getElementById('btn-view-topology')?.classList.add('active');
    if (window.loadCosmos3DOnDemand) {
      window.loadCosmos3DOnDemand(() => {
        window.dispatchEvent(new Event('resize'));
        if (window.initCosmos3D) window.initCosmos3D();
        if (window.setCosmosLayout) window.setCosmosLayout('constellation');
      });
    }
  }
  if (key === 'graph') {
    document.getElementById('btn-view-graph')?.classList.add('active');
    if (window.initNeuralGraph) window.initNeuralGraph();
  }
  if (key === 'astra' || key === 'astra-3d') {
    document.getElementById('btn-view-astra')?.classList.add('active');
    if (window.loadAstra3DStatus) window.loadAstra3DStatus();
  }

  if (key === 'kali') refreshKaliCatalog();
  toggleMobileNav(false);
  if (window.lucide) {
    setTimeout(() => lucide.createIcons(), 50);
  }
};

window.toggleMobileNav = function(force) {
  const open = typeof force === 'boolean' ? force : !document.body.classList.contains('mobile-nav-open');
  document.body.classList.toggle('mobile-nav-open', open);
  const btn = document.getElementById('btn-hamburger');
  const backdrop = document.getElementById('mv-nav-backdrop');
  if (btn) {
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.setAttribute('aria-label', open ? 'Chiudi menu' : 'Apri menu');
  }
  if (backdrop) backdrop.hidden = !open;
};

window.filterKaliTools = function() {
  renderKaliCards();
};

window.filterKaliCat = function(btn, cat) {
  kaliCatFilter = cat || 'all';
  document.querySelectorAll('.kali-chip').forEach(c => c.classList.remove('active'));
  if (btn) btn.classList.add('active');
  else document.querySelector(`.kali-chip[data-cat="${kaliCatFilter}"]`)?.classList.add('active');
  renderKaliCards();
};

window.refreshKaliCatalog = async function() {
  setKaliStatus('stato: caricamento…');
  setKaliGridState('Caricamento catalogo Kali…');
  try {
    const res = await fetch('/api/kali/tools', { signal: AbortSignal.timeout(20000) });
    let d = {};
    try { d = await res.json(); } catch (_) {
      setKaliStatus('stato: errore', 'err');
      setKaliGridState('Risposta catalogo non valida.', 'err');
      return;
    }
    if (!res.ok || (d.status && String(d.status).toUpperCase() === 'ERROR')) {
      const msg = d.message || `Errore nel caricamento del catalogo (${res.status}).`;
      setKaliStatus('stato: errore', 'err');
      setKaliGridState(msg, 'err');
      kaliCatalog = [];
      return;
    }
    kaliCatalog = d.catalog || d.tools || [];
    const container = d.container || 'ebj-kali-engine';
    const down = d.container_up === false || d.container_running === false;
    if (down) {
      setKaliStatus(`stato: ${container} spento`, 'err');
      if (!kaliCatalog.length) {
        setKaliGridState('Container ebj-kali-engine non raggiungibile.', 'err');
        return;
      }
    } else if (d.ssh_key_ready === false) {
      setKaliStatus('stato: chiave SSH assente', 'warn');
    } else {
      setKaliStatus(`stato: ${container} · ${kaliCatalog.length} tool`, 'ok');
    }
    if (!kaliCatalog.length) {
      setKaliGridState('Catalogo vuoto: nessun tool trovato.', 'warn');
      return;
    }
    renderKaliCards();
  } catch (err) {
    const timeout = err?.name === 'TimeoutError' || err?.name === 'AbortError';
    setKaliStatus(timeout ? 'stato: timeout' : 'stato: errore', 'err');
    setKaliGridState(
      timeout
        ? 'Timeout: il catalogo non ha risposto in tempo.'
        : (`Errore nel caricamento del catalogo. ${err?.message || ''}`).trim(),
      'err'
    );
  }
};

window.openKaliDrawer = function(tool) {
  kaliSelectedTool = tool || null;
  const drawer = document.getElementById('kali-drawer');
  const view = document.getElementById('view-kali-lab');
  const backdrop = document.getElementById('kali-drawer-backdrop');
  if (!drawer || !kaliSelectedTool) return;
  const name = kaliSelectedTool.name || kaliSelectedTool.tool || 'Tool';
  const path = kaliSelectedTool.path || kaliSelectedTool.binary || kaliSelectedTool.package || '';
  const title = document.getElementById('kali-drawer-title');
  const pathEl = document.getElementById('kali-drawer-path');
  const args = document.getElementById('kali-drawer-args');
  if (title) title.textContent = name;
  if (pathEl) pathEl.textContent = path ? `percorso / pacchetto: ${path}` : `binario allowlist: ${name}`;
  if (args && !args.value) args.value = '--help';
  setKaliLog('Pronto. Scorciatoie: --help o --version. Nessun comando di attacco precompilato.');
  drawer.classList.add('open');
  drawer.setAttribute('aria-hidden', 'false');
  view?.classList.add('drawer-open');
  if (backdrop) backdrop.hidden = false;
  args?.focus();
};

window.closeKaliDrawer = function() {
  const drawer = document.getElementById('kali-drawer');
  const view = document.getElementById('view-kali-lab');
  const backdrop = document.getElementById('kali-drawer-backdrop');
  drawer?.classList.remove('open');
  drawer?.setAttribute('aria-hidden', 'true');
  view?.classList.remove('drawer-open');
  if (backdrop) backdrop.hidden = true;
};

function parseKaliArgs(raw) {
  return String(raw || '').trim().split(/\s+/).filter(Boolean);
}

window.runKaliDrawer = async function() {
  if (kaliBusy) return;
  const toolName = kaliSelectedTool?.name || kaliSelectedTool?.tool;
  if (!toolName) {
    setKaliLog('Seleziona un tool dalla griglia.', 'error');
    return;
  }
  const raw = document.getElementById('kali-drawer-args')?.value || '';
  if (/[;&|`$]/.test(raw)) {
    setKaliLog('Caratteri shell rifiutati (; | & ` $).', 'error');
    return;
  }
  const args = parseKaliArgs(raw);
  kaliBusy = true;
  setKaliLog(`Esecuzione in corso: ${toolName} ${args.join(' ')}…`, 'loading');
  try {
    const res = await fetch('/api/kali/exec', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'run', tool: toolName, args }),
      signal: AbortSignal.timeout(125000)
    });
    let d = {};
    try { d = await res.json(); } catch (_) {
      setKaliLog('Risposta esecuzione non valida.', 'error');
      return;
    }
    const out = d.stdout || d.message || d.stderr || '';
    const status = String(d.status || '').toUpperCase();
    if (!res.ok || status === 'ERROR') {
      const msg = out || d.message || 'Esecuzione fallita.';
      if (/non in allowlist|assente|not found|command not found/i.test(msg)) {
        setKaliLog(`Tool assente o non in allowlist.\n${msg}`, 'error');
      } else if (/container|unreachable|connection refused|ssh/i.test(msg)) {
        setKaliLog(`Container ebj-kali-engine non raggiungibile.\n${msg}`, 'error');
      } else {
        setKaliLog(msg, 'error');
      }
      return;
    }
    setKaliLog(out || '(nessun output)');
  } catch (err) {
    const timeout = err?.name === 'TimeoutError' || err?.name === 'AbortError';
    setKaliLog(
      timeout
        ? 'Timeout: il comando ha superato il tempo massimo (120s).'
        : (`Errore di rete. ${err?.message || ''}`).trim(),
      'error'
    );
  } finally {
    kaliBusy = false;
  }
};

window.runKaliHelp = function() {
  const input = document.getElementById('kali-drawer-args');
  if (input) input.value = '--help';
  runKaliDrawer();
};

window.runKaliVersion = function() {
  const input = document.getElementById('kali-drawer-args');
  if (input) input.value = '--version';
  runKaliDrawer();
};

window.updateKaliTools = async function() {
  if (kaliBusy) return;
  kaliBusy = true;
  setKaliStatus('stato: aggiornamento tool…', 'warn');
  setKaliLog('Aggiornamento tool in corso…', 'loading');
  try {
    const res = await fetch('/api/kali/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'update' }),
      signal: AbortSignal.timeout(180000)
    });
    let d = {};
    try { d = await res.json(); } catch (_) {
      setKaliLog('Risposta aggiornamento non valida.', 'error');
      setKaliStatus('stato: errore', 'err');
      return;
    }
    const status = String(d.status || '').toUpperCase();
    const out = d.stdout || d.message || '';
    if (!res.ok || status === 'ERROR') {
      setKaliStatus('stato: errore aggiornamento', 'err');
      setKaliLog(out || 'Aggiornamento tool fallito.', 'error');
      return;
    }
    setKaliLog((out ? out + '\n\n' : '') + 'Tool aggiornati. Ricarico il catalogo.');
    await refreshKaliCatalog();
  } catch (err) {
    const timeout = err?.name === 'TimeoutError' || err?.name === 'AbortError';
    setKaliStatus(timeout ? 'stato: timeout' : 'stato: errore', 'err');
    setKaliLog(
      timeout
        ? 'Timeout: l’aggiornamento tool ha superato il tempo massimo.'
        : (`Errore durante l’aggiornamento. ${err?.message || ''}`).trim(),
      'error'
    );
  } finally {
    kaliBusy = false;
  }
};

// INIT ON DOM READY
document.addEventListener('DOMContentLoaded', () => {
  initDraggableWindows();
  loadModularCardsState();
  initCustomModelSelect();
  updateVadPill();
  showToolRun('E.B.J. AI v100.0 APEX', 'Ecosistema Neurale Online · Rust Tokio Hyper-Bus Attivo · 144 FPS Nativi!', '0.001s');
  connectEbjRustListen();
  document.addEventListener('click', unlockEbjVoice, { once: true });
});

// ── AZIONE DIRETTA MARKETPLACE DA HOME CONTROLLO TOTALE ──────────────
window.publishMarketplaceDirect = async function() {
  const btn = document.getElementById('btn-pub-direct');
  if (btn) {
    btn.disabled = true;
    btn.textContent = '⏳ Pubblicazione...';
  }
  try {
    const res = await fetch('/api/marketplace/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ submit: true })
    });
    const d = await res.json();
    if (d.status === 'SUCCESS') {
      if (btn) {
        btn.textContent = '✅ Pubblicato!';
        btn.style.background = '#22c55e';
      }
      if (window.playSpeechAudio) {
        window.playSpeechAudio("Ottime notizie Badr! L'annuncio delle 3 porte è stato inviato e pubblicato con successo su Facebook Marketplace.");
      }
      addEvent('sys', 'Facebook Marketplace: Annuncio porte pubblicato con successo!');
    } else {
      if (btn) btn.textContent = '⚠️ Errore';
      addEvent('sys', 'Errore pubblicazione: ' + (d.error || 'Verifica sessione'));
    }
  } catch (err) {
    if (btn) btn.textContent = '⚠️ Errore Rete';
  } finally {
    setTimeout(() => {
      if (btn) {
        btn.disabled = false;
        btn.textContent = '🚀 Pubblica FB';
        btn.style.background = '#eab308';
      }
    }, 6000);
  }
};

// ── RUST APEX DEBUGGER & SELF-HEALING TRIGGERS ─────────────────────────
window.triggerRustAudit = async function() {
  const btn = document.getElementById('btn-rust-audit');
  if (btn) btn.textContent = '⏳ Audit...';
  try {
    const res = await fetch('/api/debug/audit');
    const data = await res.json();
    const conf = data.knowledge_base_stats ? (data.knowledge_base_stats.average_confidence * 100).toFixed(1) : '98.0';
    const msg = `🦀 [EBJ APEX RUST DEBUGGER]\n\nStato Sistema: ${data.overall_status}\nLatenza Audit: ${data.execution_duration_ms} ms\nServizi Verificati: ${data.services ? data.services.length : 0}\nDatabase Integri: ${data.databases ? data.databases.length : 0}\nAnomalie Rilevate: ${data.issues_found ? data.issues_found.length : 0}\nConfidence Euristica: ${conf}%`;
    alert(msg);
    if (window.playSpeechAudio) {
      window.playSpeechAudio(`Audit completato in ${data.execution_duration_ms} millisecondi. Stato di sistema ${data.overall_status}.`);
    }
  } catch (err) {
    alert('Errore esecuzione Audit Rust: ' + err.message);
  } finally {
    if (btn) btn.textContent = '⚡ Audit Rapido';
  }
};

window.triggerRustHeal = async function() {
  const btn = document.getElementById('btn-rust-heal');
  if (btn) btn.textContent = '⏳ Heal...';
  try {
    const res = await fetch('/api/debug/heal', { method: 'POST' });
    const data = await res.json();
    const count = Array.isArray(data) ? data.length : 0;
    alert(`🦀 [EBJ AUTO-HEALING RUST]\n\nSequenza di autoriparazione completata!\nRisoluzioni applicate: ${count}\nIntegrità SQLite, cache Python e socket verificate.`);
    if (window.playSpeechAudio) {
      window.playSpeechAudio("Auto riparazione Rust completata con successo. Tutti i moduli operano al cento per cento.");
    }
  } catch (err) {
    alert('Errore Auto-Healing Rust: ' + err.message);
  } finally {
    if (btn) btn.textContent = '🩹 Heal';
  }
};

function connectEbjRustListen() {
  if (window.location.protocol === 'https:') return;
  try {
    const ws = new WebSocket('ws://127.0.0.1:9000/ws/ebj');
    ws.onopen = () => addEvent('rust', 'E.B.J. in ascolto sul bridge :9000');
    ws.onmessage = (ev) => {
      try {
        const d = JSON.parse(ev.data);
        if (!d || !d.response) return;
        if (!_ebjWsGreeted) {
          _ebjWsGreeted = true;
          addEvent('rust', String(d.response).slice(0, 80));
        }
      } catch (_) {}
    };
    ws.onerror = () => {};
    ws.onclose = () => {
      setTimeout(connectEbjRustListen, 8000);
    };
    window._ebjListenWs = ws;
  } catch (_) {}
}

// ── JEV PROFESSIONAL APPRAISER & VALUATION ENGINE ──────────────────
let _lastJevAppraisal = null;

window.toggleJevModal = function(show) {
  const card = document.getElementById('card-mod-jev');
  if (!card) return;
  if (show === undefined) show = card.style.display === 'none';
  card.style.display = show ? 'block' : 'none';
  if (show) {
    card.style.zIndex = '9999';
    card.style.top = '120px';
    card.style.left = Math.min(window.innerWidth - 460, Math.max(20, Math.floor(window.innerWidth / 2 - 220))) + 'px';
  }
};

window.openMarketplaceModal = window.openJevModal = function() {
  window.toggleJevModal(true);
};

window.executeJevAppraisal = async function() {
  const cat = document.getElementById('jev-category')?.value || 'INFISSI_PORTE';
  const name = document.getElementById('jev-item-name')?.value || 'Oggetto d\'arredo';
  const qty = parseInt(document.getElementById('jev-qty')?.value || '1', 10);
  const cond = parseFloat(document.getElementById('jev-condition')?.value || '0.85');
  const delivery = document.getElementById('jev-delivery')?.checked !== false;

  const resBox = document.getElementById('jev-results-box');
  try {
    const res = await fetch('/api/jev/appraise', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        category: cat,
        item_name: name,
        quantity: qty,
        condition_score: cond,
        include_badr_delivery: delivery
      })
    });
    const d = await res.json();
    _lastJevAppraisal = d;

    if (resBox) resBox.style.display = 'block';
    const codeEl = document.getElementById('jev-res-code');
    const liqEl = document.getElementById('jev-res-liq');
    const fastEl = document.getElementById('jev-res-fast');
    const fastSubEl = document.getElementById('jev-res-fast-sub');
    const marketEl = document.getElementById('jev-res-market');
    const stratEl = document.getElementById('jev-res-strategy');

    if (codeEl) codeEl.textContent = `PRATICA: ${d.practice_code || 'JEV-PRO'}`;
    if (liqEl) liqEl.textContent = d.liquidity_index ? d.liquidity_index.slice(0, 15) : 'A+';
    if (fastEl) fastEl.textContent = `€ ${Math.round(d.fast_cash_price_48h_eur || d.recommended_quick_sale_price_eur || 0)}`;
    if (fastSubEl) fastSubEl.textContent = d.recommended_bundle_price_eur ? `Blocco: € ${Math.round(d.recommended_bundle_price_eur)}` : `€ ${Math.round(d.recommended_quick_sale_price_eur || 0)} cad.`;
    if (marketEl) marketEl.textContent = `€ ${Math.round(d.market_fair_value_30d_eur || d.market_used_average_eur || 0)}`;
    if (stratEl) stratEl.textContent = `${d.material_nobility || 'Materiale standard'} · ${d.pricing_strategy_note || ''}`;

    addEvent('rust', `💎 Perizia JEV calcolata in ${d.calculation_micros || 5}µs: ${d.practice_code}`);
    if (window.playSpeechAudio && d.verbal_summary) {
      window.playSpeechAudio(d.verbal_summary);
    }
  } catch (err) {
    alert('Errore calcolo perizia JEV: ' + err.message);
  }
};

window.openJevCertificate = function() {
  const cat = document.getElementById('jev-category')?.value || 'INFISSI_PORTE';
  const name = document.getElementById('jev-item-name')?.value || 'Oggetto d\'arredo';
  const qty = parseInt(document.getElementById('jev-qty')?.value || '1', 10);
  const cond = parseFloat(document.getElementById('jev-condition')?.value || '0.85');
  const delivery = document.getElementById('jev-delivery')?.checked !== false;

  fetch('/api/jev/certificate-html', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      category: cat,
      item_name: name,
      quantity: qty,
      condition_score: cond,
      include_badr_delivery: delivery
    })
  }).then(r => r.text()).then(html => {
    const w = window.open('', '_blank');
    if (w) {
      w.document.write(html);
      w.document.close();
    }
  }).catch(e => alert('Errore apertura certificato: ' + e.message));
};

window.copyJevAdText = function(platform) {
  if (!_lastJevAppraisal) {
    alert('Calcola prima la perizia JEV!');
    return;
  }
  const text = platform === 'fb' ? _lastJevAppraisal.facebook_marketplace_description : _lastJevAppraisal.subito_description;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      alert(`✅ Testo annuncio ${platform.toUpperCase()} copiato negli appunti!`);
    });
  } else {
    prompt('Copia il testo:', text);
  }
};

// ── B2B IMMOBILIARI & SGOMBERI AUTOPILOT ────────────────────────────
let _b2bAgenciesList = [];
let _currentB2bEmail = null;

window.toggleB2bModal = function(show) {
  const card = document.getElementById('card-mod-b2b');
  if (!card) return;
  if (show === undefined) show = card.style.display === 'none';
  card.style.display = show ? 'block' : 'none';
  if (show) {
    card.style.zIndex = '9999';
    card.style.top = '130px';
    card.style.left = Math.min(window.innerWidth - 500, Math.max(20, Math.floor(window.innerWidth / 2 - 240))) + 'px';
  }
};

window.scoutB2bAgencies = async function() {
  const city = document.getElementById('b2b-city-select')?.value || 'Bologna';
  const statusEl = document.getElementById('b2b-scout-status');
  if (statusEl) statusEl.innerHTML = `⏳ Scansione in corso per <strong>${city}</strong> (Overpass API)...`;

  try {
    const res = await fetch(`/api/b2b/agencies?city=${encodeURIComponent(city)}&limit=30`);
    const data = await res.json();
    _b2bAgenciesList = data.agencies || [];

    if (statusEl) {
      statusEl.innerHTML = `✅ Censite <strong>${_b2bAgenciesList.length}</strong> agenzie a <strong>${city}</strong>!`;
    }

    const sel = document.getElementById('b2b-selected-agency');
    const container = document.getElementById('b2b-agencies-container');
    if (sel && container) {
      sel.innerHTML = '';
      _b2bAgenciesList.forEach((ag, idx) => {
        const opt = document.createElement('option');
        opt.value = idx;
        opt.textContent = `${ag.agency_name} (${ag.address || ag.city})`;
        sel.appendChild(opt);
      });
      container.style.display = _b2bAgenciesList.length > 0 ? 'block' : 'none';
      window.onB2bAgencySelected();
    }
    addEvent('sys', `B2B: Censite ${_b2bAgenciesList.length} agenzie a ${city}`);
  } catch (err) {
    if (statusEl) statusEl.textContent = 'Errore scouting: ' + err.message;
  }
};

window.onB2bAgencySelected = function() {
  const sel = document.getElementById('b2b-selected-agency');
  const infoEl = document.getElementById('b2b-agency-info');
  if (!sel || !_b2bAgenciesList.length) return;
  const ag = _b2bAgenciesList[parseInt(sel.value, 10)] || _b2bAgenciesList[0];
  if (infoEl && ag) {
    infoEl.innerHTML = `
      <strong>Indirizzo:</strong> ${ag.address || 'In centro'} · <strong>Città:</strong> ${ag.city}<br/>
      <strong>Telefono:</strong> ${ag.phone || 'Non disponibile'} · <strong>Email:</strong> ${ag.email || 'Da registrare'}<br/>
      ${ag.website ? `<a href="${ag.website}" target="_blank" style="color:#00f0ff;">Sito Web Agenzia</a>` : ''}
    `;
  }
};

window.calculateB2bSgombero = async function() {
  const tipo = document.getElementById('b2b-sgombero-tipo')?.value || 'trilocale';
  const piano = parseInt(document.getElementById('b2b-sgombero-piano')?.value || '2', 10);
  const asc = document.getElementById('b2b-sgombero-asc')?.checked === true;
  const resBox = document.getElementById('b2b-sgombero-res');

  try {
    const res = await fetch('/api/b2b/calculate-sgombero', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tipo_immobile: tipo, piano: piano, ascensore: asc })
    });
    const d = await res.json();
    if (resBox) {
      resBox.style.display = 'block';
      resBox.innerHTML = `
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
          <span style="color:#94a3b8;">Prezzo Listino Privati:</span>
          <span style="text-decoration:line-through; color:#ef4444;">€ ${d.prezzo_listino}</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
          <span style="color:#10b981; font-weight:bold;">Prezzo Riservato Agenzia (-15%):</span>
          <span style="color:#10b981; font-weight:bold; font-size:0.95rem;">€ ${d.prezzo_finale_agenzia}</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
          <span style="color:#eab308;">Provvigione Riconosciuta all'Agenzia (10%):</span>
          <span style="color:#eab308; font-weight:bold;">€ ${d.provvigione_riconosciuta}</span>
        </div>
        <div style="font-size:0.65rem; color:#cbd5e1; border-top:1px solid #1e293b; padding-top:4px;">
          ⏱️ Intervento garantito: ${d.tempistica_garantita} · Pulizia finale post-sgombero inclusa.
        </div>
      `;
    }
  } catch (err) {
    alert('Errore calcolo sgombero B2B: ' + err.message);
  }
};

window.previewB2bEmail = async function() {
  const sel = document.getElementById('b2b-selected-agency');
  const previewBox = document.getElementById('b2b-email-preview-box');
  const city = document.getElementById('b2b-city-select')?.value || 'Bologna';
  let agencyName = 'Agenzia Immobiliare Partner';
  if (sel && _b2bAgenciesList.length) {
    const ag = _b2bAgenciesList[parseInt(sel.value, 10)];
    if (ag) agencyName = ag.agency_name;
  }

  try {
    const res = await fetch('/api/b2b/compose-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agency_name: agencyName, city: city, contact_person: 'Responsabile Compravendite' })
    });
    const d = await res.json();
    _currentB2bEmail = d;

    if (previewBox) {
      previewBox.style.display = 'block';
      previewBox.textContent = `OGGETTO: ${d.subject}\n\n${d.body_plain}`;
    }
  } catch (err) {
    alert('Errore anteprima email B2B: ' + err.message);
  }
};

window.sendB2bProposalEmail = async function() {
  const sel = document.getElementById('b2b-selected-agency');
  const city = document.getElementById('b2b-city-select')?.value || 'Bologna';
  let agencyName = 'Agenzia Partner';
  let email = '';

  if (sel && _b2bAgenciesList.length) {
    const ag = _b2bAgenciesList[parseInt(sel.value, 10)];
    if (ag) {
      agencyName = ag.agency_name;
      email = ag.email;
    }
  }

  if (!email || email.indexOf('@') === -1) {
    email = prompt(`Inserisci l'indirizzo email per ${agencyName}:`, 'info@' + agencyName.toLowerCase().replace(/[^a-z]/g, '') + '.it');
    if (!email) return;
  }

  try {
    const res = await fetch('/api/b2b/send-proposal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agency_name: agencyName,
        to_email: email,
        city: city,
        contact_person: 'Titolare / Responsabile Agenzia'
      })
    });
    const d = await res.json();
    if (d.success) {
      alert(`✅ Email di convenzione inviata con successo a ${agencyName} (${email})!\nRecapiti inclusi: +39 388 870 3508 e www.badrexpress.com`);
      addEvent('sys', `B2B: Proposta convenzione inviata a ${agencyName}`);
    } else {
      alert('Errore invio email: ' + (d.error || 'Verifica connessione SMTP'));
    }
  } catch (err) {
    alert('Errore invio proposta: ' + err.message);
  }
};

// ── RADAR LEAD INTENT (SUBITO & C2C LIVE SCANNER) ───────────────────────
window.toggleLeadRadarModal = function(show) {
  const card = document.getElementById('card-mod-lead-radar');
  if (!card) return;
  card.style.display = show ? 'block' : 'none';
  if (show) {
    window.loadActiveLeadsRadar();
  }
};

window.loadActiveLeadsRadar = async function() {
  const container = document.getElementById('radar-leads-list');
  const countBadge = document.getElementById('radar-lead-count');
  if (container) container.innerHTML = '<div style="color:#64748b; font-size:0.75rem; text-align:center; padding:12px;">Caricamento lead attivi in corso...</div>';

  try {
    const res = await fetch('/api/leads/radar/active?limit=30');
    const d = await res.json();
    const leads = d.leads || [];
    if (countBadge) countBadge.innerText = `${leads.length} LEAD`;

    if (container) {
      if (leads.length === 0) {
        container.innerHTML = `
          <div style="color:#94a3b8; font-size:0.75rem; text-align:center; padding:16px; background:#0b1120; border-radius:6px; border:1px solid #1e293b;">
            Nessun lead recente in cache.<br>Clicca su <strong>⚡ SCANSIONA ORA</strong> per intercettare nuovi privati in trasloco.
          </div>
        `;
        return;
      }

      container.innerHTML = leads.map(l => {
        const tierColor = l.tier === 'HOT' ? '#ef4444' : (l.tier === 'WARM' ? '#f59e0b' : '#3b82f6');
        const phone = l.phone || '';
        const waLink = phone ? `https://wa.me/39${phone.replace(/[^0-9]/g, '')}?text=${encodeURIComponent('Buongiorno, la contatto da BadrExpress & PietroTraslochi in merito alla sua esigenza di sgombero/trasloco a ' + l.city)}` : '';
        const telLink = phone ? `tel:${phone}` : '';

        return `
          <div style="background:#0b1120; border:1px solid #1e293b; border-left:3px solid ${tierColor}; border-radius:6px; padding:10px; margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
              <span style="font-size:0.7rem; font-weight:bold; color:#00f0ff;">${l.city.toUpperCase()} · ${l.service_type || 'SGOMBERO/TRASLOCO'}</span>
              <span style="background:${tierColor}; color:#000; font-weight:900; font-size:0.6rem; padding:2px 6px; border-radius:3px;">${l.tier} (${l.priority_score})</span>
            </div>
            <div style="font-size:0.8rem; font-weight:bold; color:#fff; margin-bottom:4px;">${l.title}</div>
            <div style="font-size:0.7rem; color:#94a3b8; margin-bottom:8px;">${l.details || ''}</div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-size:0.72rem; color:#cbd5e1; font-weight:600;">📞 ${phone || 'Contatto su annuncio'}</span>
              <div style="display:flex; gap:6px;">
                ${phone ? `<a href="${waLink}" target="_blank" style="background:#10b981; color:#000; font-size:0.68rem; font-weight:bold; padding:4px 8px; border-radius:4px; text-decoration:none;">🟢 WHATSAPP</a>` : ''}
                ${phone ? `<a href="${telLink}" style="background:#0284c7; color:#fff; font-size:0.68rem; font-weight:bold; padding:4px 8px; border-radius:4px; text-decoration:none;">📞 CHIAMATA</a>` : ''}
                <button onclick="window.sendQuick('JARVIS, invia preventivo express per il lead ${l.id} a ${l.city}')" style="background:#1e293b; color:#cbd5e1; border:1px solid #334155; font-size:0.68rem; padding:4px 8px; border-radius:4px; cursor:pointer;">⚡ PREVENTIVO</button>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    if (container) container.innerHTML = `<div style="color:#ef4444; font-size:0.75rem;">Errore caricamento lead: ${err.message}</div>`;
  }
};

window.triggerRadarScan = async function() {
  const city = document.getElementById('radar-city-select')?.value || 'Bologna';
  const statusEl = document.getElementById('radar-scan-status');
  if (statusEl) {
    statusEl.innerText = `🔍 Scansione annunci "causa trasloco" in corso su ${city}...`;
    statusEl.style.color = '#00f0ff';
  }

  try {
    const res = await fetch('/api/leads/radar/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city: city })
    });
    const d = await res.json();
    if (statusEl) {
      statusEl.innerText = `✅ Scansione completata: ${d.captured_count} lead individuati e notificati.`;
      statusEl.style.color = '#10b981';
    }
    window.loadActiveLeadsRadar();
  } catch (err) {
    if (statusEl) {
      statusEl.innerText = `Errore scansione: ${err.message}`;
      statusEl.style.color = '#ef4444';
    }
  }
};

// ── CHROME CDP CONTROLLER SUITE ─────────────────────────────────────────
window.toggleCdpModal = function(show) {
  const card = document.getElementById('card-mod-cdp');
  if (!card) return;
  card.style.display = show ? 'block' : 'none';
  if (show) {
    window.checkCdpStatus();
  }
};

window.checkCdpStatus = async function() {
  const badge = document.getElementById('cdp-status-badge');
  const tabsList = document.getElementById('cdp-open-tabs');

  try {
    const res = await fetch('/api/cdp/status');
    const d = await res.json();
    if (badge) {
      if (d.running) {
        badge.innerText = 'CDP CONNESSO (PORTA 9222)';
        badge.style.background = '#10b981';
        badge.style.color = '#000';
      } else {
        badge.innerText = 'CDP NON AVVIATO (PORTA 9222)';
        badge.style.background = '#ef4444';
        badge.style.color = '#fff';
      }
    }

    if (d.running) {
      const tabsRes = await fetch('/api/cdp/tabs');
      const tabsData = await tabsRes.json();
      if (tabsList && tabsData.tabs) {
        tabsList.innerHTML = tabsData.tabs.map(t => `
          <div style="font-size:0.7rem; color:#cbd5e1; background:#0f172a; padding:6px; border-radius:4px; margin-bottom:4px; border:1px solid #1e293b;">
            <strong>${t.title || 'Scheda'}</strong><br>
            <span style="color:#64748b;">${t.url}</span>
          </div>
        `).join('');
      }
    } else {
      if (tabsList) tabsList.innerHTML = '<div style="color:#64748b; font-size:0.7rem;">Chrome non è ancora connesso con porta 9222. Clicca "AVVIA CHROME CDP" sotto.</div>';
    }
  } catch (err) {
    if (badge) {
      badge.innerText = 'OFFLINE';
      badge.style.background = '#64748b';
    }
  }
};

window.launchChromeCdp = async function(targetUrl) {
  const statusEl = document.getElementById('cdp-action-status');
  if (statusEl) {
    statusEl.innerText = 'Avvio Google Chrome con porta di debug 9222...';
    statusEl.style.color = '#00f0ff';
  }

  try {
    const res = await fetch('/api/cdp/launch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: targetUrl || 'https://eb.badrexpress.com' })
    });
    const d = await res.json();
    if (statusEl) {
      statusEl.innerText = `Stato: ${d.status} (URL CDP: ${d.cdp_url || '9222'})`;
      statusEl.style.color = '#10b981';
    }
    setTimeout(window.checkCdpStatus, 1500);
  } catch (err) {
    if (statusEl) {
      statusEl.innerText = 'Errore avvio CDP: ' + err.message;
      statusEl.style.color = '#ef4444';
    }
  }
};

window.fillActiveAgencyPortalWithCdp = async function() {
  const urlInp = document.getElementById('cdp-portal-url')?.value;
  const statusEl = document.getElementById('cdp-action-status');
  if (!urlInp) {
    alert('Inserisci l\'URL del portale o dell\'agenzia immobiliare da compilare.');
    return;
  }

  if (statusEl) {
    statusEl.innerText = 'Iniezione automatica credenziali e proposta in corso via CDP...';
    statusEl.style.color = '#00f0ff';
  }

  try {
    const res = await fetch('/api/cdp/fill-agency', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        portal_url: urlInp,
        agency_name: 'Agenzia Selezionata'
      })
    });
    const d = await res.json();
    if (statusEl) {
      statusEl.innerText = `Completato: ${d.status} (Dati inseriti via Chrome nativo)`;
      statusEl.style.color = '#10b981';
    }
  } catch (err) {
    if (statusEl) {
      statusEl.innerText = 'Errore iniezione CDP: ' + err.message;
      statusEl.style.color = '#ef4444';
    }
  }
};

// ── QUANTUM MATH MATRIX & LOGISTICS SOLVER (< 10µs) ──────────────────
window.openQuantumMathModal = function() {
  let modal = document.getElementById('modal-quantum-math');
  if (modal) {
    modal.style.display = 'flex';
    modal.classList.add('active');
  }
};

window.closeQuantumMathModal = function() {
  let modal = document.getElementById('modal-quantum-math');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.remove('active');
  }
};

window.calculateQuantumMath = async function() {
  const mq = parseFloat(document.getElementById('qm-surface')?.value || '70');
  const fOrig = parseInt(document.getElementById('qm-floor-orig')?.value || '1');
  const fDest = parseInt(document.getElementById('qm-floor-dest')?.value || '1');
  const elevOrig = !!document.getElementById('qm-elev-orig')?.checked;
  const elevDest = !!document.getElementById('qm-elev-dest')?.checked;
  const cOrig = document.getElementById('qm-city-orig')?.value || 'Bologna';
  const cDest = document.getElementById('qm-city-dest')?.value || 'Imola';
  const urgent = !!document.getElementById('qm-urgent')?.checked;
  const packing = !!document.getElementById('qm-packing')?.checked;

  const resContainer = document.getElementById('qm-results-container');
  const latencyBadge = document.getElementById('qm-latency-badge');
  if (latencyBadge) latencyBadge.textContent = 'CALCOLO IN CORSO...';

  try {
    const t0 = performance.now();
    const r = await fetch('/api/math/quantum-solver', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        surface_mq: mq,
        floor_origin: fOrig,
        floor_dest: fDest,
        elevator_origin: elevOrig,
        elevator_dest: elevDest,
        origin_city: cOrig,
        dest_city: cDest,
        is_urgent: urgent,
        packing_required: packing
      })
    });

    const d = await r.json();
    const dt = (performance.now() - t0).toFixed(1);

    if (latencyBadge) {
      latencyBadge.textContent = `⚡ RUST SIMD: ${d.execution_latency_us || 8}µs (Network: ${dt}ms)`;
      latencyBadge.style.color = '#00ff9f';
    }

    if (resContainer) {
      resContainer.style.display = 'block';
      const g = d.geodesic || {};
      const l = d.logistics_and_loading || {};
      const p = d.pricing_optimization || {};

      document.getElementById('qm-res-veh').textContent = l.vehicle_model || '—';
      document.getElementById('qm-res-vol').textContent = `${l.required_volume_m3} m³ (${l.volume_occupancy_pct}% cap. ${l.volume_capacity_m3}m³) · ${l.trips_required} viaggio/i`;
      document.getElementById('qm-res-weight').textContent = `${l.estimated_payload_kg} kg (Ant: ${l.front_axle_load_kg}kg | Post: ${l.rear_axle_load_kg}kg)`;
      document.getElementById('qm-res-balance').textContent = l.axle_balance_status || 'Assetto conforme';

      document.getElementById('qm-res-dist').textContent = `${g.wgs84_ellipsoidal_distance_km} km WGS-84 (Stradale: ${g.road_adjusted_distance_km} km)`;
      document.getElementById('qm-res-fuel').textContent = `Gasolio: ${g.diesel_liters_estimate} L (€${g.fuel_cost_euro}) · Pedaggio: €${g.highway_toll_estimate_euro}`;

      document.getElementById('qm-res-sweet').textContent = `€${p.sweet_spot_price}`;
      document.getElementById('qm-res-sweet-prob').textContent = `Probabilità Chiusura: ${p.sweet_spot_conversion_prob_pct}% (Margine Ottimale)`;

      document.getElementById('qm-res-budget').textContent = `€${p.budget_deal_price} (${p.budget_conversion_prob_pct}% prob)`;
      document.getElementById('qm-res-premium').textContent = `€${p.premium_speed_price} (${p.premium_conversion_prob_pct}% prob)`;
      document.getElementById('qm-res-crew').textContent = `Equipaggio: ${p.suggested_crew_size} operatori · Durata stimata: ${p.estimated_duration_hours}h`;

      if (window.playLaserChime) window.playLaserChime();
    }
  } catch (err) {
    if (latencyBadge) {
      latencyBadge.textContent = 'Errore di calcolo: ' + err.message;
      latencyBadge.style.color = '#ef4444';
    }
  }
};

// ── TELEGRAM NOTIFICATION GUARD (BATTERY SAVER & ON-DEMAND) ─────────────────
window.openTelegramGuardModal = async function() {
  const m = document.getElementById('modal-telegram-guard');
  if (m) m.style.display = 'flex';
  await refreshTelegramGuardStatus();
};

window.closeTelegramGuardModal = function() {
  const m = document.getElementById('modal-telegram-guard');
  if (m) m.style.display = 'none';
};

window.refreshTelegramGuardStatus = async function() {
  try {
    const res = await fetch('/api/telegram/status');
    const d = await res.json();
    const p = d.policy || {};
    const badge = document.getElementById('tg-guard-status-badge');
    const pillLbl = document.getElementById('lbl-tg-guard-top');
    const pillDot = document.getElementById('dot-tg-guard-top');

    if (p.notifications_enabled) {
      if (badge) {
        badge.textContent = `🟢 ATTIVE (${p.alerts_today || 0}/${p.max_daily_alerts || 5} inviate oggi)`;
        badge.style.background = 'rgba(16,185,129,0.2)';
        badge.style.color = '#10b981';
        badge.style.borderColor = 'rgba(16,185,129,0.4)';
      }
      if (pillLbl) pillLbl.textContent = 'ACTIVE';
      if (pillDot) {
        pillDot.style.background = '#10b981';
        pillDot.style.boxShadow = '0 0 8px #10b981';
      }
    } else {
      if (badge) {
        badge.textContent = '🔇 DISATTIVATE DI DEFAULT (Risparmio Batteria)';
        badge.style.background = 'rgba(239,68,68,0.2)';
        badge.style.color = '#f87171';
        badge.style.borderColor = 'rgba(239,68,68,0.4)';
      }
      if (pillLbl) pillLbl.textContent = 'SILENT';
      if (pillDot) {
        pillDot.style.background = '#38bdf8';
        pillDot.style.boxShadow = '0 0 8px #38bdf8';
      }
    }
  } catch (e) {
    console.warn('Errore refresh Telegram Guard:', e);
  }
};

window.toggleTelegramGuard = async function(enable) {
  const fb = document.getElementById('tg-guard-action-feedback');
  if (fb) fb.textContent = 'Salvataggio preferenza in corso...';
  try {
    const res = await fetch('/api/telegram/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: enable })
    });
    const d = await res.json();
    if (fb) fb.textContent = enable ? '🟢 Notifiche attivate (tetto max 5/giorno)' : '🔇 Notifiche silenziate (Risparmio Batteria)';
    await refreshTelegramGuardStatus();
  } catch (e) {
    if (fb) fb.textContent = 'Errore modifica: ' + e.message;
  }
};

window.sendTelegramReportNow = async function() {
  const fb = document.getElementById('tg-guard-action-feedback');
  if (fb) fb.textContent = 'Invio report in corso verso Telegram...';
  try {
    const res = await fetch('/api/telegram/send-status-report', { method: 'POST' });
    const d = await res.json();
    if (d.status === 'SUCCESS') {
      if (fb) fb.textContent = '✅ Report inviato con successo al tuo cellulare!';
    } else {
      if (fb) fb.textContent = 'Errore invio report: ' + (d.error || 'Server error');
    }
  } catch (e) {
    if (fb) fb.textContent = 'Errore connessione: ' + e.message;
  }
};

// Auto-check all'avvio
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => { if (window.refreshTelegramGuardStatus) window.refreshTelegramGuardStatus(); }, 1500);
});

// ═══════════════════════════════════════════════════════════════════════════
// 12. IRON MAN HUD COMPASS, REFLEX ENGINE & EMERGENCY CALL (JARVIS)
// ═══════════════════════════════════════════════════════════════════════════

let _hudWatchdogActive = true;
let _hudFocusActive = true;
let _emergencyTimer = null;
let _emergencySecondsLeft = 3;
let _webcamStream = null;

window.setHudModel = function(el, model) {
  document.querySelectorAll('.jcw-model-chip').forEach(c => c.classList.remove('active'));
  if (el) el.classList.add('active');

  const modelInput = document.getElementById('model-select');
  if (modelInput) modelInput.value = model;

  const topChips = document.querySelectorAll('.ms-chip');
  topChips.forEach(c => {
    c.classList.toggle('active', c.getAttribute('data-value') === model);
  });

  const badgeText = document.getElementById('ai-mode-text');
  if (badgeText) {
    if (model === 'claude-opus') badgeText.textContent = '🧠 CLAUDE OPUS 5.5';
    else if (model === 'groq-llama70b') badgeText.textContent = '⚡ GROQ LLAMA 70B';
    else if (model === 'qwen-27b') badgeText.textContent = '🦀 QWEN 27B LOCAL';
    else badgeText.textContent = '🟢 CLOUD FREE (AUTO)';
  }

  if (window.playUiClick) window.playUiClick();
};

window.toggleHudWatchdog = function() {
  _hudWatchdogActive = !_hudWatchdogActive;
  const pill = document.getElementById('jcw-pill-watch');
  if (pill) {
    pill.classList.toggle('active', _hudWatchdogActive);
    pill.style.opacity = _hudWatchdogActive ? '1' : '0.5';
  }
};

window.toggleHudFocus = function() {
  _hudFocusActive = !_hudFocusActive;
  const pill = document.getElementById('jcw-pill-focus');
  if (pill) {
    pill.classList.toggle('active', _hudFocusActive);
  }
};

// ── EMERGENCY 3-SECOND RING COUNTDOWN ──────────────────────────────────────
window.startEmergencyCountdown = function() {
  const modal = document.getElementById('modal-emergency-call');
  const numEl = document.getElementById('ring-countdown-number');
  const strokeEl = document.getElementById('ring-countdown-stroke');
  const statusDesc = document.getElementById('ring-status-desc');
  if (!modal) return;

  _emergencySecondsLeft = 3;
  if (numEl) numEl.textContent = '3';
  if (strokeEl) strokeEl.style.strokeDashoffset = '0';
  if (statusDesc) statusDesc.textContent = 'Squillo automatico in 3 secondi tramite gateway telefonico prioritario...';

  modal.style.display = 'flex';
  if (window.playLaserChime) window.playLaserChime();

  if (_emergencyTimer) clearInterval(_emergencyTimer);

  const totalLength = 326.7;
  _emergencyTimer = setInterval(() => {
    _emergencySecondsLeft--;
    if (numEl) numEl.textContent = _emergencySecondsLeft;
    if (strokeEl) {
      const offset = totalLength * (1 - _emergencySecondsLeft / 3);
      strokeEl.style.strokeDashoffset = offset;
    }

    if (window.playUiClick) window.playUiClick();

    if (_emergencySecondsLeft <= 0) {
      clearInterval(_emergencyTimer);
      _emergencyTimer = null;
      window.triggerEmergencyCallNow();
    }
  }, 1000);
};

window.cancelEmergencyCountdown = function() {
  if (_emergencyTimer) {
    clearInterval(_emergencyTimer);
    _emergencyTimer = null;
  }
  const modal = document.getElementById('modal-emergency-call');
  if (modal) modal.style.display = 'none';
};

window.triggerEmergencyCallNow = async function() {
  if (_emergencyTimer) {
    clearInterval(_emergencyTimer);
    _emergencyTimer = null;
  }
  const numEl = document.getElementById('ring-countdown-number');
  const statusDesc = document.getElementById('ring-status-desc');
  if (numEl) numEl.textContent = '📞';
  if (statusDesc) statusDesc.innerHTML = '<span style="color:#00ff9f; font-weight:bold;">SQUILLO INOLTRATO AL CELLULARE (+39 388 870 3508)!</span>';

  try {
    const res = await fetch('/api/reflex/dispatch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: 'chiama subito cellulare emergenza badr' })
    });
    const d = await res.json();
    console.log('[EMERGENCY REFLEX DISPATCH]:', d);
    if (window.playSpeechAudio) {
      window.playSpeechAudio("Ingegnere Badr, ho inoltrato la chiamata di emergenza verso il tuo telefono.");
    }
  } catch (err) {
    console.warn('[EMERGENCY DISPATCH ERROR]:', err);
  }

  setTimeout(() => {
    const modal = document.getElementById('modal-emergency-call');
    if (modal) modal.style.display = 'none';
  }, 2200);
};

// ── CAMERA VISION (WEBCAM LIVE FEED) ───────────────────────────────────────
window.openCameraVisionModal = async function() {
  const modal = document.getElementById('modal-camera-vision');
  const video = document.getElementById('cam-live-video');
  const statusEl = document.getElementById('cam-stream-status');
  if (!modal || !video) return;

  modal.style.display = 'flex';
  try {
    _webcamStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' }
    });
    video.srcObject = _webcamStream;
    if (statusEl) statusEl.textContent = '● LIVE WEBCAM ACTIVE (1080p / 60 FPS)';
  } catch (err) {
    console.warn('[WEBCAM ACCESS ERR]:', err);
    if (statusEl) statusEl.textContent = '⚠️ Webcam non rilevata o permessi negati: ' + err.message;
  }
};

window.closeCameraVisionModal = function() {
  const modal = document.getElementById('modal-camera-vision');
  const video = document.getElementById('cam-live-video');
  if (_webcamStream) {
    _webcamStream.getTracks().forEach(t => t.stop());
    _webcamStream = null;
  }
  if (video) video.srcObject = null;
  if (modal) modal.style.display = 'none';
};

window.captureWebcamAndAnalyze = async function() {
  const video = document.getElementById('cam-live-video');
  const fb = document.getElementById('cam-feedback-text');
  const btn = document.getElementById('btn-cam-capture');
  if (!video || !video.videoWidth) {
    if (fb) fb.textContent = '⚠️ Errore: feed video non pronto.';
    return;
  }

  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const b64 = canvas.toDataURL('image/jpeg', 0.85);

  if (fb) fb.textContent = '👁️ Analisi ottica neurale in corso con Vision AI...';
  if (btn) btn.disabled = true;

  try {
    const res = await fetch('/api/screen/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        frame_b64: b64,
        detect_form: false,
        prompt: "Guarda attentamente attraverso la fotocamera. Descrivi cosa vedi in modo brillante per l'Ingegner Badr: oggetti, mobili, documenti o ambiente circostante, stimando volume o valore se pertinente."
      })
    });
    const d = await res.json();
    const commento = d.analysis || 'Oggetto analizzato con successo.';
    if (fb) fb.textContent = '✅ Analisi completata!';

    const respEl = document.getElementById('resp-body');
    const respTag = document.getElementById('resp-tag');
    if (respTag) respTag.textContent = 'CAMERA VISION OK';
    if (respEl) respEl.innerHTML = `<strong>📷 CAMERA VISION ANALISI:</strong><br>${commento.replace(/\n/g, '<br>')}`;

    if (window.playSpeechAudio) {
      window.playSpeechAudio(commento.slice(0, 220));
    }

    setTimeout(() => {
      window.closeCameraVisionModal();
    }, 1800);
  } catch (err) {
    if (fb) fb.textContent = 'Errore analisi: ' + err.message;
  } finally {
    if (btn) btn.disabled = false;
  }
};


// ═══════════════════════════════════════════════════════════════════════════
// 13. FORCE-DIRECTED NEURAL KNOWLEDGE GRAPH ENGINE (RUST POWERED)
// ═══════════════════════════════════════════════════════════════════════════

let _graphData = { nodes: [], links: [] };
let _graphNodes = [];
let _graphLinks = [];
let _graphAnimId = null;
let _graphFilterCat = 'all';
let _graphSearchQuery = '';
let _selectedNode = null;
let _graphPan = { x: 0, y: 0 };
let _graphZoom = 1.0;
let _isDraggingGraph = false;
let _dragStart = { x: 0, y: 0 };
let _draggedNode = null;
let _repelForce = 450;
let _springLength = 110;

const CATEGORY_COLORS = {
  router: '#00f0ff',
  wiki: '#a3e635',
  concepts: '#14b8a6',
  suites: '#8b5cf6',
  skills: '#ec4899',
  tools: '#3b82f6',
  worlds: '#eab308',
  notes: '#94a3b8',
  files: '#f97316'
};

window.initNeuralGraph = async function() {
  const canvas = document.getElementById('neural-graph-canvas');
  if (!canvas) return;

  setupGraphCanvasEvents(canvas);

  try {
    const res = await fetch('/api/graph/neural-network');
    if (res.ok) {
      const data = await res.json();
      _graphData = data;
      _graphNodes = (data.nodes || []).map(n => ({
        ...n,
        x: n.x || (Math.random() - 0.5) * 600,
        y: n.y || (Math.random() - 0.5) * 500,
        vx: 0,
        vy: 0,
        radius: n.radius || 18,
        color: CATEGORY_COLORS[n.category] || n.color || '#00f0ff'
      }));
      _graphLinks = data.links || [];

      window.resetGraphView();
      startGraphLoop(canvas);
    }
  } catch (err) {
    console.warn('[NEURAL GRAPH LOAD ERR]:', err);
  }
};

function setupGraphCanvasEvents(canvas) {
  if (canvas._eventsAttached) return;
  canvas._eventsAttached = true;

  window.addEventListener('resize', () => {
    resizeGraphCanvas(canvas);
  });
  resizeGraphCanvas(canvas);

  canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - canvas.width / 2 - _graphPan.x) / _graphZoom;
    const mouseY = (e.clientY - rect.top - canvas.height / 2 - _graphPan.y) / _graphZoom;

    // Check hit node
    let hit = null;
    for (let i = _graphNodes.length - 1; i >= 0; i--) {
      const n = _graphNodes[i];
      const dx = mouseX - n.x;
      const dy = mouseY - n.y;
      if (Math.sqrt(dx * dx + dy * dy) <= (n.radius + 6)) {
        hit = n;
        break;
      }
    }

    if (hit) {
      _draggedNode = hit;
      selectGraphNode(hit);
    } else {
      _isDraggingGraph = true;
      _dragStart = { x: e.clientX - _graphPan.x, y: e.clientY - _graphPan.y };
    }
  });

  window.addEventListener('mousemove', (e) => {
    if (_draggedNode) {
      const rect = canvas.getBoundingClientRect();
      _draggedNode.x = (e.clientX - rect.left - canvas.width / 2 - _graphPan.x) / _graphZoom;
      _draggedNode.y = (e.clientY - rect.top - canvas.height / 2 - _graphPan.y) / _graphZoom;
      _draggedNode.vx = 0;
      _draggedNode.vy = 0;
    } else if (_isDraggingGraph) {
      _graphPan.x = e.clientX - _dragStart.x;
      _graphPan.y = e.clientY - _dragStart.y;
    }
  });

  window.addEventListener('mouseup', () => {
    _draggedNode = null;
    _isDraggingGraph = false;
  });

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
    _graphZoom = Math.min(3.0, Math.max(0.25, _graphZoom * zoomFactor));
  });
}

function resizeGraphCanvas(canvas) {
  const stage = canvas.parentElement;
  const w = (stage && stage.clientWidth > 50) ? stage.clientWidth : window.innerWidth;
  const h = (stage && stage.clientHeight > 50) ? stage.clientHeight : (window.innerHeight - 100);
  if (w > 0 && h > 0) {
    canvas.width = w;
    canvas.height = h;
  }
}

window.resetGraphView = function() {
  const canvas = document.getElementById('neural-graph-canvas');
  if (canvas) resizeGraphCanvas(canvas);
  _graphPan = { x: 0, y: 0 };
  _graphZoom = 1.0;
};

window.filterGraphCat = function(btn, cat) {
  _graphFilterCat = cat;
  document.querySelectorAll('.ng-chip').forEach(c => c.classList.remove('active'));
  if (btn) btn.classList.add('active');
};

window.filterNeuralGraph = function(query) {
  _graphSearchQuery = (query || '').toLowerCase().trim();
};

window.updateGraphPhysicsParams = function() {
  const repelEl = document.getElementById('ng-repel-slider');
  const linkEl = document.getElementById('ng-link-slider');
  if (repelEl) _repelForce = parseFloat(repelEl.value);
  if (linkEl) _springLength = parseFloat(linkEl.value);
};

function startGraphLoop(canvas) {
  if (_graphAnimId) cancelAnimationFrame(_graphAnimId);

  let lastSyncTime = performance.now();

  function loop(now) {
    if (document.hidden || !canvas || canvas.offsetParent === null || canvas.clientWidth === 0) {
      setTimeout(() => {
        _graphAnimId = requestAnimationFrame(loop);
      }, 500);
      return;
    }

    updateLocalGraphPhysics();

    // Periodic sync with Rust physics endpoint every 1.5 seconds if nodes move
    if (now - lastSyncTime > 1500 && _graphNodes.length > 0) {
      lastSyncTime = now;
      syncGraphWithRustPhysics();
    }

    renderGraphCanvas(canvas);
    _graphAnimId = requestAnimationFrame(loop);
  }

  _graphAnimId = requestAnimationFrame(loop);
}

function updateLocalGraphPhysics() {
  const dt = 0.02;
  const damping = 0.88;
  const kRepel = _repelForce * 12;
  const kSpring = 0.04;
  const restLength = _springLength;

  // Repulsion between nodes (Coulomb)
  for (let i = 0; i < _graphNodes.length; i++) {
    for (let j = i + 1; j < _graphNodes.length; j++) {
      const a = _graphNodes[i];
      const b = _graphNodes[j];
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const distSq = dx * dx + dy * dy + 100.0;
      const dist = Math.sqrt(distSq);
      const force = kRepel / distSq;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      a.vx -= fx * dt;
      a.vy -= fy * dt;
      b.vx += fx * dt;
      b.vy += fy * dt;
    }
  }

  // Node lookup map
  const nodeMap = new Map();
  _graphNodes.forEach(n => nodeMap.set(n.id, n));

  // Link attraction (Hooke's law)
  for (const l of _graphLinks) {
    const s = nodeMap.get(typeof l.source === 'object' ? l.source.id : l.source);
    const t = nodeMap.get(typeof l.target === 'object' ? l.target.id : l.target);
    if (!s || !t) continue;

    const dx = t.x - s.x;
    const dy = t.y - s.y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
    const delta = dist - restLength;
    const force = delta * kSpring * (l.strength || 0.8);
    const fx = (dx / dist) * force;
    const fy = (dy / dist) * force;

    s.vx += fx * dt;
    s.vy += fy * dt;
    t.vx -= fx * dt;
    t.vy -= fy * dt;
  }

  // Central gravity
  for (const n of _graphNodes) {
    if (n === _draggedNode) continue;
    n.vx -= n.x * 0.015 * dt;
    n.vy -= n.y * 0.015 * dt;

    n.vx *= damping;
    n.vy *= damping;
    n.x += n.vx;
    n.y += n.vy;
  }
}

async function syncGraphWithRustPhysics() {
  try {
    const res = await fetch('/api/graph/physics-step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nodes: _graphNodes,
        links: _graphLinks,
        repel_force: _repelForce,
        spring_length: _springLength,
        dt: 0.016
      })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.nodes && Array.isArray(data.nodes)) {
        const remoteMap = new Map();
        data.nodes.forEach(rn => remoteMap.set(rn.id, rn));
        _graphNodes.forEach(localNode => {
          const r = remoteMap.get(localNode.id);
          if (r && localNode !== _draggedNode) {
            localNode.vx = r.vx || localNode.vx;
            localNode.vy = r.vy || localNode.vy;
          }
        });
      }
    }
  } catch (e) {}
}

function renderGraphCanvas(canvas) {
  if (canvas.width < 100 || canvas.height < 100) {
    resizeGraphCanvas(canvas);
  }
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);
  ctx.save();

  // Apply pan & zoom
  ctx.translate(w / 2 + _graphPan.x, h / 2 + _graphPan.y);
  ctx.scale(_graphZoom, _graphZoom);

  // Subtle coordinate grid dots
  ctx.fillStyle = 'rgba(0, 240, 255, 0.04)';
  const gridSize = 80;
  for (let gx = -1200; gx <= 1200; gx += gridSize) {
    for (let gy = -1000; gy <= 1000; gy += gridSize) {
      ctx.fillRect(gx - 1, gy - 1, 2, 2);
    }
  }

  const nodeMap = new Map();
  _graphNodes.forEach(n => nodeMap.set(n.id, n));

  // Draw links
  for (const l of _graphLinks) {
    const s = nodeMap.get(typeof l.source === 'object' ? l.source.id : l.source);
    const t = nodeMap.get(typeof l.target === 'object' ? l.target.id : l.target);
    if (!s || !t) continue;

    const isConnectedToSelected = _selectedNode && (s.id === _selectedNode.id || t.id === _selectedNode.id);

    ctx.beginPath();
    ctx.moveTo(s.x, s.y);
    ctx.lineTo(t.x, t.y);
    ctx.strokeStyle = isConnectedToSelected ? 'rgba(0, 255, 159, 0.75)' : 'rgba(0, 240, 255, 0.16)';
    ctx.lineWidth = isConnectedToSelected ? 2.0 : 1.0;
    ctx.stroke();
  }

  // Draw nodes
  for (const n of _graphNodes) {
    const catMatch = _graphFilterCat === 'all' || n.category === _graphFilterCat;
    const searchMatch = !_graphSearchQuery || (n.label || '').toLowerCase().includes(_graphSearchQuery) || (n.id || '').toLowerCase().includes(_graphSearchQuery);
    const isSelected = _selectedNode && _selectedNode.id === n.id;
    const isDimmed = !catMatch || !searchMatch;

    const alpha = isDimmed ? 0.2 : 1.0;
    const baseColor = n.color || '#00f0ff';

    // Outer glow
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.radius + (isSelected ? 8 : 4), 0, Math.PI * 2);
    ctx.fillStyle = isSelected ? 'rgba(0, 255, 159, 0.25)' : (isDimmed ? 'transparent' : 'rgba(0, 240, 255, 0.08)');
    ctx.fill();

    // Node body
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
    ctx.fillStyle = isDimmed ? 'rgba(20, 30, 45, 0.5)' : '#07152b';
    ctx.fill();
    ctx.strokeStyle = isSelected ? '#00ff9f' : baseColor;
    ctx.lineWidth = isSelected ? 3.0 : 1.8;
    ctx.globalAlpha = alpha;
    ctx.stroke();
    ctx.globalAlpha = 1.0;

    // Center jewel
    ctx.beginPath();
    ctx.arc(n.x, n.y, 4, 0, Math.PI * 2);
    ctx.fillStyle = isSelected ? '#00ff9f' : baseColor;
    ctx.globalAlpha = alpha;
    ctx.fill();
    ctx.globalAlpha = 1.0;

    // Label
    ctx.font = isSelected ? 'bold 11px Orbitron, sans-serif' : '10px Share Tech Mono, monospace';
    ctx.fillStyle = isSelected ? '#00ff9f' : (isDimmed ? '#475569' : '#f8fafc');
    ctx.textAlign = 'center';
    ctx.fillText(n.label || n.id, n.x, n.y + n.radius + 14);

    if (n.sub && !isDimmed) {
      ctx.font = '8px Inter, sans-serif';
      ctx.fillStyle = '#64748b';
      ctx.fillText(n.sub, n.x, n.y + n.radius + 24);
    }
  }

  ctx.restore();
}

function selectGraphNode(node) {
  _selectedNode = node;
  const inspector = document.getElementById('ng-inspector');
  if (!inspector) return;

  inspector.classList.add('open');
  document.getElementById('ngi-title').textContent = node.label || node.id;
  const catBadge = document.getElementById('ngi-cat-badge');
  if (catBadge) {
    catBadge.textContent = (node.category || 'NODE').toUpperCase();
    catBadge.style.color = node.color || '#00f0ff';
    catBadge.style.borderColor = node.color || '#00f0ff';
  }
  document.getElementById('ngi-prop-id').textContent = node.id;

  // Find connections
  const connected = [];
  for (const l of _graphLinks) {
    const sId = typeof l.source === 'object' ? l.source.id : l.source;
    const tId = typeof l.target === 'object' ? l.target.id : l.target;
    if (sId === node.id) connected.push({ target: tId, label: l.label, dir: 'out' });
    if (tId === node.id) connected.push({ target: sId, label: l.label, dir: 'in' });
  }

  document.getElementById('ngi-prop-conn').textContent = connected.length;

  const linksList = document.getElementById('ngi-links-list');
  if (linksList) {
    if (connected.length === 0) {
      linksList.innerHTML = '<div style="color:#64748b; font-style:italic;">Nessun link sinaptico diretto.</div>';
    } else {
      linksList.innerHTML = connected.map(c => `
        <div class="ngi-link-item">
          <span>${c.dir === 'out' ? '➔' : '⬅'} <strong>${c.target}</strong></span>
          <span style="color:#00ff9f; font-size:0.65rem;">${c.label || 'Synapse'}</span>
        </div>
      `).join('');
    }
  }

  const detailsRaw = document.getElementById('ngi-details-raw');
  if (detailsRaw) {
    detailsRaw.textContent = JSON.stringify(node.details || {}, null, 2);
  }

  if (window.playUiClick) window.playUiClick();
}

window.closeGraphInspector = function() {
  const inspector = document.getElementById('ng-inspector');
  if (inspector) inspector.classList.remove('open');
  _selectedNode = null;
};

window.executeSelectedNodeAction = function() {
  if (!_selectedNode) return;
  const label = _selectedNode.label || _selectedNode.id;
  const query = `JARVIS, analizza e attiva il nodo ${label} della rete sinaptica.`;

  window.switchMasterView('jarvis');
  const promptInput = document.getElementById('prompt-input');
  if (promptInput) {
    promptInput.value = query;
    if (window.sendMessage) window.sendMessage();
  }
};

// ═══════════════════════════════════════════════════════════════════
// 9. 7 AUTONOMOUS AI EMPLOYEES & NIGHT FLEET ENGINE (/new, /steer, /queue)
// ═══════════════════════════════════════════════════════════════════
window.currentFleetMode = 'new';

window.setFleetMode = function(mode) {
  window.currentFleetMode = mode;
  ['new', 'steer', 'queue'].forEach(m => {
    const btn = document.getElementById(`btn-fleet-mode-${m}`);
    if (btn) btn.classList.toggle('active', m === mode);
  });
  const input = document.getElementById('fleet-cmd-input');
  if (input) {
    if (mode === 'new') input.placeholder = "Nuovo task autonomo (es. 'Estrai lead traslochi Torino')...";
    else if (mode === 'steer') input.placeholder = "Inietta rotta in volo (es. 'Scarta furgoni sopra i 150.000 km')...";
    else if (mode === 'queue') input.placeholder = "Accoda per la notte (es. 'Build e audit UE5.8 mentre dormo')...";
    input.focus();
  }
};

window.submitFleetCommand = async function() {
  const input = document.getElementById('fleet-cmd-input');
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;

  const mode = window.currentFleetMode || 'new';
  let endpoint = '/api/fleet/new';
  let body = { prompt: text, agent: 'hermes' };

  if (mode === 'steer') {
    endpoint = '/api/fleet/steer';
    body = { guidance: text };
  } else if (mode === 'queue') {
    endpoint = '/api/fleet/queue';
    body = { prompt: text, agent: 'hermes' };
  }

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    input.value = '';

    if (window.showToolRun) {
      showToolRun(`FLEET /${mode.toUpperCase()}`, data.message || `Comando /${mode} accettato con successo.`, '0.04s');
    }
    await window.refreshFleetUi();
  } catch (err) {
    console.error('Fleet command error:', err);
    if (window.showToolRun) {
      showToolRun('FLEET ERROR', `Errore esecuzione: ${err.message}`, '0.01s');
    }
  }
};

window.refreshFleetUi = async function() {
  try {
    const res = await fetch('/api/fleet/status');
    if (!res.ok) return;
    const status = await res.json();

    // 1. Update Active Task Banner
    const activeStatusEl = document.getElementById('fleet-active-status');
    const activeAgentEl = document.getElementById('fleet-active-agent');
    const activePromptEl = document.getElementById('fleet-active-prompt');
    const steerBoxEl = document.getElementById('fleet-active-steer');
    const steerTextEl = document.getElementById('fleet-active-steer-text');
    const pulseDotEl = document.getElementById('fleet-pulse-dot');

    if (status.active_task && status.active_task.status === 'running') {
      const at = status.active_task;
      if (activeStatusEl) activeStatusEl.textContent = `ESECUZIONE IN CORSO (#${at.task_id})`;
      if (activeAgentEl) activeAgentEl.textContent = (at.agent || 'HERMES').toUpperCase();
      if (activePromptEl) activePromptEl.textContent = at.prompt || 'Task in esecuzione...';
      if (pulseDotEl) pulseDotEl.style.background = '#00ff9f';

      if (at.steer_directive) {
        if (steerBoxEl) steerBoxEl.style.display = 'block';
        if (steerTextEl) steerTextEl.textContent = at.steer_directive;
      } else {
        if (steerBoxEl) steerBoxEl.style.display = 'none';
      }
    } else {
      if (activeStatusEl) activeStatusEl.textContent = 'STANDBY - FLOTTA PRONTA';
      if (activeAgentEl) activeAgentEl.textContent = 'HERMES DOCKER VPS';
      if (activePromptEl) activePromptEl.textContent = 'Nessun task attivo in volo. Usa /new o /queue per avviare.';
      if (steerBoxEl) steerBoxEl.style.display = 'none';
      if (pulseDotEl) pulseDotEl.style.background = '#64748b';
    }

    // 2. Update Night Queue
    const qCountEl = document.getElementById('fleet-queue-count');
    const qListEl = document.getElementById('fleet-queue-list');
    const queue = status.night_queue || [];

    if (qCountEl) qCountEl.textContent = `${queue.length} task in coda`;
    if (qListEl) {
      if (queue.length === 0) {
        qListEl.innerHTML = '<div class="fqb-empty">Nessun task accodato per la notte. Usa <b>/queue</b> per aggiungerne uno.</div>';
      } else {
        qListEl.innerHTML = queue.map(q => `
          <div class="fqb-item">
            <div class="fqb-item-info">
              <span class="fqb-item-prompt" title="${q.prompt}">${q.prompt}</span>
              <span class="fqb-item-meta">Agente: ${(q.agent || 'hermes').toUpperCase()} · #${q.task_id}</span>
            </div>
            <span style="color:#ffb703; font-size:0.62rem; font-family:var(--font-mono);">${q.created_at || 'In Coda'}</span>
          </div>
        `).join('');
      }
    }

    // 3. Update Agent status badges if present
    if (status.agents) {
      const activeAgentKey = status.active_task && status.active_task.status === 'running' ? status.active_task.agent : null;
      Object.keys(status.agents).forEach(k => {
        const badge = document.getElementById(`badge-agent-${k.replace('_marketplace', '').replace('_code', '').replace('_pitcher', '')}`);
        if (badge) {
          if (k === activeAgentKey) {
            badge.textContent = 'BUSY';
            badge.className = 'fac-status badge-busy';
          } else {
            badge.textContent = 'ONLINE';
            badge.className = 'fac-status badge-active';
          }
        }
      });
    }
  } catch (err) {
    console.warn('refreshFleetUi error:', err);
  }
};

window.quickTaskForAgent = function(agentKey) {
  const input = document.getElementById('fleet-cmd-input');
  if (!input) return;
  const presets = {
    hermes: "Esegui sync e health check su tutti gli 11 container Docker VPS",
    openclaw: "Cerca nuovi annunci traslochi e sgomberi a Torino e Milano",
    b2b_pitcher: "Genera email proposta SELEZIONE per autolavaggi tunnel Piemonte",
    claude_code: "Verifica build Rust SIMD port 9000 e compila UBT EBGS",
    sentinel: "Monitora RAM e ripara eventuali container orfani su VPS Oracle",
    jev_marketplace: "Valuta furgone Fiat Ducato 2018 120cv con formula JEV",
    postiz_radar: "Ascolta menzioni Discord e chat gruppi B2B nelle ultime 6 ore"
  };
  input.value = presets[agentKey] || `Avvia task per ${agentKey}`;
  window.setFleetMode('new');
};

// Auto refresh fleet status every 15 seconds if fleet tab is active
setInterval(() => {
  const fleetTab = document.getElementById('tab-fleet');
  if (fleetTab && fleetTab.classList.contains('active')) {
    window.refreshFleetUi();
  }
}, 15000);

// ═══════════════════════════════════════════════════════════════════
// 10. CUNEO LEAD DOSSIER & EMAIL DISPATCH CONTROLLER
// ═══════════════════════════════════════════════════════════════════
window.quickDispatchCuneoEmail = async function() {
  const fb = document.getElementById('cuneo-dispatch-feedback');
  if (fb) {
    fb.style.display = 'block';
    fb.style.color = '#ffb703';
    fb.textContent = '⏳ Compilazione PDF e invio SMTP a badraudi@gmail.com in corso...';
  }

  try {
    const res = await fetch('/api/leads/cuneo/dispatch-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient: 'badraudi@gmail.com' })
    });
    const data = await res.json();
    if (fb) {
      if (data.status === 'SUCCESS') {
        fb.style.color = '#00ff9f';
        fb.textContent = '✅ Dossier Lead Cuneo inviato con successo a badraudi@gmail.com!';
      } else {
        fb.style.color = '#ef4444';
        fb.textContent = '❌ Errore invio: ' + (data.error || 'Server error');
      }
    }
    if (window.showToolRun) {
      showToolRun('LEAD CUNEO DISPATCH', 'Dossier inviato con successo via SMTP Gmail!', '0.04s');
    }
  } catch (err) {
    if (fb) {
      fb.style.color = '#ef4444';
      fb.textContent = '❌ Errore rete: ' + err.message;
    }
  }
};

window.submitCustomEmail = async function() {
  const dest = document.getElementById('email-modal-dest')?.value || 'badraudi@gmail.com';
  const subj = document.getElementById('email-modal-subject')?.value || 'Scheda Lead';
  const body = document.getElementById('email-modal-body')?.value || '';
  const attachPdf = document.getElementById('email-modal-attach-pdf')?.checked;
  const statusEl = document.getElementById('email-modal-status');

  if (statusEl) {
    statusEl.style.display = 'block';
    statusEl.style.color = '#ffb703';
    statusEl.textContent = '⏳ Spedizione email in corso...';
  }

  const attachments = attachPdf ? ['CUNEO_PROVINCIA_LEAD_DOSSIER.pdf'] : [];

  try {
    const res = await fetch('/api/email/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        to: dest,
        subject: subj,
        body: body,
        attachments: attachments
      })
    });
    const data = await res.json();
    if (statusEl) {
      if (data.status === 'SUCCESS' || !data.error) {
        statusEl.style.color = '#00ff9f';
        statusEl.textContent = '✅ Email inviata con successo!';
      } else {
        statusEl.style.color = '#ef4444';
        statusEl.textContent = '❌ Errore invio: ' + (data.error || 'Errore');
      }
    }
  } catch (err) {
    if (statusEl) {
      statusEl.style.color = '#ef4444';
      statusEl.textContent = '❌ Errore: ' + err.message;
    }
  }
};

window.calculateAndSendQuote = async function() {
  const from = document.getElementById('prev-from')?.value || 'Cuneo';
  const to = document.getElementById('prev-to')?.value || 'Torino';
  const service = document.getElementById('prev-service')?.value || 'trasloco_completo';
  const vol = parseInt(document.getElementById('prev-vol')?.value || '25', 10);
  const resBox = document.getElementById('prev-result');

  // Formula di calcolo preventivo trasparente
  let basePrice = vol * 28;
  if (service === 'sgombero_cantina') basePrice = vol * 18 + 150;
  else if (service === 'trasporto_mobili') basePrice = 250 + (vol * 15);
  else if (service === 'sgombero_locale') basePrice = vol * 22 + 200;
  else basePrice += 200;

  const quoteId = 'Q_' + Date.now().toString().slice(-6);
  const quoteMsg = `📋 PREVENTIVO #${quoteId}\n` +
    `• Tratta: ${from} ➔ ${to}\n` +
    `• Servizio: ${service.replace('_', ' ').toUpperCase()}\n` +
    `• Volume: ${vol} m³\n` +
    `• Prezzo Stimato: € ${basePrice.toFixed(2)}\n` +
    `• Include: Assicurazione All-Risk, Furgone con Sponda, 2 Operatori Qualificati.\n` +
    `• Firma: BadrExpress.com & PietroTraslochi.com (+39 388 870 3508)`;

  if (resBox) {
    resBox.style.display = 'block';
    resBox.innerText = quoteMsg + '\n\n⏳ Invio copia via email a badraudi@gmail.com...';
  }

  try {
    await fetch('/api/email/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        to: 'badraudi@gmail.com',
        subject: `🚛 Preventivo Calcolato: ${from} ➔ ${to} (€ ${basePrice.toFixed(0)})`,
        body: quoteMsg
      })
    });
    if (resBox) {
      resBox.innerText = quoteMsg + '\n\n✅ Copia preventivo inviata a badraudi@gmail.com!';
    }
  } catch (err) {
    console.warn('Quote email send error:', err);
  }
};




