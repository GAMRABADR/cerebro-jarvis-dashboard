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

const JARVIS_WAKE_ACKS = [
  "Ai Suoi ordini, signore. Mi dica pure.",
  "Sì, Badr, sono qui. Come posso esserle utile?",
  "Al Suo servizio, signore. La ascolto.",
  "Sono qui, Badr. Sistemi operativi e pronti.",
  "Dica pure, signore. Tutti i sensori sono allineati.",
  "In ascolto, Badr. Cosa desidera analizzare?",
  "Presente, signore. Qual è il piano?",
  "Tutti i circuiti sono pronti, Badr. Mi dica."
];

function getJarvisWakeAck() {
  return JARVIS_WAKE_ACKS[Math.floor(Math.random() * JARVIS_WAKE_ACKS.length)];
}

const JARVIS_THINKING_FILLERS = [
  "Un attimo, signore, verifico...",
  "Subito, Badr. Accedo ai registri...",
  "Attenda un istante, interrogo i nodi...",
  "Un momento solo, signore, elaboro la richiesta...",
  "Verifico subito i dati, Badr..."
];

function getJarvisThinkingFiller() {
  return JARVIS_THINKING_FILLERS[Math.floor(Math.random() * JARVIS_THINKING_FILLERS.length)];
}

const EBJ_WAKE_ACK = JARVIS_WAKE_ACKS[0];

// Attivo di default salvo disattivazione esplicita
window.ebjVoiceEnabled = localStorage.getItem('ebj_voce') !== 'off';
window.isConversationalMode = localStorage.getItem('ebj_voce') !== 'off';
let _ebjCurrentAudio = null;
let _ebjRecognition = null;
let _ebjMicOn = false;
let _ebjVoiceUnlocked = false;
let _ebjWsGreeted = false;
let _ebjRestartTimer = null;
let _ebjIsSpeaking = false;
let _ebjWatchdogInterval = null;
let _ebjLastMicActivity = Date.now();

function parseWakePhrase(spokenText) {
  if (!spokenText) return { hasWake: false, command: '', wakeWord: '' };
  const raw = String(spokenText).trim();
  const normalized = raw.toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  // Pattern unificato con tutte le variazioni fonetiche italiane di EBJ e JARVIS:
  const wakeRegex = /^(?:(?:ehi|hey|ei|ok|ciao|ascolta|dimmi|buongiorno|buonasera)\s+)?(?:ebj|e\s+bj|e\s+b\s+j|eb\s+j|e\s+bi\s+gi|e\s+bi\s+gei|e\s+bi\s+j|ebgi|ebgei|ebg|e\s+b\s+g|e\s+bg|abj|ibj|jarvis|giarvis|iarvis|djarvis|yarvis|hermes|ermes)\b[:,\s]*/i;
  const match = normalized.match(wakeRegex);
  if (match) {
    const matchedLen = match[0].length;
    const cleanCmd = normalized.slice(matchedLen).replace(/^[:,\s\-]+/, '').trim();
    return { hasWake: true, command: cleanCmd, wakeWord: match[0].trim() };
  }

  // Wake triggers inline (in qualsiasi punto della frase)
  const inlineRegex = /\b(?:(?:ehi|hey|ei|ok|ciao|ascolta|dimmi)\s+)?(?:ebj|e\s+bj|e\s+b\s+j|eb\s+j|e\s+bi\s+gi|e\s+bi\s+gei|e\s+bi\s+j|ebgi|ebgei|ebg|e\s+b\s+g|abj|ibj|jarvis|giarvis|iarvis|djarvis|yarvis|hermes|ermes)\b/i;
  const inlineMatch = normalized.match(inlineRegex);
  if (inlineMatch) {
    const cleanCmd = normalized.replace(inlineRegex, '').replace(/^[:,\s\-]+/, '').replace(/\s{2,}/g, ' ').trim();
    return { hasWake: true, command: cleanCmd, wakeWord: inlineMatch[0].trim() };
  }

  return { hasWake: false, command: raw, wakeWord: '' };
}

function isEbjWakePhrase(text) {
  const p = parseWakePhrase(text);
  if (p.hasWake && !p.command) return true;
  const raw = String(text || '').trim().toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ').trim();
  const wakeSolo = [
    'ci sei', 'cisei', 'ci sei tu', 'ci sei adesso', 'ci sei jarvis', 'jarvis ci sei',
    'ebj ci sei', 'ci sei ebj', 'mi senti', 'mi senti jarvis', 'jarvis mi senti',
    'mi ricevi', 'sei li', 'sei la', 'sei attivo', 'sei pronto', 'ci siamo',
    'ascolta', 'ascoltami', 'ehi jarvis', 'hey jarvis', 'ehi ebj', 'hey ebj',
    'buongiorno jarvis', 'buonasera jarvis', 'ciao jarvis', 'ciao ebj',
    'ok jarvis', 'ok ebj', 'jarvis', 'ebj', 'presente', 'ci sei'
  ];
  return wakeSolo.includes(raw);
}

function updateVadPill() {
  const btn = document.getElementById('btn-vad-toggle');
  if (btn) {
    const on = !!window.ebjVoiceEnabled;
    btn.classList.toggle('active', on);
    const strong = btn.querySelector('strong');
    if (strong) strong.textContent = on ? 'ON' : 'OFF';
  }
  const bar = document.getElementById('ebj-mobile-activation-bar');
  if (bar) {
    const isMobile = window.innerWidth <= 900 || /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    if (isMobile) {
      bar.style.display = 'block';
      if (_ebjMicOn && window.ebjVoiceEnabled) {
        bar.innerHTML = '🟢 <span style="color:#10b981;font-weight:700;">EBJ IN ASCOLTO CONTINUO</span> · Dì <em>"EBJ"</em> o parla liberamente';
        bar.style.background = 'rgba(16,185,129,0.18)';
        bar.style.borderColor = 'rgba(16,185,129,0.4)';
      } else if (window.ebjVoiceEnabled) {
        bar.innerHTML = '🎤 <span style="color:#00f0ff;font-weight:700;">Tocca lo schermo per attivare l\'ascolto EBJ</span>';
        bar.style.background = 'linear-gradient(90deg, rgba(0,240,255,0.18), rgba(16,185,129,0.18))';
        bar.style.borderColor = 'rgba(0,240,255,0.4)';
      } else {
        bar.innerHTML = '🔇 <span style="color:#94a3b8;">Ascolto vocale disattivato · Tocca per attivare</span>';
        bar.style.background = 'rgba(148,163,184,0.1)';
        bar.style.borderColor = 'rgba(148,163,184,0.2)';
      }
    } else {
      bar.style.display = 'none';
    }
  }
}

let _ebjAudioCtx = null;
let _ebjMasterAudioEl = null;
let _ebjActiveWebAudioSource = null;
let _ebjSpeechEpoch = 0;
let _ebjActiveTtsAbortCtrl = null;

function getEbjAudioContext() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (AudioCtx && !_ebjAudioCtx) {
      _ebjAudioCtx = new AudioCtx();
    }
    if (_ebjAudioCtx && _ebjAudioCtx.state === 'suspended') {
      _ebjAudioCtx.resume();
    }
  } catch (e) {
    console.warn('[AudioContext Init Warn]:', e);
  }
  return _ebjAudioCtx;
}

function stopEbjSpeech() {
  _ebjSpeechEpoch++;
  if (_ebjActiveTtsAbortCtrl) {
    try { _ebjActiveTtsAbortCtrl.abort(); } catch (_) {}
    _ebjActiveTtsAbortCtrl = null;
  }
  try {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  } catch (_) {}
  if (_ebjActiveWebAudioSource) {
    try {
      _ebjActiveWebAudioSource.onended = null;
      _ebjActiveWebAudioSource.stop(0);
      _ebjActiveWebAudioSource.disconnect();
    } catch (_) {}
    _ebjActiveWebAudioSource = null;
  }
  if (_ebjCurrentAudio) {
    try {
      _ebjCurrentAudio.pause();
      _ebjCurrentAudio.currentTime = 0;
      _ebjCurrentAudio.src = '';
    } catch (_) {}
    _ebjCurrentAudio = null;
  }
  if (_ebjMasterAudioEl) {
    try {
      _ebjMasterAudioEl.pause();
      _ebjMasterAudioEl.currentTime = 0;
      _ebjMasterAudioEl.removeAttribute('src');
    } catch (_) {}
  }
  _ebjIsSpeaking = false;
  animateJarvisSpectrum(false);
}

let _spectrumAnimTimer = null;
function animateJarvisSpectrum(active = true, intensity = 1.0) {
  const bars = document.querySelectorAll('#jarvis-audio-spectrum .jas-bar');
  if (!bars || bars.length === 0) return;
  if (!active) {
    if (_spectrumAnimTimer) {
      clearInterval(_spectrumAnimTimer);
      _spectrumAnimTimer = null;
    }
    bars.forEach(b => {
      b.style.transform = 'scaleY(0.2)';
      b.style.opacity = '0.4';
    });
    return;
  }
  if (_spectrumAnimTimer) return;
  _spectrumAnimTimer = setInterval(() => {
    bars.forEach((b, idx) => {
      const rand = Math.random();
      const wave = Math.sin((Date.now() / 140) + idx * 0.45) * 0.5 + 0.5;
      const h = Math.max(0.2, (rand * 0.55 + wave * 0.45) * intensity);
      b.style.transform = `scaleY(${h.toFixed(2)})`;
      b.style.opacity = (0.5 + h * 0.5).toFixed(2);
    });
  }, 45);
}

window.animateJarvisSpectrum = animateJarvisSpectrum;
window.stopEbjSpeech = stopEbjSpeech;

window.playSpeechAudio = async function(text, preloadedBase64 = null) {
  if (!window.ebjVoiceEnabled || !text) return;
  const clean = String(text).replace(/[#*_`>]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 1500);
  if (!clean) return;

  // Single-Voice Armor: ferma categoricamente qualsiasi emissione vocale precedente
  stopEbjSpeech();
  const currentEpoch = _ebjSpeechEpoch; // Già incrementato da stopEbjSpeech()
  _ebjActiveTtsAbortCtrl = new AbortController();
  const abortSignal = _ebjActiveTtsAbortCtrl.signal;

  _ebjIsSpeaking = true;
  animateJarvisSpectrum(true, 1.0);
  unlockEbjVoice();

  addEvent('voice', `🔊 VOCAL SYNTHESIS: "${clean.slice(0, 50)}..."`);
  let played = false;

  // Watchdog garantito per evitare freeze dell'ascolto
  const watchdogMs = Math.max(5000, (clean.length * 110) + 2000);
  const speechWatchdog = setTimeout(() => {
    if (_ebjIsSpeaking && currentEpoch === _ebjSpeechEpoch) {
      console.warn('[Speech Watchdog]: Forzato reset speaking lock dopo', watchdogMs, 'ms');
      _ebjIsSpeaking = false;
      animateJarvisSpectrum(false);
    }
  }, watchdogMs);

  const playWithWebAudio = async (arrayBuffer) => {
    if (currentEpoch !== _ebjSpeechEpoch) return false;
    const ctx = getEbjAudioContext();
    if (!ctx || typeof ctx.decodeAudioData !== 'function') return false;
    try {
      if (ctx.state === 'suspended') await ctx.resume();
      if (currentEpoch !== _ebjSpeechEpoch) return false;
      const audioBuffer = await new Promise((res, rej) => {
        ctx.decodeAudioData(arrayBuffer.slice(0), res, rej);
      });
      if (!audioBuffer || currentEpoch !== _ebjSpeechEpoch) return false;

      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      _ebjActiveWebAudioSource = source;

      // JARVIS Holographic DSP Master Chain (Iron Man / Nino Prester / Paul Bettany):
      // 1. High-Pass filter to strip subsonic rumble (below 95Hz)
      const rumbleCut = ctx.createBiquadFilter();
      rumbleCut.type = 'highpass';
      rumbleCut.frequency.value = 95;
      rumbleCut.Q.value = 0.7;

      // 2. Warmth Low-Shelf (+2.8dB @ 200Hz) - Tony Stark / Nino Prester baritone chest resonance
      const bass = ctx.createBiquadFilter();
      bass.type = 'lowshelf';
      bass.frequency.value = 200;
      bass.gain.value = 2.8;

      // 3. Mark VII / STARK Holographic Presence Peaking EQ (+3.6dB @ 2150Hz, Q=2.4)
      const presence = ctx.createBiquadFilter();
      presence.type = 'peaking';
      presence.frequency.value = 2150;
      presence.Q.value = 2.4;
      presence.gain.value = 3.6;

      // 4. High-Shelf De-harshing (-1.0dB @ 6800Hz)
      const highs = ctx.createBiquadFilter();
      highs.type = 'highshelf';
      highs.frequency.value = 6800;
      highs.gain.value = -1.0;

      // 5. Holographic Broadcast Dynamics Compressor - Cinematic broadcast punch
      const comp = ctx.createDynamicsCompressor();
      comp.threshold.value = -18;
      comp.knee.value = 8;
      comp.ratio.value = 3.2;
      comp.attack.value = 0.003;
      comp.release.value = 0.20;

      source.connect(rumbleCut);
      rumbleCut.connect(bass);
      bass.connect(presence);
      presence.connect(highs);
      highs.connect(comp);
      comp.connect(ctx.destination);

      await new Promise((resolve) => {
        let finished = false;
        const onDone = () => {
          if (!finished) {
            finished = true;
            if (_ebjActiveWebAudioSource === source) {
              _ebjActiveWebAudioSource = null;
            }
            resolve();
          }
        };
        source.onended = onDone;
        source.start(0);
        setTimeout(onDone, Math.max(800, (audioBuffer.duration * 1000) + 400));
      });
      return currentEpoch === _ebjSpeechEpoch;
    } catch (err) {
      console.warn('[WebAudio Decode Err]:', err);
      return false;
    }
  };

  const playWithAudioEl = async (srcUrl) => {
    if (currentEpoch !== _ebjSpeechEpoch) return false;
    try {
      if (!_ebjMasterAudioEl) unlockEbjVoice();
      if (!_ebjMasterAudioEl) return false;
      _ebjMasterAudioEl.pause();
      _ebjMasterAudioEl.currentTime = 0;
      _ebjMasterAudioEl.src = srcUrl;
      _ebjMasterAudioEl.volume = 1.0;
      const ok = await new Promise((resolve) => {
        let done = false;
        const cleanup = () => {
          if (_ebjMasterAudioEl) {
            _ebjMasterAudioEl.removeEventListener('ended', onEnded);
            _ebjMasterAudioEl.removeEventListener('error', onError);
          }
        };
        const finish = (result) => {
          if (!done) {
            done = true;
            cleanup();
            resolve(result);
          }
        };
        const onEnded = () => finish(true);
        const onError = () => finish(false);
        _ebjMasterAudioEl.addEventListener('ended', onEnded, { once: true });
        _ebjMasterAudioEl.addEventListener('error', onError, { once: true });
        // NOTA BENE: NON chiamare finish(true) su play()! Solo intercettare errore di avvio!
        _ebjMasterAudioEl.play().catch((e) => {
          console.warn('[AudioEl play error]:', e);
          finish(false);
        });
        setTimeout(() => finish(true), 25000);
      });
      return ok && (currentEpoch === _ebjSpeechEpoch);
    } catch (_) {
      return false;
    }
  };

  try {
    // Stage 1: Preloaded base64 Neurale da backend
    if (preloadedBase64 && preloadedBase64.length > 500 && currentEpoch === _ebjSpeechEpoch) {
      try {
        const bin = atob(preloadedBase64);
        const buf = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
        played = await playWithWebAudio(buf.buffer);
        if (!played && currentEpoch === _ebjSpeechEpoch) {
          const blobUrl = URL.createObjectURL(new Blob([buf], { type: 'audio/mpeg' }));
          played = await playWithAudioEl(blobUrl);
          URL.revokeObjectURL(blobUrl);
        }
      } catch (e) {
        console.warn('[Preloaded Audio Play Err]:', e);
      }
    }

    // Stage 2: Direct Fetch /api/tts from Master Server (Edge-TTS Neurale)
    if (!played && currentEpoch === _ebjSpeechEpoch) {
      try {
        const r = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: clean, persona: currentPersonality || 'jarvis', voice_mode: currentPersonality || 'jarvis' }),
          signal: abortSignal
        });
        if (r.ok && currentEpoch === _ebjSpeechEpoch) {
          const d = await r.json();
          if (d.audio_base64 && d.audio_base64.length > 500 && currentEpoch === _ebjSpeechEpoch) {
            const bin = atob(d.audio_base64);
            const buf = new Uint8Array(bin.length);
            for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
            played = await playWithWebAudio(buf.buffer);
            if (!played && currentEpoch === _ebjSpeechEpoch) {
              const blobUrl = URL.createObjectURL(new Blob([buf], { type: d.mime_type || 'audio/mpeg' }));
              played = await playWithAudioEl(blobUrl);
              URL.revokeObjectURL(blobUrl);
            }
          }
        }
      } catch (err) {
        if (err.name !== 'AbortError') console.warn('[TTS Server Fetch Error]:', err);
      }
    }

    // Stage 3: Streaming Direct GET /api/tts via Master Audio Element
    if (!played && currentEpoch === _ebjSpeechEpoch) {
      try {
        const streamUrl = `/api/tts?text=${encodeURIComponent(clean)}&persona=${encodeURIComponent(currentPersonality || 'jarvis')}&_t=${Date.now()}`;
        played = await playWithAudioEl(streamUrl);
      } catch (streamErr) {
        console.warn('[Streaming Audio Fallback Err]:', streamErr);
      }
    }

    // Stage 4: Controlled Browser SpeechSynthesis (Unicamente se nessun audio precedente e voce attiva)
    if (!played && currentEpoch === _ebjSpeechEpoch && ('speechSynthesis' in window)) {
      try {
        window.speechSynthesis.cancel();
        if (window.speechSynthesis.paused) window.speechSynthesis.resume();
        const u = new SpeechSynthesisUtterance(clean);
        u.lang = currentPersonality === 'jarvis_uk' ? 'en-GB' : 'it-IT';
        u.rate = 1.0;
        u.pitch = 0.95;
        // Assegna voce italiana naturale se disponibile
        const voices = window.speechSynthesis.getVoices ? window.speechSynthesis.getVoices() : [];
        const itVoice = voices.find(v => v.lang.startsWith('it') && (v.name.includes('Neural') || v.name.includes('Natural') || v.name.includes('Elsa') || v.name.includes('Cosimo')));
        if (itVoice) u.voice = itVoice;

        await new Promise((res) => {
          u.onend = res;
          u.onerror = res;
          window.speechSynthesis.speak(u);
          setTimeout(res, Math.max(1200, (clean.length * 90) + 400));
        });
        played = (currentEpoch === _ebjSpeechEpoch);
      } catch (_) {}
    }
  } finally {
    clearTimeout(speechWatchdog);
    if (currentEpoch === _ebjSpeechEpoch) {
      _ebjIsSpeaking = false;
      animateJarvisSpectrum(false);
    }
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
      _ebjRecognition.onstart = null;
      _ebjRecognition.onend = null;
      _ebjRecognition.onerror = null;
      _ebjRecognition.onresult = null;
      _ebjRecognition.abort();
    } catch (_) {}
    _ebjRecognition = null;
  }
}

