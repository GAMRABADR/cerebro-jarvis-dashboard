// ═══════════════════════════════════════════════════════════════════════════════
//  CEREBRO JARVIS · INTERACTIVE FORCE-DIRECTED NEURAL SYNAPSE GRAPH v12.0
//  Features: Click-to-Focus Subgraph, Physics Drag-and-Drop, Electric Pulse Waves,
//            Holographic Memory Inspector Popup, Real-Time Task Neural Lightning
// ═══════════════════════════════════════════════════════════════════════════════

class InteractiveNeuralGraph {
  constructor(canvasId, containerId) {
    this.canvas = document.getElementById(canvasId);
    this.container = document.getElementById(containerId) || this.canvas?.parentElement;
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.nodes = [];
    this.edges = [];
    this.selectedNode = null;
    this.hoveredNode = null;
    this.draggedNode = null;
    this.particles = [];
    this.time = 0;

    this.initGraph();
    this.resize();
    this.bindEvents();
    this.animate();
  }

  resize() {
    if (!this.canvas || !this.container) return;
    this.width = this.canvas.width = this.container.clientWidth || 340;
    this.height = this.canvas.height = this.container.clientHeight || 220;
  }

  initGraph() {
    const rawNodes = [
      { id: 'badr', label: '👑 BADR (DIRETTORE)', color: '#00ff88', radius: 9, role: 'Comandante Supremo & Fondatore', memory: 'Decisioni strategiche, approvazione preventivi, rilascio release' },
      { id: 'ebgs', label: '🎮 EBGS MMO', color: '#00d4ff', radius: 8, role: 'Unreal Engine 5.8 Survival Game', memory: 'MMO multiplayer dedicato, Lumen lighting, shader GPU' },
      { id: 'steam', label: '📦 STEAM 2886940', color: '#38bdf8', radius: 7, role: 'Steamworks Partner & CI/CD', memory: 'AppID 2886940, VDF scripts, depot builds, patch notes' },
      { id: 'sgomberi', label: '🚛 SGOMBERI & TRASLOCHI', color: '#eab308', radius: 8, role: 'Preventivatore & Logistica', memory: 'Stima volumetrica m³, coefficienti piano/ascensore, preventivi WhatsApp' },
      { id: 'mkt', label: '🏷️ MARKETPLACE SELLER', color: '#f59e0b', radius: 7, role: 'Copywriting & Stima Prezzi', memory: 'Subito.it, Facebook Marketplace, annunci persuasivi CTR' },
      { id: 'hermes', label: '📋 HERMES KANBAN L5', color: '#a855f7', radius: 8, role: 'Autonomous DAG Task Engine', memory: 'Catene di dipendenza T1+T2 -> T3 -> T4, Angle Gap analysis' },
      { id: 'agente0', label: '🤖 AGENTE ZERO', color: '#ec4899', radius: 8, role: 'Python Code & Web Agent', memory: 'Interprete codice locale, scraping web, sandbox esecutiva' },
      { id: 'n8n', label: '⚙️ N8N AUTOMATION', color: '#10b981', radius: 8, role: 'Workflow Hub 24/7 (Port 5678)', memory: 'Webhooks, auto-editor video silence cutter, cron mail scanner' },
      { id: 'vault', label: '📁 SQLITE VAULT', color: '#6366f1', radius: 7, role: 'Archivio Crittografato', memory: 'Cedolini, bustepaghe Glastebo, licenze software, atti legali' },
      { id: 'gemma', label: '💎 GEMMA 12B HERETIC', color: '#c084fc', radius: 7, role: 'Modello Locale VPS (Ollama)', memory: '65k token di contesto, reasoning denso, unfilter neural' }
    ];

    const rawEdges = [
      ['badr', 'ebgs'], ['badr', 'sgomberi'], ['badr', 'hermes'], ['badr', 'vault'],
      ['ebgs', 'steam'], ['ebgs', 'hermes'], ['ebgs', 'gemma'],
      ['sgomberi', 'n8n'], ['sgomberi', 'mkt'], ['sgomberi', 'vault'],
      ['mkt', 'agente0'], ['mkt', 'n8n'],
      ['hermes', 'agente0'], ['hermes', 'n8n'], ['hermes', 'gemma'],
      ['agente0', 'n8n'], ['agente0', 'vault'], ['n8n', 'vault']
    ];

    const centerX = 170;
    const centerY = 110;
    const radius = 75;

    this.nodes = rawNodes.map((n, i) => {
      const angle = (i / rawNodes.length) * Math.PI * 2;
      return {
        ...n,
        x: i === 0 ? centerX : centerX + Math.cos(angle) * radius + (Math.random() - 0.5) * 20,
        y: i === 0 ? centerY : centerY + Math.sin(angle) * radius + (Math.random() - 0.5) * 20,
        vx: 0,
        vy: 0,
        activityPulse: 0
      };
    });

    this.edges = rawEdges.map(([fromId, toId]) => ({
      from: this.nodes.find(n => n.id === fromId),
      to: this.nodes.find(n => n.id === toId),
      pulseProgress: Math.random(),
      speed: 0.008 + Math.random() * 0.012
    })).filter(e => e.from && e.to);
  }

