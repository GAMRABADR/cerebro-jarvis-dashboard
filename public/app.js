// ═══════════════════════════════════════════════════════════════════════════════
//  CEREBRO MASTER SUITE · 3D BIO-NEURAL CORTEX & 4-HUB CONTROLLER v15.0 PRO
// ═══════════════════════════════════════════════════════════════════════════════

const API = '';
let currentAudio = null;
let isBusy = false;
let isRecording = false;
let audioUnlocked = false;
let currentMasterView = 'jarvis';
let kanbanLanesData = {};
let bioCortex = null;
let ambientPlexus = null;
let audioCtx = null;
let microphoneStream = null;
let mediaRecorder = null;
let audioChunks = [];
let animFrameId = null;
let oscAnimFrame = null;
let neuralMessageQueue = [];

let liveTunnels = {
  jarvis: 'https://eb.badrexpress.com',
  n8n: 'https://n8n.badrexpress.com',
  agente0: 'https://agent0.badrexpress.com'
};

async function loadTunnelsConfig() {
  try {
    const r = await fetch('tunnels_config.json?' + Date.now());
    if (r.ok) {
      liveTunnels = await r.json();
      const nFrame = document.getElementById('n8n-frame');
      const aFrame = document.getElementById('agente0-frame');
      if (nFrame && liveTunnels.n8n) nFrame.src = liveTunnels.n8n;
      if (aFrame && liveTunnels.agente0) aFrame.src = liveTunnels.agente0;
    }
  } catch (e) {}
}

let currentInspectedSkill = null;

window.showSkillDetailModal = function(node) {
  currentInspectedSkill = node;
  const titleEl = document.getElementById('msd-title');
  const catEl = document.getElementById('msd-cat');
  const idEl = document.getElementById('msd-id');
  const descEl = document.getElementById('msd-desc');
  const cmdEl = document.getElementById('msd-cmd');

  if (titleEl) titleEl.textContent = `⚡ ${node.label || node.id}`;
  if (catEl) catEl.textContent = `${node.category} · OFFICIAL ARSENAL`;
  if (idEl) idEl.textContent = `ID: ${node.id || node.key} | ENGINE: skills_vault/${node.id || node.key}`;
  if (descEl) descEl.textContent = node.description || `Skill ufficiale ${node.label} integrata nell'ecosistema CEREBRO JARVIS.`;
  if (cmdEl) cmdEl.value = node.command || `JARVIS, esegui ${node.label}`;

  openModal('modal-skill-detail');
};

window.executeCurrentInspectedSkill = function() {
  if (!currentInspectedSkill) return;
  const cmd = currentInspectedSkill.command || `JARVIS, esegui ${currentInspectedSkill.label}`;
  closeModal('modal-skill-detail');
  sendCommand(cmd);
};

window.openModal = function(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('active');
};

window.closeModal = function(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('active');
};

function openN8nFull() {
  if (liveTunnels.n8n) window.open(liveTunnels.n8n, '_blank');
}

function openAgente0Full() {
  if (liveTunnels.agente0) window.open(liveTunnels.agente0, '_blank');
}

function reloadN8nFrame() {
  const f = document.getElementById('n8n-frame');
  if (f && liveTunnels.n8n) f.src = liveTunnels.n8n;
}

function reloadAgente0Frame() {
  const f = document.getElementById('agente0-frame');
  if (f && liveTunnels.agente0) f.src = liveTunnels.agente0;
}

// ── 4-HUB MASTER VIEW TOGGLE ─────────────────────────────────────
function switchMasterView(view) {
  currentMasterView = view;
  const hubs = ['jarvis', 'kanban', 'agente0', 'n8n'];
  
  hubs.forEach(h => {
    const el = document.getElementById(`view-${h}`);
    const btn = document.getElementById(`btn-view-${h}`);
    if (el) el.classList.toggle('active', h === view);
    if (btn) btn.classList.toggle('active', h === view);
  });

  const titles = {
    'jarvis': 'ECOSISTEMA: ONLINE · CEREBRO CORE',
    'kanban': 'HERMES MISSION CONTROL (L5 AUTONOMOUS)',
    'agente0': 'AGENTE ZERO NEURAL DOCK',
    'n8n': 'N8N INTEGRATION ENGINE'
  };
  const statEl = document.getElementById('master-status');
  if (statEl) statEl.textContent = titles[view] || 'ECOSISTEMA: ONLINE';

  if (view === 'kanban') refreshKanban();
  if (view === 'n8n') reloadN8nFrame();
  if (view === 'agente0') reloadAgente0Frame();
}

function initAudioContext() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) audioCtx = new AudioContext();
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
}

// ── NEURAL MESSAGE QUEUE CONTROLLER (GESTIONE / ELIMINAZIONE CODA) ──
function updateQueueUI() {
  const badge = document.getElementById('queue-badge');
  const countEl = document.getElementById('queue-count');
  const countTray = document.getElementById('queue-count-tray');
  const tray = document.getElementById('neural-queue-tray');
  const itemsList = document.getElementById('queue-items-list');

  if (countEl) countEl.textContent = neuralMessageQueue.length;
  if (countTray) countTray.textContent = neuralMessageQueue.length;

  if (badge) {
    if (neuralMessageQueue.length > 0) badge.classList.remove('hidden');
    else badge.classList.add('hidden');
  }

  if (itemsList) {
    itemsList.innerHTML = '';
    neuralMessageQueue.forEach((msg, idx) => {
      const item = document.createElement('div');
      item.className = 'nqt-item';
      item.innerHTML = `
        <span class="nqt-item-num">#${idx + 1}</span>
        <span class="nqt-item-text" title="${msg}">${msg}</span>
        <button class="nqt-item-del" onclick="deleteQueuedItem(${idx})" title="Elimina questo messaggio">✕</button>
      `;
      itemsList.appendChild(item);
    });
  }

  if (tray && neuralMessageQueue.length === 0) {
    tray.classList.add('hidden');
  }
}

window.toggleQueueTray = function() {
  const tray = document.getElementById('neural-queue-tray');
  if (tray) tray.classList.toggle('hidden');
};

window.clearMessageQueue = function() {
  const count = neuralMessageQueue.length;
  neuralMessageQueue = [];
  updateQueueUI();
  addEvent('sys', `🗑️ Coda messaggi annullata e svuotata (${count} messaggi rimossi).`);
};

window.deleteQueuedItem = function(index) {
  if (index >= 0 && index < neuralMessageQueue.length) {
    const removed = neuralMessageQueue.splice(index, 1);
    updateQueueUI();
    addEvent('sys', `🗑️ Messaggio rimosso dalla coda: "${removed[0].slice(0, 24)}..."`);
  }
};