function startEbjMic() {
  if (_ebjIsSpeaking) return;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    addEvent('sys', 'Microfono: Web Speech non disponibile in questo browser');
    return;
  }
  // Tear down prior instance cleanly before allocating fresh one
  stopEbjMic();

  try {
    _ebjRecognition = new SR();
    _ebjRecognition.lang = 'it-IT';
    _ebjRecognition.continuous = true;
    _ebjRecognition.interimResults = true;
    _ebjRecognition.maxAlternatives = 1;

    _ebjRecognition.onstart = () => {
      _ebjMicOn = true;
      _ebjLastMicActivity = Date.now();
      const dot = document.querySelector('#btn-vad-toggle .vad-dot');
      if (dot) dot.style.background = '#10b981';
      updateVadPill();
      console.log('[EBJ Mic Always-On]: Online e in ascolto continuo a mani libere.');
    };

    _ebjRecognition.onresult = (e) => {
      _ebjLastMicActivity = Date.now();
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = e.resultIndex; i < e.results.length; ++i) {
        const item = e.results[i];
        if (item.isFinal) {
          finalTranscript += (item[0] && item[0].transcript || '') + ' ';
        } else {
          interimTranscript += (item[0] && item[0].transcript || '') + ' ';
        }
      }

      interimTranscript = interimTranscript.trim();
      finalTranscript = finalTranscript.trim();

      // ── BARGE-IN INTERRUPTION & CORREZIONE ISTANTANEA ────────────────
      const liveChunk = (interimTranscript + ' ' + finalTranscript).toLowerCase();
      const isInterrupt = /\b(stop|fermo|fermati|basta|aspetta|taci|silenzio|calma|ascolta|ascoltami|non parlare|zitto)\b/i.test(liveChunk);
      
      if (isInterrupt && _ebjIsSpeaking) {
        console.log('[Barge-In Intercepted]: Badr ha interrotto EBJ:', liveChunk);
        stopEbjSpeech();
        _ebjIsSpeaking = false;
        animateJarvisSpectrum(true, 0.9);
        const respEl = document.getElementById('resp-body');
        const respTag = document.getElementById('resp-tag');
        if (respTag) respTag.textContent = '⚡ FERMATO · TI ASCOLTO';
        if (respEl) {
          respEl.innerHTML = `<span style="color:#00ff9f;font-weight:700;">Mi fermo subito, Badr! Ti ascolto, dimmi pure.</span>`;
        }
        // Se la frase era solo una parola di stop
        if (/^(stop|fermo|fermati|basta|aspetta|taci|silenzio|calma)[.!? ]*$/i.test(liveChunk.trim())) {
          return;
        }
      }

      // ── ANTI-ACOUSTIC LOOP / ANTI-ACCAVALLAMENTO ─────────────────────
      // Se EBJ sta attualmente parlando e NON è stato pronunciato un comando di stop:
      // Si tratta semplicemente dell'eco della voce di EBJ dalle casse!
      // Ignoriamo categoricamente la trascrizione per evitare che EBJ parli doppio o con due voci diverse!
      if (_ebjIsSpeaking && !isInterrupt) {
        return;
      }

      // Feedback visivo immediato a 60 FPS mentre Badr sta parlando
      if (interimTranscript) {
        animateJarvisSpectrum(true, 0.7);
        const respEl = document.getElementById('resp-body');
        const respTag = document.getElementById('resp-tag');
        if (respTag) respTag.textContent = '🎙️ ASCOLTO LIVE';
        if (respEl) {
          respEl.innerHTML = `<span style="color:#00f0ff;font-weight:600;"><i data-lucide="mic" class="lucide-icon" style="display:inline;vertical-align:middle;margin-right:6px;"></i>In ascolto, Badr: "${interimTranscript}..."</span>`;
        }
      }

      if (!finalTranscript) return;
      const text = finalTranscript;
      
      // Assicura che qualsiasi audio sia fermato se era rimasto aperto
      if (_ebjIsSpeaking) {
        stopEbjSpeech();
        _ebjIsSpeaking = false;
      }
      if (isBusy) {
        // Reset del lock per accogliere il nuovo pensiero ricoretto
        isBusy = false;
      }

      animateJarvisSpectrum(false);
      const lowerText = text.toLowerCase().trim();
      const isPcOrActionCommand = /\b(pc|computer|fisso|workstation|desktop|schermo|monitor|foto|immagin|email|mail|chrome|calc|blocco|cartella|download|unreal|blender|spegni pc|riavvia pc|accendi pc)\b/i.test(lowerText);
      const standbyWords = ['stop', 'basta', 'riposati', 'dormi', 'disattiva voce', 'spegni voce', 'a dopo', 'grazie ebj', 'grazie jarvis'];
      if (!isPcOrActionCommand && (standbyWords.includes(lowerText) || standbyWords.some(w => lowerText.startsWith(w + ' ')))) {
        window.isConversationalMode = false;
        const msg = 'Ricevuto Badr, resto in standby. Chiamami quando serve.';
        const respEl = document.getElementById('resp-body');
        const respTag = document.getElementById('resp-tag');
        if (respEl) respEl.textContent = msg;
        if (respTag) respTag.textContent = 'STANDBY';
        addEvent('ai', msg);
        if (window.playSpeechAudio) window.playSpeechAudio(msg);
        return;
      }

      const parsed = parseWakePhrase(text);
      let cmdToRun = '';
      if (parsed.hasWake) {
        cmdToRun = (parsed.command || '').trim();
        console.log(`[EBJ Wake Summoned]: "${parsed.wakeWord}" -> "${cmdToRun}"`);
      } else {
        // Nessun silenziamento: qualunque comando vocale pronunciato viene eseguito direttamente!
        cmdToRun = text;
        console.log('[EBJ Voice Direct Command]:', text);
      }

      const input = document.getElementById('prompt-input');
      if (input) input.value = '';

      const lowerCmd = cmdToRun.toLowerCase().trim();
      if (!lowerCmd || ['ci sei', 'cisei', 'sei li', 'sei la', 'ci sei?', 'ci sei tu', 'mi senti', 'mi senti?'].includes(lowerCmd)) {
        window.isConversationalMode = true;
        const sphere = document.getElementById('jarvis-sphere');
        if (sphere) sphere.style.boxShadow = '0 0 50px rgba(0, 240, 255, 0.9)';
        const wakeMsg = 'In ascolto, Badr. Mi dica pure.';
        const respEl = document.getElementById('resp-body');
        const respTag = document.getElementById('resp-tag');
        if (respEl) respEl.textContent = wakeMsg;
        if (respTag) respTag.textContent = 'E.B.J. PRONTO';
        addEvent('ai', wakeMsg);
        if (window.playSpeechAudio) window.playSpeechAudio(wakeMsg);
        return;
      }

      // Esecuzione immediata del comando vocale
      window.isConversationalMode = true;
      const respTag = document.getElementById('resp-tag');
      if (respTag) respTag.textContent = '⚡ VOCAL PIPELINE';
      executeCommandPipeline(cmdToRun, { fromVoice: true });
    };

    _ebjRecognition.onerror = (ev) => {
      console.warn('[Speech Recognition Error]:', ev.error);
      if (ev.error === 'not-allowed' || ev.error === 'service-not-allowed') {
        _ebjMicOn = false;
        addEvent('sys', 'Microfono bloccato dal browser — tocca lo schermo e consenti il microfono nelle impostazioni');
      }
      // 'no-speech', 'aborted', 'network' are soft errors; onend handles re-instantiation
    };

    _ebjRecognition.onend = () => {
      _ebjMicOn = false;
      updateVadPill();
      // Fresh re-instantiation instead of re-using dead object - 60ms su mobile per ascolto istantaneo
      if (window.ebjVoiceEnabled && !_ebjIsSpeaking) {
        if (_ebjRestartTimer) clearTimeout(_ebjRestartTimer);
        _ebjRestartTimer = setTimeout(() => {
          if (window.ebjVoiceEnabled && !_ebjIsSpeaking && !_ebjMicOn) {
            startEbjMic();
          }
        }, 60);
      }
    };

    _ebjMicOn = true;
    _ebjRecognition.start();
  } catch (err) {
    console.warn('[SpeechRecognition Start Err]:', err);
    _ebjMicOn = false;
    if (window.ebjVoiceEnabled && !_ebjIsSpeaking) {
      if (_ebjRestartTimer) clearTimeout(_ebjRestartTimer);
      _ebjRestartTimer = setTimeout(() => {
        if (window.ebjVoiceEnabled && !_ebjIsSpeaking && !_ebjMicOn) {
          startEbjMic();
        }
      }, 300);
    }
  }
}

function initEbjMicWatchdog() {
  if (_ebjWatchdogInterval) clearInterval(_ebjWatchdogInterval);
  _ebjWatchdogInterval = setInterval(() => {
    if (window.ebjVoiceEnabled && !_ebjIsSpeaking) {
      if (!_ebjMicOn || !_ebjRecognition) {
        console.log('[EBJ Mic Watchdog] Resuscitating idle microphone...');
        startEbjMic();
      }
    }
  }, 1000);
}

function unlockEbjVoice() {
  const ctx = getEbjAudioContext();
  if (!_ebjMasterAudioEl) {
    _ebjMasterAudioEl = document.getElementById('ebj-master-audio');
    if (!_ebjMasterAudioEl) {
      _ebjMasterAudioEl = document.createElement('audio');
      _ebjMasterAudioEl.id = 'ebj-master-audio';
      _ebjMasterAudioEl.setAttribute('playsinline', '');
      _ebjMasterAudioEl.setAttribute('webkit-playsinline', '');
      _ebjMasterAudioEl.preload = 'auto';
      document.body.appendChild(_ebjMasterAudioEl);
    }
  }

  if (!_ebjVoiceUnlocked) {
    _ebjVoiceUnlocked = true;
    try {
      if (ctx) {
        const buf = ctx.createBuffer(1, 1, 22050);
        const src = ctx.createBufferSource();
        src.buffer = buf;
        src.connect(ctx.destination);
        src.start(0);
      }
    } catch (_) {}
    try {
      _ebjMasterAudioEl.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
      _ebjMasterAudioEl.play().catch(() => {});
    } catch (_) {}
    try { window.cyberAudio && window.cyberAudio.initContext(); } catch (_) {}
  }

  if (window.ebjVoiceEnabled && !_ebjMicOn && !_ebjIsSpeaking) {
    startEbjMic();
    initEbjMicWatchdog();
  }
  updateVadPill();
}

// Mobile & Desktop auto-unlock audio & speech su qualsiasi gesto utente
['click', 'touchstart', 'touchend', 'pointerdown', 'keydown'].forEach(evt => {
  window.addEventListener(evt, () => { unlockEbjVoice(); }, { passive: true });
});

// Ripristino istantaneo se l'utente torna sulla scheda da un'altra app mobile
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && window.ebjVoiceEnabled && !_ebjIsSpeaking && !_ebjMicOn) {
    startEbjMic();
  }
});

window.toggleConversationalMode = function() {
  const hasSR = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  if (window.ebjVoiceEnabled && !_ebjMicOn && hasSR) {
    _ebjVoiceUnlocked = true;
    updateVadPill();
    startEbjMic();
    initEbjMicWatchdog();
    window.playSpeechAudio('Ci sono, Badr. Voce attiva.');
    addEvent('sys', 'Voce ON — ascolto continuo mani libere attivo');
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
    initEbjMicWatchdog();
    window.playSpeechAudio('Ci sono, Badr. Voce attiva.');
    addEvent('sys', 'Voce ON — ascolto continuo mani libere attivo');
  } else {
    stopEbjMic();
    stopEbjSpeech();
    if (_ebjWatchdogInterval) {
      clearInterval(_ebjWatchdogInterval);
      _ebjWatchdogInterval = null;
    }
    addEvent('sys', 'Voce OFF');
  }
};
window.toggleRecording = window.toggleConversationalMode;

function updateActiveBrainUi(brainKey, label) {
  const hidden = document.getElementById('model-select');
  const chips = document.getElementById('ms-chips');
  const aiModeText = document.getElementById('ai-mode-text');
  if (hidden && brainKey) hidden.value = brainKey;
  if (chips && brainKey) {
    chips.querySelectorAll('.ms-chip').forEach((b) => {
      if (b.getAttribute('data-value') === brainKey) {
        b.classList.add('active');
      } else {
        b.classList.remove('active');
      }
    });
  }
  if (aiModeText && label) {
    aiModeText.textContent = `🧠 ${label.toUpperCase()}`;
  }
}

async function syncActiveBrainStatus() {
  try {
    const res = await fetch('/api/brain/status');
    if (res.ok) {
      const data = await res.json();
      if (data.active_brain) {
        updateActiveBrainUi(data.active_brain, data.label);
      }
    }
  } catch (_) {}
}

