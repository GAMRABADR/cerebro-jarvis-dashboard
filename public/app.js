// ═══════════════════════════════════════════════════════════════════════════════
//  CEREBRO MASTER SUITE · 3D BIO-NEURAL CORTEX & 4-HUB CONTROLLER v14.0 PRO
// ═══════════════════════════════════════════════════════════════════════════════

const API = '';
let currentAudio = null;
let isBusy = false;
let audioUnlocked = false;
let currentMasterView = 'jarvis';
let kanbanLanesData = {};
let bioCortex = null;
let liveTunnels = {
  jarvis: 'https://stored-october-pope-marina.trycloudflare.com',
  n8n: 'https://transmit-whats-impressive-eugene.trycloudflare.com',
  agente0: 'https://analysts-depend-creatures-borders.trycloudflare.com'
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

  if (view === 'kanban') refreshKanban();
  if (view === 'agente0' && bioCortex) bioCortex.pulseNeuron('agente0');
  if (view === 'n8n' && bioCortex) bioCortex.pulseNeuron('n8n');
}

// Global action trigger for 3D Cortex inspector
window.triggerNeuronAction = function(id) {
  if (id === 'sgomberi') openSgomberoModal();
  else if (id === 'mkt') openMarketplaceModal();
  else if (id === 'hermes') { switchMasterView('kanban'); launchLevel5Pipeline(); }
  else if (id === 'agente0') switchMasterView('agente0');
  else if (id === 'n8n') switchMasterView('n8n');
  else if (id === 'ebgs' || id === 'steam') sendQuick('JARVIS, verifica build e patch notes di EBGS Steamworks');
  else if (id === 'vault') queryVault('bustepaghe');
  else sendQuick(`JARVIS, attiva il neurone ${id} e procedi.`);
};

// ── SGOMBERI & TRASLOCHI WIZARD ──────────────────────────────────
async function openSgomberoModal() {
  const details = prompt('Descrivi il locale o gli oggetti da sgomberare:\n(Es: "Soggiorno con divano 3 posti, parete attrezzata, tavolo 6 sedie, 4 scatoloni")', 'Sgombero appartamento 3 locali con mobili in legno ed elettrodomestici');
  if (!details) return;

  const floor = parseInt(prompt('A quale piano si trova il locale? (Es: 0, 1, 2, 3, 4)', '2') || '1', 10);
  const has_elevator = confirm('È presente l\'ascensore o montacarichi utilizzabile per il trasloco? (OK = SÌ, Annulla = NO)');
  const sq_meters = parseInt(prompt('Metratura indicativa in mq:', '60') || '50', 10);
  const distance_km = parseInt(prompt('Distanza di trasporto/ecocentro in km:', '15') || '10', 10);

  if (bioCortex) bioCortex.pulseNeuron('sgomberi');
  setReactorState('processing', 'PREVENTIVO', 'CALCOLO IN CORSO');
  document.getElementById('resp-tag').textContent = 'CALCOLO PREVENTIVO';
  document.getElementById('resp-body').textContent = 'Calcolo preventivo sgombero e stima volumetrica in corso con l\'Agente Preventivatore...';

  try {
    const r = await fetch(API + '/api/workflow/quote', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({details, floor, has_elevator, sq_meters, distance_km})
    });
    const d = await r.json();
    document.getElementById('resp-body').textContent = d.quote_text || 'Preventivo calcolato.';
    addEvent('ai', `📋 Preventivo generato da ${d.model}`);

    if (bioCortex) bioCortex.addSynapseNode(`Sgombero P.${floor}`, '#eab308', `Piano ${floor} (~${sq_meters}mq)`, d.quote_text.slice(0, 100));

    await fetch(API + '/api/kanban/add', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        title: `Preventivo Sgombero: Piano ${floor} (~${sq_meters}mq)`,
        description: details.slice(0, 80),
        assignee: 'AG-LegalVault',
        lane: 'ready'
      })
    });
    refreshKanban();
    switchMasterView('jarvis');
  } catch (e) {
    document.getElementById('resp-body').textContent = `Errore preventivo: ${e.message}`;
  }
}