window.stopJarvisVoice = function() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  isBusy = false;
  setReactorState('', 'READY', 'IN ATTESA');
  if (window.bioCortexInstance) window.bioCortexInstance.setSpeaking(false);
  const wf = document.getElementById('waveform');
  if (wf) wf.classList.remove('active');
  addEvent('sys', '⏹️ Voce di JARVIS interrotta su richiesta.');
  processNextQueuedMessage();
};

async function processNextQueuedMessage() {
  if (neuralMessageQueue.length > 0 && !isBusy) {
    const nextMsg = neuralMessageQueue.shift();
    updateQueueUI();
    addEvent('sys', `⚡ [DEQUEUE]: Elaborazione messaggio in coda...`);
    await executeCommandPipeline(nextMsg);
  }
}

// ── REAL-TIME AUDIO OSCILLOSCOPE EQUALIZER ───────────────────────
function animateOscilloscope(analyser) {
  const bars = document.querySelectorAll('.osc-bar');
  if (!bars || bars.length === 0) return;

  const dataArray = new Uint8Array(analyser ? analyser.frequencyBinCount : 32);

  function draw() {
    if (analyser) {
      analyser.getByteFrequencyData(dataArray);
    }
    let sum = 0;
    for (let i = 0; i < bars.length; i++) {
      const idx = analyser ? Math.floor((i / bars.length) * (dataArray.length / 2)) : 0;
      const val = analyser ? dataArray[idx] : 0;
      sum += val;
      const height = Math.max(3, (val / 255) * 24);
      bars[i].style.height = `${height}px`;

      if (val > 130) {
        bars[i].style.background = 'linear-gradient(to top, #00f0ff, #00ff9f)';
        bars[i].style.boxShadow = '0 0 8px #00ff9f';
      } else {
        bars[i].style.background = 'linear-gradient(to top, #00d4ff, #00ff9f)';
        bars[i].style.boxShadow = 'none';
      }
    }

    const avg = Math.round((sum / (bars.length * 255)) * 100);
    const vuVal = document.getElementById('vu-meter-val');
    if (vuVal) {
      if (isRecording) vuVal.textContent = `${avg}% · ASCOLTO VOCE`;
      else if (currentAudio) vuVal.textContent = `${avg}% · VOCE JARVIS`;
      else vuVal.textContent = `0% · IDLE`;
    }

    if (isRecording || currentAudio) {
      oscAnimFrame = requestAnimationFrame(draw);
    } else {
      for (let i = 0; i < bars.length; i++) { bars[i].style.height = '3px'; }
    }
  }

  if (oscAnimFrame) cancelAnimationFrame(oscAnimFrame);
  draw();
}

// ── VOICE RECORDING WITH BARGE-IN & CONVERSATIONAL COURTESY ──────
async function startRecording() {
  initAudioContext();

  // BARGE-IN: If E.B. is speaking, interrupt immediately with courteous etiquette!
  if (currentAudio) {
    wasInterrupted = true;
    currentAudio.pause();
    currentAudio = null;
    isBusy = false;
    const wf = document.getElementById('waveform');
    if (wf) wf.classList.remove('active');
    setReactorState('', 'READY', 'IN ATTESA');
    if (window.bioCortexInstance) window.bioCortexInstance.setSpeaking(false);
    // Track barge-in event to DNA Vault in background
    fetch(API + '/api/dna/bargein-event', {method: 'POST'}).catch(() => {});
  }

  if (isRecording) return;


  try {
    if (!microphoneStream) {
      microphoneStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    }
    const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : '';
    mediaRecorder = mime ? new MediaRecorder(microphoneStream, { mimeType: mime }) : new MediaRecorder(microphoneStream);

    audioChunks = [];
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      if (oscAnimFrame) cancelAnimationFrame(oscAnimFrame);

      const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      audioChunks = [];

      if (blob.size < 800) {
        setReactorState('', 'READY', 'IN ATTESA');
        return;
      }

      setReactorState('processing', 'AI-STT', 'TRASCRIZIONE VOCALE');
      document.getElementById('hud-status').textContent = 'TRASCRIZIONE GEMINI FLASH...';

      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = async () => {
        const b64 = reader.result.split(',')[1];
        try {
          const r = await fetch(API + '/api/transcribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ audio_base64: b64, mime_type: blob.type })
          });
          const d = await r.json();
          if (d.text && d.text.trim()) {
            addEvent('usr', `🎙️ [VOCE]: "${d.text}"`);
            document.getElementById('prompt-input').value = d.text;
            sendCommand(d.text);
          } else {
            addEvent('err', 'Nessun parlato rilevato.');
            setReactorState('', 'READY', 'IN ATTESA');
          }
        } catch (err) {
          addEvent('err', `Errore trascrizione: ${err.message}`);
          setReactorState('', 'ERROR', 'ERRORE VOCE');
        }
      };
    };

    mediaRecorder.start();
    isRecording = true;
    playSound('start');

    const btn = document.getElementById('mic-btn');
    const micWrapper = document.getElementById('discord-mic-wrapper');
    if (btn) btn.classList.add('active');
    if (micWrapper) micWrapper.classList.add('speaking');
    setReactorState('speaking', 'LISTEN', 'ASCOLTO ATTIVO');

    // Hook microphone to Oscilloscope Analyser
    if (audioCtx && microphoneStream) {
      const source = audioCtx.createMediaStreamSource(microphoneStream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      animateOscilloscope(analyser);
    }
  } catch (e) {
    addEvent('err', 'Accesso al microfono negato.');
  }
}

function stopRecording() {
  if (!isRecording || !mediaRecorder) return;
  try {
    mediaRecorder.stop();
    isRecording = false;
    playSound('end');
    const btn = document.getElementById('mic-btn');
    const micWrapper = document.getElementById('discord-mic-wrapper');
    if (btn) btn.classList.remove('active');
    if (micWrapper) micWrapper.classList.remove('speaking');
  } catch (e) {}
}

// ── DYNAMIC COLLAPSIBLE TACTICAL ACTION DOCK CONTROLLER ─────────────
window.toggleActionDock = function() {
  const dock = document.getElementById('dynamic-action-dock');
  if (!dock) return;
  dock.classList.toggle('collapsed');
  const isCollapsed = dock.classList.contains('collapsed');
  localStorage.setItem('jarvis_action_dock_collapsed', isCollapsed ? 'true' : 'false');
};