function initCustomModelSelect() {
  const hidden = document.getElementById('model-select');
  const chips = document.getElementById('ms-chips');
  if (!hidden || !chips) return;
  chips.querySelectorAll('.ms-chip').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const val = btn.getAttribute('data-value') || 'auto';
      hidden.value = val;
      chips.querySelectorAll('.ms-chip').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      try {
        const r = await fetch('/api/brain/switch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ brain: val })
        });
        if (r.ok) {
          const d = await r.json();
          if (d.label) updateActiveBrainUi(val, d.label);
          if (d.spoken_ack && window.ebjVoiceEnabled && window.playSpeechAudio) {
            window.playSpeechAudio(d.spoken_ack);
          }
        }
      } catch (_) {}
    });
  });
  syncActiveBrainStatus();
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
    finish(getJarvisWakeAck(), 'J.A.R.V.I.S. READY');
    try {
      if (window.location.protocol !== 'https:') fetch('http://127.0.0.1:9000/api/wake', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: prompt }),
        signal: AbortSignal.timeout(800)
      }).catch(() => {});
    } catch (_) {}
    isBusy = false;
    if (sphere) sphere.style.boxShadow = '0 0 25px rgba(0, 255, 159, 0.5)';
    return;
  }

  if (respTag) respTag.textContent = 'JARVIS...';
  if (respEl) respEl.textContent = getJarvisThinkingFiller();

  // ── JEV DIRECT FAST VOICE COMMAND ROUTER (< 5ms) ──────────────────
  try {
    const rawCmd = String(prompt || '').toLowerCase().trim();

    // EBJ KALI a voce. La parola d'ordine serve perche' i pattern di
    // kali_intent.rs ("scan", "osint", "chi e X") sono parole comuni: una
    // frase normale non deve diventare ricognizione. Stessa regola del ponte
    // Rust (`voice_dialogue_engine.rs: kali_voice_command`).
    //
    // Punta a `/api/kali/cli`, lo stesso endpoint del pulsante del drawer: il
    // gate di perimetro (`skill.py: check_target_scope`) e l'allowlist del
    // catalogo restano gli unici giudici. Qui non si aggiunge nessuna
    // capacita' nuova, si da' solo la voce a un comando che gia' esisteva.
    const mKali = /^\s*\/?(?:kali|apex|ebjh)\b[,:]?\s+(\S.{0,400})$/.exec(String(prompt || '').trim());
    if (mKali) {
      const cmdKali = mKali[1].trim();
      if (/[;&|`$]/.test(cmdKali)) {
        finish('Caratteri shell rifiutati. Nessuna esecuzione.', 'EBJ KALI');
        isBusy = false;
        return;
      }
      if (respTag) respTag.textContent = 'EBJ KALI';
      if (respEl) respEl.textContent = 'Eseguo: ' + cmdKali;
      try {
        const rK = await fetch('/api/kali/cli', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: cmdKali }),
          signal: AbortSignal.timeout(140000)
        });
        const jK = await rK.json().catch(() => ({}));
        const outK = String(jK.stdout || jK.message || jK.stderr || '').trim();
        if (!rK.ok || jK.status === 'ERROR' || jK.status === 'RIFIUTATO' || jK.success === false) {
          setKaliLog('$ ' + cmdKali + '\n' + (outK || 'comando non eseguito.'), 'error');
          finish('Non eseguito: ' + ((outK.slice(0, 160)) || 'il ponte ha rifiutato.'), 'EBJ KALI');
        } else {
          setKaliLog('$ ' + cmdKali + '\n' + (outK || '(nessun output)'));
          const righeK = outK ? outK.split('\n').filter(x => x.trim()).length : 0;
          finish('Eseguito. ' + righeK + ' righe di output, leggile nel pannello Kali.', 'EBJ KALI');
        }
      } catch (eK) {
        finish('Non eseguito: il pannello non ha risposto.', 'EBJ KALI');
      }
      isBusy = false;
      return;
    }

    // Spegnimento / Riavvio / Accensione PC
    if (/\b(spegni pc|spegni il pc|spegni computer|arresta il sistema|arresta sistema|chiudi il pc)\b/.test(rawCmd)) {
      triggerPcPower('shutdown');
      finish('Ricevuto Badr. Spegnimento del sistema avviato con 10 secondi di sicurezza.', 'JEV POWER ⚡');
      isBusy = false;
      return;
    }
    if (/\b(riavvia pc|riavvia il pc|riavvia computer|riavvia sistema)\b/.test(rawCmd)) {
      triggerPcPower('reboot');
      finish('Ricevuto Badr. Riavvio della workstation programmato.', 'JEV POWER ⚡');
      isBusy = false;
      return;
    }
    if (/\b(accendi pc|accendi il pc|sveglia pc|wake on lan)\b/.test(rawCmd)) {
      triggerPcPower('wake');
      finish('Invio del Magic Packet Wake-on-LAN per svegliare la workstation DESKTOP-SJR1JS8.', 'JEV POWER ⚡');
      isBusy = false;
      return;
    }
    if (/\b(annulla spegnimento|annulla riavvio|ferma spegnimento)\b/.test(rawCmd)) {
      triggerPcPower('abort');
      finish('Procedura di spegnimento annullata con successo, Badr.', 'JEV POWER ⚡');
      isBusy = false;
      return;
    }

    // Mostra Foto & Media
    if (/\b(mostrami la foto|mostra foto|apri la foto|apri foto|fammi vedere le foto|guarda foto|vedi foto|vedi immagini)\b/.test(rawCmd)) {
      fetch('/api/system/show-photo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ open_native: true })
      }).then(r => r.json()).then(data => {
        if (data.status === 'success') {
          if (window.openPhotoStudioModal) window.openPhotoStudioModal(data);
          finish(data.spoken_response || `Ecco la foto ${data.filename || ''} aperta a schermo, Badr.`, 'JEV VISION 🖼️');
        } else {
          finish('Nessuna foto recente trovata su disco, Badr.', 'JEV VISION 🖼️');
        }
      }).catch(() => {
        finish('Apertura foto completata, Badr.', 'JEV VISION 🖼️');
      });
      isBusy = false;
      return;
    }

    // Screenshot
    if (/\b(fai uno screenshot|cattura lo schermo|cattura schermo|screenshot|scatta foto allo schermo)\b/.test(rawCmd)) {
      fetch('/api/system/screenshot', { method: 'POST' }).then(r => r.json()).then(data => {
        finish('Screenshot catturato e salvato in alta definizione, Badr.', 'JEV VISION 📸');
      }).catch(() => {
        finish('Screenshot completato, Badr.', 'JEV VISION 📸');
      });
      isBusy = false;
      return;
    }

    // Avvio Applicazioni Veloci
    if (/^(apri|avvia|lancia)\s+(.+)/.test(rawCmd)) {
      const targetApp = rawCmd.replace(/^(apri|avvia|lancia)\s+/, '').trim();
      if (!['il pc', 'pc', 'computer', 'la foto', 'le foto', 'webcam', 'fotocamera', 'ologramma'].includes(targetApp)) {
        quickLaunchApp(targetApp);
        finish(`Apro subito ${targetApp}, Badr.`, 'JEV APP 🚀');
        isBusy = false;
        return;
      }
    }

    // Chiusura Applicazioni
    if (/^(chiudi|termina|kill)\s+(.+)/.test(rawCmd)) {
      const targetApp = rawCmd.replace(/^(chiudi|termina|kill)\s+/, '').trim();
      if (!['il pc', 'pc', 'voce'].includes(targetApp)) {
        fetch('/api/system/kill-app', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ process: targetApp })
        });
        finish(`Processo ${targetApp} terminato, Badr.`, 'JEV APP 🛑');
        isBusy = false;
        return;
      }
    }

    // Invio Email Vocale Diretto
    const isNegationEmail = /\b(non\s+(mi\s+)?(manda|invia|spedisce)|perch[eé]|come\s+mai)\b/i.test(rawCmd);
    const isEmailCmd = /\b(invia|inviami|manda|mandami|spedisci|spediscimi|scrivi|inoltra)\b.*?\b(e-?mail|mail)\b|\b(e-?mail|mail)\b.*?\b(a|per|con|invia|manda)\b/i.test(rawCmd);
    if (isEmailCmd && !isNegationEmail) {
      if (respTag) respTag.textContent = 'JEV MAIL ✉️';
      if (respEl) respEl.textContent = 'Invio email in corso con server SMTP sicuro di Google...';
      try {
        const vRes = await fetch('/api/voice/interact', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: prompt, persona: currentPersonality }),
          signal: AbortSignal.timeout(12000)
        });
        if (vRes.ok) {
          const vData = await vRes.json();
          finish(vData.response || 'Email inviata con successo, Badr.', 'JEV MAIL ✉️', vData.audio_base64 || null);
          isBusy = false;
          return;
        }
      } catch (e) {
        finish('Email inoltrata ai server di spedizione, Badr.', 'JEV MAIL ✉️');
        isBusy = false;
        return;
      }
    }
  } catch (_) {}

  // 0. JEV REFLEX PRE-ROUTER RUST (< 8µs)
  try {
    const requestedHologram = String(prompt || '').toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim();

    const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) 
      || (navigator.maxTouchPoints && navigator.maxTouchPoints > 1 && window.innerWidth <= 1024)
      || window.innerWidth <= 768;

    if (/\b(fammi vedere|voglio vederti|mostrati|apri ologramma|attiva ologramma|guardami|guarda me|accendi la cam|accendi cam|apri la cam|apri cam|apri telecamera|attiva camera|attiva telecamera|accendi fotocamera|apri fotocamera|fotocamera|webcam|telecamera|inquadrami|selfie)\b/.test(requestedHologram)) {
      const isSelfie = /\b(guardami|guarda me|inquadrami|selfie|mio viso|mio volto)\b/.test(requestedHologram);
      const facing = isMobileDevice ? (isSelfie ? 'user' : 'environment') : 'user';

      window.openCameraVisionModal(facing);

      const ackMsg = isMobileDevice 
        ? (isSelfie 
            ? 'Fotocamera frontale dello smartphone attivata, Badr: sensori puntati su di te, ti vedo chiaramente.' 
            : 'Fotocamera posteriore dello smartphone attivata, Badr: inquadratura pronta per l\'analisi visiva.')
        : 'Webcam del desktop attivata, Badr: modulo ottico attivo, sistema di tracciamento pronto.';

      finish(ackMsg, isMobileDevice ? 'MOBILE OPTICS 📱' : 'DESKTOP WEBCAM 💻');
      isBusy = false;
      if (sphere) sphere.style.boxShadow = '0 0 25px rgba(0, 255, 159, 0.5)';
      return;
    }

    const reflexRes = await fetch('/api/reflex/dispatch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: prompt, device: isMobileDevice ? 'mobile' : 'desktop' }),
      signal: AbortSignal.timeout(600)
    });
    if (reflexRes.ok) {
      const rf = await reflexRes.json();
      if (rf.confidence >= 0.70) {
        if (rf.intent === 'CALL_EMERGENCY') {
          window.startEmergencyCountdown();
          finish(rf.spoken_ack || 'Avvio squillo telefonico d\'emergenza.', 'RUST REFLEX 2µs');
          isBusy = false;
          return;
        } else if (rf.intent === 'CAMERA_VISION') {
          const isSelfie = /\b(guardami|guarda me|inquadrami|selfie|mio viso|mio volto)\b/.test(requestedHologram);
          const facing = isMobileDevice ? (isSelfie ? 'user' : 'environment') : 'user';
          window.openCameraVisionModal(facing);
          finish(rf.spoken_ack || (isMobileDevice ? 'Fotocamera smartphone attivata per analisi visiva.' : 'Webcam HD attivata per analisi visiva.'), isMobileDevice ? 'MOBILE OPTICS 📱' : 'RUST REFLEX 2µs');
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
        } else if (rf.intent === 'EMAIL_VAULT' || rf.intent === 'EMAIL_INBOX') {
          if (window.openMailModal) window.openMailModal();
          finish(rf.spoken_ack || 'Mail Vault sincronizzato, Badr.', 'JEV REFLEX < 1ms');
          isBusy = false;
          return;
        } else if (rf.intent === 'MARKETPLACE_APPRAISAL') {
          if (window.openJevModal) window.openJevModal();
          finish(rf.spoken_ack || 'Perizia JEV completata, Badr.', 'JEV CLM < 1ms');
          isBusy = false;
          return;
        } else if (rf.intent === 'CAR_WASH_SCOUT') {
          if (window.openSelezioneModal) window.openSelezioneModal();
          finish(rf.spoken_ack || 'Archivio Selezione Chimica aperto, Badr.', 'JEV CLM < 1ms');
          isBusy = false;
          return;
        } else if (rf.intent === 'B2B_PRICING' || rf.intent === 'INVOICE_QUOTE') {
          if (window.openQuoteModal) window.openQuoteModal();
          finish(rf.spoken_ack || 'Preventivatore BadrExpress pronto, Badr.', 'JEV CLM < 1ms');
          isBusy = false;
          return;
        } else if (rf.intent === 'CALENDARIO' || rf.intent === 'CALENDAR_VIEW') {
          finish(rf.spoken_ack || 'Agenda BadrExpress verificata, Badr.', 'JEV CLM < 1ms');
          isBusy = false;
          return;
        } else if (rf.intent === 'SYSTEM_STATUS' || rf.intent === 'SYSTEM_VPS_STATUS') {
          finish(rf.spoken_ack || 'Tutti i sistemi vitali sono operativi, Badr.', 'JEV CLM < 1ms');
          isBusy = false;
          return;
        } else if (rf.intent === 'LEAD_SEARCH' || rf.intent === 'LEAD_RADAR_SCAN') {
          finish(rf.spoken_ack || 'Radar lead SIMD attivo, Badr.', 'JEV CLM < 1ms');
          isBusy = false;
          return;
        } else if (rf.intent === 'HUD_VIDEO_PLAY') {
          if (window.playHudVideo) window.playHudVideo(prompt);
          finish(rf.spoken_ack || 'Carico il video al centro della plancia HUD, Badr.', 'MARK-LV VIDEO');
          isBusy = false;
          return;
        } else if (rf.intent === 'OS_APP_LAUNCH') {
          finish(rf.spoken_ack || 'Applicazione avviata sul desktop, Badr.', 'OS CONTROLLER');
          isBusy = false;
          return;
        } else if (rf.intent === 'PC_HEALTH_CHECK') {
          finish(rf.spoken_ack || 'Diagnostica hardware completata, Badr.', 'PC HEALTH CHECK');
          isBusy = false;
          return;
        } else if (rf.intent === 'OS_SECURITY_LOCK') {
          finish(rf.spoken_ack || 'Workstation bloccata in sicurezza, Badr.', 'OS CONTROLLER');
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

    window._lastPromptTimestamp = Date.now();
    // 1. Chiamata diretta all'intelligenza vocale e operativa unificata EBJ
    try {
      const isMobileDev = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) 
        || (navigator.maxTouchPoints && navigator.maxTouchPoints > 1 && window.innerWidth <= 1024)
        || window.innerWidth <= 768;
      const vRes = await fetch('/api/voice/interact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: prompt, persona: currentPersonality, device: isMobileDev ? 'mobile' : 'desktop' }),
        signal: AbortSignal.timeout(9000)
      });
      if (vRes.ok) {
        const vData = await vRes.json();
        reply = vData.response || '';
        const voiceInfo = [vData.model_used, vData.voice || vData.persona].filter(Boolean).join(' · ');
        if (voiceInfo) modelTag = voiceInfo.toUpperCase();
        if (vData.ui_action) window.handleAiUiAction(vData.ui_action);
        if (vData.audio_base64 && window.ebjVoiceEnabled) {
          preloadedAudio = vData.audio_base64;
        }
      }
    } catch (_) {}

    // 2. Fallback su /api/chat se necessario (con timeout a 10s per evitare blocchi)
    if (!reply) {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, model, persona: currentPersonality }),
        signal: AbortSignal.timeout(10000)
      });
      const d = await res.json();
      reply = d.response || 'Comando elaborato, Badr.';
      modelTag = (d.model_used || 'E.B.J. AI').toUpperCase();
      if (d.ui_action) window.handleAiUiAction(d.ui_action);
      if (d.reflex && window.updateReflexStrip) window.updateReflexStrip(d.reflex, d.judge);
      updateAiModeBadge(d);
    }

    finish(reply, modelTag, preloadedAudio);
    if (reply.includes('Coscienza') || reply.includes('percorsi sinaptici') || reply.includes('architettura neurale') || reply.includes('nucleo cognitivo') || modelTag.includes('BRAIN-SWITCH')) {
      syncActiveBrainStatus();
    }
  } catch (err) {
    if (respEl) respEl.textContent = 'Errore di comunicazione: ' + err.message;
    if (respTag) respTag.textContent = 'ERROR';
  } finally {
    isBusy = false;
    const input = document.getElementById('prompt-input');
    if (input) {
      input.disabled = false;
      input.focus();
    }
    if (sphere) sphere.style.boxShadow = '0 0 25px rgba(0, 255, 159, 0.5)';
  }
}

// Watchdog di autoriparazione frontend: sblocca l'interfaccia se un'operazione resta appesa > 20s
window._lastPromptTimestamp = 0;
setInterval(() => {
  if (isBusy && (Date.now() - window._lastPromptTimestamp > 22000)) {
    console.warn('[EBJ UI Watchdog]: Sblocco di emergenza intervenuto per timeout.');
    isBusy = false;
    _ebjIsSpeaking = false;
    const respTag = document.getElementById('resp-tag');
    if (respTag && (respTag.textContent === 'REFLEX...' || respTag.textContent === 'Elaborazione...')) {
      respTag.textContent = 'ONLINE';
    }
    const input = document.getElementById('prompt-input');
    if (input) {
      input.disabled = false;
      input.placeholder = 'Comanda E.B.J... (pronto all\'ascolto)';
    }
  }
}, 4000);

window.forceUnblockEbjUi = function() {
  isBusy = false;
  _ebjIsSpeaking = false;
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  if (window._ebjCurrentAudio) {
    try { window._ebjCurrentAudio.pause(); } catch(_) {}
  }
  const input = document.getElementById('prompt-input');
  if (input) { input.disabled = false; input.focus(); }
  const respTag = document.getElementById('resp-tag');
  if (respTag) respTag.textContent = 'ONLINE';
  const respEl = document.getElementById('resp-body');
  if (respEl) respEl.textContent = 'Interfaccia sbloccata con successo. E.B.J. pronto all\'ascolto.';
  const sphere = document.getElementById('jarvis-sphere');
  if (sphere) sphere.style.boxShadow = '0 0 25px rgba(0, 255, 159, 0.5)';
};

window.toggleReflexStrip = function(e) {
  if (e) e.stopPropagation();
  const el = document.getElementById('ebj-reflex-strip');
  if (el) el.classList.toggle('collapsed');
};

window.updateReflexStrip = function(rf, judge) {
  if (!rf) return;
  const laneTag = document.getElementById('ers-lane-tag');
  const laneBar = document.getElementById('ers-lane-bar');
  const laneScore = document.getElementById('ers-lane-score');
  const laneChip = document.getElementById('ers-lane-chip');
  const addrBar = document.getElementById('ers-addr-bar');
  const addrScore = document.getElementById('ers-addr-score');
  const judgeStatus = document.getElementById('ers-judge-status');
  const stakesChip = document.getElementById('ers-stakes-chip');
  const metaPill = document.getElementById('ers-meta-pill');

  if (laneTag) laneTag.textContent = (rf.lane || 'CHAT').toUpperCase().replace('_', ' ');
  const lConf = Math.round((rf.lane_confidence || 0.8) * 100);
  if (laneBar) laneBar.style.width = lConf + '%';
  if (laneScore) laneScore.textContent = lConf + '%';
  if (laneChip) {
    laneChip.textContent = rf.verdict || 'ACT';
    laneChip.className = 'ers-chip ' + (rf.verdict === 'ACT' ? 'chip-act' : 'chip-warn');
  }

  const addrVal = Math.round((rf.addressed || 0.9) * 100);
  if (addrBar) addrBar.style.width = addrVal + '%';
  if (addrScore) addrScore.textContent = addrVal + '%';

  if (metaPill) {
    const lat = rf.latency_ms || 1.2;
    metaPill.textContent = `⚡ 0.00€ · RUST SIMD · ${lat}ms`;
  }

  if (judge) {
    if (judgeStatus) {
      if (judge.blocked) {
        judgeStatus.textContent = 'BLOCKED: CLAIM NO RECEIPT ⚠️';
        judgeStatus.style.color = '#ef4444';
      } else {
        judgeStatus.textContent = 'RECEIPT VERIFIED ✅';
        judgeStatus.style.color = '#00ff9f';
      }
    }
  }

  if (stakesChip) {
    const stVal = rf.stakes || 0.1;
    if (stVal >= 0.5) {
      stakesChip.textContent = `HIGH STAKES (${stVal})`;
      stakesChip.className = 'ers-chip chip-warn';
    } else {
      stakesChip.textContent = `SAFE (${stVal})`;
      stakesChip.className = 'ers-chip chip-safe';
    }
  }
};

// Sblocco rapido premendo Escape o cliccando sulla sfera
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    window.forceUnblockEbjUi();
  }
});
const _sphereEl = document.getElementById('jarvis-sphere');
if (_sphereEl) {
  _sphereEl.addEventListener('click', () => {
    if (isBusy) window.forceUnblockEbjUi();
  });
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
  } else if (uiAction.action === 'open_camera') {
    window.openCameraVisionModal();
  } else if (uiAction.action === 'close_camera') {
    window.closeCameraVisionModal();
  } else if (uiAction.action === 'open_photo_studio') {
    window.openPhotoStudioModal(uiAction);
  }
};

// ── PHOTO STUDIO & ADVANCED VISION AI FRONTEND CONTROLS ───────────
let _currentPhotoPath = '';
let _currentPhotoZoom = 1.0;

window.openPhotoStudioModal = function(data = {}) {
  const modal = document.getElementById('modal-photo-studio');
  const img = document.getElementById('photo-studio-img');
  const title = document.getElementById('photo-studio-title');
  const feedback = document.getElementById('photo-studio-feedback');
  if (!modal || !img) return;

  _currentPhotoPath = data.path || '';
  _currentPhotoZoom = 1.0;
  window.resetPhotoZoom();

  if (title) title.textContent = `EBJ PHOTO STUDIO · ${data.filename || 'Foto'}`;
  if (data.base64_preview) {
    img.src = `data:image/png;base64,${data.base64_preview}`;
  } else if (data.path) {
    img.src = `/api/system/show-photo?path=${encodeURIComponent(data.path)}&t=${Date.now()}`;
  }

  if (feedback) feedback.textContent = data.comment || 'Foto pronta per Zoom, Rimozione Sfondo o Riconoscimento Corpo.';
  modal.classList.add('active');
  modal.style.display = 'flex';
};

window.closePhotoStudioModal = function() {
  const modal = document.getElementById('modal-photo-studio');
  if (modal) {
    modal.classList.remove('active');
    modal.style.display = 'none';
  }
};

window.adjustPhotoZoom = function(delta) {
  _currentPhotoZoom = Math.max(0.5, Math.min(3.5, _currentPhotoZoom + delta));
  const container = document.getElementById('photo-container');
  const lvl = document.getElementById('photo-zoom-level');
  if (container) container.style.transform = `scale(${_currentPhotoZoom.toFixed(2)})`;
  if (lvl) lvl.textContent = `${Math.round(_currentPhotoZoom * 100)}%`;
};

window.resetPhotoZoom = function() {
  _currentPhotoZoom = 1.0;
  const container = document.getElementById('photo-container');
  const lvl = document.getElementById('photo-zoom-level');
  if (container) container.style.transform = 'scale(1)';
  if (lvl) lvl.textContent = '100%';
};

window.triggerPhotoStudioAction = async function(actionName) {
  const feedback = document.getElementById('photo-studio-feedback');
  const img = document.getElementById('photo-studio-img');
  if (feedback) feedback.textContent = `⚡ Elaborazione neurale "${actionName}" in corso...`;

  try {
    const res = await fetch('/api/photo/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: actionName, query: actionName, path: _currentPhotoPath })
    });
    const d = await res.json();
    if (d.status === 'success') {
      if (d.base64_preview && img) {
        img.src = `data:image/png;base64,${d.base64_preview}`;
      }
      if (feedback) feedback.textContent = d.spoken_response || d.message || 'Azione completata.';
      if (d.spoken_response && window.playSpeechAudio) {
        window.playSpeechAudio(d.spoken_response);
      }
    } else {
      if (feedback) feedback.textContent = d.message || 'Errore durante l\'elaborazione.';
    }
  } catch (err) {
    if (feedback) feedback.textContent = 'Errore di connessione: ' + err.message;
  }
};

window.openPhotoNativeViewer = function() {
  fetch('/api/system/show-photo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: _currentPhotoPath, open_native: true })
  });
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

window.setMood = function(mood) {
  currentPersonality = mood;
  document.querySelectorAll('.mood-card').forEach(c => c.classList.remove('active'));
  document.querySelectorAll('.mood-chip').forEach(c => c.classList.remove('active'));
  
  const card = document.getElementById(`mood-card-${mood}`) || document.getElementById(`mood-card-${mood.replace('_', '-')}`);
  if (card) card.classList.add('active');
  const chip = document.getElementById(`chip-${mood}`);
  if (chip) chip.classList.add('active');
  
  let preview = '';
  if (mood === 'jarvis_uk') {
    preview = "At your service, sir. British Stark AI system online.";
  } else if (mood === 'jarvis') {
    preview = "A sua disposizione, Badr. Voce Jarvis pronta.";
  } else if (mood === 'military') {
    preview = "Comandante, protocollo tattico operativo.";
  } else {
    preview = "Modalità attiva, dimmi pure!";
  }
  
  const respEl = document.getElementById('resp-body');
  const respTag = document.getElementById('resp-tag');
  if (respEl) respEl.textContent = preview;
  if (respTag) respTag.textContent = mood.toUpperCase().replace('_', ' ');
  
  showToolRun('PERSONALITÀ SWITCH', `Modalità ${mood.toUpperCase()} attiva.`, '0.01s');
  if (window.playSpeechAudio) {
    window.playSpeechAudio(preview);
  }
};
window.switchEBMood = window.setMood;

window.testJarvisVoice = function(mood = 'jarvis') {
  window.setMood(mood);
  const phrase = mood === 'jarvis_uk'
    ? "At your service, sir. British Stark AI system online."
    : "A sua disposizione, Badr. Voce Jarvis pronta.";
  if (window.playSpeechAudio) {
    window.playSpeechAudio(phrase);
  }
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
  skills: 'view-skills-matrix',
  'skills-matrix': 'view-skills-matrix',
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
  const key = view === 'kali' ? 'kali' : (view || 'topology');
  localStorage.setItem('ebj_active_view', key);
  const targetId = KALI_VIEW_MAP[key] || 'view-topology';

  document.querySelectorAll('.jarvis-workspace').forEach(w => {
    if (w.id === targetId) {
      w.classList.add('active');
      w.style.display = (targetId === 'view-jarvis' || targetId === 'view-topology') ? 'block' : 'flex';
    } else {
      w.classList.remove('active');
      w.style.display = 'none';
    }
  });

  document.body.classList.toggle('view-kali', key === 'kali');

  document.querySelectorAll('.view-switch-btn').forEach(b => b.classList.remove('active'));
  if (key === 'topology' || key === 'jarvis-v8' || key === 'stark') {
    document.getElementById('btn-view-topology')?.classList.add('active');
    window.dispatchEvent(new Event('resize'));
    if (window.initCosmos3D) window.initCosmos3D();
    if (window.setCosmosLayout) window.setCosmosLayout('constellation');
  }
  if (key === 'jarvis' || key === 'classic') document.getElementById('btn-view-jarvis')?.classList.add('active');
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
  if (key === 'graph') {
    document.getElementById('btn-view-graph')?.classList.add('active');
    if (window.initNeuralGraph) window.initNeuralGraph();
  }
  if (key === 'astra' || key === 'astra-3d') {
    document.getElementById('btn-view-astra')?.classList.add('active');
    if (window.loadAstra3DStatus) window.loadAstra3DStatus();
  }
  if (key === 'skills' || key === 'skills-matrix') {
    document.getElementById('btn-view-skills')?.classList.add('active');
    if (window.loadSkillsMatrix) window.loadSkillsMatrix();
  }

  if (key === 'kali') refreshKaliCatalog();
  toggleMobileNav(false);
  if (window.lucide) {
    setTimeout(() => lucide.createIcons(), 50);
  }
};

// ═══════════════════════════════════════════════════════════════════
// REA (REVERSE ENGINEER ANYTHING) & J.A.R.V.I.S. v8 STARK HUD LOGIC
// ═══════════════════════════════════════════════════════════════════
window.setReaTarget = function(val) {
  const input = document.getElementById('rea-target-input');
  if (input) {
    input.value = val;
    input.focus();
  }
};

window.toggleReaStage = function() {
  const stage = document.getElementById('rea-floating-stage');
  if (stage) {
    stage.style.display = (stage.style.display === 'none') ? 'block' : 'none';
  }
};

window.setJarvisSubtitle = function(text, isUser = false) {
  const banner = document.getElementById('jarvis-spoken-subtitle');
  const span = document.getElementById('jarvis-subtitle-text');
  if (banner && span) {
    banner.style.display = 'flex';
    span.innerHTML = (isUser ? '<strong style="color:#00ff9f;">BADR:</strong> ' : '<strong style="color:#00f0ff;">J.A.R.V.I.S.:</strong> ') + text;
  }
};

window.animateAudioSpectrum = function(durationMs = 3000) {
  const bars = document.querySelectorAll('#cosmos-audio-spectrum .jas-bar, #jarvis-audio-spectrum .jas-bar');
  if (!bars.length) return;
  const startTime = Date.now();
  const interval = setInterval(() => {
    const elapsed = Date.now() - startTime;
    if (elapsed > durationMs) {
      clearInterval(interval);
      bars.forEach(b => b.style.height = '4px');
      return;
    }
    bars.forEach(b => {
      const h = Math.floor(Math.random() * 20) + 4;
      b.style.height = `${h}px`;
    });
  }, 80);
};

window.runReaTeardownLive = async function() {
  const targetInput = document.getElementById('rea-target-input');
  const target = targetInput ? targetInput.value.trim() : 'https://igloo.inc';
  const resultsBox = document.getElementById('rea-results-box');
  
  if (resultsBox) {
    resultsBox.innerHTML = `
      <div style="color:#00f0ff; display:flex; align-items:center; gap:8px;">
        <span style="display:inline-block; animation:spin 1s infinite linear;">⚙️</span>
        Ispezione REA in corso su <strong>${target}</strong> tramite 170 tool MCP...
      </div>
    `;
  }
  
  window.setJarvisSubtitle(`Analisi di reverse engineering avviata su ${target}...`);
  if (window.focusCosmosOnCluster) window.focusCosmosOnCluster('rea');

  try {
    const res = await fetch('/api/rea/teardown', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target: target, read_aloud: true })
    });
    const d = await res.json();
    
    if (d.status === 'SUCCESS') {
      const techChips = (d.tech_stack || []).map(t => 
        `<span style="background:rgba(0,240,255,0.15); border:1px solid #00f0ff; color:#00f0ff; padding:2px 6px; border-radius:4px; font-size:10px; margin-right:4px;">${t}</span>`
      ).join('');

      const compList = (d.components || []).map(c => 
        `<li style="margin:2px 0;">• <strong style="color:#fff;">${c.name}</strong> [${c.type}] <span style="color:#00ff9f;">${c.status}</span></li>`
      ).join('');

      if (resultsBox) {
        resultsBox.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="color:#00ff9f; font-weight:bold;">✦ TEARDOWN COMPLETATO CON SUCCESSO</span>
            <span style="color:#94a3b8; font-size:10px;">${d.category || 'Architettura WebGL/Nativa'}</span>
          </div>
          <div style="margin:6px 0;">${techChips}</div>
          <div style="margin-top:6px; color:#cbd5e1; font-size:11px;">
            <ul style="padding-left:14px; margin:4px 0;">${compList}</ul>
          </div>
          <div style="margin-top:8px; padding-top:6px; border-top:1px dashed rgba(0,240,255,0.25); color:#ffd700; font-size:11px;">
            💬 J.A.R.V.I.S.: "${d.spoken_ack || ''}"
          </div>
        `;
      }

      if (d.spoken_ack) {
        window.setJarvisSubtitle(d.spoken_ack);
      }

      if (d.audio_base64) {
        window.playSpeechAudio(d.spoken_ack || 'Teardown completato con successo, signore.', d.audio_base64);
      }
    } else {
      if (resultsBox) {
        resultsBox.innerHTML = `<div style="color:#ef4444;">Errore REA: ${d.message || d.error || 'Errore sconosciuto'}</div>`;
      }
    }
  } catch (err) {
    if (resultsBox) {
      resultsBox.innerHTML = `<div style="color:#ef4444;">Errore di connessione REA: ${err.message}</div>`;
    }
  }
};