// ── MARKETPLACE AUTO-SELLER WIZARD ───────────────────────────────
async function openMarketplaceModal() {
  const item = prompt('Descrivi l\'oggetto che vuoi stimare e mettere in vendita:\n(Es: "Sedia da gaming Secretlab Titan 2022 nera in pelle, perfetta")', 'Sedia da gaming Secretlab Titan nera in tessuto');
  if (!item) return;

  const condition = prompt('Condizione dell\'oggetto:\n(Nuovo sigillato, Come nuovo, Ottime condizioni, Usato garantito)', 'Ottime condizioni');
  const platforms = prompt('Piattaforme su cui pubblicare:\n(Subito.it, Facebook Marketplace, eBay, Vinted)', 'Subito & Facebook Marketplace');

  if (bioCortex) bioCortex.pulseNeuron('mkt');
  setReactorState('processing', 'VALUTAZIONE', 'STIMA PREZZO & COPY');
  document.getElementById('resp-tag').textContent = 'ANALISI MARKETPLACE';
  document.getElementById('resp-body').textContent = 'Analisi prezzi di mercato e generazione annuncio persuasivo in corso...';

  try {
    const r = await fetch(API + '/api/workflow/marketplace', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({item, condition, platforms})
    });
    const d = await r.json();
    document.getElementById('resp-body').textContent = d.listing_text || 'Annuncio generato.';
    addEvent('ai', `🏷️ Inserzione Marketplace generata da ${d.model}`);

    if (bioCortex) bioCortex.addSynapseNode(item.slice(0, 15), '#f59e0b', 'Articolo in Vendita', d.listing_text.slice(0, 100));

    await fetch(API + '/api/kanban/add', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        title: `Vendita: ${item.slice(0, 40)}`,
        description: `Stima e copy per ${platforms}`,
        assignee: 'AG-SocialMedia',
        lane: 'ready'
      })
    });
    refreshKanban();
    switchMasterView('jarvis');
  } catch (e) {
    document.getElementById('resp-body').textContent = `Errore marketplace: ${e.message}`;
  }
}

// ── HERMES KANBAN ENGINE ─────────────────────────────────────────
async function refreshKanban() {
  try {
    const r = await fetch(API + '/api/kanban');
    if (!r.ok) return;
    const d = await r.json();
    kanbanLanesData = d.lanes || {};
    renderKanbanLanes(kanbanLanesData);
  } catch (e) {}
}

function timeAgo(ts) {
  const diff = Math.floor(Date.now() / 1000) - ts;
  if (diff < 60) return 'JUST NOW';
  if (diff < 3600) return `${Math.floor(diff / 60)}M AGO`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}H AGO`;
  return `${Math.floor(diff / 86400)}D AGO`;
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
      <div class="k-card" onclick="cardDetails('${c.id}')">
        <div class="kc-top">
          <span class="kc-id">${c.id}</span>
          ${c.dependencies ? `<span style="font-size:0.58rem; color:#a855f7; border:1px solid #a855f7; padding:1px 3px; border-radius:2px;">🔗 Waits: ${c.dependencies}</span>` : ''}
          <span class="kc-time">${timeAgo(c.created_at)}</span>
        </div>
        <div class="kc-title">${c.title}</div>
        ${c.description ? `<div class="kc-desc">${c.description}</div>` : ''}
        ${c.result ? `<div class="kc-result"><b>✓ Output:</b> ${c.result}</div>` : ''}
        <div class="kc-bottom">
          <span class="kc-assignee">${c.assignee}</span>
          <div class="kc-actions">
            ${lane !== 'ready' && lane !== 'in_progress' && lane !== 'done' ? `<button class="kc-btn" onclick="event.stopPropagation(); moveTask('${c.id}', 'ready')">➔ Ready</button>` : ''}
            ${lane === 'ready' ? `<button class="kc-btn" onclick="event.stopPropagation(); moveTask('${c.id}', 'in_progress')">▶️ Run</button>` : ''}
            ${lane !== 'done' ? `<button class="kc-btn" onclick="event.stopPropagation(); moveTask('${c.id}', 'done')">✓ Done</button>` : ''}
          </div>
        </div>
      </div>
    `).join('');
  });
}

function filterKanbanCards() { renderKanbanLanes(kanbanLanesData); }