// Restore dock state on boot
(function initActionDock() {
  const saved = localStorage.getItem('jarvis_action_dock_collapsed');
  const dock = document.getElementById('dynamic-action-dock');
  if (dock && saved === 'true') {
    dock.classList.add('collapsed');
  }
})();

let voiceHotkey = localStorage.getItem('jarvis_voice_hotkey') || 'Control+Space';

function updateHotkeyDisplay() {
  const el = document.getElementById('hotkey-display');
  if (el) el.textContent = voiceHotkey.replace('Control', 'Ctrl').replace('Space', 'Spazio');
}

function setCustomHotkey() {
  const newKey = prompt('Imposta tasto per parlare:\n(Esempi: "Control+Space", "Space", "Alt+v", "Control+Win")', voiceHotkey);
  if (newKey) {
    voiceHotkey = newKey.trim();
    localStorage.setItem('jarvis_voice_hotkey', voiceHotkey);
    updateHotkeyDisplay();
    addEvent('sys', `Tasto vocale impostato: ${voiceHotkey}`);
  }
}

window.addEventListener('keydown', (e) => {
  const tag = (document.activeElement && document.activeElement.tagName || '').toLowerCase();
  const targetTag = (e.target && e.target.tagName || '').toLowerCase();
  if (['input', 'textarea'].includes(tag) || ['input', 'textarea'].includes(targetTag)) return;
  const parts = voiceHotkey.split('+');

  const needsCtrl = parts.includes('Control');
  const needsAlt = parts.includes('Alt');
  const needsShift = parts.includes('Shift');
  const mainKey = parts[parts.length - 1].toLowerCase();

  const ctrlOk = needsCtrl ? (e.ctrlKey || e.metaKey) : true;
  const altOk = needsAlt ? e.altKey : true;
  const shiftOk = needsShift ? e.shiftKey : true;

  let match = false;
  if (mainKey === 'space' && e.code === 'Space') match = true;
  else if (e.key.toLowerCase() === mainKey) match = true;

  if (ctrlOk && altOk && shiftOk && match && !isRecording) {
    e.preventDefault();
    startRecording();
  }
});

window.addEventListener('keyup', (e) => {
  const parts = voiceHotkey.split('+');
  const mainKey = parts[parts.length - 1].toLowerCase();
  let match = false;
  if (mainKey === 'space' && e.code === 'Space') match = true;
  else if (e.key.toLowerCase() === mainKey) match = true;

  if (match && isRecording) stopRecording();
});

function tickClock() {
  const n = new Date();
  const p = v => String(v).padStart(2, '0');
  const el = document.getElementById('utc-clock');
  if (el) el.textContent = `${p(n.getUTCHours())}:${p(n.getUTCMinutes())}:${p(n.getUTCSeconds())}`;
}
setInterval(tickClock, 1000);
tickClock();

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

function setReactorState(state, label, sub) {
  const core = document.getElementById('reactor-core');
  const sphere = document.getElementById('jarvis-sphere');
  const accRing = document.getElementById('accretion-ring');
  const arSub = document.getElementById('ar-sub');
  const arWidget = document.getElementById('arc-reactor-widget');

  if (sphere) {
    sphere.className = 'black-hole-sphere' + (state ? ` ${state}` : '');
  }
  if (accRing) {
    accRing.className = 'accretion-ring' + (state === 'processing' ? ' fast' : '');
  }
  if (arSub) {
    arSub.textContent = `● ${label || 'READY'}`;
    arSub.style.color = state === 'speaking' ? '#00f0ff' : (state === 'processing' ? '#ffaa00' : '#00ff9f');
  }
  if (arWidget) {
    arWidget.style.filter = state === 'speaking' ? 'drop-shadow(0 0 12px #00f0ff)' : 'none';
  }
}

// ── FLOATING TOOL RUN HUD CARD — AUTO-FADE 4.5s + HOVER PAUSE ──────────────
let _toolCardTimer = null;
window.showToolRun = function(toolName, message, latency = "0.04s") {
  const card = document.getElementById('tool-run-card');
  const title = document.getElementById('trc-title');
  const body = document.getElementById('trc-main');
  const time = document.getElementById('trc-time');
  if (!card || !title || !body) return;

  title.textContent = `TOOL RUN · ${toolName.toUpperCase()}`;
  body.textContent = message;
  if (time) time.textContent = `⚡ ${latency} LATENCY`;

  // Show card (reset any previous fade-out)
  card.style.opacity = '1';
  card.style.transform = 'translateY(0) scale(1)';
  card.style.pointerEvents = 'all';
  card.classList.remove('hidden', 'fade-out-card');

  // Clear previous timer
  if (_toolCardTimer) clearTimeout(_toolCardTimer);

  // Auto-dismiss after 4.5s
  _toolCardTimer = setTimeout(() => {
    _autoFadeToolCard();
  }, 4500);

  // Hover = pause timer
  card.onmouseenter = () => { if (_toolCardTimer) clearTimeout(_toolCardTimer); };
  card.onmouseleave = () => {
    if (_toolCardTimer) clearTimeout(_toolCardTimer);
    _toolCardTimer = setTimeout(_autoFadeToolCard, 2000);
  };
  // Touch-hold on mobile = pause timer (tap = dismiss)
  card.ontouchstart = (e) => { if (_toolCardTimer) clearTimeout(_toolCardTimer); };
  card.ontouchend = (e) => {
    if (_toolCardTimer) clearTimeout(_toolCardTimer);
    _toolCardTimer = setTimeout(_autoFadeToolCard, 2000);
  };
};

function _autoFadeToolCard() {
  const card = document.getElementById('tool-run-card');
  if (!card) return;
  card.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
  card.style.opacity = '0';
  card.style.transform = 'translateY(-8px) scale(0.97)';
  card.style.pointerEvents = 'none';
  setTimeout(() => { card.classList.add('hidden'); card.style.transition = ''; }, 850);
}

window.closeToolCard = function() { _autoFadeToolCard(); if (_toolCardTimer) clearTimeout(_toolCardTimer); };


// ── GRAPH PHYSICS CONTROLLER ─────────────────────────────────────────
window.updateGraphPhysics = function() {
  const repelSlider = document.getElementById('repel-slider');
  const linkSlider = document.getElementById('link-slider');
  const repelVal = document.getElementById('repel-val');
  const linkVal = document.getElementById('link-val');

  const repel = repelSlider ? parseInt(repelSlider.value) : 160;
  const link = linkSlider ? parseInt(linkSlider.value) : 90;

  if (repelVal) repelVal.textContent = repel;
  if (linkVal) linkVal.textContent = link;

  if (window.bioCortexInstance && typeof window.bioCortexInstance.setPhysics === 'function') {
    window.bioCortexInstance.setPhysics(repel, link);
  }
};