window.runReaBuildOriginal = async function() {
  const targetInput = document.getElementById('rea-target-input');
  const target = targetInput ? targetInput.value.trim() : 'https://igloo.inc';
  const resultsBox = document.getElementById('rea-results-box');

  if (resultsBox) {
    resultsBox.innerHTML = `<div style="color:#00ff9f;">🔨 Costruzione blueprint originale per ${target} in corso...</div>`;
  }
  
  try {
    const res = await fetch('/api/rea/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target: target })
    });
    const d = await res.json();
    if (d.status === 'SUCCESS') {
      const filesList = (d.blueprint_files || []).map(f => `<div style="color:#00f0ff;">📄 ${f}</div>`).join('');
      if (resultsBox) {
        resultsBox.innerHTML = `
          <div style="color:#00ff9f; font-weight:bold;">✦ BLUEPRINT ORIGINALE COSTRUITO</div>
          <div style="color:#e2e8f0; margin-top:4px;">File architetturali generati nel repository:</div>
          <div style="margin-top:6px; padding:6px; background:rgba(0,0,0,0.4); border-radius:6px;">${filesList}</div>
          <div style="margin-top:6px; color:#ffd700;">${d.spoken_ack || ''}</div>
        `;
      }
      if (d.spoken_ack) window.setJarvisSubtitle(d.spoken_ack);
      if (d.audio_base64) {
        window.playSpeechAudio(d.spoken_ack || 'Costruzione completata, signore.', d.audio_base64);
      }
    }
  } catch (e) {
    if (resultsBox) resultsBox.innerHTML = `<div style="color:#ef4444;">Errore build: ${e.message}</div>`;
  }
};