  bindEvents() {
    window.addEventListener('resize', () => this.resize());

    const getPos = (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      return {
        x: (clientX - rect.left) * (this.canvas.width / rect.width),
        y: (clientY - rect.top) * (this.canvas.height / rect.height)
      };
    };

    const findNodeAt = (pos) => {
      for (let i = this.nodes.length - 1; i >= 0; i--) {
        const n = this.nodes[i];
        const dx = pos.x - n.x;
        const dy = pos.y - n.y;
        if (Math.sqrt(dx * dx + dy * dy) <= n.radius + 10) return n;
      }
      return null;
    };

    this.canvas.addEventListener('mousemove', (e) => {
      const pos = getPos(e);
      if (this.draggedNode) {
        this.draggedNode.x = pos.x;
        this.draggedNode.y = pos.y;
        this.draggedNode.vx = 0;
        this.draggedNode.vy = 0;
      } else {
        const found = findNodeAt(pos);
        this.hoveredNode = found;
        this.canvas.style.cursor = found ? 'pointer' : 'default';
      }
    });

    this.canvas.addEventListener('mousedown', (e) => {
      const pos = getPos(e);
      const clicked = findNodeAt(pos);
      if (clicked) {
        this.draggedNode = clicked;
        this.selectNode(clicked);
        this.pulseNeuron(clicked.id);
      } else {
        this.selectedNode = null;
        this.hideInspector();
      }
    });

    window.addEventListener('mouseup', () => {
      this.draggedNode = null;
    });

    // Touch events
    this.canvas.addEventListener('touchstart', (e) => {
      const pos = getPos(e);
      const clicked = findNodeAt(pos);
      if (clicked) {
        this.draggedNode = clicked;
        this.selectNode(clicked);
        this.pulseNeuron(clicked.id);
      }
    }, { passive: true });

    this.canvas.addEventListener('touchmove', (e) => {
      if (!this.draggedNode) return;
      const pos = getPos(e);
      this.draggedNode.x = pos.x;
      this.draggedNode.y = pos.y;
    }, { passive: true });

    this.canvas.addEventListener('touchend', () => {
      this.draggedNode = null;
    });
  }

  selectNode(node) {
    this.selectedNode = node;
    this.showInspector(node);
  }

  showInspector(node) {
    let inspector = document.getElementById('synapse-inspector');
    if (!inspector) {
      inspector = document.createElement('div');
      inspector.id = 'synapse-inspector';
      inspector.className = 'synapse-inspector-card';
      this.container.appendChild(inspector);
    }

    const connectedNodes = this.edges
      .filter(e => e.from.id === node.id || e.to.id === node.id)
      .map(e => (e.from.id === node.id ? e.to : e.from));

    inspector.innerHTML = `
      <div class="si-header" style="border-color:${node.color}">
        <span class="si-title" style="color:${node.color}">${node.label}</span>
        <button class="si-close" onclick="document.getElementById('synapse-inspector').classList.remove('active')">✕</button>
      </div>
      <div class="si-role">${node.role}</div>
      <div class="si-memory"><b>🧠 Memoria:</b> ${node.memory}</div>
      <div class="si-connections">
        <b>🔗 Sinapsi Collegate (${connectedNodes.length}):</b>
        <div class="si-tags">
          ${connectedNodes.map(cn => `<span class="si-tag" style="border-color:${cn.color}44; color:${cn.color}">${cn.label}</span>`).join('')}
        </div>
      </div>
      <div class="si-actions">
        <button class="si-btn" onclick="sendQuick('JARVIS, esegui diagnosi e interroga la memoria di ${node.label}')">⚡ Interroga</button>
        <button class="si-btn primary" style="background:${node.color}33; border-color:${node.color}; color:${node.color}" onclick="triggerNeuronAction('${node.id}')">🚀 Esegui</button>
      </div>
    `;
    inspector.classList.add('active');
  }