// ── E.B. PERSONALITY & SETTINGS DRAWER CONTROLLER ────────────────────
let currentPersonality = 'jarvis';
let wasInterrupted = false;

window.toggleLeftWing = function() {
  const dock = document.getElementById('left-tactical-dock');
  const restoreBtn = document.getElementById('restore-left-btn');
  const grid = document.querySelector('.main-grid');
  if (dock && grid) {
    dock.classList.toggle('collapsed');
    const isCollapsed = dock.classList.contains('collapsed');
    if (restoreBtn) restoreBtn.style.display = isCollapsed ? 'block' : 'none';
    grid.classList.toggle('left-collapsed', isCollapsed);
    setTimeout(() => { if (window.bioCortexInstance) window.bioCortexInstance.resize(); }, 150);
  }
};

window.toggleRightWing = function() {
  const dock = document.getElementById('right-telemetry-dock');
  const restoreBtn = document.getElementById('restore-right-btn');
  const grid = document.querySelector('.main-grid');
  if (dock && grid) {
    dock.classList.toggle('collapsed');
    const isCollapsed = dock.classList.contains('collapsed');
    if (restoreBtn) restoreBtn.style.display = isCollapsed ? 'block' : 'none';
    grid.classList.toggle('right-collapsed', isCollapsed);
    setTimeout(() => { if (window.bioCortexInstance) window.bioCortexInstance.resize(); }, 150);
  }
};

window.openLeadRadarModal = function() {
  openModal('modal-lead-radar');
  loadLeadRadar();
};

window.loadLeadRadar = async function() {
  const container = document.getElementById('lead-radar-list');
  if (!container) return;
  container.innerHTML = '<div style="color:#00f0ff; text-align:center; padding:15px; font-family:var(--font-hud);">⚡ Scansione Lead Vault SQLite in corso...</div>';
  try {
    const res = await fetch('/api/leads/radar');
    const data = await res.json();
    if (data.status === 'SUCCESS' && data.leads && data.leads.length > 0) {
      container.innerHTML = data.leads.map(l => `
        <div class="lead-card-item">
          <div class="lci-top">
            <span class="lci-name">${l.name}</span>
            <span class="lci-badge">🛡️ ${l.status}</span>
          </div>
          <div class="lci-details">
            <span>📍 <strong>${l.city}</strong></span>
            <span>🚛 ${l.service} (${l.volume_mq} mq)</span>
            <span>💰 Stima: <strong>€${l.budget.toFixed(2)}</strong></span>
            <span>📅 ${l.date}</span>
          </div>
          <div style="font-size:0.68rem; color:#cbd5e1; font-style:italic;">"${l.notes || ''}"</div>
          <div class="lci-actions">
            <a href="tel:${l.phone.replace(/\\s+/g, '')}" class="lci-btn call">📞 Chiama (${l.phone})</a>
            <a href="https://wa.me/${l.phone.replace(/[^0-9]/g, '')}" target="_blank" class="lci-btn wa">💬 WhatsApp</a>
          </div>
        </div>
      `).join('');
    } else {
      container.innerHTML = '<div style="color:#94a3b8; text-align:center; padding:15px;">Nessun lead recente trovato.</div>';
    }
  } catch (e) {
    container.innerHTML = `<div style="color:#ef4444; text-align:center; padding:15px;">Errore caricamento radar: ${e.message}</div>`;
  }
};

window.toggleSettingsDrawer = function() {

  const drawer = document.getElementById('settings-drawer');
  const backdrop = document.getElementById('settings-backdrop');
  if (drawer && backdrop) {
    drawer.classList.toggle('open');
    backdrop.classList.toggle('open');
  }
};

window.switchEBMood = async function(mode) {
  currentPersonality = mode;
  // Update chips in cockpit
  document.querySelectorAll('.mood-chip').forEach(c => c.classList.remove('active'));
  const activeChip = document.getElementById(`chip-${mode}`);
  if (activeChip) activeChip.classList.add('active');

  // Update cards in drawer
  document.querySelectorAll('.sds-mood-card').forEach(c => c.classList.remove('active'));
  const activeCard = document.getElementById(`sd-mood-${mode}`);
  if (activeCard) activeCard.classList.add('active');

  // Update 3D BioCortex theme colors
  if (window.bioCortexInstance && typeof window.bioCortexInstance.setPersonalityTheme === 'function') {
    window.bioCortexInstance.setPersonalityTheme(mode);
  }

  // Update status label
  const statusEl = document.getElementById('hud-status');
  if (statusEl) {
    const titles = {
      'jarvis': 'MODALITÀ J.A.R.V.I.S. · ONLINE',
      'military': 'MODALITÀ TATTICA MILITARE · ATTIVA',
      'architect': 'MODALITÀ SENIOR ARCHITECT · ATTIVA',
      'friendly': 'MODALITÀ AMICHEVOLE · ATTIVA'
    };
    statusEl.textContent = titles[mode] || 'SISTEMA NEURALE SUB-SECOND ONLINE';
  }

  // Send to backend
  try {
    await fetch(API + '/api/settings/personality', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({personality: mode})
    });
  } catch (e) {}
};