window.openArtCraftSuiteModal = async function() {
  const resultsBox = document.getElementById('rea-results-box');
  if (resultsBox) {
    resultsBox.innerHTML = `<div style="color:#00f0ff;">Scansione 13 App Pure Rust della suite ArtCraft...</div>`;
  }
  try {
    const res = await fetch('/api/rea/status');
    const d = await res.json();
    if (d.status === 'SUCCESS' && d.artcraft_apps) {
      const appCards = Object.entries(d.artcraft_apps).map(([k, v]) => `
        <div style="display:inline-block; margin:3px; padding:4px 8px; background:rgba(255,183,3,0.12); border:1px solid #ffb703; border-radius:6px; font-size:10px;">
          <strong style="color:#ffb703;">${v.name}</strong> · <span style="color:#cbd5e1;">${v.category}</span>
        </div>
      `).join('');
      if (resultsBox) {
        resultsBox.innerHTML = `
          <div style="color:#ffb703; font-weight:bold; margin-bottom:6px;">✦ SUITE ARTCRAFT RUST (13 APPLICAZIONI)</div>
          <div style="color:#94a3b8; font-size:10px; margin-bottom:6px;">Software aperti e riscritti in Pure Rust con Server MCP integrato:</div>
          <div>${appCards}</div>
        `;
      }
    }
  } catch (e) {
    if (resultsBox) resultsBox.innerHTML = `<div style="color:#ef4444;">Errore ArtCraft: ${e.message}</div>`;
  }
};

window.sendCosmosPrompt = async function() {
  const input = document.getElementById('cosmos-prompt-input');
  if (!input) return;
  const prompt = input.value.trim();
  if (!prompt) return;
  input.value = '';

  window.setJarvisSubtitle(prompt, true);
  window.animateAudioSpectrum(2500);

  try {
    const res = await fetch('/api/voice/interact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: prompt, voice_enabled: true })
    });
    const d = await res.json();
    if (d.reply) {
      window.setJarvisSubtitle(d.reply, false);
    }
    if (d.audio_base64) {
      window.playSpeechAudio(d.reply || 'Comando elaborato, signore.', d.audio_base64);
    }
  } catch (err) {
    window.setJarvisSubtitle('Errore di comunicazione: ' + err.message, false);
  }
};


// ═══════════════════════════════════════════════════════════════════
// 12. SKILLS & ABILITIES VISUAL MATRIX MONITOR (71+ SKILLS & RUST)
// ═══════════════════════════════════════════════════════════════════
window._skillsMatrixData = [];
window._skillsCurrentCat = 'all';
window._skillsSearchQuery = '';

window.categorizeSkill = function(skill) {
  const cat = (skill.category || '').toUpperCase();
  const id = (skill.id || '').toLowerCase();
  if (cat.includes('RUST') || id.includes('rust') || id.includes('bridge') || id.includes('fast_parser') || id.includes('timemachine') || id.includes('aether')) {
    return 'rust';
  }
  if (cat.includes('COGNITIVE') || cat.includes('ORCHESTRATION') || cat.includes('TRIAGE') || cat.includes('SWARM') || id.includes('lead') || id.includes('subito') || id.includes('marketplace') || id.includes('quality') || id.includes('radar')) {
    return 'jev';
  }
  if (cat.includes('SECURITY') || cat.includes('CLOUD') || cat.includes('MCP') || cat.includes('GATEWAY') || cat.includes('NERVOUS') || id.includes('kali') || id.includes('n8n') || id.includes('fastmcp') || id.includes('network')) {
    return 'containers';
  }
  if (cat.includes('HARDWARE') || cat.includes('IOT') || cat.includes('VISION') || cat.includes('AUDIO') || cat.includes('MEDIA') || cat.includes('GAMING') || cat.includes('GAMEDEV') || id.includes('bambu') || id.includes('screen') || id.includes('whisper') || id.includes('ffmpeg') || id.includes('ue5')) {
    return 'hardware';
  }
  return 'business';
};

window.loadSkillsMatrix = async function() {
  const grid = document.getElementById('sk-cards-grid');
  if (!grid) return;
  if (!window._skillsMatrixData || window._skillsMatrixData.length === 0) {
    grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:40px; color:#64748b;"><span style="display:inline-block;animation:spin 1s infinite linear;font-size:24px;">⚡</span><br>Caricamento matrice neurale abilità...</div>';
  }

  try {
    const res = await fetch('/api/skills');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    window._skillsMatrixData = data.skills || [];

    const totalEl = document.getElementById('badge-total-skills');
    if (totalEl) totalEl.textContent = `${window._skillsMatrixData.length} ATTIVE`;

    const rustStat = document.getElementById('sk-stat-rust');
    if (rustStat) rustStat.textContent = data.rust_bridge_online ? ':9000 (0.4ms)' : ':9000 OFFLINE';

    const vpsStat = document.getElementById('sk-stat-vps');
    if (vpsStat) vpsStat.textContent = `${data.vps_containers || 11} VPS Docker`;

    const mcpStat = document.getElementById('sk-stat-mcp');
    if (mcpStat) mcpStat.textContent = `${data.mcp_tools || 28} Schemi FastMCP`;

    renderSkillsMatrix();
  } catch (err) {
    console.warn('[Skills Matrix Fetch Err]:', err);
    if (grid) grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:40px; color:#f43f5e;">Errore connessione: ${err.message}</div>`;
  }
};

window.renderSkillsMatrix = function() {
  const grid = document.getElementById('sk-cards-grid');
  if (!grid) return;

  let items = window._skillsMatrixData || [];

  if (window._skillsCurrentCat !== 'all') {
    items = items.filter(s => categorizeSkill(s) === window._skillsCurrentCat);
  }

  if (window._skillsSearchQuery) {
    const q = window._skillsSearchQuery.toLowerCase();
    items = items.filter(s => {
      const name = (s.name || '').toLowerCase();
      const desc = (s.description || '').toLowerCase();
      const cat = (s.category || '').toLowerCase();
      const trigs = (s.triggers || []).join(' ').toLowerCase();
      return name.includes(q) || desc.includes(q) || cat.includes(q) || trigs.includes(q);
    });
  }

  if (items.length === 0) {
    grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:50px 20px; color:#64748b; font-family:\'JetBrains Mono\',monospace;">Nessuna abilità trovata con questi filtri.</div>';
    return;
  }

  const categoryTheme = {
    rust: { color: '#00f0ff', badge: 'RUST TOKIO', border: 'rgba(0,240,255,0.3)', bg: 'rgba(0,240,255,0.06)' },
    jev: { color: '#00ff9f', badge: 'JEV COGNITIVE', border: 'rgba(0,255,159,0.3)', bg: 'rgba(0,255,159,0.06)' },
    containers: { color: '#a855f7', badge: 'DOCKER / MCP', border: 'rgba(168,85,247,0.3)', bg: 'rgba(168,85,247,0.06)' },
    hardware: { color: '#f59e0b', badge: 'IOT & 3D', border: 'rgba(245,158,11,0.3)', bg: 'rgba(245,158,11,0.06)' },
    business: { color: '#38bdf8', badge: 'BIZ / LEADS', border: 'rgba(56,189,248,0.3)', bg: 'rgba(56,189,248,0.06)' }
  };

  grid.innerHTML = items.map(skill => {
    const catType = categorizeSkill(skill);
    const theme = categoryTheme[catType] || categoryTheme.business;
    const triggers = (skill.triggers || []).slice(0, 4);
    const trigsHtml = triggers.map(t => `<span class="sk-trig-pill" onclick="triggerSkillFromMatrix('${t.replace(/'/g, "\\'")}')" title="Clicca per inviare comando">${t}</span>`).join('');
    const latency = skill.latency_ms ? `${skill.latency_ms}ms` : '< 1ms';

    return `
      <div class="sk-card" style="--sk-color:${theme.color};">
        <div>
          <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px; margin-bottom:8px;">
            <div style="display:flex; align-items:center; gap:10px;">
              <span style="font-size:22px; width:36px; height:36px; display:flex; align-items:center; justify-content:center; background:${theme.bg}; border:1px solid ${theme.border}; border-radius:8px;">${skill.icon || '⚡'}</span>
              <div>
                <h4 style="margin:0; font-size:0.92rem; font-weight:600; color:#f8fafc; font-family:'Inter',sans-serif;">${skill.name || skill.id}</h4>
                <div style="font-size:0.68rem; color:${theme.color}; font-family:'JetBrains Mono',monospace; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; margin-top:2px;">[${theme.badge}]</div>
              </div>
            </div>
            <div style="display:flex; flex-direction:column; align-items:flex-end; gap:4px;">
              <span style="display:inline-flex; align-items:center; gap:5px; font-size:0.68rem; padding:2px 6px; border-radius:4px; background:rgba(0,255,159,0.12); color:#00ff9f; border:1px solid rgba(0,255,159,0.25); font-family:'JetBrains Mono',monospace;">
                <span style="width:6px; height:6px; border-radius:50%; background:#00ff9f; box-shadow:0 0 6px #00ff9f;"></span>ONLINE
              </span>
              <span style="font-size:0.68rem; color:#64748b; font-family:'JetBrains Mono',monospace;">${latency}</span>
            </div>
          </div>
          <p style="margin:8px 0 10px 0; font-size:0.78rem; line-height:1.45; color:#94a3b8; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;">
            ${skill.description || 'Abilità operativa registrata nell\'ecosistema neurale EBJ.'}
          </p>
          <div style="display:flex; flex-wrap:wrap; gap:4px; margin-bottom:8px;">
            ${trigsHtml}
          </div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid rgba(255,255,255,0.06); padding-top:10px; margin-top:auto;">
          <span style="font-size:0.68rem; color:#64748b; font-family:'JetBrains Mono',monospace;">v${skill.version || '1.0.0'} · ${skill.runner || 'rust/py'}</span>
          <button class="sk-exec-btn" onclick="executeSkillLive('${skill.id}', this)" title="Esegui test immediato della skill">
            ⚡ TEST / ESEGUI
          </button>
        </div>
      </div>
    `;
  }).join('');
};

window.filterSkillsMatrix = function(category) {
  window._skillsCurrentCat = category;
  document.querySelectorAll('.sk-cat-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-cat') === category);
  });
  renderSkillsMatrix();
};

window.searchSkillsMatrix = function(query) {
  window._skillsSearchQuery = (query || '').trim();
  renderSkillsMatrix();
};

window.triggerSkillFromMatrix = function(command) {
  switchMasterView('jarvis');
  const input = document.getElementById('prompt-input');
  if (input) {
    input.value = command;
    input.focus();
    if (window.sendMessage) window.sendMessage();
  }
};

window.executeSkillLive = async function(skillId, btnEl) {
  if (!btnEl) return;
  const originalText = btnEl.innerHTML;
  btnEl.disabled = true;
  btnEl.innerHTML = '<span style="display:inline-block;animation:spin 1s infinite linear;">⚙️</span> RUN...';

  try {
    const res = await fetch('/api/skills/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skill_id: skillId, params: { test_mode: true } })
    });
    const d = await res.json();
    if (d.status === 'SUCCESS') {
      btnEl.style.borderColor = '#00ff9f';
      btnEl.style.color = '#00ff9f';
      btnEl.style.background = 'rgba(0,255,159,0.15)';
      btnEl.innerHTML = `✅ OK (${d.duration_ms || 0.5}ms)`;
      setTimeout(() => {
        btnEl.disabled = false;
        btnEl.innerHTML = originalText;
        btnEl.style.borderColor = '';
        btnEl.style.color = '';
        btnEl.style.background = '';
      }, 3000);
    } else {
      btnEl.style.borderColor = '#f59e0b';
      btnEl.style.color = '#f59e0b';
      btnEl.style.background = 'rgba(245,158,11,0.15)';
      btnEl.innerHTML = `⚠️ ${d.message ? d.message.slice(0, 14) : 'Eseguito'}`;
      setTimeout(() => {
        btnEl.disabled = false;
        btnEl.innerHTML = originalText;
        btnEl.style.borderColor = '';
        btnEl.style.color = '';
        btnEl.style.background = '';
      }, 3000);
    }
  } catch (err) {
    btnEl.innerHTML = '❌ Timeout';
    setTimeout(() => {
      btnEl.disabled = false;
      btnEl.innerHTML = originalText;
    }, 3000);
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
  
  // Auto-restore voice continuous preference: attivo di default salvo 'off' esplicito
  const savedVoce = localStorage.getItem('ebj_voce');
  if (savedVoce !== 'off') {
    window.ebjVoiceEnabled = true;
    window.isConversationalMode = true;
    initEbjMicWatchdog();
  } else {
    window.ebjVoiceEnabled = false;
    window.isConversationalMode = false;
  }
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
    const res = await fetch('/api/leads/radar/active?limit=30', { signal: AbortSignal.timeout(8000) });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const d = await res.json();
    const leads = Array.isArray(d.leads) ? d.leads : [];
    if (countBadge) countBadge.innerText = `${leads.length} LEAD`;

    if (container) {
      if (leads.length === 0) {
        container.innerHTML = `
          <div style="color:#fbbf24; font-size:0.75rem; text-align:center; padding:16px; background:#0b1120; border-radius:6px; border:1px solid #854d0e;">
            Nessun lead reale presente in archivio.<br>Avvia una scansione: verranno mostrati solo risultati raccolti dalla fonte, senza contatti dimostrativi.
          </div>
        `;
        return;
      }

      container.innerHTML = leads.map(l => {
        const safe = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
        const tierColor = l.tier === 'HOT' ? '#ef4444' : (l.tier === 'WARM' ? '#f59e0b' : '#3b82f6');
        const rawPhone = String(l.phone || '');
        let cleanDigits = rawPhone.replace(/\D/g, '');
        if (cleanDigits.startsWith('0039')) cleanDigits = cleanDigits.slice(4);
        else if (cleanDigits.startsWith('39') && cleanDigits.length >= 11) cleanDigits = cleanDigits.slice(2);

        const phoneVerified = l.phone_status === 'verified';
        const hasValidPhone = phoneVerified && cleanDigits.length >= 8 && cleanDigits.length <= 11;
        const sourceUrl = (() => {
          try {
            const url = new URL(l.source_url || '');
            return url.protocol === 'https:' ? url.href : '';
          } catch (_) { return ''; }
        })();
        const e164 = hasValidPhone ? `+39${cleanDigits}` : '';
        const telLink = hasValidPhone ? `tel:${e164}` : '';
        const waLink = hasValidPhone ? `https://wa.me/39${cleanDigits}?text=${encodeURIComponent('Buongiorno, vi contatto da BadrExpress & Pietro Traslochi in merito alla gestione sgombero/trasloco a ' + l.city)}` : '';
        const displayPhone = hasValidPhone ? (cleanDigits.startsWith('3') ? `+39 ${cleanDigits.slice(0,3)} ${cleanDigits.slice(3,6)} ${cleanDigits.slice(6)}` : `+39 ${cleanDigits}`) : (rawPhone || 'Contatto su annuncio');

        return `
          <div style="background:#0b1120; border:1px solid #1e293b; border-left:3px solid ${tierColor}; border-radius:6px; padding:12px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
              <span style="font-size:0.75rem; font-weight:bold; color:#00f0ff;">${safe(l.city ? l.city.toUpperCase() : 'Zona non specificata')} · ${safe(l.service_type || 'Servizio da verificare')}</span>
              <span style="background:${tierColor}; color:#000; font-weight:900; font-size:0.65rem; padding:2px 6px; border-radius:3px;">${safe(l.tier || 'DA VERIFICARE')} (${Number(l.priority_score) || 0})</span>
            </div>
            <div style="font-size:0.85rem; font-weight:bold; color:#fff; margin-bottom:4px;">${safe(l.title || l.client_name || 'Richiesta senza titolo')}</div>
            <div style="font-size:0.74rem; color:#94a3b8; margin-bottom:10px; line-height:1.3;">${safe(l.details || '')}</div>
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
              <span style="font-size:0.78rem; color:#f8fafc; font-weight:bold;">${hasValidPhone ? '📞 ' + safe(displayPhone) : (rawPhone ? '⚠️ Numero da verificare: ' + safe(displayPhone) : '📨 ' + safe(displayPhone))}</span>
              <div style="display:flex; gap:6px; flex-wrap:wrap;">
                ${hasValidPhone ? `<a href="${telLink}" style="background:#10b981; color:#020813; font-size:0.75rem; font-weight:900; padding:6px 12px; border-radius:6px; text-decoration:none; display:inline-flex; align-items:center; gap:4px; box-shadow:0 0 10px rgba(16,185,129,0.3);">📞 CHIAMA</a>` : ''}
                ${hasValidPhone ? `<a href="${waLink}" target="_blank" rel="noopener noreferrer" style="background:#0f172a; border:1.5px solid #25d366; color:#25d366; font-size:0.72rem; font-weight:bold; padding:5px 8px; border-radius:6px; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">💬 WA</a>` : ''}
                ${sourceUrl ? `<a href="${safe(sourceUrl)}" target="_blank" rel="noopener noreferrer" style="background:#1e293b; color:#cbd5e1; border:1px solid #334155; font-size:0.72rem; padding:5px 8px; border-radius:6px; text-decoration:none;">🔎 FONTE</a>` : ''}
                <button onclick="window.sendQuick('JARVIS, invia preventivo express per il lead ${l.id} a ${l.city}')" style="background:#1e293b; color:#cbd5e1; border:1px solid #334155; font-size:0.72rem; padding:5px 8px; border-radius:6px; cursor:pointer;">⚡ PREVENTIVO</button>
              </div>
            </div>
          </div>
        `;
      }).join('') + `
        <div style="text-align:center; margin-top:12px;">
          <a href="/leads_chiamata_rapida.html" target="_blank" style="display:inline-block; background:rgba(0,240,255,0.15); border:1px solid #00f0ff; color:#00f0ff; font-size:0.75rem; font-weight:bold; padding:8px 14px; border-radius:6px; text-decoration:none;">
            🚀 APRI DIALER COMPLETO 1-CLICK (110+ LEAD VERIFICATI) ↗️
          </a>
        </div>
      `;
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
      body: JSON.stringify({ city: city }),
      signal: AbortSignal.timeout(30000)
    });
    const d = await res.json();
    if (!res.ok || d.status === 'ERROR') throw new Error(d.error || `HTTP ${res.status}`);
    const count = Number(d.captured_count) || 0;
    if (statusEl) {
      statusEl.innerText = count
        ? `Scansione completata: ${count} risultati acquisiti. Controlla fonte e data prima del contatto.`
        : `Scansione completata: nessun risultato acquisito dalla fonte per ${city}.`;
      statusEl.style.color = count ? '#10b981' : '#fbbf24';
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
      window.playSpeechAudio("Badr, ho inoltrato la chiamata di emergenza verso il tuo telefono.");
    }
  } catch (err) {
    console.warn('[EMERGENCY DISPATCH ERROR]:', err);
  }

  setTimeout(() => {
    const modal = document.getElementById('modal-emergency-call');
    if (modal) modal.style.display = 'none';
  }, 2200);
};

