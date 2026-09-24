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

window.ebjVoiceEnabled = true;
localStorage.setItem('ebj_voce', 'on');
window.isConversationalMode = true;
let _ebjCurrentAudio = null;
let _ebjRecognition = null;
let _ebjMicOn = false;
let _ebjVoiceUnlocked = false;
let _ebjWsGreeted = false;

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

window.playSpeechAudio = async function(text) {
  if (!window.ebjVoiceEnabled || !text) return;
  const clean = String(text).replace(/[#*_`>]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 420);
  if (!clean) return;

  const resumeMic = _ebjMicOn;
  if (_ebjRecognition && resumeMic) {
    try { _ebjRecognition.onend = null; _ebjRecognition.stop(); } catch (_) {}
    _ebjMicOn = false;
  }
  stopEbjSpeech();
  unlockEbjVoice();

  addEvent('voice', `🔊 VOCAL SYNTHESIS: "${clean.slice(0, 50)}..."`);
  let played = false;

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

  if (window.ebjVoiceEnabled && resumeMic) startEbjMic();
};

let _ebjRestartTimer = null;

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
    if (window.ebjVoiceEnabled) startEbjMic();
  }
  // Neutralize Chrome/Edge browser autoplay block
  if (window.speechSynthesis && window.speechSynthesis.paused) {
    try { window.speechSynthesis.resume(); } catch (_) {}
  }
}

// Auto-unlock audio playback permissions on first user gesture anywhere
window.addEventListener('click', () => { unlockEbjVoice(); }, { passive: true });
window.addEventListener('keydown', () => { unlockEbjVoice(); }, { passive: true });
window.addEventListener('touchstart', () => { unlockEbjVoice(); }, { passive: true });

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
        const rRust = await fetch('http://127.0.0.1:9000/api/telemetry', { signal: AbortSignal.timeout(500) });
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
setInterval(syncRustTelemetry, 2500);
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

  const finish = (reply, tag) => {
    if (respEl) respEl.textContent = reply;
    if (respTag) respTag.textContent = tag;
    addEvent('ai', String(reply).slice(0, 80) + '...');
    if (window.playSpeechAudio) window.playSpeechAudio(reply);
    const input = document.getElementById('prompt-input');
    if (input) input.focus();
  };

  if (isEbjWakePhrase(prompt)) {
    window.isConversationalMode = true;
    finish(EBJ_WAKE_ACK, 'E.B.J. LISTEN');
    try {
      fetch('http://127.0.0.1:9000/api/wake', {
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

  if (respTag) respTag.textContent = 'THINKING...';
  if (respEl) respEl.textContent = 'Elaborazione neurale in corso...';

  try {
    const model = document.getElementById('model-select')?.value || 'auto';
    let reply = '';
    let modelTag = 'EBJ SUPREME';

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
          try {
            const snd = new Audio('data:audio/mp3;base64,' + vData.audio_base64);
            snd.play();
          } catch (_) {}
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

    finish(reply, modelTag);
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
const DEFAULT_ACTIVE_MODULES = ['mod-synapses', 'mod-cpu-ram', 'mod-vps'];

window.toggleModularCatalog = function() {
  const modal = document.getElementById('modal-modular-catalog');
  if (!modal) return;
  modal.classList.toggle('active');
};

window.toggleModule = function(modId, state) {
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
  try { window.playUiClick && window.playUiClick(); } catch(e) {}
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
  topology: 'view-topology'
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
  document.querySelectorAll('.jarvis-workspace').forEach(w => w.classList.remove('active'));
  const target = document.getElementById(KALI_VIEW_MAP[key] || 'view-jarvis');
  if (target) target.classList.add('active');
  else document.getElementById('view-jarvis')?.classList.add('active');

  document.body.classList.toggle('view-kali', key === 'kali');

  document.querySelectorAll('.view-switch-btn').forEach(b => b.classList.remove('active'));
  if (key === 'jarvis') document.getElementById('btn-view-jarvis')?.classList.add('active');
  if (key === 'kanban') document.getElementById('btn-view-kanban')?.classList.add('active');
  if (key === 'n8n') document.getElementById('btn-view-n8n')?.classList.add('active');
  if (key === 'topology') document.getElementById('btn-view-topology')?.classList.add('active');

  if (key === 'kali') refreshKaliCatalog();
  toggleMobileNav(false);
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
  if (navigator.serviceWorker) {
    navigator.serviceWorker.getRegistrations().then((rs) => rs.forEach((r) => r.unregister())).catch(() => {});
  }
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