window.saveAutofillProfile = async function() {
  const payload = {
    full_name: document.getElementById('af-fullname')?.value || '',
    email: document.getElementById('af-email')?.value || '',
    phone: document.getElementById('af-phone')?.value || '',
    company: document.getElementById('af-company')?.value || '',
    city: document.getElementById('af-city')?.value || '',
    notes: document.getElementById('af-notes')?.value || ''
  };
  try {
    const r = await fetch(API + '/api/autofill/profile', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const d = await r.json();
    alert('✅ Profilo Autofill salvato con successo nel Vault SQLite!');
  } catch (e) {
    alert('Errore nel salvataggio: ' + e);
  }
};

window.loadUserSettings = async function() {
  try {
    const r = await fetch(API + '/api/settings');
    if (r.ok) {
      const d = await r.json();
      if (d.current_personality) {
        switchEBMood(d.current_personality);
      }
      if (d.autofill_profile) {
        const p = d.autofill_profile;
        if (document.getElementById('af-fullname')) document.getElementById('af-fullname').value = p.full_name || '';
        if (document.getElementById('af-email')) document.getElementById('af-email').value = p.email || '';
        if (document.getElementById('af-phone')) document.getElementById('af-phone').value = p.phone || '';
        if (document.getElementById('af-company')) document.getElementById('af-company').value = p.company || '';
        if (document.getElementById('af-city')) document.getElementById('af-city').value = p.city || '';
        if (document.getElementById('af-notes')) document.getElementById('af-notes').value = p.notes || '';
      }
      if (d.behavioral_dna) {
        const dna = d.behavioral_dna;
        if (document.getElementById('dna-interrupts')) document.getElementById('dna-interrupts').textContent = dna.interrupt_count || 0;
        if (document.getElementById('dna-interactions')) document.getElementById('dna-interactions').textContent = dna.total_interactions || 42;
      }
    }
  } catch (e) {}
};

async function speak(text) {
  const wf = document.getElementById('waveform');
  if (wf) wf.classList.add('active');
  setReactorState('speaking', 'SPEAK', 'E.B. PARLA');
  if (window.bioCortexInstance) window.bioCortexInstance.setSpeaking(true);
  initAudioContext();

  try {
    const r = await fetch(API + '/api/tts', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text})
    });
    if (r.ok) {
      const d = await r.json();
      if (!d.audio_base64) throw new Error('No audio data');
      if (currentAudio) { currentAudio.pause(); currentAudio = null; }
      
      currentAudio = new Audio('data:audio/mp3;base64,' + d.audio_base64);
      currentAudio.crossOrigin = 'anonymous';

      if (audioCtx) {
        try {
          const source = audioCtx.createMediaElementSource(currentAudio);
          const speakerAnalyser = audioCtx.createAnalyser();
          speakerAnalyser.fftSize = 64;
          source.connect(speakerAnalyser);
          speakerAnalyser.connect(audioCtx.destination);
          animateOscilloscope(speakerAnalyser);
        } catch (e) {}
      }

      currentAudio.onended = () => {
        if (wf) wf.classList.remove('active');
        setReactorState('', 'READY', 'IN ATTESA');
        if (window.bioCortexInstance) window.bioCortexInstance.setSpeaking(false);
        isBusy = false;
        processNextQueuedMessage();
      };
      currentAudio.play().catch(() => {});
    } else {
      if (wf) wf.classList.remove('active');
      setReactorState('', 'READY', 'IN ATTESA');
      if (window.bioCortexInstance) window.bioCortexInstance.setSpeaking(false);
      isBusy = false;
      processNextQueuedMessage();
    }
  } catch (e) {
    if (wf) wf.classList.remove('active');
    setReactorState('', 'READY', 'IN ATTESA');
    if (window.bioCortexInstance) window.bioCortexInstance.setSpeaking(false);
    isBusy = false;
    processNextQueuedMessage();
  }
}


// ── COMMAND INGESTION WITH DYNAMIC ZOOM & QUEUE ──────────────────
window.sendQuick = function(text) {
  if (!text) return;
  document.getElementById('prompt-input').value = text;
  sendCommand(text);
};

async function sendCommand(prompt) {
  if (!prompt || !prompt.trim()) return;
  const text = prompt.trim();
  document.getElementById('prompt-input').value = '';

  if (isBusy) {
    // Queue message during speaking or processing
    neuralMessageQueue.push(text);
    updateQueueUI();
    addEvent('sys', `📥 Messaggio in coda (${neuralMessageQueue.length}): "${text.slice(0, 32)}..."`);
    return;
  }

  await executeCommandPipeline(text);
}

// ── CYBERPUNK LIVE SKILLS ACTIVITY MATRIX CONTROLLER ─────────────
function highlightSkillActivityHUD(category, skillKey) {
  const catMap = {
    'BUSINESS_SGOMBERI': 'biz',
    'GAME_DEV': 'game',
    'LTM_MEMORY': 'ltm',
    'API_INFRASTRUCTURE': 'vps',
    'VOICE_DEVOPS': 'voice',
    'MARKETPLACE': 'market',
    'WEB_RESEARCH': 'web',
    'AUTONOMOUS_FLEET': 'fleet'
  };
  const key = catMap[category] || 'biz';
  const row = document.getElementById(`sah-${key}`);
  const led = document.getElementById(`sah-led-${key}`);
  const fill = document.getElementById(`sah-bar-${key}`);
  const statusEl = document.getElementById('sah-overall-status');
  
  if (row) {
    row.classList.add('active-firing');
    setTimeout(() => row.classList.remove('active-firing'), 6500);
  }
  if (led) {
    led.classList.add('active');
    setTimeout(() => led.classList.remove('active'), 6500);
  }
  if (fill) {
    fill.style.width = '100%';
    setTimeout(() => fill.style.width = '75%', 6500);
  }
  if (statusEl && skillKey) {
    statusEl.textContent = `DISPATCHING: ${skillKey.toUpperCase()}`;
    statusEl.style.color = '#00ff9f';
    setTimeout(() => {
      statusEl.textContent = 'ALL SYSTEMS ONLINE';
      statusEl.style.color = '#00ff9f';
    }, 6500);
  }
}