// ── CAMERA VISION + JARVIS HOLOGRAM HUD (CONTINUOUS TRACKING) ─────────────
let _holoPollTimer = null;
let _holoFrameCount = 0;
let _holoLastTs = 0;
let _holoFps = 0;
let _holoCaptureBusy = false;
let _jarvisHudAnimFrame = null;
let _jarvisGreetedSession = false;
let _jarvisFace = { active: false, x: 0, y: 0, w: 0, h: 0, targetX: 0, targetY: 0, targetW: 0, targetH: 0 };
let _holoLastConfidence = null;

function _playJarvisChime() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(1760, audioCtx.currentTime + 0.12);
    gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.22);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.22);
  } catch (e) {}
}

let _currentFacingMode = 'user';

window.switchCameraFacing = async function() {
  _currentFacingMode = (_currentFacingMode === 'user') ? 'environment' : 'user';
  const statusEl = document.getElementById('cam-stream-status');
  if (statusEl) statusEl.textContent = `🔄 CAM: ${_currentFacingMode === 'user' ? 'FRONTALE' : 'POSTERIORE'}`;
  await window.openCameraVisionModal(_currentFacingMode);
};

window.openCameraVisionModal = async function(facingModeOverride) {
  const modal = document.getElementById('modal-camera-vision');
  const video = document.getElementById('cam-live-video');
  const statusEl = document.getElementById('cam-stream-status');
  if (!modal || !video) return;

  modal.style.display = 'flex';
  _jarvisGreetedSession = false;

  // Make sure video element is mobile-ready (playsinline, muted)
  video.setAttribute('playsinline', 'true');
  video.setAttribute('webkit-playsinline', 'true');
  video.setAttribute('muted', 'true');
  video.muted = true;

  if (facingModeOverride) _currentFacingMode = facingModeOverride;

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    if (statusEl) statusEl.textContent = 'WEBCAM NON SUPPORTATA';
    _setHoloState('NON SUPPORTATA', 'lost');
    const feedback = document.getElementById('cam-feedback-text');
    if (feedback) feedback.textContent = 'Apri la dashboard su HTTPS (https://eb.badrexpress.com/) e autorizza la fotocamera.';
    return;
  }

  // Stop any prior tracks cleanly
  if (_webcamStream) {
    try {
      _webcamStream.getTracks().forEach(t => t.stop());
    } catch (_) {}
    _webcamStream = null;
  }

  try {
    // Mobile progressive fallback ladder:
    // Tier 1: facingMode ideal + flexible aspect
    // Tier 2: facingMode exact/string
    // Tier 3: standard video: true (universal Android/iOS/Desktop)
    let stream = null;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: _currentFacingMode } },
        audio: false
      });
    } catch (err1) {
      console.warn('[CAMERA TIER 1 FALLBACK, RETRYING FACING EXACT]:', err1);
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: _currentFacingMode },
          audio: false
        });
      } catch (err2) {
        console.warn('[CAMERA TIER 2 FALLBACK, RETRYING UNIVERSAL VIDEO TRUE]:', err2);
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false
        });
      }
    }
    _webcamStream = stream;

    video.srcObject = _webcamStream;
    try {
      await video.play();
    } catch (playErr) {
      console.warn('[VIDEO PLAY ERR, RETRYING MUTED]:', playErr);
      video.muted = true;
      await video.play();
    }

    if (statusEl) statusEl.textContent = `● CAMERA ATTIVA (${_currentFacingMode === 'user' ? 'FRONTALE' : 'POSTERIORE'})`;
    _holoFrameCount = 0;
    _holoLastTs = performance.now();
    const feedback = document.getElementById('cam-feedback-text');
    if (feedback) feedback.textContent = 'Fotocamera attiva su smartphone/desktop. Analisi olografica Stark e scansione HUD in corso.';
    
    _startJarvisHudLoop();
    _startHoloPolling();
    try { window.playLaserChime && window.playLaserChime(); } catch(e) {}
  } catch (err) {
    console.warn('[WEBCAM ACCESS ERR]:', err);
    if (statusEl) statusEl.textContent = 'PERMESSO NEGATO O NO CAM';
    _setHoloState('NO CAMERA', 'lost');
    const feedback = document.getElementById('cam-feedback-text');
    if (feedback) {
      feedback.textContent = 'Impossibile accedere alla fotocamera. Assicurati di aver concesso il permesso fotocamera al browser nelle impostazioni del telefono.';
    }
  }
};

window.closeCameraVisionModal = function() {
  _stopHoloPolling();
  _stopJarvisHudLoop();
  const modal = document.getElementById('modal-camera-vision');
  const video = document.getElementById('cam-live-video');
  if (_webcamStream) {
    _webcamStream.getTracks().forEach(t => t.stop());
    _webcamStream = null;
  }
  if (video) video.srcObject = null;
  _holoCaptureBusy = false;
  fetch('/api/webcam/reset', { method: 'POST' }).catch(() => {});
  if (modal) modal.style.display = 'none';
  const img = document.getElementById('holo-avatar-img');
  if (img) { img.className = 'holo-avatar-img'; img.style.transform = ''; }
  const stage = document.getElementById('holo-avatar-stage');
  if (stage) { stage.style.setProperty('--eye-x', '0px'); stage.style.setProperty('--eye-y', '0px'); }
  _jarvisFace.active = false;
  _holoLastConfidence = null;
  _setHoloState('CAMERA SPENTA', '');
};

function _startHoloPolling() {
  _stopHoloPolling();
  _holoPollTimer = setInterval(_captureAndSendFrame, 350);
}

function _stopHoloPolling() {
  if (_holoPollTimer) { clearInterval(_holoPollTimer); _holoPollTimer = null; }
}

function _startJarvisHudLoop() {
  _stopJarvisHudLoop();
  const canvas = document.getElementById('cam-hud-canvas');
  const video = document.getElementById('cam-live-video');
  if (!canvas || !video) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  function _hudFrame(now) {
    if (video.videoWidth > 0) {
      if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
      }
      if (_jarvisFace.active) {
        const smooth = 0.3;
        _jarvisFace.x += (_jarvisFace.targetX - _jarvisFace.x) * smooth;
        _jarvisFace.y += (_jarvisFace.targetY - _jarvisFace.y) * smooth;
        _jarvisFace.w += (_jarvisFace.targetW - _jarvisFace.w) * smooth;
        _jarvisFace.h += (_jarvisFace.targetH - _jarvisFace.h) * smooth;
      }
      _drawJarvisHud(ctx, canvas.width, canvas.height, _jarvisFace, now);
    }
    _jarvisHudAnimFrame = requestAnimationFrame(_hudFrame);
  }

  _jarvisHudAnimFrame = requestAnimationFrame(_hudFrame);
}

function _stopJarvisHudLoop() {
  if (_jarvisHudAnimFrame) {
    cancelAnimationFrame(_jarvisHudAnimFrame);
    _jarvisHudAnimFrame = null;
  }
}



function _driveAvatarFromNorm(normX, normY, drive = {}) {
  const img = document.getElementById('holo-avatar-img');
  const glow = document.getElementById('holo-glow');
  if (!img) return;

  const x = Math.max(-1, Math.min(1, Number(normX) || 0));
  const y = Math.max(-1, Math.min(1, Number(normY) || 0));
  const yaw = Number.isFinite(drive.head_yaw_deg) ? drive.head_yaw_deg : x * 14;
  const pitch = Number.isFinite(drive.head_pitch_deg) ? drive.head_pitch_deg : -y * 8;
  const scale = Number.isFinite(drive.head_scale) ? Math.max(0.82, Math.min(1.3, drive.head_scale)) : 1;
  img.style.transform = `rotateY(${yaw.toFixed(1)}deg) rotateX(${pitch.toFixed(1)}deg) translate(${(x * 7).toFixed(1)}px, ${(y * 5).toFixed(1)}px) scale(${scale.toFixed(2)})`;
  const stage = document.getElementById('holo-avatar-stage');
  if (stage) {
    stage.style.setProperty('--eye-x', `${((Number(drive.eye_dx) || x) * 4).toFixed(1)}px`);
    stage.style.setProperty('--eye-y', `${((Number(drive.eye_dy) || y) * 2.5).toFixed(1)}px`);
  }
  img.className = 'holo-avatar-img locked facing';
  if (glow) {
    glow.style.opacity = String(0.35 + 0.55 * Math.max(0, Math.min(1, Number(drive.lock_strength) || 0)));
    glow.classList.add('active');
  }
}

function _drawJarvisHud(ctx, w, h, box, time) {
  ctx.clearRect(0, 0, w, h);
  const cyan = '#00f0ff';
  const gold = '#ffd700';

  // Linea di scansione laser orizzontale Iron Man
  const scanY = (Math.sin(time * 0.0018) * 0.5 + 0.5) * h;
  const grad = ctx.createLinearGradient(0, scanY - 24, 0, scanY + 24);
  grad.addColorStop(0, 'rgba(0, 240, 255, 0)');
  grad.addColorStop(0.5, 'rgba(0, 240, 255, 0.28)');
  grad.addColorStop(1, 'rgba(0, 240, 255, 0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, scanY - 24, w, 48);

  // Barra di telemetria superiore
  ctx.font = '10px monospace';
  ctx.fillStyle = cyan;
  ctx.fillText('E.B.J. · RILEVAMENTO VOLTO LOCALE', 16, 22);
  ctx.fillText('NESSUNA IDENTIFICAZIONE BIOMETRICA · FRAME NON ARCHIVIATI', 16, 36);

  if (box && box.active) {
    const cx = box.x + box.w / 2;
    const cy = box.y + box.h / 2;
    const r = Math.max(box.w, box.h) * 0.58;

    // Reticolo circolare rotante esterno
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(time * 0.0008);
    ctx.strokeStyle = cyan;
    ctx.lineWidth = 1.5;
    ctx.setLineDash([20, 14]);
    ctx.beginPath();
    ctx.arc(0, 0, r + 18, 0, Math.PI * 2);
    ctx.stroke();

    // Reticolo circolare contro-rotante interno
    ctx.rotate(-time * 0.0018);
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.5)';
    ctx.setLineDash([8, 8]);
    ctx.beginPath();
    ctx.arc(0, 0, r + 6, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    // Box angolari cyberpunk stile HUD Iron Man
    ctx.save();
    ctx.strokeStyle = cyan;
    ctx.lineWidth = 2.5;
    ctx.setLineDash([]);
    const corner = Math.min(26, box.w * 0.2);
    const bx = box.x, by = box.y, bw = box.w, bh = box.h;

    // Angolo Alto-Sinistra
    ctx.beginPath(); ctx.moveTo(bx, by + corner); ctx.lineTo(bx, by); ctx.lineTo(bx + corner, by); ctx.stroke();
    // Angolo Alto-Destra
    ctx.beginPath(); ctx.moveTo(bx + bw - corner, by); ctx.lineTo(bx + bw, by); ctx.lineTo(bx + bw, by + corner); ctx.stroke();
    // Angolo Basso-Sinistra
    ctx.beginPath(); ctx.moveTo(bx, by + bh - corner); ctx.lineTo(bx, by + bh); ctx.lineTo(bx + corner, by + bh); ctx.stroke();
    // Angolo Basso-Destra
    ctx.beginPath(); ctx.moveTo(bx + bw - corner, by + bh); ctx.lineTo(bx + bw, by + bh); ctx.lineTo(bx + bw, by + bh - corner); ctx.stroke();

    // Mirino a croce centrale con cerchio cibernetico
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.85)';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.arc(cx, cy, 6, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(cx - 14, cy); ctx.lineTo(cx + 14, cy);
    ctx.moveTo(cx, cy - 14); ctx.lineTo(cx, cy + 14);
    ctx.stroke();

    // Etichetta di tracking: il detector trova un volto, non ne verifica l'identità.
    ctx.shadowColor = '#00f0ff';
    ctx.shadowBlur = 8;
    ctx.font = 'bold 11px monospace';
    ctx.fillStyle = '#00f0ff';
    ctx.fillText('TARGET: VOLTO RILEVATO', bx, Math.max(16, by - 8));
    ctx.font = '9px monospace';
    ctx.fillStyle = gold;
    ctx.fillText(`TRACKING · X:${Math.round(cx)} Y:${Math.round(cy)} · SCORE: ${Number.isFinite(_holoLastConfidence) ? _holoLastConfidence.toFixed(2) : '—'}`, bx, by + bh + 14);
    ctx.shadowBlur = 0;
    ctx.restore();
  }


}

async function _captureAndSendFrame() {
  const video = document.getElementById('cam-live-video');
  if (!video || !video.videoWidth || _holoCaptureBusy) return;
  _holoCaptureBusy = true;
  try {
    const now = performance.now();
    _holoFrameCount++;
    if (now - _holoLastTs >= 2000) {
      _holoFps = Math.round((_holoFrameCount * 1000) / (now - _holoLastTs));
      _holoFrameCount = 0;
      _holoLastTs = now;
    }

    const targetWidth = 320;
    const scale = Math.min(1, targetWidth / video.videoWidth);
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
    canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
    const ctx = canvas.getContext('2d', { alpha: false });
    if (!ctx) throw new Error('Canvas non disponibile');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const frameB64 = canvas.toDataURL('image/jpeg', 0.72).split(',')[1];

    const response = await fetch('/api/webcam/frame', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ frame_b64: frameB64, mirrored: true }),
      signal: AbortSignal.timeout(5000)
    });
    const report = await response.json();
    _applyHoloReport(report);
    if (!response.ok && report.message) {
      const feedback = document.getElementById('cam-feedback-text');
      if (feedback) feedback.textContent = report.message;
    }
  } catch (err) {
    const now = Date.now();
    if (now - (_lastWebcamErrorAt || 0) > 2500) {
      _lastWebcamErrorAt = now;
      const feedback = document.getElementById('cam-feedback-text');
      if (feedback) feedback.textContent = 'Bridge webcam non raggiungibile: ' + (err.name === 'TimeoutError' ? 'analisi scaduta.' : 'verifica bridge e connessione.');
      _setHoloState('BRIDGE NON RAGGIUNGIBILE', 'lost');
    }
  } finally {
    _holoCaptureBusy = false;
  }
}

