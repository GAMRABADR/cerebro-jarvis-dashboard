// Cybernetic WebAudio Spatial Synthesizer for CEREBRO E.B.J.
class CyberAudioEngine {
  constructor() {
    this.ctx = null;
    this.isMuted = false;
  }

  initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playEclipseChirp() {
    if (this.isMuted) return;
    this.initContext();
    if (!this.ctx) return;

    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const filter = this.ctx.createBiquadFilter();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
      osc.frequency.exponentialRampToValueAtTime(1320, now + 0.25);

      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(880, now);
      filter.Q.setValueAtTime(8.0, now);

      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.08, now + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.3);
    } catch (e) {}
  }

  playConfirmationLaser() {
    if (this.isMuted) return;
    this.initContext();
    if (!this.ctx) return;

    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(1760, now);
      osc.frequency.exponentialRampToValueAtTime(440, now + 0.18);

      gain.gain.setValueAtTime(0.09, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.20);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.22);
    } catch (e) {}
  }

  playRecordingBeep() {
    if (this.isMuted) return;
    this.initContext();
    if (!this.ctx) return;

    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(987.77, now);

      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.14);
    } catch (e) {}
  }

  // ── J.A.R.V.I.S. STARK INDUSTRIES AUDIO DSP ─────────────────────────────
  createJarvisDspChain(inputNode) {
    if (!this.ctx) return inputNode;
    try {
      // 1. Peaking EQ per risonanza metallica elmo Iron Man / Stark Mark VII
      const helmetPeaking = this.ctx.createBiquadFilter();
      helmetPeaking.type = 'peaking';
      helmetPeaking.frequency.setValueAtTime(1850, this.ctx.currentTime);
      helmetPeaking.Q.setValueAtTime(2.8, this.ctx.currentTime);
      helmetPeaking.gain.setValueAtTime(3.8, this.ctx.currentTime); // +3.8 dB boost

      // 2. High-pass filter per tagliare il rumble sub-sonico non vocale
      const highPass = this.ctx.createBiquadFilter();
      highPass.type = 'highpass';
      highPass.frequency.setValueAtTime(120, this.ctx.currentTime);

      // 3. Dynamics Compressor da studio broadcast cinematografico
      const compressor = this.ctx.createDynamicsCompressor();
      compressor.threshold.setValueAtTime(-18, this.ctx.currentTime);
      compressor.knee.setValueAtTime(6, this.ctx.currentTime);
      compressor.ratio.setValueAtTime(4.0, this.ctx.currentTime);
      compressor.attack.setValueAtTime(0.003, this.ctx.currentTime);
      compressor.release.setValueAtTime(0.25, this.ctx.currentTime);

      inputNode.connect(highPass);
      highPass.connect(helmetPeaking);
      helmetPeaking.connect(compressor);
      compressor.connect(this.ctx.destination);

      return compressor;
    } catch (e) {
      inputNode.connect(this.ctx.destination);
      return inputNode;
    }
  }

  playArcReactorBoot() {
    if (this.isMuted) return;
    this.initContext();
    if (!this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(55, now);
      osc.frequency.exponentialRampToValueAtTime(110, now + 0.5);
      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.65);
    } catch (e) {}
  }

  playTargetLock() {
    if (this.isMuted) return;
    this.initContext();
    if (!this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(2400, now);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.16);
    } catch (e) {}
  }

  playAccessGranted() {
    if (this.isMuted) return;
    this.initContext();
    if (!this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + i * 0.06);
        gain.gain.setValueAtTime(0.06, now + i * 0.06);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.06 + 0.2);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now + i * 0.06);
        osc.stop(now + i * 0.06 + 0.22);
      });
    } catch (e) {}
  }
  // ── FULL-DUPLEX CONTINUOUS DIALOGUE & LIVE VAD ─────────────────────────
  async startContinuousVoice(onSpeechStart, onSpeechEnd, onEnergyUpdate) {
    if (this.isListeningActive) return;
    this.initContext();
    if (!this.ctx) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      this.micStream = stream;
      this.micSource = this.ctx.createMediaStreamSource(stream);
      this.analyser = this.ctx.createAnalyser();
      this.analyser.fftSize = 128; // 64 bande di frequenza
      this.analyser.smoothingTimeConstant = 0.4;
      this.micSource.connect(this.analyser);

      // WebSocket Rust locale solo se in chiaro (evita mixed content su HTTPS)
      if (window.location.protocol !== 'https:') {
        try {
          this.dialogueWs = new WebSocket('ws://localhost:9000/ws/voice-dialogue');
          this.dialogueWs.onmessage = (ev) => {
            try {
              const msg = JSON.parse(ev.data);
              if (msg.type === 'VAD_SPEECH_START') {
                this.interruptJarvisSpeaking(); // BARGE-IN IMMEDIATO
                onSpeechStart && onSpeechStart(msg);
              } else if (msg.type === 'VAD_SPEECH_END') {
                onSpeechEnd && onSpeechEnd(msg);
              }
            } catch (e) {}
          };
        } catch (_) {}
      }

      this.isListeningActive = true;
      const dataArray = new Uint8Array(this.analyser.frequencyBinCount);

      const loop = () => {
        if (!this.isListeningActive) return;
        this.analyser.getByteFrequencyData(dataArray);

        // Calcolo energia RMS vocale
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i] * dataArray[i];
        }
        const rms = Math.sqrt(sum / dataArray.length) / 255.0;

        // Invia telemetria audio ogni frame se il socket è aperto
        if (this.dialogueWs && this.dialogueWs.readyState === WebSocket.OPEN) {
          this.dialogueWs.send(JSON.stringify({
            type: 'AUDIO_FRAME_ENERGY',
            energy: rms
          }));
        }

        onEnergyUpdate && onEnergyUpdate(rms, dataArray);
        this.vadRaf = requestAnimationFrame(loop);
      };

      this.vadRaf = requestAnimationFrame(loop);
      this.playAccessGranted();
      return true;
    } catch (err) {
      console.warn('Impossibile accedere al microfono:', err);
      return false;
    }
  }

  stopContinuousVoice() {
    this.isListeningActive = false;
    if (this.vadRaf) cancelAnimationFrame(this.vadRaf);
    if (this.micStream) {
      this.micStream.getTracks().forEach(t => t.stop());
    }
    if (this.dialogueWs) {
      this.dialogueWs.close();
    }
    this.playEclipseChirp();
  }

  interruptJarvisSpeaking() {
    // Barge-In: ferma qualsiasi audio in riproduzione attiva (WebAudio, Audio Element, SpeechSynthesis)
    if (typeof window.stopEbjSpeech === 'function') {
      window.stopEbjSpeech();
    }
    if (window.currentPlayingVoiceAudio) {
      try {
        window.currentPlayingVoiceAudio.pause();
        window.currentPlayingVoiceAudio.currentTime = 0;
        window.currentPlayingVoiceAudio = null;
      } catch (e) {}
    }
  }
}

window.cyberAudio = new CyberAudioEngine();
window.playUiClick = function () { window.cyberAudio && window.cyberAudio.playEclipseChirp(); };
window.playLaserChime = function () { window.cyberAudio && window.cyberAudio.playConfirmationLaser(); };
window.playArcReactor = function () { window.cyberAudio && window.cyberAudio.playArcReactorBoot(); };
window.playTargetLock = function () { window.cyberAudio && window.cyberAudio.playTargetLock(); };
window.playAccessGranted = function () { window.cyberAudio && window.cyberAudio.playAccessGranted(); };