async function executeCommandPipeline(prompt) {
  isBusy = true;
  initAudioContext();

  const model = document.getElementById('model-select').value;
  addEvent('usr', prompt);
  setReactorState('processing', 'PROC', 'NEURAL THINKING');

  // ── PRECISE INTENT & SKILL KEY DETECTION ──
  let targetCategory = 'LTM_MEMORY';
  let targetSkill = 'hermes_memory';
  const pLower = prompt.toLowerCase();

  if (pLower.includes('lead') || pLower.includes('clienti') || pLower.includes('preventiv') || pLower.includes('quanto costa') || pLower.includes('trasloc') || pLower.includes('sgomber') || pLower.includes('fattur') || pLower.includes('pietro') || pLower.includes('badrexpress')) {
    targetCategory = 'BUSINESS_SGOMBERI';
    targetSkill = (pLower.includes('lead') || pLower.includes('clienti')) ? 'leads_and_quotes_tracker' : (pLower.includes('fattur') ? 'auto_invoice_pdf_generator' : 'traslochi_funnel');
  } else if (pLower.includes('game') || pLower.includes('ue5') || pLower.includes('unreal') || pLower.includes('steam') || pLower.includes('lumen') || pLower.includes('chaos') || pLower.includes('blender') || pLower.includes('gaea') || pLower.includes('shader')) {
    targetCategory = 'GAME_DEV';
    targetSkill = pLower.includes('steam') ? 'steam_pipeline' : 'ue5_game_ops';
  } else if (pLower.includes('vendi') || pLower.includes('marketplace') || pLower.includes('prezzo') || pLower.includes('valuta') || pLower.includes('usato') || pLower.includes('subito') || pLower.includes('annuncio')) {
    targetCategory = 'MARKETPLACE';
    targetSkill = 'marketplace_seller_and_evaluator';
  } else if (pLower.includes('chiama') || pLower.includes('telefono') || pLower.includes('whatsapp') || pLower.includes('messaggio a') || pLower.includes('voce') || pLower.includes('audio')) {
    targetCategory = 'VOICE_DEVOPS';
    targetSkill = 'phone_call_and_whatsapp_dispatcher';
  } else if (pLower.includes('meteo') || pLower.includes('tempo fa') || pLower.includes('traffico') || pLower.includes('strada') || pLower.includes('tratta') || pLower.includes('naviga') || pLower.includes('internet') || pLower.includes('cerca') || pLower.includes('notizie') || pLower.includes('google') || pLower.includes('sito')) {
    targetCategory = 'WEB_RESEARCH';
    targetSkill = (pLower.includes('meteo') || pLower.includes('traffico')) ? 'meteo_and_traffic_intelligence' : 'autonomous_web_browser';
  } else if (pLower.includes('agente') || pLower.includes('hermes') || pLower.includes('kanban') || pLower.includes('sync') || pLower.includes('tokio') || pLower.includes('rust')) {
    targetCategory = 'AUTONOMOUS_FLEET';
    targetSkill = pLower.includes('kanban') ? 'hermes_kanban' : 'agente_zero_vps';
  } else if (pLower.includes('audit') || pLower.includes('kali') || pLower.includes('porte') || pLower.includes('porta') || pLower.includes('diagnostica rete') || pLower.includes('scansione') || pLower.includes('ping') || pLower.includes('dns') || pLower.includes('traceroute')) {
    targetCategory = 'API_INFRASTRUCTURE';
    targetSkill = 'network_audit_diagnostics';
  } else if (pLower.includes('vps') || pLower.includes('n8n') || pLower.includes('cloud') || pLower.includes('tunnel') || pLower.includes('oracle') || pLower.includes('docker') || pLower.includes('telemetria')) {
    targetCategory = 'API_INFRASTRUCTURE';
    targetSkill = pLower.includes('n8n') ? 'n8n_workflows' : 'oracle_vps_monitor';
  } else if (pLower.includes('email') || pLower.includes('posta') || pLower.includes('invia cv') || pLower.includes('curriculum') || pLower.includes('triage') || pLower.includes('inbox')) {
    targetCategory = 'BUSINESS_SGOMBERI';
    targetSkill = (pLower.includes('invia') || pLower.includes('cv')) ? 'real_smtp_mailer' : 'autonomous_email_triage';
  }

  if (window.bioCortexInstance) {
    window.bioCortexInstance.igniteSkill(targetSkill, targetCategory);
  }
  if (window.projectSynapseTo) {
    window.projectSynapseTo('.response-box', '#00ff9f');
  }
  highlightSkillActivityHUD(targetCategory, targetSkill);

  document.getElementById('resp-tag').textContent = 'PROCESSING';
  const respEl = document.getElementById('resp-body');
  if (respEl) {
    respEl.innerHTML = `<div class="chat-msg user-msg"><span class="c-tag">👤 BADR:</span> ${prompt.replace(/</g, '&lt;')}</div><div class="chat-msg ai-msg"><span class="c-tag">⚡ E.B.:</span> <span id="ai-live-stream">⚡ Elaborazione quantistica in corso...</span></div>`;
  }

  try {
    const r = await fetch(API + '/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({prompt, model, persona: currentPersonality})
    });
    if (window.bioCortexInstance) window.bioCortexInstance.setThinking(false);
    const d = await r.json();
    let reply = d.response || 'Nessuna risposta.';
    const modelUsed = d.model_used || model;

    if (d.current_personality && d.current_personality !== currentPersonality) {
      switchEBMood(d.current_personality);
    }

    // Prepend courteous transition if user interrupted E.B.
    if (wasInterrupted) {
      const courtesies = {
        'jarvis': 'Sì, stavo concludendo, ma vai pure Badr, dimmi tutto!\n\n',
        'military': 'Interruzione registrata. Avanti con la priorità, Comandante.\n\n',
        'architect': 'Interruzione rilevata. In ascolto per nuovo input dati.\n\n',
        'friendly': 'Tranquillo Badr, dimmi pure tutto, sono tutt\'orecchi!\n\n'
      };
      reply = (courtesies[currentPersonality] || '') + reply;
      wasInterrupted = false;
    }

    const liveStream = document.getElementById('ai-live-stream');
    if (liveStream) {
      liveStream.textContent = '';
      let i = 0;
      const typeInterval = setInterval(() => {
        liveStream.textContent += reply[i] || '';
        i++;
        if (i >= reply.length) clearInterval(typeInterval);
        if (respEl) respEl.scrollTop = respEl.scrollHeight;
      }, 8);
    }

    addEvent('ai', reply.slice(0, 140) + (reply.length > 140 ? '…' : ''));
    document.getElementById('hud-status').textContent = `[${modelUsed} · ${currentPersonality.toUpperCase()}]`;

    await speak(reply);

  } catch (e) {
    if (respEl) {
      respEl.innerHTML = `<div class="chat-msg user-msg"><span class="c-tag">👤 BADR:</span> ${prompt.replace(/</g, '&lt;')}</div><div class="chat-msg ai-msg" style="border-left-color:#ff0055;"><span class="c-tag" style="color:#ff0055;">⚠️ ERRORE:</span> ${e.message}</div>`;
    }
    addEvent('err', e.message);
    setReactorState('', 'ERROR', 'ERRORE RETE');
    isBusy = false;
    processNextQueuedMessage();
  }

}

function sendQuick(text) { sendCommand(text); }
function clearLog() {
  document.getElementById('event-stream').innerHTML = '';
  document.getElementById('resp-body').textContent = 'Console resettata.';
}

function switchTab(tabId) {
  const tabs = ['hubs', 'biz', 'game', 'vault', 'fleet'];
  tabs.forEach(t => {
    const el = document.getElementById(`tab-${t}`);
    if (el) el.classList.toggle('active', t === tabId);
  });
  document.querySelectorAll('.tab-navigation .tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.textContent.toLowerCase().includes(tabId));
  });
}

function playSound(type) {
  if (!audioCtx) return;
  try {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    if (type === 'start') {
      osc.frequency.setValueAtTime(440, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.12);
      gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.12);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.12);
    } else {
      osc.frequency.setValueAtTime(880, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(330, audioCtx.currentTime + 0.12);
      gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.12);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.12);
    }
  } catch (e) {}
}

async function refreshKanban() {
  try {
    const r = await fetch(API + '/api/kanban');
    const d = await r.json();
    kanbanLanesData = d.lanes || {};
    renderKanbanLanes(kanbanLanesData);
  } catch (e) {}
}