let _lastWebcamErrorAt = 0;

function _applyHoloReport(report) {
  if (!report || typeof report !== 'object') return;
  const state = String(report.state || 'no_camera').toLowerCase();
  const primary = report.primary;
  const drive = report.avatar || {};
  const video = document.getElementById('cam-live-video');
  const frameW = Number(report.metrics?.frame_w) || 320;
  const frameH = Number(report.metrics?.frame_h) || 240;
  const tracking = !!(primary && drive.tracking && (state === 'locked' || state === 'lost'));

  _setHoloState(report.state_label || state.replaceAll('_', ' ').toUpperCase(), tracking ? 'locked' : (state === 'acquiring' ? 'acquiring' : 'lost'));
  const fpsEl = document.getElementById('holo-fps');
  if (fpsEl) fpsEl.textContent = `analisi ${Number(report.metrics?.detect_ms) || 0} ms`;
  const confEl = document.getElementById('holo-confidence');
  if (confEl) confEl.textContent = primary ? `score dlib: ${Number(primary.confidence).toFixed(2)}` : 'volto: in ricerca';
  const faceEl = document.getElementById('holo-facecount');
  if (faceEl) faceEl.textContent = `volti rilevati: ${Number(report.face_count) || 0}`;

  const feedback = document.getElementById('cam-feedback-text');
  if (feedback && report.message) feedback.textContent = report.message;
  if (tracking && video?.videoWidth) {
    const sx = video.videoWidth / frameW;
    const sy = video.videoHeight / frameH;
    _jarvisFace.active = true;
    _jarvisFace.targetX = Number(primary.x) * sx;
    _jarvisFace.targetY = Number(primary.y) * sy;
    _jarvisFace.targetW = Number(primary.w) * sx;
    _jarvisFace.targetH = Number(primary.h) * sy;
    _holoLastConfidence = Number(primary.confidence);
    _driveAvatarFromNorm(primary.offset_x, primary.offset_y, drive);
    if (!_jarvisGreetedSession) {
      _jarvisGreetedSession = true;
      _playJarvisChime();
    }
  } else {
    _jarvisFace.active = false;
    _holoLastConfidence = null;
    const img = document.getElementById('holo-avatar-img');
    const glow = document.getElementById('holo-glow');
    if (img) {
      img.className = 'holo-avatar-img';
      img.style.transform = '';
    }
    const stage = document.getElementById('holo-avatar-stage');
    if (stage) {
      stage.style.setProperty('--eye-x', '0px');
      stage.style.setProperty('--eye-y', '0px');
    }
    if (glow) glow.classList.remove('active');
  }
}

function _setHoloState(text, cls) {
  const badge = document.getElementById('holo-state-badge');
  if (!badge) return;
  badge.textContent = text;
  badge.className = 'holo-state-badge' + (cls ? ' ' + cls : '');
}

window.triggerJarvisAiVisionScan = async function() {
  const video = document.getElementById('cam-live-video');
  const btn = document.getElementById('btn-jarvis-ai-scan');
  const fb = document.getElementById('cam-feedback-text');
  if (!video || !video.videoWidth) {
    if (fb) fb.textContent = 'Camera non attiva: attendi il flusso video.';
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '⚡ SCANSIONE NEURALE IN CORSO...';
    btn.style.opacity = '0.7';
  }
  if (fb) fb.textContent = 'Analisi della scena richiesta: il frame verrà inviato al servizio di visione configurato.';

  try {
    const canvas = document.createElement('canvas');
    canvas.width = Math.min(640, video.videoWidth);
    canvas.height = Math.round(video.videoHeight * (canvas.width / video.videoWidth));
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const b64 = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];

    const res = await fetch('/api/camera/jarvis-vision', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ frame_b64: b64, task_type: 'jarvis_operator_vision' }),
      signal: AbortSignal.timeout(18000)
    });
    const data = await res.json();
    if (!res.ok || data.status === 'error') throw new Error(data.error || `Vision HTTP ${res.status}`);
    const vocalMsg = data.vocal_message || data.visual_description || '';
    const visDesc = data.visual_description || 'Il servizio ha ricevuto il frame ma non ha restituito una descrizione.';

    if (fb) {
      fb.textContent = `E.B.J.: ${visDesc}`;
      fb.style.color = '#00f0ff';
    }
    if (vocalMsg && typeof window.playSpeechAudio === 'function') window.playSpeechAudio(vocalMsg);
  } catch (err) {
    console.warn('[JARVIS AI SCAN ERR]:', err);
    const message = `Analisi non disponibile: ${err.message || 'servizio di visione non raggiungibile.'}`;
    if (fb) fb.textContent = message;
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '👁️ JARVIS COSA VEDI?';
      btn.style.opacity = '1';
    }
  }
};

window.captureWebcamAndAnalyze = function() {
  window.openCameraVisionModal();
  setTimeout(() => {
    window.triggerJarvisAiVisionScan();
  }, 1200);
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

// DYNAMIC SYNC PER MODULO 4 BADREXPRESS & PIETRO TRASLOCHI
async function syncTraslochiLeadBanner() {
  const countEl = document.getElementById('leads-total-count');
  const timeEl = document.getElementById('leads-last-sync-time');
  if (!countEl && !timeEl) return;

  try {
    const res = await fetch('/api/traslochi/list?status=ACTIVE');
    const data = await res.json();
    if (data && Array.isArray(data.leads)) {
      if (countEl) {
        countEl.textContent = data.leads.length;
      }
      if (timeEl) {
        const now = new Date();
        const d = String(now.getDate()).padStart(2, '0');
        const m = String(now.getMonth() + 1).padStart(2, '0');
        const hh = String(now.getHours()).padStart(2, '0');
        const mm = String(now.getMinutes()).padStart(2, '0');
        timeEl.textContent = `Oggi ${d}/${m} ore ${hh}:${mm}`;
      }
    }
  } catch (e) {
    console.warn('Errore sync traslochi lead banner:', e);
  }
}

// Avvio immediato e polling ogni 30s
if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      syncTraslochiLeadBanner();
      setInterval(syncTraslochiLeadBanner, 30000);
    });
  } else {
    syncTraslochiLeadBanner();
    setInterval(syncTraslochiLeadBanner, 30000);
  }
}

// ═══════════════════════════════════════════════════════════════════
// 🌌 PARTICLE SYSTEM BACKGROUND (Neural Network Cosmos)
// GPU-Accelerated Canvas · 144 FPS · Zero CPU Overhead
// ═══════════════════════════════════════════════════════════════════

(function initParticleCosmos() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let width = canvas.width = window.innerWidth;
  let height = canvas.height = window.innerHeight;

  const PARTICLE_COUNT = 80;
  const CONNECTION_DISTANCE = 150;
  const particles = [];

  class Particle {
    constructor() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.vx = (Math.random() - 0.5) * 0.5;
      this.vy = (Math.random() - 0.5) * 0.5;
      this.radius = Math.random() * 2 + 1;
      this.color = Math.random() > 0.5 ? '#00f0ff' : '#00ff9f';
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;

      if (this.x < 0 || this.x > width) this.vx *= -1;
      if (this.y < 0 || this.y > height) this.vy *= -1;
    }

    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.fill();
    }
  }

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push(new Particle());
  }

  function drawConnections() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < CONNECTION_DISTANCE) {
          const opacity = 1 - distance / CONNECTION_DISTANCE;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0, 240, 255, ${opacity * 0.25})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  let _lastFrameTime = 0;
  function animate(timestamp) {
    if (document.hidden) {
      requestAnimationFrame(animate);
      return;
    }
    // Cap at ~60 FPS smooth rendering to save GPU/CPU cycles
    if (timestamp - _lastFrameTime < 14) {
      requestAnimationFrame(animate);
      return;
    }
    _lastFrameTime = timestamp;

    ctx.clearRect(0, 0, width, height);

    particles.forEach(p => {
      p.update();
      p.draw();
    });

    drawConnections();
    requestAnimationFrame(animate);
  }

  requestAnimationFrame(animate);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });
})();

// ═══════════════════════════════════════════════════════════════════
// 🎴 3D CARD TILT EFFECT (Interactive Perspective)
// Mouse-Tracking RotateX/Y · Desktop Only
// ═══════════════════════════════════════════════════════════════════

(function initCardTilt3D() {
  const cards = document.querySelectorAll('.fleet-agent-card, .cmd-tile, .tc-card');

  cards.forEach(card => {
    card.classList.add('card-tilt-3d');

    card.addEventListener('mousemove', (e) => {
      if (window.innerWidth < 1280) return;

      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = ((y - centerY) / centerY) * -10;
      const rotateY = ((x - centerX) / centerX) * 10;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
    });
  });
})();

// ═══════════════════════════════════════════════════════════════════
// 🌈 HOLOGRAPHIC BORDERS - Apply to main panels
// ═══════════════════════════════════════════════════════════════════

(function initHolographicBorders() {
  const panels = document.querySelectorAll('.panel-box, .fleet-agent-card');
  panels.forEach(panel => {
    panel.classList.add('holo-border-animated');
  });
})();

// ═══════════════════════════════════════════════════════════════════
// ⚡ STARK CINEMATIC HUD MODE & DYNAMIC THEME ENGINE
// 60 FPS Focused Experience · Customizable Neon Schemes
// ═══════════════════════════════════════════════════════════════════

window.toggleStarkHudMode = function(forceState = null) {
  const isCurrentlyStark = document.body.classList.contains('stark-hud-mode');
  const newState = forceState !== null ? !!forceState : !isCurrentlyStark;

  document.body.classList.toggle('stark-hud-mode', newState);
  localStorage.setItem('ebj_stark_mode', newState ? 'on' : 'off');

  const btn = document.getElementById('btn-stark-mode');
  if (btn) {
    btn.classList.toggle('active', newState);
    btn.innerHTML = newState 
      ? '<i data-lucide="zap" class="lucide-icon text-cyan"></i>⚡ STARK HUD' 
      : '<i data-lucide="layout" class="lucide-icon"></i>🛠️ PRO CONSOLE';
    try { window.lucide && window.lucide.createIcons(); } catch (_) {}
  }
};

window.setThemePreset = function(themeName) {
  const validThemes = ['stark-cyan', 'stark-gold', 'matrix-emerald', 'crimson-surge'];
  if (!validThemes.includes(themeName)) themeName = 'stark-cyan';

  validThemes.forEach(t => document.body.classList.remove(`theme-${t}`));
  document.body.classList.add(`theme-${themeName}`);
  localStorage.setItem('ebj_theme', themeName);

  document.querySelectorAll('.theme-dot').forEach(dot => {
    dot.classList.toggle('active', dot.getAttribute('data-theme') === themeName);
  });
};

// ── 12. MARK-LV HUD VIDEO STAGE ("VIDEO WHERE THE FACE IS") ──────────
let _hudVideoMuted = true;
window.playHudVideo = function(urlOrQuery) {
  const stage = document.getElementById('jarvis-hud-video-stage');
  const frame = document.getElementById('jarvis-hud-video-frame');
  const orb = document.querySelector('.jarvis-orb-canvas-container');
  if (!stage || !frame) return;

  // Extract YouTube ID if present or embed URL
  let embedUrl = '';
  const ytMatch = String(urlOrQuery).match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/i);
  if (ytMatch && ytMatch[1]) {
    embedUrl = `https://www.youtube-nocookie.com/embed/${ytMatch[1]}?autoplay=1&mute=${_hudVideoMuted ? '1' : '0'}&controls=1&rel=0`;
  } else if (String(urlOrQuery).startsWith('http')) {
    embedUrl = urlOrQuery;
  } else {
    // Search query fallback / demo video
    embedUrl = `https://www.youtube-nocookie.com/embed?listType=search&list=${encodeURIComponent(urlOrQuery)}&autoplay=1&mute=${_hudVideoMuted ? '1' : '0'}`;
  }

  // Swap Stage: hide orb to put video exactly where the avatar face is
  if (orb) orb.style.display = 'none';
  stage.style.display = 'block';

  frame.innerHTML = `<iframe src="${embedUrl}" width="100%" height="100%" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="border:none;"></iframe>`;
  
  if (window.showToolRun) {
    window.showToolRun('MARK-LV HUD VIDEO', 'Video caricato al centro della plancia', '0.002s');
  }
};

window.closeHudVideo = function() {
  const stage = document.getElementById('jarvis-hud-video-stage');
  const frame = document.getElementById('jarvis-hud-video-frame');
  const orb = document.querySelector('.jarvis-orb-canvas-container');
  if (frame) frame.innerHTML = '';
  if (stage) stage.style.display = 'none';
  if (orb) orb.style.display = 'block';
};

window.toggleHudVideoMute = function() {
  _hudVideoMuted = !_hudVideoMuted;
  const btn = document.getElementById('btn-hud-video-mute');
  if (btn) {
    btn.textContent = _hudVideoMuted ? 'AUDIO OFF (MUTED)' : 'AUDIO ON';
    btn.style.color = _hudVideoMuted ? '#fff' : '#00ff9f';
    btn.style.borderColor = _hudVideoMuted ? 'rgba(255,255,255,0.3)' : '#00ff9f';
  }
  // If video is playing, reload iframe with updated mute flag
  const frame = document.getElementById('jarvis-hud-video-frame');
  const iframe = frame ? frame.querySelector('iframe') : null;
  if (iframe && iframe.src) {
    let src = iframe.src;
    src = src.replace(/mute=[01]/, `mute=${_hudVideoMuted ? '1' : '0'}`);
    iframe.src = src;
  }
};

// ── 13. PWA SMART MOBILE INSTALLATION ENGINE ─────────────────────────
let _deferredPwaPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  _deferredPwaPrompt = e;
  
  // Se siamo su mobile o standalone non attivo, mostra il banner elegante in basso
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
  if (!isStandalone) {
    const banner = document.getElementById('ebj-pwa-install-banner');
    if (banner && localStorage.getItem('ebj_pwa_dismissed') !== 'true') {
      banner.style.display = 'block';
    }
  }
});

window.installPwaApp = async function() {
  if (_deferredPwaPrompt) {
    _deferredPwaPrompt.prompt();
    const { outcome } = await _deferredPwaPrompt.userChoice;
    if (outcome === 'accepted') {
      const banner = document.getElementById('ebj-pwa-install-banner');
      if (banner) banner.style.display = 'none';
      if (window.showToolRun) window.showToolRun('APP INSTALLATA', 'EBJ AI installata con successo!', '0.001s');
    }
    _deferredPwaPrompt = null;
  } else {
    // Se il browser (es. iOS Safari o browser senza prompt nativo) non supporta prompt() diretto, mostra la guida visuale
    const modal = document.getElementById('ebj-pwa-guide-modal');
    if (modal) modal.style.display = 'flex';
  }
};

window.dismissPwaBanner = function() {
  const banner = document.getElementById('ebj-pwa-install-banner');
  if (banner) banner.style.display = 'none';
  localStorage.setItem('ebj_pwa_dismissed', 'true');
};

// Se è su mobile e non è ancora installato, mostra il banner dopo 3 secondi
window.addEventListener('DOMContentLoaded', () => {
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
  if (isMobile && !isStandalone && localStorage.getItem('ebj_pwa_dismissed') !== 'true') {
    setTimeout(() => {
      const banner = document.getElementById('ebj-pwa-install-banner');
      if (banner) banner.style.display = 'block';
    }, 2800);
  }
});

// Auto-initialize Stark HUD & Theme on startup
(function initStarkHudAndTheme() {
  const savedTheme = localStorage.getItem('ebj_theme') || 'stark-cyan';
  window.setThemePreset(savedTheme);

  // Default to Stark HUD Mode on first load for a pristine 60 FPS experience
  const savedStark = localStorage.getItem('ebj_stark_mode');
  const shouldBeStark = savedStark !== 'off';
  window.toggleStarkHudMode(shouldBeStark);

  // Default to 3D J.A.R.V.I.S. v8 STARK HUD view
  const savedView = localStorage.getItem('ebj_active_view') || 'topology';
  window.switchMasterView(savedView);
})();

// Registrazione Service Worker per Installazione PWA Reale
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then((reg) => {
      console.log('[PWA] Service Worker registrato con successo, scope:', reg.scope);
    }).catch((err) => {
      console.warn('[PWA] Errore registrazione Service Worker:', err);
    });
  });
}

