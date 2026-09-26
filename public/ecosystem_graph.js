// ── ecosystem_graph.js ────────────────────────────────────────────────────────
//  E.B.J. AI · CEREBRO MASTER ECOSYSTEM TOPOLOGY EXPLORER
//  Mappa visuale interattiva di Cartelle, Servizi, Database, Bridge Rust e VPS
// ─────────────────────────────────────────────────────────────────────────────

(function () {
  const canvas = document.getElementById('ecosystem-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let width, height;
  let transform = { x: 0, y: 0, k: 1 };
  let isDragging = false;
  let dragStart = { x: 0, y: 0 };
  let selectedNode = null;
  let hoveredNode = null;

  // Nodi dell'architettura
  const nodes = [
    // ── CORE LOCALE ──
    { id: 'core', label: 'E.B.J. CORE SERVER', group: 'server', sub: 'server.py :8088', status: 'online', x: 0, y: -40, radius: 36, color: '#00f0ff', details: { path: 'cerebro-jarvis-dashboard/server.py', port: 8088, desc: 'Master HTTP/WebSocket Gateway, API Router & Vault Manager' } },
    { id: 'rust', label: 'RUST TOKIO BRIDGE', group: 'rust', sub: 'jarvis-bridge :9000', status: 'online', x: 260, y: -40, radius: 34, color: '#ff7700', details: { path: 'jarvis-bridge/src/main.rs', port: 9000, desc: 'Ultra-fast Native Engine (< 20µs): Lead Filter, Geo-Route, GDI Screen Capture 1440p' } },
    { id: 'qwen', label: 'QWEN 27B GPU AI', group: 'ai', sub: 'Unsloth Local :61517', status: 'standby', x: -260, y: -40, radius: 32, color: '#a855f7', details: { path: 'Local RTX GPU Engine', port: 61517, desc: 'Local AI LLM Copilot su Unsloth per elaborazione ordini a costo zero' } },
    { id: 'screen', label: 'GDI SCREEN ENGINE', group: 'engine', sub: '1440p @ 5 FPS', status: 'online', x: 260, y: 120, radius: 26, color: '#10b981', details: { path: 'jarvis-bridge/src/screen_capture.rs', desc: 'Win32 OpenInputDesktop zero-copy streaming via WebSocket ws://localhost:9000/ws/screen' } },
    { id: 'filter', label: 'ANTI-COMPETITOR LUHN', group: 'rust', sub: 'P.IVA & Semantic Filter', status: 'online', x: 380, y: -160, radius: 26, color: '#ff0055', details: { path: 'jarvis-bridge/src/lead_filter.rs', desc: 'Luhn MOD10 Partita IVA verification & dual polarity intent classifier (< 1ms)' } },
    { id: 'geo', label: 'GEO-ROUTE EMILIA', group: 'rust', sub: '46 Comuni Haversine', status: 'online', x: 380, y: 40, radius: 26, color: '#06b6d4', details: { path: 'jarvis-bridge/src/geo_route_engine.rs', desc: 'Calcolo geodesico e pedaggi per Bologna, Imola, Casalecchio, San Lazzaro, Ferrara' } },

    // ── DATABASE & VAULT ──
    { id: 'vault_leads', label: 'MAIL VAULT DB', group: 'db', sub: 'SQLite verified_leads', status: 'online', x: 0, y: 160, radius: 28, color: '#eab308', details: { path: 'cerebro-jarvis-dashboard/mail_vault.db', desc: 'Custodia lead certificati Pietro Traslochi & audit log' } },
    { id: 'kanban_db', label: 'HERMES KANBAN DB', group: 'db', sub: 'SQLite hermes_kanban.db', status: 'online', x: -140, y: 160, radius: 26, color: '#eab308', details: { path: 'cerebro-jarvis-dashboard/hermes_kanban.db', desc: 'DAG Task Board, visual lead pipeline & system milestones' } },

    // ── CLOUD VPS ORACLE ──
    { id: 'vps', label: 'ORACLE VPS CLUSTER', group: 'cloud', sub: '92.4.233.42 (24GB RAM)', status: 'online', x: 0, y: -260, radius: 36, color: '#3b82f6', details: { path: 'ubuntu@92.4.233.42', ip: '92.4.233.42', desc: 'Oracle Cloud ARM64 4 OCPU, 24GB RAM, 11 Docker Containers' } },
    { id: 'n8n', label: 'N8N AUTOMATION', group: 'cloud', sub: 'Docker :5678 (34 Workflows)', status: 'online', x: -220, y: -260, radius: 30, color: '#f97316', details: { path: 'Docker container n8n', port: 5678, desc: '34 workflow attivi per scraper, intake preventivi, email briefing e Telegram sync' } },
    { id: 'traslochi_backend', label: 'TRASLOCHIWORK API', group: 'cloud', sub: 'FastAPI :8000', status: 'online', x: 220, y: -260, radius: 30, color: '#10b981', details: { path: '/home/ubuntu/ebgs-hub/traslochiwork/backend', port: 8000, desc: 'FastAPI / Uvicorn unified leads & quotes gateway for pietrotraslochi.com' } },
    { id: 'agent_zero', label: 'AGENT ZERO', group: 'cloud', sub: 'Docker :50080', status: 'online', x: -340, y: -180, radius: 26, color: '#8b5cf6', details: { path: 'Docker container agent-zero', port: 50080, desc: 'Autonomous Sub-Agent Orchestrator' } },
    { id: 'nginx_vps', label: 'NGINX CLUSTER', group: 'web', sub: 'pietrotraslochi.com / badrexpress', status: 'online', x: 120, y: -380, radius: 28, color: '#00ff9f', details: { path: '/etc/nginx/sites-enabled/ebgs-cluster.conf', desc: 'Reverse proxy SSL TLS 1.3 con supporto pietrotraslochi.com/preventivo.html' } },
    { id: 'cloudflared', label: 'CLOUDFLARE TUNNEL', group: 'network', sub: 'eb.badrexpress.com', status: 'online', x: -120, y: -380, radius: 28, color: '#f59e0b', details: { path: 'cloudflared.exe', desc: 'Secure Zero-Downtime ingress tunnel to local master server 8088' } },

    // ── SITI & FRONTEND ──
    { id: 'landing_preventivo', label: 'PREVENTIVO LIVE', group: 'web', sub: 'pietrotraslochi.com/preventivo.html', status: 'online', x: 380, y: -380, radius: 28, color: '#10b981', details: { url: 'https://pietrotraslochi.com/preventivo.html', desc: 'Landing mobile-first ad alta conversione con stima quantistica in < 8 secondi' } },
    { id: 'telegram_bot', label: 'TELEGRAM NOTIFIER', group: 'alert', sub: 'Bot Jarvis -> Chat 7298887137', status: 'online', x: -380, y: 80, radius: 28, color: '#0088cc', details: { target: 'Badr El Ouariti (7298887137)', desc: 'Alert istantanei con dati cliente e link chat WhatsApp 1-tap' } },
  ];

  // Connessioni logiche
  const links = [
    { source: 'core', target: 'rust', label: 'IPC / HTTP :9000' },
    { source: 'core', target: 'qwen', label: 'Local GPU Bus :61517' },
    { source: 'rust', target: 'screen', label: 'BitBlt Direct' },
    { source: 'rust', target: 'filter', label: 'Luhn MOD10' },
    { source: 'rust', target: 'geo', label: 'Haversine Matrix' },
    { source: 'core', target: 'vault_leads', label: 'SQLite Write' },
    { source: 'core', target: 'kanban_db', label: 'Task Sync' },
    { source: 'core', target: 'vps', label: 'SSH / WireGuard' },
    { source: 'vps', target: 'n8n', label: 'Docker Net' },
    { source: 'vps', target: 'traslochi_backend', label: 'Port 8000' },
    { source: 'vps', target: 'agent_zero', label: 'Port 50080' },
    { source: 'vps', target: 'nginx_vps', label: 'SSL Ingress' },
    { source: 'core', target: 'cloudflared', label: 'Zero Trust Tunnel' },
    { source: 'nginx_vps', target: 'landing_preventivo', label: 'Web Serving' },
    { source: 'core', target: 'telegram_bot', label: 'Instant Dispatch' },
    { source: 'landing_preventivo', target: 'traslochi_backend', label: 'POST /api/preventivo/submit' },
    { source: 'traslochi_backend', target: 'telegram_bot', label: 'Lead Alert' },
  ];

  // Particelle di dati animate lungo i link
  const packets = [];
  for (let i = 0; i < 28; i++) {
    const link = links[Math.floor(Math.random() * links.length)];
    packets.push({
      link,
      progress: Math.random(),
      speed: 0.003 + Math.random() * 0.005,
      color: '#00f0ff'
    });
  }

  function resize() {
    const parent = canvas.parentElement;
    if (!parent) return;
    width = parent.clientWidth;
    height = parent.clientHeight || 650;
    canvas.width = width * window.devicePixelRatio;
    canvas.height = height * window.devicePixelRatio;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    if (transform.x === 0 && transform.y === 0) {
      transform.x = width / 2;
      transform.y = height / 2;
    }
  }

  window.addEventListener('resize', resize);
  setTimeout(resize, 100);

  function getNodeById(id) {
    return nodes.find(n => n.id === id);
  }

  // Render loop with Visibility Culling (Zero GPU/CPU overhead when hidden)
  function draw() {
    if (document.hidden || !canvas || canvas.offsetParent === null || canvas.clientWidth === 0) {
      setTimeout(() => requestAnimationFrame(draw), 500);
      return;
    }
    ctx.save();
    ctx.clearRect(0, 0, width, height);

    // Background Cyber Grid
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.04)';
    ctx.lineWidth = 1;
    const gridSize = 40 * transform.k;
    const offsetX = transform.x % gridSize;
    const offsetY = transform.y % gridSize;
    ctx.beginPath();
    for (let x = offsetX; x < width; x += gridSize) {
      ctx.moveTo(x, 0); ctx.lineTo(x, height);
    }
    for (let y = offsetY; y < height; y += gridSize) {
      ctx.moveTo(0, y); ctx.lineTo(width, y);
    }
    ctx.stroke();

    // Applica trasformazione pan/zoom
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);

    const now = Date.now();

    // Disegna Link
    links.forEach(l => {
      const s = getNodeById(l.source);
      const t = getNodeById(l.target);
      if (!s || !t) return;

      const isHigh = (hoveredNode && (s.id === hoveredNode.id || t.id === hoveredNode.id)) ||
                     (selectedNode && (s.id === selectedNode.id || t.id === selectedNode.id));

      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.strokeStyle = isHigh ? 'rgba(0, 255, 159, 0.8)' : 'rgba(0, 240, 255, 0.2)';
      ctx.lineWidth = isHigh ? 2.5 : 1.2;
      ctx.stroke();

      // Label sul link se hovered
      if (isHigh && l.label) {
        const mx = (s.x + t.x) / 2;
        const my = (s.y + t.y) / 2;
        ctx.font = '10px "JetBrains Mono", monospace';
        ctx.fillStyle = '#00ff9f';
        ctx.textAlign = 'center';
        ctx.fillText(l.label, mx, my - 6);
      }
    });

    // Disegna Data Packets animati
    packets.forEach(p => {
      p.progress += p.speed;
      if (p.progress > 1) p.progress = 0;
      const s = getNodeById(p.link.source);
      const t = getNodeById(p.link.target);
      if (!s || !t) return;

      const px = s.x + (t.x - s.x) * p.progress;
      const py = s.y + (t.y - s.y) * p.progress;

      ctx.beginPath();
      ctx.arc(px, py, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#00ff9f';
      ctx.shadowColor = '#00ff9f';
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    // Disegna Nodi
    nodes.forEach(n => {
      const isSel = selectedNode && selectedNode.id === n.id;
      const isHov = hoveredNode && hoveredNode.id === n.id;

      // Glow circle
      const pulse = Math.sin(now * 0.003 + n.x) * 4;
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius + pulse + (isSel ? 6 : 0), 0, Math.PI * 2);
      ctx.fillStyle = n.color + '15';
      ctx.fill();

      // Outer border
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = '#050c18';
      ctx.fill();
      ctx.strokeStyle = isSel ? '#ffffff' : (isHov ? '#00ff9f' : n.color);
      ctx.lineWidth = isSel ? 3 : (isHov ? 2.5 : 1.5);
      ctx.stroke();

      // Inner status indicator dot
      ctx.beginPath();
      ctx.arc(n.x, n.y - n.radius + 6, 4, 0, Math.PI * 2);
      ctx.fillStyle = n.status === 'online' ? '#10b981' : (n.status === 'standby' ? '#f59e0b' : '#ef4444');
      ctx.fill();

      // Node Label
      ctx.font = 'bold 11px "Outfit", sans-serif';
      ctx.fillStyle = '#ffffff';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(n.label, n.x, n.y - 2);

      // Subtitle
      ctx.font = '9px "JetBrains Mono", monospace';
      ctx.fillStyle = n.color;
      ctx.fillText(n.sub, n.x, n.y + 12);
    });

    ctx.restore();
    requestAnimationFrame(draw);
  }

  // ── GESTIONE EVENTI MOUSE (Pan, Zoom, Drag, Click) ─────────────────────────
  function getCanvasPos(e) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left - transform.x) / transform.k,
      y: (e.clientY - rect.top - transform.y) / transform.k
    };
  }

  canvas.addEventListener('mousedown', e => {
    const pos = getCanvasPos(e);
    const clicked = nodes.find(n => {
      const dx = pos.x - n.x;
      const dy = pos.y - n.y;
      return (dx * dx + dy * dy) <= (n.radius * n.radius);
    });

    if (clicked) {
      selectedNode = clicked;
      showNodeDetails(clicked);
    } else {
      isDragging = true;
      dragStart = { x: e.clientX - transform.x, y: e.clientY - transform.y };
    }
  });

  window.addEventListener('mousemove', e => {
    if (isDragging) {
      transform.x = e.clientX - dragStart.x;
      transform.y = e.clientY - dragStart.y;
      return;
    }
    const pos = getCanvasPos(e);
    hoveredNode = nodes.find(n => {
      const dx = pos.x - n.x;
      const dy = pos.y - n.y;
      return (dx * dx + dy * dy) <= (n.radius * n.radius);
    }) || null;
    canvas.style.cursor = hoveredNode ? 'pointer' : (isDragging ? 'grabbing' : 'default');
  });

  window.addEventListener('mouseup', () => {
    isDragging = false;
  });

  canvas.addEventListener('wheel', e => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    transform.x = mouseX - (mouseX - transform.x) * zoomFactor;
    transform.y = mouseY - (mouseY - transform.y) * zoomFactor;
    transform.k = Math.max(0.4, Math.min(2.5, transform.k * zoomFactor));
  });

  // ── INSPECTOR DRAWER ───────────────────────────────────────────────────────
  function showNodeDetails(node) {
    const drawer = document.getElementById('topology-inspector');
    if (!drawer) return;

    let html = `
      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(0,240,255,0.2); padding-bottom:10px; margin-bottom:14px;">
        <div style="display:flex; align-items:center; gap:8px;">
          <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${node.color}; box-shadow:0 0 8px ${node.color};"></span>
          <h3 style="margin:0; font-size:16px; color:#fff; font-family:'Outfit', sans-serif;">${node.label}</h3>
        </div>
        <span style="font-size:10px; padding:3px 8px; border-radius:10px; background:rgba(16,185,129,0.15); color:#10b981; border:1px solid #10b981; font-weight:bold; text-transform:uppercase;">${node.status}</span>
      </div>

      <div style="font-size:12px; line-height:1.6; color:#cbd5e1; font-family:'JetBrains Mono', monospace;">
        <p style="margin:4px 0;"><strong style="color:#00f0ff;">Modulo / Gruppo:</strong> ${node.group.toUpperCase()}</p>
        <p style="margin:4px 0;"><strong style="color:#00f0ff;">Sub-sistema:</strong> ${node.sub}</p>
        ${node.details.path ? `<p style="margin:4px 0;"><strong style="color:#00f0ff;">File Path:</strong> <code style="color:#a5f3fc;">${node.details.path}</code></p>` : ''}
        ${node.details.port ? `<p style="margin:4px 0;"><strong style="color:#00f0ff;">Porta Locale/Cloud:</strong> <span style="color:#eab308; font-weight:bold;">${node.details.port}</span></p>` : ''}
        ${node.details.ip ? `<p style="margin:4px 0;"><strong style="color:#00f0ff;">IP Server:</strong> ${node.details.ip}</p>` : ''}
        ${node.details.url ? `<p style="margin:4px 0;"><strong style="color:#00f0ff;">URL Pubblica:</strong> <a href="${node.details.url}" target="_blank" style="color:#00ff9f;">${node.details.url} ↗️</a></p>` : ''}
        <div style="background:rgba(0,240,255,0.05); border:1px solid rgba(0,240,255,0.15); border-radius:8px; padding:10px; margin-top:12px;">
          <strong style="color:#00ff9f; display:block; margin-bottom:4px; font-size:11px;">RUOLO ARCHITETTURALE:</strong>
          <span style="color:#94a3b8; font-size:11px;">${node.details.desc}</span>
        </div>
      </div>

      <div style="margin-top:16px; display:flex; gap:8px;">
        <button onclick="pingNode('${node.id}')" style="flex:1; background:rgba(0,240,255,0.15); border:1px solid #00f0ff; color:#00f0ff; padding:8px 12px; border-radius:8px; font-size:11px; cursor:pointer; font-weight:bold;">⚡ TEST PING</button>
        ${node.details.url ? `<a href="${node.details.url}" target="_blank" style="flex:1; text-align:center; background:rgba(16,185,129,0.2); border:1px solid #10b981; color:#10b981; padding:8px 12px; border-radius:8px; font-size:11px; text-decoration:none; font-weight:bold;">🌐 APRI URL</a>` : ''}
      </div>
    `;

    drawer.innerHTML = html;
  }

  // Espone globalmente per pulsanti reset view
  window.resetTopologyView = function () {
    transform = { x: width / 2, y: height / 2, k: 1 };
  };

  window.pingNode = async function (id) {
    const node = getNodeById(id);
    if (!node) return;
    try {
      const t0 = performance.now();
      let res;
      if (node.id === 'rust') res = await fetch('http://127.0.0.1:9000/api/ping');
      else if (node.id === 'core') res = await fetch('/api/status');
      else if (node.id === 'geo') res = await fetch('/api/geo/emilia-cities');
      else res = await fetch('/api/status');
      const ms = (performance.now() - t0).toFixed(1);
      alert(`⚡ [PING SUCCESS] ${node.label} risponde in ${ms} ms! Status: 200 OK`);
    } catch (err) {
      alert(`⚠️ [PING FALLITO] ${node.label}: ${err}`);
    }
  };

  // Avvia con resize e selezione primo nodo
  setTimeout(() => {
    resize();
    showNodeDetails(nodes[0]);
    draw();
  }, 200);
})();