  hideInspector() {
    const inspector = document.getElementById('synapse-inspector');
    if (inspector) inspector.classList.remove('active');
  }

  pulseNeuron(id) {
    const node = this.nodes.find(n => n.id === id);
    if (!node) return;
    node.activityPulse = 1.0;

    // Spawn burst particles
    for (let i = 0; i < 16; i++) {
      const angle = (i / 16) * Math.PI * 2;
      const speed = 1.5 + Math.random() * 2;
      this.particles.push({
        x: node.x,
        y: node.y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        color: node.color,
        life: 1.0,
        decay: 0.03 + Math.random() * 0.02
      });
    }
  }

  addSynapseNode(label, color = '#00d4ff', role = 'Nuovo Nodo Appreso', memory = 'Informazione memorizzata da JARVIS') {
    const id = 'n_' + Date.now();
    const newNode = {
      id,
      label: label.toUpperCase(),
      color,
      radius: 6,
      role,
      memory,
      x: this.width * 0.5 + (Math.random() - 0.5) * 60,
      y: this.height * 0.5 + (Math.random() - 0.5) * 60,
      vx: (Math.random() - 0.5) * 1,
      vy: (Math.random() - 0.5) * 1,
      activityPulse: 1.0
    };

    this.nodes.push(newNode);

    // Connect to 2 nearest nodes
    const sorted = [...this.nodes].filter(n => n.id !== id).sort((a, b) => {
      const d1 = Math.hypot(a.x - newNode.x, a.y - newNode.y);
      const d2 = Math.hypot(b.x - newNode.x, b.y - newNode.y);
      return d1 - d2;
    });

    if (sorted[0]) this.edges.push({ from: newNode, to: sorted[0], pulseProgress: 0, speed: 0.01 });
    if (sorted[1]) this.edges.push({ from: newNode, to: sorted[1], pulseProgress: 0.5, speed: 0.012 });

    this.pulseNeuron(id);
  }

