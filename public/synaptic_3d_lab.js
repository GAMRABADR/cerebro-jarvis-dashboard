// ═══════════════════════════════════════════════════════════════════════════════
//  CEREBRO JARVIS · BORDERLESS 3D HOLOGRAPHIC CONNECTOME v14.0
//  Pure Holographic Spatial Projection (No Box Frames, No Bounding Border)
//  Oracle VPS Core integrated directly into the Neural Cluster as White Star
//  Dotted Green Bio-Plasma Impulses & Precise Category Synaptic Flares
// ═══════════════════════════════════════════════════════════════════════════════

/* ─────────────────────────────────────────────────────────────────────────────
   CLASS 1: HollywoodNeuralPlexus — Fullscreen Deep Space Ambient Network
───────────────────────────────────────────────────────────────────────────── */
class HollywoodNeuralPlexus {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.nodes = [];
    this.mouse = { x: -1000, y: -1000 };
    this.time = 0;
    this.isThinking = false;
    this.isSpeaking = false;

    this.resize();
    this.initPlexus();
    this.bindEvents();
    this.animate();
  }

  resize() {
    this.width  = this.canvas.width  = window.innerWidth;
    this.height = this.canvas.height = window.innerHeight;
  }

  initPlexus() {
    const count = Math.min(45, Math.floor((this.width * this.height) / 36000));
    this.nodes  = [];
    const hubs = [
      { label: 'COGNITIVE CORE', color: '#00f0ff', size: 3.5 },
      { label: 'MEMORY VAULT',   color: '#ffb703', size: 3.2 },
      { label: 'API CONNECTORS', color: '#00ff9f', size: 3.0 },
      { label: 'VOICE SYNTHESIS',color: '#00ff88', size: 3.0 },
      { label: 'RUST ENGINE',    color: '#fb5607', size: 3.0 }
    ];

    for (let i = 0; i < count; i++) {
      const hub = i < hubs.length ? hubs[i] : null;
      this.nodes.push({
        x: Math.random() * this.width,
        y: Math.random() * this.height,
        vx: (Math.random() - 0.5) * 0.08,
        vy: (Math.random() - 0.5) * 0.08,
        radius: hub ? hub.size : 0.9 + Math.random() * 1.2,
        color: hub ? hub.color : '#00d4ff',
        label: hub ? hub.label : ''
      });
    }
  }

  bindEvents() {
    window.addEventListener('resize', () => { this.resize(); this.initPlexus(); });
    window.addEventListener('mousemove', (e) => { this.mouse.x = e.clientX; this.mouse.y = e.clientY; });
  }

  setThinking(val) { this.isThinking = val; }
  setSpeaking(val) { this.isSpeaking = val; }

  animate() {
    this.time += 0.005;
    const ctx = this.ctx, w = this.width, h = this.height;
    ctx.clearRect(0, 0, w, h);

    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const dx = this.nodes[i].x - this.nodes[j].x;
        const dy = this.nodes[i].y - this.nodes[j].y;
        const dist = Math.hypot(dx, dy);
        if (dist < 105) {
          ctx.beginPath();
          ctx.moveTo(this.nodes[i].x, this.nodes[i].y);
          ctx.lineTo(this.nodes[j].x, this.nodes[j].y);
          ctx.strokeStyle = `rgba(0, 255, 159, ${(1 - dist/105) * 0.065})`;
          ctx.lineWidth = 0.45;
          ctx.stroke();
        }
      }
    }

    this.nodes.forEach(n => {
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 0 || n.x > w) n.vx *= -1;
      if (n.y < 0 || n.y > h) n.vy *= -1;

      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = n.color;
      ctx.fill();

      if (n.label) {
        ctx.fillStyle = 'rgba(0, 255, 159, 0.55)';
        ctx.font = '7.5px "Share Tech Mono", monospace';
        ctx.fillText(n.label, n.x + 5, n.y + 2);
      }
    });

    requestAnimationFrame(() => this.animate());
  }
}

/* ─────────────────────────────────────────────────────────────────────────────
   CLASS 2: BorderlessHologramConnectome — Pure Volumetric Floating Brain
───────────────────────────────────────────────────────────────────────────── */
class BorderlessHologramConnectome {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.time = 0;