async function moveTask(taskId, newLane) {
  try {
    const r = await fetch(API + '/api/kanban/move', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({task_id: taskId, lane: newLane})
    });
    const d = await r.json();
    kanbanLanesData = d.lanes;
    renderKanbanLanes(kanbanLanesData);
    if (bioCortex) bioCortex.pulseNeuron('hermes');
  } catch (e) {}
}

async function openNewTaskModal() {
  const title = prompt('Inserisci il Titolo del nuovo Task per Hermes:');
  if (!title) return;
  const assignee = prompt('Assegna ad Agente:\n(AG-EBGStudio, AG-MailMaster, AG-SocialMedia, AG-LegalVault, AG-WebIntel, UNASSIGNED)', 'AG-EBGStudio');

  try {
    const r = await fetch(API + '/api/kanban/add', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({title, assignee: assignee || 'UNASSIGNED', lane: 'ready'})
    });
    const d = await r.json();
    kanbanLanesData = d.lanes;
    renderKanbanLanes(kanbanLanesData);
    if (bioCortex) bioCortex.addSynapseNode(title.slice(0, 15), '#00d4ff', `Task ${assignee}`, title);
  } catch (e) {}
}

async function launchLevel5Pipeline() {
  const topic = prompt('Inserisci il Topic per la Pipeline Level 5 (Parallel + DAG Gap Analysis):', 'EBGS Unreal Engine 5.8 Survival MMO');
  if (!topic) return;

  if (bioCortex) {
    bioCortex.pulseNeuron('hermes');
    bioCortex.pulseNeuron('ebgs');
  }

  alert('🚀 PIPELINE LEVEL 5 AVVIATA!\n\n1. T1 (AG-WebIntel) e T2 (AG-SocialMedia) in parallelo.\n2. T3 (Analyst) calcola l\'Angle Gap.\n3. T4 (Writer) produce i Concept Video!');

  try {
    const r = await fetch(API + '/api/kanban/level5', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({topic})
    });
    const d = await r.json();
    kanbanLanesData = d.lanes;
    renderKanbanLanes(kanbanLanesData);
    if (bioCortex) bioCortex.addSynapseNode('Angle Gap UE5', '#a855f7', 'Analisi Gap Competitor', topic);

    let pollCount = 0;
    const interval = setInterval(async () => {
      await refreshKanban();
      pollCount++;
      if (pollCount > 8) clearInterval(interval);
    }, 2500);
  } catch (e) {
    alert(`Errore pipeline: ${e.message}`);
  }
}

function cardDetails(id) {
  for (const lane of Object.values(kanbanLanesData)) {
    const found = lane.find(c => c.id === id);
    if (found) {
      alert(`📋 DETTAGLI TASK HERMES [${found.id}]\n\nTitolo: ${found.title}\nAssegnato a: ${found.assignee}\nColonna: ${found.lane.toUpperCase()}\n\nRisultato: ${found.result || 'In attesa di completamento'}`);
      return;
    }
  }
}

// ── AUDIO & CEREBRO JARVIS ENGINE ────────────────────────────────
let audioCtx = null;
let analyser = null;
let microphoneStream = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let animFrameId = null;

function initAudioContext() {
  if (audioCtx) return;
  try {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    audioUnlocked = true;
  } catch (e) {}
}

window.addEventListener('click', initAudioContext, { once: true });
window.addEventListener('touchstart', initAudioContext, { once: true });
window.addEventListener('keydown', initAudioContext, { once: true });