  updatePhysics() {
    const kRepulsion = 1200;
    const kSpring = 0.003;
    const restLength = 65;
    const damping = 0.88;

    // Repulsion between nodes
    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const n1 = this.nodes[i];
        const n2 = this.nodes[j];
        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist < 180) {
          const force = kRepulsion / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          n1.vx -= fx;
          n1.vy -= fy;
          n2.vx += fx;
          n2.vy += fy;
        }
      }
    }

    // Spring attraction along edges
    for (const edge of this.edges) {
      const dx = edge.to.x - edge.from.x;
      const dy = edge.to.y - edge.from.y;
      const dist = Math.hypot(dx, dy) || 1;
      const delta = dist - restLength;
      const force = delta * kSpring;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      edge.from.vx += fx;
      edge.from.vy += fy;
      edge.to.vx -= fx;
      edge.to.vy -= fy;
    }

    // Apply velocity & bounds
    for (const n of this.nodes) {
      if (n === this.draggedNode) continue;
      n.vx *= damping;
      n.vy *= damping;
      n.x += n.vx;
      n.y += n.vy;

      // Keep within bounds
      const pad = 24;
      if (n.x < pad) { n.x = pad; n.vx *= -0.5; }
      if (n.x > this.width - pad) { n.x = this.width - pad; n.vx *= -0.5; }
      if (n.y < pad) { n.y = pad; n.vy *= -0.5; }
      if (n.y > this.height - pad) { n.y = this.height - pad; n.vy *= -0.5; }

      // Decay activity pulse
      if (n.activityPulse > 0) n.activityPulse = Math.max(0, n.activityPulse - 0.02);
    }

    // Update Particles
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.life -= p.decay;
      if (p.life <= 0) this.particles.splice(i, 1);
    }
  }

  animate() {
    this.time += 0.03;
    this.updatePhysics();
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;

    ctx.clearRect(0, 0, w, h);

    const isConnectedToSelected = (node) => {
      if (!this.selectedNode) return true;
      if (node.id === this.selectedNode.id) return true;
      return this.edges.some(e => 
        (e.from.id === this.selectedNode.id && e.to.id === node.id) ||
        (e.to.id === this.selectedNode.id && e.from.id === node.id)
      );
    };

    // ── DRAW EDGES ───────────────────────────────────────────────
    for (const edge of this.edges) {
      const isHighlighted = this.selectedNode && (edge.from.id === this.selectedNode.id || edge.to.id === this.selectedNode.id);
      const isHovered = this.hoveredNode && (edge.from.id === this.hoveredNode.id || edge.to.id === this.hoveredNode.id);

      ctx.beginPath();
      ctx.moveTo(edge.from.x, edge.from.y);
      ctx.lineTo(edge.to.x, edge.to.y);

      if (isHighlighted || isHovered) {
        ctx.strokeStyle = '#00ff88';
        ctx.lineWidth = 2.2;
        ctx.shadowBlur = 8;
        ctx.shadowColor = '#00ff88';
      } else if (this.selectedNode) {
        ctx.strokeStyle = 'rgba(0, 212, 255, 0.06)';
        ctx.lineWidth = 0.8;
        ctx.shadowBlur = 0;
      } else {
        ctx.strokeStyle = 'rgba(0, 212, 255, 0.22)';
        ctx.lineWidth = 1.1;
        ctx.shadowBlur = 0;
      }
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Pulse wave traveling along edge
      edge.pulseProgress += edge.speed;
      if (edge.pulseProgress > 1) edge.pulseProgress = 0;

      const px = edge.from.x + (edge.to.x - edge.from.x) * edge.pulseProgress;
      const py = edge.from.y + (edge.to.y - edge.from.y) * edge.pulseProgress;

      ctx.beginPath();
      ctx.arc(px, py, isHighlighted ? 2.5 : 1.5, 0, Math.PI * 2);
      ctx.fillStyle = isHighlighted ? '#00ff88' : '#00d4ff';
      ctx.shadowBlur = isHighlighted ? 8 : 4;
      ctx.shadowColor = isHighlighted ? '#00ff88' : '#00d4ff';
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    // ── DRAW PARTICLES ───────────────────────────────────────────
    for (const p of this.particles) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.life * 2.5, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.shadowBlur = 6;
      ctx.shadowColor = p.color;
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    // ── DRAW NODES ───────────────────────────────────────────────
    for (const n of this.nodes) {
      const isSelected = this.selectedNode && n.id === this.selectedNode.id;
      const isHovered = this.hoveredNode && n.id === this.hoveredNode.id;
      const isConnected = isConnectedToSelected(n);
      const alpha = isConnected ? 1.0 : 0.25;

      ctx.globalAlpha = alpha;

      // Electric Pulse Waves if active
      if (n.activityPulse > 0 || isSelected) {
        const ringRad = n.radius + (1 - (n.activityPulse || 0)) * 14 + Math.sin(this.time * 4) * 3;
        ctx.beginPath();
        ctx.arc(n.x, n.y, ringRad, 0, Math.PI * 2);
        ctx.strokeStyle = n.color;
        ctx.lineWidth = 1.5;
        ctx.shadowBlur = 12;
        ctx.shadowColor = n.color;
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      // Outer Glow Aura
      const auraRad = n.radius + Math.sin(this.time * 2 + n.x) * 1.5 + (isSelected ? 4 : 0);
      ctx.beginPath();
      ctx.arc(n.x, n.y, auraRad * 1.8, 0, Math.PI * 2);
      ctx.fillStyle = n.color + '22';
      ctx.fill();

      // Node Body
      ctx.beginPath();
      ctx.arc(n.x, n.y, auraRad, 0, Math.PI * 2);
      ctx.fillStyle = isSelected ? '#ffffff' : n.color;
      ctx.shadowBlur = isSelected ? 18 : (isHovered ? 12 : 6);
      ctx.shadowColor = n.color;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Label
      ctx.font = isSelected ? '700 9px Orbitron, sans-serif' : '600 7.5px Orbitron, sans-serif';
      ctx.fillStyle = isSelected ? '#00ff88' : '#e2e8f0';
      ctx.fillText(n.label, n.x + n.radius + 5, n.y + 3);

      ctx.globalAlpha = 1.0;
    }

    requestAnimationFrame(() => this.animate());
  }
}

// Global action trigger for inspector
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

window.InteractiveNeuralGraph = InteractiveNeuralGraph;