    // Smooth Euler Rotation angles
    this.rotX = 0.22;
    this.rotY = 0.0;
    this.targetRotX = 0.22;
    this.targetRotY = 0.0;

    this.isDragging = false;
    this.prevMouse = { x: 0, y: 0 };
    this.isThinking = false;
    this.isSpeaking = false;

    // Web Audio API Analyser
    this.audioAnalyser = null;
    this.audioData = new Uint8Array(32);
    this.currentAudioLevel = 0.0;

    // Active Tool State Tracking
    this.activeTools = new Map();
    this.eruptions = [];

    this.zoneNodes = [];
    this.synapticCords = [];
    this.dottedPlasmaPackets = [];
    this.hoveredNode = null;

    this.zoneAngles = {
      'cognition': { x: 0.35, y: 0.0 },
      'api':       { x: 0.20, y: -Math.PI / 2.4 },
      'voice':     { x: 0.15, y: 0.0 },
      'vision':    { x: 0.20, y: Math.PI },
      'action':    { x: -0.45, y: 0.0 },
      'memory':    { x: 0.15, y: 0.0 }
    };

    this.resize();
    this.generateConnectomeArchitecture();
    this.bindEvents();
    this.startEventPolling();
    this.animate();
  }

  resize() {
    const parent = this.canvas.parentElement;
    this.width  = this.canvas.width  = parent ? parent.clientWidth : 340;
    this.height = this.canvas.height = parent ? parent.clientHeight : 340;
    this.cx = this.width / 2;
    this.cy = this.height / 2;
  }

  setAudioAnalyser(analyser) {
    this.audioAnalyser = analyser;
    if (analyser) {
      this.audioData = new Uint8Array(analyser.frequencyBinCount);
      this.isSpeaking = true;
    } else {
      this.isSpeaking = false;
      this.currentAudioLevel = 0.0;
    }
  }

  generateConnectomeArchitecture() {
    this.zoneNodes = [];
    this.synapticCords = [];

    const scale = Math.min(this.width, this.height) * 0.44;

    // 1. Functional Cortical Zones & Tool Nodes
    const zones = [
      { id: 'cognition', name: 'FRONTAL COGNITION', color: '#00f0ff', lx: 0.0, ly: -0.75, lz: 0.65, count: 18, desc: 'Ragionamento, Planning & LLM Logic', toolId: 'llm_reasoning' },
      { id: 'memory', name: 'AI MEMORY & SKILL VAULT', color: '#ffb703', lx: 0.0, ly: -0.05, lz: 0.0, count: 20, desc: 'Archivio Skill, FTS5 & Memoria Olografica', toolId: 'memory_vault' },
      { id: 'api', name: 'API CONNECTORS & SMTP', color: '#00ff9f', lx: 0.75, ly: -0.4, lz: 0.25, count: 14, desc: 'Google SMTP SSL, Webhook & Telegram Bot', toolId: 'real_smtp_mailer' },
      { id: 'voice', name: 'TEMPORAL VOICE & AUDIO', color: '#38bdf8', lx: -0.75, ly: 0.15, lz: 0.35, count: 14, desc: 'Fish Audio, Edge TTS & Whisper STT', toolId: 'voice_tts' },
      { id: 'action', name: 'ACTION EXECUTION & RUST', color: '#fb5607', lx: 0.0, ly: 0.75, lz: -0.35, count: 14, desc: 'Motore Rust Sub-ms, Pipeline & Runner', toolId: 'rust_fast_parser' },
      { id: 'vision', name: 'OCCIPITAL VISION & UE5', color: '#818cf8', lx: 0.0, ly: -0.2, lz: -0.85, count: 16, desc: 'Game Ops, Unreal Engine 5.8 & Media Forge', toolId: 'ue5_game_ops' }
    ];

    zones.forEach(z => {
      for (let i = 0; i < z.count; i++) {
        const spread = (z.id === 'memory') ? 0.30 : 0.25;
        const ox = (Math.random() - 0.5) * scale * spread;
        const oy = (Math.random() - 0.5) * scale * spread;
        const oz = (Math.random() - 0.5) * scale * spread;

        this.zoneNodes.push({
          zoneId: z.id,
          zoneName: z.name,
          toolId: z.toolId,
          color: z.color,
          desc: z.desc,
          x: z.lx * scale + ox,
          y: z.ly * scale + oy,
          z: z.lz * scale + oz,
          baseSize: z.id === 'memory' ? (1.7 + Math.random() * 1.5) : (1.3 + Math.random() * 1.3),
          pulseOffset: Math.random() * Math.PI * 2,
          screenX: 0, screenY: 0, depth: 0,
          isToolMasterNode: (i === 0)
        });
      }
    });

    // 2. ORACLE VPS WHITE QUANTUM NODE (Integrated directly inside the brain cluster!)
    this.zoneNodes.push({
      zoneId: 'api',
      zoneName: 'ORACLE VPS CLOUD HUB',
      toolId: 'oracle_vps_core',
      color: '#ffffff', // Glowing White Star!
      desc: 'Nodo Centrale Oracle VPS Ubuntu (92.4.233.42)',
      x: 0.45 * scale,
      y: 0.35 * scale,
      z: 0.15 * scale,
      baseSize: 2.6,
      pulseOffset: 0,
      screenX: 0, screenY: 0, depth: 0,
      isToolMasterNode: true
    });

    // 3. Parametric Outer Brain Cortex Frame Points
    for (let i = 0; i < 150; i++) {
      const u = Math.random() * Math.PI * 2;
      const v = (Math.random() - 0.5) * Math.PI;
      const hemi = Math.random() > 0.5 ? 1 : -1;

      let rX = Math.cos(v) * Math.cos(u);
      let rY = Math.sin(v) * (1.0 - Math.abs(rX) * 0.15);
      let rZ = Math.cos(v) * Math.sin(u) * 1.25;

      rX = (rX * 0.72 + (hemi * 0.28)) * (1.0 + Math.sin(u * 5) * 0.06);
      rY = (rY * 0.85 - 0.1) * (1.0 + Math.cos(v * 6) * 0.05);

      this.zoneNodes.push({
        zoneId: 'cortex_contour',
        zoneName: 'CORTICAL CONNECTOME',
        color: hemi > 0 ? '#00f0ff' : '#00ff9f',
        desc: 'Corteccia neurale a fibre ottiche',
        x: rX * scale,
        y: rY * scale,
        z: rZ * scale * 0.95,
        baseSize: 0.8 + Math.random() * 0.8,
        pulseOffset: Math.random() * Math.PI * 2,
        screenX: 0, screenY: 0, depth: 0
      });
    }

    // 4. Synaptic Projection Cords
    for (let i = 0; i < this.zoneNodes.length; i++) {
      for (let j = i + 1; j < this.zoneNodes.length; j++) {
        const n1 = this.zoneNodes[i];
        const n2 = this.zoneNodes[j];
        const dist = Math.hypot(n1.x - n2.x, n1.y - n2.y, n1.z - n2.z);

        const sameZone = (n1.zoneId === n2.zoneId && n1.zoneId !== 'cortex_contour');
        const memoryLink = (n1.zoneId === 'memory' || n2.zoneId === 'memory');

        if ((sameZone && dist < scale * 0.36) || (memoryLink && dist < scale * 0.72 && Math.random() < 0.2)) {
          this.synapticCords.push({
            n1: n1,
            n2: n2,
            baseColor: n1.color,
            isProjectionTrunk: memoryLink
          });
        }
      }
    }
  }

  bindEvents() {
    window.addEventListener('resize', () => {
      this.resize();
      this.generateConnectomeArchitecture();
    });

    this.canvas.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.prevMouse = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mouseup', () => { this.isDragging = false; });

    window.addEventListener('mousemove', (e) => {
      if (this.isDragging) {
        const dx = e.clientX - this.prevMouse.x;
        const dy = e.clientY - this.prevMouse.y;
        this.targetRotY += dx * 0.006;
        this.targetRotX += dy * 0.006;
        this.prevMouse = { x: e.clientX, y: e.clientY };
      } else {
        const rect = this.canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        let found = null;
        this.zoneNodes.forEach(node => {
          if (node.depth > 0 && node.zoneId !== 'cortex_contour') {
            const d = Math.hypot(mx - node.screenX, my - node.screenY);
            if (d < 15) found = node;
          }
        });
        this.hoveredNode = found;
        this.canvas.style.cursor = found ? 'pointer' : (this.isDragging ? 'grabbing' : 'grab');
      }
    });

    this.canvas.addEventListener('click', () => {
      if (this.hoveredNode) {
        this.activateTool(this.hoveredNode.zoneId, 3600);
      }
    });
  }

  activateTool(zoneId, durationMs = 3600, skillName = '') {
    const now = Date.now();
    const zoneInfo = this.zoneAngles[zoneId];
    if (!zoneInfo) return;

    const targetNodeColor = this.zoneNodes.find(n => n.zoneId === zoneId)?.color || '#00f0ff';

    this.activeTools.set(zoneId, {
      endTime: now + durationMs,
      name: skillName || zoneId.toUpperCase(),
      categoryColor: targetNodeColor
    });

    const currentRotY = this.rotY;
    const baseTargetY = zoneInfo.y;
    const turns = Math.round((currentRotY - baseTargetY) / (Math.PI * 2));
    this.targetRotY = baseTargetY + turns * (Math.PI * 2);
    this.targetRotX = zoneInfo.x;

    const targetNodes = this.zoneNodes.filter(n => n.zoneId === zoneId);
    if (targetNodes.length > 0) {
      for (let i = 0; i < 3; i++) {
        const dst = targetNodes[Math.floor(Math.random() * targetNodes.length)];
        for (let b = 0; b < 3; b++) {
          this.dottedPlasmaPackets.push({
            startX: 0, startY: 0, startZ: 0,
            endX: dst.x, endY: dst.y, endZ: dst.z,
            progress: -(b * 0.14),
            speed: 0.022,
            color: '#00ff9f',
            targetColor: targetNodeColor,
            dstNode: dst
          });
        }
      }
    }
  }

  triggerEruption(zoneId) {
    const nodes = this.zoneNodes.filter(n => n.zoneId === zoneId);
    if (nodes.length === 0) return;
    const centerNode = nodes[0];

    this.eruptions.push({
      x: centerNode.x, y: centerNode.y, z: centerNode.z,
      radius: 3,
      maxRadius: 45,
      alpha: 0.85,
      color: centerNode.color,
      sparks: Array.from({ length: 14 }, () => ({
        vx: (Math.random() - 0.5) * 2.4,
        vy: (Math.random() - 0.5) * 2.4,
        vz: (Math.random() - 0.5) * 2.4,
        x: centerNode.x, y: centerNode.y, z: centerNode.z,
        life: 1.0,
        decay: 0.035 + Math.random() * 0.03
      }))
    });
  }

  startEventPolling() {
    setInterval(async () => {
      try {
        const res = await fetch('/api/synapse/events');
        const data = await res.json();
        if (data.events && data.events.length > 0) {
          data.events.forEach(ev => {
            const mapping = {
              'traslochi_funnel': 'api',
              'real_smtp_mailer': 'api',
              'ue5_game_ops': 'vision',
              'youtube_dayz_studio': 'vision',
              'rust_fast_parser': 'action',
              'n8n_nervous_system': 'api'
            };
            const zone = mapping[ev.skill_id] || 'cognition';
            this.activateTool(zone, 3800, ev.skill_id);
          });
        }
      } catch (e) {}
    }, 240);
  }

  setThinking(val) {
    this.isThinking = val;
    if (val) this.activateTool('cognition', 3000, 'LLM THINKING');
    else this.activeTools.delete('cognition');
  }

  setSpeaking(val) {
    this.isSpeaking = val;
    if (val) {
      this.activateTool('voice', 4000, 'CEREBRO VOICE');
    } else {
      this.activeTools.delete('voice');
    }
  }

  project3D(x, y, z) {
    const cosY = Math.cos(this.rotY), sinY = Math.sin(this.rotY);
    const cosX = Math.cos(this.rotX), sinX = Math.sin(this.rotX);

    let x1 = x * cosY + z * sinY;
    let z1 = -x * sinY + z * cosY;

    let y2 = y * cosX - z1 * sinX;
    let z2 = y * sinX + z1 * cosX;

    const distance = 270;
    const depth = (z2 + distance) / distance;
    if (depth <= 0.05) return { x: this.cx, y: this.cy, scale: 0, depth: -1 };

    return {
      x: this.cx + (x1 / depth),
      y: this.cy + (y2 / depth),
      depth: depth,
      scale: 1 / depth,
      rawZ: z2
    };
  }

  animate() {
    this.time += 0.015;
    const now = Date.now();
    const ctx = this.ctx, w = this.width, h = this.height;
    
    // Pure transparent clear — NO black bounding boxes
    ctx.clearRect(0, 0, w, h);

    let realAudioVolume = 0.0;
    if (this.audioAnalyser && this.isSpeaking) {
      this.audioAnalyser.getByteFrequencyData(this.audioData);
      let sum = 0;
      for (let i = 0; i < this.audioData.length; i++) sum += this.audioData[i];
      realAudioVolume = (sum / this.audioData.length) / 128.0;
      this.currentAudioLevel = this.currentAudioLevel * 0.6 + realAudioVolume * 0.4;
    } else if (this.isSpeaking) {
      this.currentAudioLevel = Math.sin(this.time * 12.0) * 0.4 + 0.5;
    } else {
      this.currentAudioLevel *= 0.85;
    }

    const hasActiveTools = this.activeTools.size > 0;
    const isSpk = this.isSpeaking;
    const isThk = this.isThinking;

    this.activeTools.forEach((tool, zoneId) => {
      if (now >= tool.endTime) {
        this.triggerEruption(zoneId);
        this.activeTools.delete(zoneId);
      }
    });

    // ── ROTATIONAL DYNAMICS ────────────────────────────────────────────────
    if (!this.isDragging) {
      if (isSpk) {
        this.targetRotY += 0.00005;
        this.rotX += (this.targetRotX - this.rotX) * 0.035;
        this.rotY += (this.targetRotY - this.rotY) * 0.035;
      } else if (hasActiveTools) {
        this.rotX += (this.targetRotX - this.rotX) * 0.035;
        this.rotY += (this.targetRotY - this.rotY) * 0.035;
      } else {
        this.targetRotY += 0.0007;
        this.rotX += (this.targetRotX - this.rotX) * 0.022;
        this.rotY += (this.targetRotY - this.rotY) * 0.022;
      }
    }

    // 1. Draw Synaptic Projection Cords (Dotted laser traces)
    this.synapticCords.forEach(cord => {
      const p1 = this.project3D(cord.n1.x, cord.n1.y, cord.n1.z);
      const p2 = this.project3D(cord.n2.x, cord.n2.y, cord.n2.z);
      if (p1.depth > 0 && p2.depth > 0) {
        const isCordActive = this.activeTools.has(cord.n1.zoneId) || this.activeTools.has(cord.n2.zoneId);
        const avgZ = (p1.rawZ + p2.rawZ) / 2;
        const depthAlpha = Math.max(0.08, Math.min(0.85, (avgZ + 120) / 240));

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);

        if (isCordActive) {
          ctx.setLineDash([3, 4]);
          ctx.lineDashOffset = -this.time * 30;
          ctx.strokeStyle = '#00ff9f';
          ctx.lineWidth = 1.4 * ((p1.scale + p2.scale) / 2);
          ctx.shadowBlur = 10;
          ctx.shadowColor = '#00ff9f';
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.shadowBlur = 0;
        } else {
          ctx.strokeStyle = cord.baseColor + Math.round(depthAlpha * (cord.isProjectionTrunk ? 38 : 20)).toString(16).padStart(2, '0');
          ctx.lineWidth = 0.5 * ((p1.scale + p2.scale) / 2);
          ctx.stroke();
        }
      }
    });

    // 2. Draw Dotted Plasma Photon Beads
    for (let i = this.dottedPlasmaPackets.length - 1; i >= 0; i--) {
      const pkt = this.dottedPlasmaPackets[i];
      pkt.progress += pkt.speed;

      if (pkt.progress >= 0 && pkt.progress <= 1.0) {
        const curX = pkt.startX + (pkt.endX - pkt.startX) * pkt.progress;
        const curY = pkt.startY + (pkt.endY - pkt.startY) * pkt.progress;
        const curZ = pkt.startZ + (pkt.endZ - pkt.startZ) * pkt.progress;

        const pCur = this.project3D(curX, curY, curZ);
        if (pCur.depth > 0) {
          ctx.beginPath();
          ctx.arc(pCur.x, pCur.y, 2.2 * pCur.scale, 0, Math.PI * 2);
          ctx.fillStyle = pkt.color;
          ctx.shadowBlur = 14;
          ctx.shadowColor = pkt.color;
          ctx.fill();
          ctx.shadowBlur = 0;

          ctx.beginPath();
          ctx.arc(pCur.x, pCur.y, 1.0 * pCur.scale, 0, Math.PI * 2);
          ctx.fillStyle = '#ffffff';
          ctx.fill();
        }
      }

      if (pkt.progress >= 1.0) {
        this.dottedPlasmaPackets.splice(i, 1);
      }
    }

    // 3. Draw Post-Execution Energy Eruptions
    for (let i = this.eruptions.length - 1; i >= 0; i--) {
      const er = this.eruptions[i];
      er.radius += 1.6;
      er.alpha -= 0.03;

      const pCenter = this.project3D(er.x, er.y, er.z);
      if (pCenter.depth > 0 && er.alpha > 0) {
        ctx.beginPath();
        ctx.arc(pCenter.x, pCenter.y, er.radius * pCenter.scale, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 255, 255, ${er.alpha * 0.75})`;
        ctx.lineWidth = 1.2 * pCenter.scale;
        ctx.shadowBlur = 12;
        ctx.shadowColor = er.color;
        ctx.stroke();
        ctx.shadowBlur = 0;

        er.sparks.forEach(sp => {
          sp.x += sp.vx; sp.y += sp.vy; sp.z += sp.vz;
          sp.life -= sp.decay;
          const pSp = this.project3D(sp.x, sp.y, sp.z);
          if (pSp.depth > 0 && sp.life > 0) {
            ctx.beginPath();
            ctx.arc(pSp.x, pSp.y, 1.2 * pSp.scale * sp.life, 0, Math.PI * 2);
            ctx.fillStyle = er.color;
            ctx.fill();
          }
        });
      }

      if (er.alpha <= 0) this.eruptions.splice(i, 1);
    }

    // 4. Draw SINGLE CENTRAL ARC REACTOR CORE (Audio Spectrum Sync)
    const pCore = this.project3D(0, 0, 0);
    if (pCore.depth > 0) {
      if (isSpk) {
        const audioMod = this.currentAudioLevel * 4.5;
        const arcRadius = (6.0 + audioMod) * pCore.scale;

        if (this.currentAudioLevel > 0.35) {
          ctx.beginPath();
          ctx.arc(pCore.x, pCore.y, (arcRadius + 14 * this.currentAudioLevel), 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(0, 255, 159, ${this.currentAudioLevel * 0.7})`;
          ctx.lineWidth = 1.2;
          ctx.stroke();
        }

        ctx.beginPath();
        ctx.arc(pCore.x, pCore.y, arcRadius * 2.2, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 255, 159, ${0.15 + this.currentAudioLevel * 0.25})`;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(pCore.x, pCore.y, arcRadius, 0, Math.PI * 2);
        ctx.fillStyle = '#00ff9f';
        ctx.shadowBlur = Math.round(20 + this.currentAudioLevel * 25);
        ctx.shadowColor = '#00ff9f';
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.beginPath();
        ctx.arc(pCore.x, pCore.y, arcRadius * 0.45, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.shadowBlur = 16;
        ctx.shadowColor = '#ffffff';
        ctx.fill();
        ctx.shadowBlur = 0;
      } else if (isThk) {
        const thinkPulse = Math.sin(this.time * 12.0) * 0.3;
        const rad = (5.5 + thinkPulse) * pCore.scale;

        ctx.beginPath();
        ctx.arc(pCore.x, pCore.y, rad, 0, Math.PI * 2);
        ctx.fillStyle = '#00f0ff';
        ctx.shadowBlur = 18;
        ctx.shadowColor = '#00f0ff';
        ctx.fill();
        ctx.shadowBlur = 0;
      } else {
        const breath = Math.sin(this.time * 1.0) * 0.12;
        const rad = (4.5 + breath) * pCore.scale;

        ctx.beginPath();
        ctx.arc(pCore.x, pCore.y, rad, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(0, 255, 159, 0.42)';
        ctx.shadowBlur = 6;
        ctx.shadowColor = '#00ff9f';
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }

    // 5. Draw Cortex Spherical Nodes (Illuminated in Category Color)
    this.zoneNodes.forEach(node => {
      const proj = this.project3D(node.x, node.y, node.z);
      node.screenX = proj.x;
      node.screenY = proj.y;
      node.depth = proj.depth;

      if (proj.depth > 0) {
        const isHov = this.hoveredNode === node;
        const isToolActive = this.activeTools.has(node.zoneId);

        let rad, fillStyle, glowBlur;

        if (isToolActive) {
          const strobe = (Math.floor(this.time * 16 + node.pulseOffset) % 2 === 0);
          rad = (node.baseSize * 1.35 + (strobe ? 0.4 : 0)) * proj.scale;
          fillStyle = strobe ? '#ffffff' : node.color;
          glowBlur = 18;
        } else if (isHov) {
          rad = (node.baseSize * 1.4) * proj.scale;
          fillStyle = '#ffffff';
          glowBlur = 14;
        } else {
          const pulse = Math.sin(this.time * 1.8 + node.pulseOffset) * 0.15;
          rad = Math.max(0.8, (node.baseSize + pulse) * proj.scale);
          fillStyle = node.color + (node.zoneId === 'memory' ? 'aa' : '45');
          glowBlur = (node.zoneId === 'memory' || node.color === '#ffffff') ? 6 : 2;
        }

        ctx.beginPath();
        ctx.arc(proj.x, proj.y, rad, 0, Math.PI * 2);
        ctx.fillStyle = fillStyle;
        ctx.shadowBlur = glowBlur;
        ctx.shadowColor = node.color;
        ctx.fill();
        ctx.shadowBlur = 0;

        if (isToolActive && node.isToolMasterNode) {
          const toolInfo = this.activeTools.get(node.zoneId);
          ctx.font = 'bold 7.5px "Orbitron", sans-serif';
          ctx.fillStyle = '#ffffff';
          ctx.shadowBlur = 8;
          ctx.shadowColor = node.color;
          ctx.fillText(`⚡ RUNNING: ${toolInfo.name}`, proj.x, proj.y - rad - 6);
          ctx.shadowBlur = 0;
        }
      }
    });

    // 6. Draw Color Legend at top-left
    ctx.font = '7px "Share Tech Mono", monospace';
    ctx.textAlign = 'left';
    const legendItems = [
      { col: '#ffb703', txt: 'MEM' },
      { col: '#00f0ff', txt: 'COG' },
      { col: '#00ff9f', txt: 'API' },
      { col: '#38bdf8', txt: 'VOX' },
      { col: '#fb5607', txt: 'RUST' },
      { col: '#818cf8', txt: 'UE5' }
    ];
    let lx = 10;
    legendItems.forEach(item => {
      ctx.fillStyle = item.col;
      ctx.fillRect(lx, 10, 5, 5);
      ctx.fillStyle = '#94a3b8';
      ctx.fillText(item.txt, lx + 7, 15);
      lx += 38;
    });

    // 7. Draw Tooltip on Hover
    if (this.hoveredNode && this.hoveredNode.depth > 0) {
      const n = this.hoveredNode;
      const boxW = 135, boxH = 42;
      const bx = Math.min(Math.max(n.screenX - boxW/2, 10), w - boxW - 10);
      const by = Math.max(n.screenY - boxH - 12, 10);

      ctx.fillStyle = 'rgba(2, 12, 22, 0.95)';
      ctx.strokeStyle = n.color;
      ctx.lineWidth = 1.0;
      ctx.beginPath();
      ctx.roundRect(bx, by, boxW, boxH, 5);
      ctx.fill();
      ctx.stroke();

      ctx.textAlign = 'left';
      ctx.font = 'bold 8px "Orbitron", sans-serif';
      ctx.fillStyle = n.color;
      ctx.fillText(n.zoneName, bx + 7, by + 11);

      ctx.font = '7px "Share Tech Mono", monospace';
      ctx.fillStyle = '#94a3b8';
      ctx.fillText(n.desc, bx + 7, by + 22);
      ctx.fillStyle = '#00ff9f';
      ctx.fillText('● CLICCA PER TEST ATTIVITÀ', bx + 7, by + 33);
    }

    requestAnimationFrame(() => this.animate());
  }
}

/* ─────────────────────────────────────────────────────────────────────────────
   BOOT & INTEGRATION
───────────────────────────────────────────────────────────────────────────── */
window.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('ambient-synapse-bg')) {
    window.ambientPlexus = new HollywoodNeuralPlexus('ambient-synapse-bg');
  }
  if (document.getElementById('synapseCanvas')) {
    window.connectomeEngine = new BorderlessHologramConnectome('synapseCanvas');
  }
});