function playSound(type) {
  try {
    initAudioContext();
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    const now = audioCtx.currentTime;

    if (type === 'start') {
      osc.frequency.setValueAtTime(450, now);
      osc.frequency.exponentialRampToValueAtTime(900, now + 0.08);
      gain.gain.setValueAtTime(0.2, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
      osc.start(now); osc.stop(now + 0.08);
    } else if (type === 'end') {
      osc.frequency.setValueAtTime(900, now);
      osc.frequency.exponentialRampToValueAtTime(450, now + 0.08);
      gain.gain.setValueAtTime(0.2, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
      osc.start(now); osc.stop(now + 0.08);
    }
  } catch (e) {}
}

function startVuMeter(stream) {
  initAudioContext();
  if (!audioCtx) return;

  const source = audioCtx.createMediaStreamSource(stream);
  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 64;
  source.connect(analyser);

  const dataArray = new Uint8Array(analyser.frequencyBinCount);
  const vuBar = document.getElementById('vu-meter-bar');
  const vuText = document.getElementById('vu-meter-val');

  function renderVu() {
    if (!isRecording) return;
    analyser.getByteFrequencyData(dataArray);
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
    const avg = sum / dataArray.length;
    const pct = Math.min(100, Math.round((avg / 128) * 100));

    if (vuBar) vuBar.style.width = `${pct}%`;
    if (vuText) vuText.textContent = `${pct}%`;
    animFrameId = requestAnimationFrame(renderVu);
  }
  renderVu();
}

async function startRecording() {
  if (isBusy || isRecording) return;
  initAudioContext();

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
      cancelAnimationFrame(animFrameId);
      const vuBar = document.getElementById('vu-meter-bar');
      if (vuBar) vuBar.style.width = '0%';

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
    if (btn) btn.classList.add('active');
    setReactorState('speaking', 'LISTEN', 'ASCOLTO ATTIVO');
    startVuMeter(microphoneStream);
    if (bioCortex) bioCortex.pulseNeuron('badr');
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
    if (btn) btn.classList.remove('active');
  } catch (e) {}
}

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
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
    if (e.key === 'Enter' && !e.shiftKey) return;
  }
  const parts = voiceHotkey.split('+');
  let match = true;
  if (parts.includes('Control') && !e.ctrlKey) match = false;
  if (parts.includes('Alt') && !e.altKey) match = false;
  if (parts.includes('Shift') && !e.shiftKey) match = false;
  if (parts.includes('Win') && !e.metaKey) match = false;
  const mainKey = parts[parts.length - 1].toLowerCase();
  if (mainKey === 'space' && e.code !== 'Space') match = false;
  else if (mainKey !== 'space' && e.key.toLowerCase() !== mainKey) match = false;

  if (match) {
    e.preventDefault();
    if (!isRecording) startRecording();
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
  const txt = document.getElementById('core-text');
  const sub_ = document.getElementById('core-sub');
  if (core) core.className = 'reactor-core' + (state ? ` ${state}` : '');
  if (txt && label) txt.textContent = label;
  if (sub_ && sub) sub_.textContent = sub;
}

async function speak(text) {
  const wf = document.getElementById('waveform');
  if (wf) wf.classList.add('active');
  setReactorState('speaking', 'SPEAK', 'JARVIS PARLA');
  if (window.connectomeEngine) window.connectomeEngine.setSpeaking(true);
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

      // Connect to Stark Armor HUD DSP Filter if AudioContext is available
      if (audioCtx) {
        try {
          const source = audioCtx.createMediaElementSource(currentAudio);
          
          // 1. High-Pass Filter (Helmet clarity > 130Hz)
          const highpass = audioCtx.createBiquadFilter();
          highpass.type = 'highpass';
          highpass.frequency.setValueAtTime(135, audioCtx.currentTime);

          // 2. Peaking Resonator (Iconic 3.2kHz crystal metallic timbre)
          const peak = audioCtx.createBiquadFilter();
          peak.type = 'peaking';
          peak.frequency.setValueAtTime(3200, audioCtx.currentTime);
          peak.Q.setValueAtTime(2.2, audioCtx.currentTime);
          peak.gain.setValueAtTime(4.0, audioCtx.currentTime);

          // 3. Dynamics Compressor (Cinematic Marvel Dialogue)
          const comp = audioCtx.createDynamicsCompressor();
          comp.threshold.setValueAtTime(-16, audioCtx.currentTime);
          comp.knee.setValueAtTime(10, audioCtx.currentTime);
          comp.ratio.setValueAtTime(4.5, audioCtx.currentTime);
          comp.attack.setValueAtTime(0.003, audioCtx.currentTime);
          comp.release.setValueAtTime(0.2, audioCtx.currentTime);

          const speakerAnalyser = audioCtx.createAnalyser();
          speakerAnalyser.fftSize = 64;

          source.connect(highpass);
          highpass.connect(peak);
          peak.connect(comp);
          comp.connect(speakerAnalyser);
          speakerAnalyser.connect(audioCtx.destination);

          if (window.connectomeEngine) window.connectomeEngine.setAudioAnalyser(speakerAnalyser);
        } catch (dspErr) {
          // If already connected, default output
        }
      }

      currentAudio.onended = () => {
        if (wf) wf.classList.remove('active');
        setReactorState('', 'READY', 'IN ATTESA');
        if (window.connectomeEngine) window.connectomeEngine.setAudioAnalyser(null);
        isBusy = false;
        document.getElementById('send-btn').disabled = false;
      };
      currentAudio.play().catch(() => {});
    } else {
      if (wf) wf.classList.remove('active');
      setReactorState('', 'READY', 'IN ATTESA');
      if (window.connectomeEngine) window.connectomeEngine.setSpeaking(false);
      isBusy = false;
      document.getElementById('send-btn').disabled = false;
    }
  } catch (e) {
    if (wf) wf.classList.remove('active');
    setReactorState('', 'READY', 'IN ATTESA');
    if (window.connectomeEngine) window.connectomeEngine.setSpeaking(false);
    isBusy = false;
    document.getElementById('send-btn').disabled = false;
  }
}