function renderKanbanLanes(lanes) {
  const laneNames = ['triage', 'todo', 'ready', 'in_progress', 'blocked', 'done'];
  const filterText = (document.getElementById('kanban-filter')?.value || '').toLowerCase();
  const filterAssignee = document.getElementById('filter-assignee')?.value || 'ALL';

  laneNames.forEach(lane => {
    const container = document.getElementById(`cards-${lane}`);
    if (!container) return;

    const cards = (lanes[lane] || []).filter(c => {
      const matchText = !filterText || c.title.toLowerCase().includes(filterText) || c.id.toLowerCase().includes(filterText);
      const matchAssignee = filterAssignee === 'ALL' || c.assignee === filterAssignee;
      return matchText && matchAssignee;
    });

    const countBadge = document.getElementById(`count-${lane}`);
    if (countBadge) countBadge.textContent = cards.length;

    if (cards.length === 0) {
      container.innerHTML = `<div style="text-align:center; padding:20px; color:#475569; font-size:0.65rem;">- NO TASKS -</div>`;
      return;
    }

    container.innerHTML = cards.map(c => `
      <div class="k-card">
        <div class="kc-top">
          <span class="kc-id">${c.id}</span>
          <span class="kc-time">${timeAgo(c.created_at)}</span>
        </div>
        <div class="kc-title">${c.title}</div>
        ${c.description ? `<div class="kc-desc">${c.description}</div>` : ''}
        <div class="kc-bottom">
          <span class="kc-assignee">${c.assignee}</span>
        </div>
      </div>
    `).join('');
  });
}