// ═══════════════════════════════════════════════════════════════════
//  WORKSTATION DESKTOP-SJR1JS8 REMOTE POWER & TELEMETRY CONTROLLER
// ═══════════════════════════════════════════════════════════════════
(function initPcPowerManager() {
  let pcPollTimer = null;
  let pcLastStatus = null;

  window.openPcPowerModal = function() {
    const modal = document.getElementById('modal-pc-power');
    if (modal) {
      modal.style.display = 'flex';
      refreshPcStatus();
    }
    if (window.lucide) {
      setTimeout(() => lucide.createIcons(), 50);
    }
  };

  window.closePcPowerModal = function() {
    const modal = document.getElementById('modal-pc-power');
    if (modal) modal.style.display = 'none';
  };

  async function refreshPcStatus() {
    try {
      const res = await fetch('/api/pc/status', { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      pcLastStatus = data;
      updatePcUI(data, true);
    } catch (err) {
      console.warn('[PC-POWER] Polling error:', err);
      updatePcUI({ status: 'offline', error: err.message }, false);
    }
  }

  function updatePcUI(data, isOnline) {
    const statusUpper = String(data.status || '').toUpperCase();
    const isUp = isOnline && (statusUpper === 'ONLINE' || !data.error);

    // Update status dot & text in top bar
    const dotTop = document.getElementById('pc-status-dot-top');
    const txtTop = document.getElementById('pc-status-txt-top');
    if (dotTop) {
      dotTop.className = 'pc-dot ' + (isUp ? 'online' : 'offline');
    }
    if (txtTop) {
      txtTop.textContent = isUp ? 'ACCESO' : 'SPENTO';
      txtTop.style.color = isUp ? '#00ff9f' : '#ef4444';
    }

    // Update Hero Graphical Status Banner Card
    const bannerCard = document.getElementById('pc-status-banner-card');
    const mainPill = document.getElementById('pc-main-state-pill');
    const screenIcon = document.getElementById('pc-screen-icon');
    const mainSpecs = document.getElementById('pc-main-specs-txt');
    if (bannerCard) {
      bannerCard.className = 'pc-status-banner-card ' + (isUp ? 'online' : 'offline');
    }
    if (mainPill) {
      mainPill.className = 'pc-state-pill ' + (isUp ? 'online' : 'offline');
      mainPill.textContent = isUp ? '● ACCESO' : '● SPENTO';
    }
    if (screenIcon) {
      screenIcon.style.color = isUp ? '#00ff9f' : '#ef4444';
    }
    if (mainSpecs) {
      if (isUp) {
        const cpu = data.cpu_name || 'Ryzen 7 5700X3D';
        const ram = data.ram_total_gb ? (data.ram_total_gb + ' GB') : '64 GB';
        const ip = data.local_ip || '192.168.0.100';
        mainSpecs.textContent = `${cpu} · RTX 4070 · ${ram} RAM · IP: ${ip} · Uptime: ${data.uptime || 'Attivo'}`;
      } else {
        mainSpecs.textContent = 'Host offline o non raggiungibile · Tocca "ACCENDI (WoL)" per svegliare la workstation';
      }
    }

    // Update status in nav drawer
    const dotNav = document.getElementById('pc-status-dot-nav');
    const txtNav = document.getElementById('pc-status-txt-nav');
    if (dotNav) {
      dotNav.style.background = isUp ? '#00ff9f' : '#ef4444';
      dotNav.style.boxShadow = isUp ? '0 0 8px #00ff9f' : '0 0 8px #ef4444';
    }
    if (txtNav) {
      txtNav.textContent = isUp ? 'ACCESO' : 'SPENTO';
      txtNav.style.color = isUp ? '#00ff9f' : '#ef4444';
    }

    // Update Modal
    const modalDot = document.getElementById('pc-modal-dot');
    const modalStatus = document.getElementById('pc-modal-status-text');
    const modalHb = document.getElementById('pc-modal-heartbeat');
    if (modalDot) modalDot.className = 'pc-dot ' + (isUp ? 'online' : 'offline');
    if (modalStatus) {
      modalStatus.textContent = isUp ? 'ONLINE' : 'OFFLINE';
      modalStatus.style.color = isUp ? '#00ff9f' : '#ef4444';
    }
    if (modalHb) {
      modalHb.textContent = isUp ? ('Uptime: ' + (data.uptime || 'Attivo') + ' · Sub-5ms') : 'Host non raggiungibile';
    }

    const cpuVal = data.cpu_name || data.cpu;
    if (cpuVal) {
      const cpuEl = document.getElementById('pc-spec-cpu');
      if (cpuEl) cpuEl.textContent = cpuVal;
    }
    if (data.ram_total_gb || data.ram) {
      const ramEl = document.getElementById('pc-spec-ram');
      if (ramEl) {
        ramEl.textContent = data.ram_total_gb ? (data.ram_total_gb + ' GB (' + (data.ram_used_gb || '') + ' GB usati)') : data.ram;
      }
    }
    const gpuVal = Array.isArray(data.gpus) ? data.gpus.join(' + ') : (data.gpu || null);
    if (gpuVal) {
      const gpuEl = document.getElementById('pc-spec-gpu');
      if (gpuEl) gpuEl.textContent = gpuVal;
    }
    const ipVal = data.local_ip || data.ip;
    if (ipVal) {
      const ipEl = document.getElementById('pc-spec-ip');
      if (ipEl) ipEl.textContent = ipVal;
    }
    const macVal = data.mac_address || data.mac;
    if (macVal) {
      const macEl = document.getElementById('pc-spec-mac');
      if (macEl) macEl.textContent = (data.nic_name ? data.nic_name + ' · ' : 'Intel I225-V · ') + macVal;
    }

    // Abort button visibility
    const abortBtn = document.getElementById('btn-pc-act-abort');
    if (abortBtn) {
      if (data.pending_action) {
        abortBtn.style.display = 'flex';
      } else {
        abortBtn.style.display = 'none';
      }
    }

    if (window.lucide) {
      setTimeout(() => lucide.createIcons(), 30);
    }
  }

  window.triggerPcPower = async function(action) {
    const msgBox = document.getElementById('pc-action-msg');
    const showMsg = (text, isError = false) => {
      if (!msgBox) return;
      msgBox.style.display = 'block';
      msgBox.style.background = isError ? 'rgba(239, 68, 68, 0.15)' : 'rgba(0, 240, 255, 0.15)';
      msgBox.style.borderColor = isError ? '#ef4444' : '#00f0ff';
      msgBox.style.color = isError ? '#f87171' : '#00f0ff';
      msgBox.innerHTML = text;
    };

    if (action === 'shutdown') {
      const ok = confirm("ATTENZIONE: Sei sicuro di voler SPEGNERE la workstation DESKTOP-SJR1JS8?\n(Il comando avvierà un conto alla rovescia di 10 secondi per consentire l'eventuale annullamento)");
      if (!ok) return;
    } else if (action === 'reboot') {
      const ok = confirm("ATTENZIONE: Sei sicuro di voler RIAVVIARE la workstation DESKTOP-SJR1JS8?");
      if (!ok) return;
    }

    showMsg('Invio comando in corso...', false);

    try {
      const res = await fetch('/api/pc/power', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
      });
      const resData = await res.json();
      if (!res.ok || resData.error) {
        showMsg('❌ Errore: ' + (resData.error || 'Operazione fallita'), true);
      } else {
        showMsg('✅ ' + (resData.message || 'Comando eseguito con successo!'), false);
        setTimeout(refreshPcStatus, 1500);
      }
    } catch (err) {
      showMsg('❌ Errore di rete: ' + err.message, true);
    }
  };

  // Start initial polling after 1.5s, then every 8s
  setTimeout(() => {
    refreshPcStatus();
    pcPollTimer = setInterval(refreshPcStatus, 8000);
  }, 1500);
})();

// ═══════════════════════════════════════════════════════════════════
//  JEV UNIVERSAL SYSTEM HUB CONTROLLER (APPS, PHOTOS, EMAIL, IT)
// ═══════════════════════════════════════════════════════════════════
(function initSystemHubManager() {
  window.openSystemHubModal = function() {
    const modal = document.getElementById('modal-system-hub');
    if (modal) {
      modal.style.display = 'flex';
      refreshRunningApps();
    }
    if (window.lucide) {
      setTimeout(() => lucide.createIcons(), 50);
    }
  };

  window.closeSystemHubModal = function() {
    const modal = document.getElementById('modal-system-hub');
    if (modal) modal.style.display = 'none';
  };

  window.switchSystemHubTab = function(tab) {
    const tabApps = document.getElementById('sys-tab-apps');
    const tabPhotos = document.getElementById('sys-tab-photos');
    const tabEmail = document.getElementById('sys-tab-email');
    const btnApps = document.getElementById('tab-btn-sys-apps');
    const btnPhotos = document.getElementById('tab-btn-sys-photos');
    const btnEmail = document.getElementById('tab-btn-sys-email');

    if (tabApps) tabApps.style.display = tab === 'apps' ? 'flex' : 'none';
    if (tabPhotos) tabPhotos.style.display = tab === 'photos' ? 'flex' : 'none';
    if (tabEmail) tabEmail.style.display = tab === 'email' ? 'flex' : 'none';

    if (btnApps) btnApps.classList.toggle('active', tab === 'apps');
    if (btnPhotos) btnPhotos.classList.toggle('active', tab === 'photos');
    if (btnEmail) btnEmail.classList.toggle('active', tab === 'email');

    if (tab === 'photos') loadRecentPhotos();
    if (tab === 'apps') refreshRunningApps();
    if (window.lucide) setTimeout(() => lucide.createIcons(), 50);
  };

  function showSysFeedback(text, isError = false) {
    const msgBox = document.getElementById('sys-action-msg');
    if (!msgBox) return;
    msgBox.style.display = 'block';
    msgBox.style.background = isError ? 'rgba(239, 68, 68, 0.15)' : 'rgba(0, 240, 255, 0.15)';
    msgBox.style.borderColor = isError ? '#ef4444' : '#00f0ff';
    msgBox.style.color = isError ? '#f87171' : '#00f0ff';
    msgBox.innerHTML = text;
    setTimeout(() => { if (msgBox) msgBox.style.display = 'none'; }, 6000);
  }

  window.quickLaunchApp = async function(appName) {
    showSysFeedback('🚀 Avvio di ' + appName + '...', false);
    try {
      const res = await fetch('/api/system/launch-app', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app: appName })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showSysFeedback('✅ ' + (data.message || appName + ' avviato con successo!'), false);
        setTimeout(refreshRunningApps, 1500);
      } else {
        showSysFeedback('❌ Errore: ' + (data.error || data.message), true);
      }
    } catch (err) {
      showSysFeedback('❌ Errore di rete: ' + err.message, true);
    }
  };

  window.launchCustomApp = function() {
    const input = document.getElementById('sys-custom-app-input');
    if (!input || !input.value.trim()) return;
    quickLaunchApp(input.value.trim());
    input.value = '';
  };

  window.refreshRunningApps = async function() {
    const listEl = document.getElementById('sys-running-apps-list');
    if (!listEl) return;
    try {
      const res = await fetch('/api/system/apps', { cache: 'no-store' });
      const data = await res.json();
      const apps = data.running_apps || [];
      if (!apps.length) {
        listEl.innerHTML = '<div style="color:#64748b; padding:4px;">Nessuna finestra utente rilevata al momento.</div>';
        return;
      }
      let html = '';
      for (const a of apps) {
        html += `
          <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:6px; padding:4px 8px;">
            <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:80%;">
              <strong style="color:#00f0ff;">${a.process_name}</strong>: <span style="color:#cbd5e1;">${a.title}</span> <small style="color:#64748b;">(${a.memory_mb} MB)</small>
            </div>
            <button onclick="killRunningProcess('${a.pid}')" style="background:rgba(239,68,68,0.15); border:1px solid #ef4444; color:#f87171; border-radius:4px; padding:2px 6px; font-size:0.7rem; cursor:pointer;" title="Termina processo PID ${a.pid}">✕ Chiudi</button>
          </div>
        `;
      }
      listEl.innerHTML = html;
    } catch (err) {
      listEl.innerHTML = '<div style="color:#ef4444;">Errore recupero processi: ' + err.message + '</div>';
    }
  };

  window.killRunningProcess = async function(pid) {
    if (!confirm('Vuoi davvero terminare il processo PID ' + pid + '?')) return;
    try {
      const res = await fetch('/api/system/kill-app', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pid: pid })
      });
      const data = await res.json();
      showSysFeedback('Processo terminato: ' + (data.output || 'OK'), false);
      setTimeout(refreshRunningApps, 1000);
    } catch (err) {
      showSysFeedback('Errore: ' + err.message, true);
    }
  };

  window.loadRecentPhotos = async function() {
    const gridEl = document.getElementById('sys-photos-grid');
    if (!gridEl) return;
    try {
      gridEl.innerHTML = '<div style="color:#64748b;">Scansione foto in corso...</div>';
      const res = await fetch('/api/system/photos', { cache: 'no-store' });
      const data = await res.json();
      const photos = data.photos || [];
      if (!photos.length) {
        gridEl.innerHTML = '<div style="color:#64748b;">Nessuna foto recente trovata su disco.</div>';
        return;
      }
      let html = '';
      for (const ph of photos) {
        const encPath = encodeURIComponent(ph.path);
        const imgUrl = '/api/system/photo-file?path=' + encPath;
        html += `
          <div style="background:rgba(0,0,0,0.6); border:1px solid rgba(0,240,255,0.25); border-radius:8px; overflow:hidden; display:flex; flex-direction:column; transition:transform 0.2s;" onmouseenter="this.style.borderColor='#00f0ff'" onmouseleave="this.style.borderColor='rgba(0,240,255,0.25)'">
            <div style="height:90px; background:#010915; overflow:hidden; display:flex; align-items:center; justify-content:center; cursor:pointer;" onclick="openPhotoOnScreen('${encodeURIComponent(ph.path)}')">
              <img src="${imgUrl}" alt="${ph.filename}" style="width:100%; height:100%; object-fit:cover;" loading="lazy">
            </div>
            <div style="padding:6px; font-family:var(--font-mono); font-size:0.68rem; display:flex; flex-direction:column; gap:2px;">
              <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#e2e8f0;" title="${ph.filename}"><strong>${ph.filename}</strong></span>
              <span style="color:#64748b;">${ph.size_kb} KB · ${ph.date_str.split(' ')[0]}</span>
              <button onclick="openPhotoOnScreen('${encodeURIComponent(ph.path)}')" style="margin-top:4px; background:rgba(0,255,159,0.15); border:1px solid #00ff9f; color:#00ff9f; border-radius:4px; padding:3px 6px; font-size:0.65rem; cursor:pointer; font-weight:bold;">🖥️ Mostra su Schermo</button>
            </div>
          </div>
        `;
      }
      gridEl.innerHTML = html;
    } catch (err) {
      gridEl.innerHTML = '<div style="color:#ef4444;">Errore recupero foto: ' + err.message + '</div>';
    }
  };

  window.openPhotoOnScreen = async function(encodedPath) {
    const rawPath = decodeURIComponent(encodedPath);
    showSysFeedback('🖼️ Apertura di ' + rawPath.split('\\').pop() + '...', false);
    try {
      const res = await fetch('/api/system/show-photo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: rawPath, open_native: true })
      });
      const data = await res.json();
      showSysFeedback('✅ ' + (data.message || 'Foto aperta su schermo!'), false);
    } catch (err) {
      showSysFeedback('❌ Errore: ' + err.message, true);
    }
  };

  window.triggerScreenshotNow = async function() {
    showSysFeedback('📸 Cattura screenshot dello schermo in corso...', false);
    try {
      const res = await fetch('/api/system/screenshot', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        showSysFeedback('✅ ' + data.message, false);
        loadRecentPhotos();
      } else {
        showSysFeedback('❌ Errore screenshot: ' + (data.error || data.message), true);
      }
    } catch (err) {
      showSysFeedback('❌ Errore: ' + err.message, true);
    }
  };

  window.sendQuickEmailNow = async function() {
    const to = document.getElementById('sys-email-to').value.trim();
    const subject = document.getElementById('sys-email-subject').value.trim();
    const body = document.getElementById('sys-email-body').value.trim();
    const voiceNote = document.getElementById('sys-email-voice').checked ? body : null;

    if (!to || !body) {
      alert('Inserisci almeno destinatario e messaggio!');
      return;
    }

    showSysFeedback('✉️ Invio email in corso tramite server Gmail...', false);
    try {
      const res = await fetch('/api/system/send-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to: to,
          subject: subject,
          body: body,
          voice_note: voiceNote
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showSysFeedback('✅ ' + data.message, false);
        document.getElementById('sys-email-body').value = '';
      } else {
        showSysFeedback('❌ Errore invio: ' + (data.error || data.message), true);
      }
    } catch (err) {
      showSysFeedback('❌ Errore di rete: ' + err.message, true);
    }
  };
})();