async function sendCommand(prompt) {
  if (!prompt || !prompt.trim() || isBusy) return;
  isBusy = true;
  initAudioContext();
  document.getElementById('send-btn').disabled = true;
  document.getElementById('prompt-input').value = '';

  const model = document.getElementById('model-select').value;
  addEvent('usr', prompt);
  setReactorState('processing', 'PROC', 'NEURAL THINKING');
  if (window.connectomeEngine) window.connectomeEngine.setThinking(true);
  document.getElementById('resp-tag').textContent = 'PROCESSING';
  document.getElementById('resp-body').textContent = '...';

  if (bioCortex) bioCortex.pulseNeuron('badr');

  try {
    const r = await fetch(API + '/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({prompt, model})
    });
    if (window.connectomeEngine) window.connectomeEngine.setThinking(false);
    const d = await r.json();
    const reply = d.response || 'Nessuna risposta.';
    const modelUsed = d.model_used || model;

    document.getElementById('resp-body').textContent = '';
    let i = 0;
    const typeInterval = setInterval(() => {
      document.getElementById('resp-body').textContent += reply[i] || '';
      i++;
      if (i >= reply.length) clearInterval(typeInterval);
    }, 10);

    addEvent('ai', reply.slice(0, 140) + (reply.length > 140 ? '…' : ''));
    document.getElementById('hud-status').textContent = `[${modelUsed}]`;

    if (bioCortex) bioCortex.addSynapseNode(prompt.slice(0, 14), '#00d4ff', 'Query Utente', prompt);

    await speak(reply);
  } catch (e) {
    document.getElementById('resp-body').textContent = `[ERRORE]: ${e.message}`;
    addEvent('err', e.message);
    setReactorState('', 'ERROR', 'ERRORE RETE');
    isBusy = false;
    document.getElementById('send-btn').disabled = false;
  }
}

async function queryVault(cat) {
  addEvent('sys', `Query Vault: ${cat}...`);
  if (bioCortex) bioCortex.pulseNeuron('vault');
  try {
    const r = await fetch(API + `/api/vault/${cat}`);
    const d = await r.json();
    if (d.items && d.items.length) {
      document.getElementById('resp-body').textContent = `📁 VAULT [${cat.toUpperCase()}]:\n\n` + d.items.join('\n');
      addEvent('ok', `Vault: ${d.items.length} record caricati.`);
    } else {
      document.getElementById('resp-body').textContent = `Nessun record trovato per ${cat}.`;
    }
  } catch (e) {
    addEvent('err', `Errore query: ${e.message}`);
  }
}

function sendQuick(text) { sendCommand(text); }
function clearLog() {
  document.getElementById('event-stream').innerHTML = '';
  document.getElementById('resp-body').textContent = 'Console resettata.';
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  event.target.classList.add('active');
  const target = document.getElementById('tab-' + tabId);
  if (target) target.classList.add('active');
}

let ambientPlexus = null;

function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('active');
}