function timeAgo(ts) {
  const diff = Math.floor(Date.now() / 1000) - ts;
  if (diff < 60) return 'JUST NOW';
  if (diff < 3600) return `${Math.floor(diff / 60)}M AGO`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}H AGO`;
  return `${Math.floor(diff / 86400)}D AGO`;
}

function toggleRecording() {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
}

// ── DOM READY INITIALIZER ────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth < 850;
  if (isMobile) {
    const hkEl = document.getElementById('hotkey-display');
    if (hkEl) hkEl.textContent = 'Tocca Nucleo 🧠 o Mic 🎙️';
  } else {
    updateHotkeyDisplay();
  }

  refreshKanban();
  loadTunnelsConfig();
  loadUserSettings();

  // Register PWA Service Worker (Native App on Mobile/Desktop)
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js').catch(() => {});
  }



  // Initialize Supreme 3D Bio-Neural Connectome at Center
  if (window.initBioNeuralCortex) {
    bioCortex = window.initBioNeuralCortex('synapseCanvas');
  }

  // ── ATTACH DYNAMIC SYNAPTIC LASER BEAMS TO HUD BUTTONS ─────────────
  document.querySelectorAll('.cmd-tile, .dad-pill, .tab-btn, .mood-chip').forEach(el => {
    el.addEventListener('mouseenter', () => {
      if (window.projectSynapseTo) window.projectSynapseTo(el);
    });
    el.addEventListener('touchstart', () => {
      if (window.projectSynapseTo) window.projectSynapseTo(el);
      if (navigator.vibrate) navigator.vibrate(20);
    }, { passive: true });
  });


  // ── TAP-TO-TALK ON NUCLEUS (CANVAS CENTER) — RISOLVE MOBILE ──────────
  const canvas = document.getElementById('synapseCanvas');
  if (canvas) {
    let _coreHeld = false;
    let _coreTapTimer = null;

    const _isNearCenter = (e) => {
      const rect = canvas.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const radius = Math.min(rect.width, rect.height) * 0.18; // 18% of smaller dim = nucleus area
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const dist = Math.sqrt((clientX - cx) ** 2 + (clientY - cy) ** 2);
      return dist < radius;
    };

    const _startCoreTalk = () => {
      _coreHeld = true;
      // Emit shockwave pulse via CSS class on canvas wrapper
      const stage = document.getElementById('cerebro-core');
      if (stage) { stage.classList.add('core-active'); }
      // Update Arc Reactor
      const arSub = document.getElementById('ar-sub');
      if (arSub) { arSub.textContent = '● TAP-TO-TALK'; arSub.style.color = '#00ff9f'; }
      startRecording();
    };
    const _stopCoreTalk = () => {
      _coreHeld = false;
      const stage = document.getElementById('cerebro-core');
      if (stage) { stage.classList.remove('core-active'); }
      stopRecording();
    };

    // Desktop: click on nucleus area
    canvas.addEventListener('mousedown', (e) => { if (_isNearCenter(e)) { e.stopPropagation(); _startCoreTalk(); } });
    canvas.addEventListener('mouseup', () => { if (_coreHeld) _stopCoreTalk(); });
    // Mobile: touch on nucleus area
    canvas.addEventListener('touchstart', (e) => {
      if (_isNearCenter(e)) { e.preventDefault(); e.stopPropagation(); _startCoreTalk(); }
    }, { passive: false });
    canvas.addEventListener('touchend', (e) => {
      if (_coreHeld) { e.preventDefault(); _stopCoreTalk(); }
    }, { passive: false });
  }

  const micBtn = document.getElementById('mic-btn');
  if (micBtn) {
    micBtn.addEventListener('click', (e) => {
      e.preventDefault();
      toggleRecording();
    });
  }

  const sendBtn = document.getElementById('send-btn');
  if (sendBtn) sendBtn.addEventListener('click', () => sendCommand(document.getElementById('prompt-input').value));

  const promptIn = document.getElementById('prompt-input');
  if (promptIn) {
    promptIn.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendCommand(promptIn.value);
      }
    });
  }

  // ── MODEL SELECTOR POPULATION FROM /api/status ────────────────────
  try {
    const r = await fetch(API + '/api/status');
    const d = await r.json();
    const sel = document.getElementById('model-select');
    if (sel && d.model_groups) {
      sel.innerHTML = '';
      for (const [groupName, groupModels] of Object.entries(d.model_groups)) {
        const optgroup = document.createElement('optgroup');
        optgroup.label = `── ${groupName.toUpperCase()} ──`;
        for (const [k, label] of Object.entries(groupModels)) {
          const opt = document.createElement('option');
          opt.value = k;
          opt.textContent = label;
          if (k === (d.default_model || 'auto')) opt.selected = true;
          optgroup.appendChild(opt);
        }
        sel.appendChild(optgroup);
      }
    }
  } catch (e) {}

  // ── LIVE VPS TELEMETRY UPDATER ────────────────────────────
  async function updateVpsTelemetry() {
    try {
      const res = await fetch(API + '/api/telemetry/vps');
      const d = await res.json();
      if (d && d.status === 'SUCCESS') {
        const cpuVal = document.getElementById('vps-cpu-val');
        const cpuBar = document.getElementById('vps-cpu-bar');
        const ramVal = document.getElementById('vps-ram-val');
        const ramBar = document.getElementById('vps-ram-bar');
        const latVal = document.getElementById('vps-latency-val');
        const tunVal = document.getElementById('vps-tunnels-val');
        const botVal = document.getElementById('vps-bots-val');

        if (cpuVal) cpuVal.textContent = d.cpu_usage + '%';
        if (cpuBar) {
          cpuBar.style.width = Math.min(100, Math.max(5, d.cpu_usage)) + '%';
          cpuBar.style.background = d.cpu_usage > 75 ? '#ff0055' : (d.cpu_usage > 45 ? '#ffb703' : '#00ff9f');
        }

        if (ramVal) ramVal.textContent = d.ram_usage + '%';
        if (ramBar) {
          ramBar.style.width = Math.min(100, Math.max(5, d.ram_usage)) + '%';
          ramBar.style.background = d.ram_usage > 85 ? '#ff0055' : '#00d4ff';
        }

        if (latVal) latVal.textContent = d.latency_ms + 'ms';
        if (tunVal) tunVal.textContent = (d.active_tunnels || 3) + '/3 ACTIVE';
        if (botVal) botVal.textContent = (d.active_bots || 7) + ' ONLINE';
      }
    } catch (e) {}
  }

  updateVpsTelemetry();
  setInterval(updateVpsTelemetry, 3000);

  // ── MODEL CREDITS LIVE TICKER ─────────────────────────────────
  async function updateModelCreditsBar() {
    try {
      const r = await fetch(API + '/api/model-credits');
      const d = await r.json();
      if (!d) return;
      const bar = document.getElementById('model-credits-bar');
      if (bar) {
        const groqPct = Math.round(((14400 - (d.groq_daily_count || 0)) / 14400) * 100);
        const geminiPct = Math.round(((1500 - (d.gemini_daily_count || 0)) / 1500) * 100);
        bar.innerHTML = `
          <span class="mcb-item" title="Groq LPU Llama 70B Free Tier">⚡ Groq <strong>${d.groq_daily_count || 0}/14400</strong></span>
          <div class="mcb-track"><div class="mcb-fill groq" style="width:${groqPct}%"></div></div>
          <span class="mcb-item" title="Gemini 2.0 Flash Free Tier">✨ Gemini <strong>${d.gemini_daily_count || 0}/1500</strong></span>
          <div class="mcb-track"><div class="mcb-fill gemini" style="width:${geminiPct}%"></div></div>
          <span class="mcb-item" title="Ollama Locale — Illimitato">🖥️ Locale <strong>∞</strong></span>
        `;
      }
    } catch (e) {}
  }
  updateModelCreditsBar();
  setInterval(updateModelCreditsBar, 30000);

  // ── FRESHNESS SENTINEL — Colora nodi del grafo ogni 45s ──────
  async function updateFreshnessSentinel() {
    try {
      const r = await fetch(API + '/api/skills/freshness-matrix');
      const d = await r.json();
      if (d && d.freshness_matrix && window.bioCortexInstance) {
        window.bioCortexInstance.applyFreshnessMatrix(d.freshness_matrix);
      }
    } catch (e) {}
  }
  updateFreshnessSentinel();
  setInterval(updateFreshnessSentinel, 45000);

  // ── E.B. NEURAL EVOLUTION MATRIX CONTROLLER ──────────────────
  async function updateEvolutionMatrix() {
    try {
      const r = await fetch(API + '/api/evolution/matrix');
      const d = await r.json();
      if (d && d.status === 'SUCCESS') {
        const lvlEl = document.getElementById('eeh-lvl-val');
        const rankEl = document.getElementById('eeh-rank');
        const fillEl = document.getElementById('eeh-bar-fill');
        const xpValEl = document.getElementById('eeh-xp-val');
        const skillsEl = document.getElementById('eeh-skills-val');
        const n8nEl = document.getElementById('eeh-n8n-val');
        const iqEl = document.getElementById('eeh-iq-val');
        const fluxEl = document.getElementById('eeh-flux-val');

        if (lvlEl) lvlEl.textContent = d.evolution_level;
        if (rankEl) rankEl.textContent = d.rank_title;
        if (fillEl) fillEl.style.width = d.xp_percent + '%';
        if (xpValEl) xpValEl.textContent = d.xp_percent + '%';
        if (skillsEl) skillsEl.textContent = d.total_skills;
        if (n8nEl) n8nEl.textContent = d.n8n_workflows;
        if (iqEl) iqEl.textContent = d.quantum_iq;
        if (fluxEl) fluxEl.textContent = d.tachyon_flux + '%';

        // Adapt 3D Cortex Physics & Scale dynamically!
        if (window.bioCortexInstance && typeof window.bioCortexInstance.setEvolutionScale === 'function') {
          window.bioCortexInstance.setEvolutionScale(d.cortex_scale, d.tachyon_flux);
        }
      }
    } catch (e) {}
  }
  updateEvolutionMatrix();
  setInterval(updateEvolutionMatrix, 8000);

  // Global Neural Surge Trigger
  window.triggerNeuralSurge = function() {
    playSound('start');
    if (window.bioCortexInstance) {
      if (typeof window.bioCortexInstance.emitNucleusShockwave === 'function') {
        window.bioCortexInstance.emitNucleusShockwave();
      }
      // Light up all nodes for 3 seconds
      if (window.bioCortexInstance.nodes) {
        window.bioCortexInstance.nodes.forEach(n => {
          n._freshnessColor = '#00ff9f';
          n._freshnessAlpha = 1.0;
        });
      }
    }
    const stage = document.getElementById('cerebro-core');
    if (stage) {
      stage.classList.add('core-active');
      setTimeout(() => stage.classList.remove('core-active'), 2500);
    }
    showToolRun('E.B. NEURAL OVERCHARGE', '⚡ Impulso Quantistico distribuito su tutti i 40 Nodi e 18 Flussi N8N! Efficienza al 100%.', '0.001s');
  };

  // ── SHOW WELCOME TOOL CARD (AUTO-FADE 4.5s) ──────────────────
  setTimeout(() => {
    showToolRun('CEREBRO JARVIS v4.1', '🧠 Ecosistema Neurale Online · N8N Router Attivo · 40 Skill in Monitoraggio · Tocca il Nucleo per Parlare!', '0.01s');
  }, 800);
});