async function submitSendEmail() {
  const to = document.getElementById('email-to').value.trim();
  const subject = document.getElementById('email-subject').value.trim();
  const body = document.getElementById('email-body').value.trim();

  if (!to || !subject || !body) {
    alert('Compila tutti i campi dell\'email.');
    return;
  }

  addEvent('sys', `Invio email a ${to}...`);
  if (ambientPlexus) ambientPlexus.setThinking(true);

  try {
    const r = await fetch(API + '/api/mail/send', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({to, subject, body})
    });
    const d = await r.json();
    if (d.status === 'SENT') {
      closeModal('modal-send-email');
      addEvent('ok', `Email inviata con successo a ${to} (ID: ${d.email_id})`);
      speak(`Email inviata con successo al destinatario ${to}, Signore. La ricevuta è archiviata nel Vault.`);
    }
  } catch (e) {
    addEvent('err', `Errore invio email: ${e.message}`);
  } finally {
    if (ambientPlexus) ambientPlexus.setThinking(false);
  }
}

async function executeLiveSift() {
  const query = document.getElementById('sift-query').value.trim();
  const resContainer = document.getElementById('sift-results');
  resContainer.innerHTML = '<div style="color:#00d4ff; font-size:0.8rem; padding:8px;">Scansione in corso...</div>';

  try {
    const r = await fetch(API + `/api/mail/search?q=${encodeURIComponent(query)}`);
    const d = await r.json();
    if (d.emails && d.emails.length) {
      resContainer.innerHTML = d.emails.map(em => `
        <div style="background:#020810; border:1px solid rgba(0,212,255,0.25); border-radius:4px; padding:10px;">
          <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#00ff88; font-weight:700;">
            <span>${em.sender}</span>
            <span>${em.category} · ${em.amount > 0 ? em.amount + ' €' : 'DOC'}</span>
          </div>
          <div style="font-weight:600; font-size:0.85rem; color:#fff; margin:4px 0;">${em.subject}</div>
          <div style="font-size:0.75rem; color:#94a3b8;">${em.body.slice(0, 130)}...</div>
        </div>
      `).join('');
    } else {
      resContainer.innerHTML = '<div style="color:#94a3b8; font-size:0.8rem; padding:8px;">Nessuna email trovata per questo criterio.</div>';
    }
  } catch (e) {
    resContainer.innerHTML = `<div style="color:#ef4444; font-size:0.8rem; padding:8px;">Errore ricerca: ${e.message}</div>`;
  }
}

function calcPrevTotal() {
  const mq = parseFloat(document.getElementById('prev-mq').value) || 0;
  const piano = parseFloat(document.getElementById('prev-piano').value) || 0;
  const asc = parseFloat(document.getElementById('prev-asc').value) || 0;
  const smalt = parseFloat(document.getElementById('prev-smalt').value) || 0;

  const base = mq * 8.0;
  const total = base + piano + asc + smalt;
  const display = document.getElementById('prev-totale-display');
  if (display) display.textContent = total.toLocaleString('it-IT', {minimumFractionDigits: 2}) + ' € + IVA';
  return total;
}

async function submitPreventivo() {
  const mq = document.getElementById('prev-mq').value;
  const total = calcPrevTotal();
  closeModal('modal-preventivo');
  
  const prompt = `JARVIS, registra formalmente il preventivo per lo sgombero di un immobile da ${mq} mq. Totale calcolato: ${total}€ + IVA.`;
  sendCommand(prompt);
}

window.addEventListener('DOMContentLoaded', async () => {
  updateHotkeyDisplay();
  refreshKanban();
  loadTunnelsConfig();

  // Initialize Hollywood Ambient Neural Plexus
  if (window.HollywoodNeuralPlexus) {
    ambientPlexus = new window.HollywoodNeuralPlexus('ambient-synapse-bg');
  }

  // Initialize 3D Bio-Neural Cortex Laboratory
  if (window.BioNeural3DCortex) {
    bioCortex = new window.BioNeural3DCortex('synapseCanvas', 'synapseCanvasWrapper');
  }

  const micBtn = document.getElementById('mic-btn');
  if (micBtn) {
    micBtn.addEventListener('mousedown', startRecording);
    micBtn.addEventListener('mouseup', stopRecording);
    micBtn.addEventListener('touchstart', (e) => { e.preventDefault(); startRecording(); });
    micBtn.addEventListener('touchend', (e) => { e.preventDefault(); stopRecording(); });
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
});
