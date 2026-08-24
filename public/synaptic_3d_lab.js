// ═══════════════════════════════════════════════════════════════════════════════
//  CEREBRO JARVIS · 1:1 REAL SKILLS & TOOLS INSPECTOR MATRIX v26.0
//  39+ Real Skills Manifest · Interactive HUD Inspector · Calm Slow Idle Orbit
// ═══════════════════════════════════════════════════════════════════════════════

class SupremeBioNeuralCortex {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    
    this.nodes = [];
    this.connections = [];
    this.pulses = [];
    this.particles = [];
    this.time = 0;
    
    // Smooth Camera & 3D Isometric Orbit
    this.zoomScale = 1.0;
    this.targetZoom = 1.0;
    this.camX = 0;
    this.camY = 0;
    this.targetCamX = 0;
    this.targetCamY = 0;
    
    // Classic 3/4 Isometric Profile Angles
    this.rotX = 0.45;
    this.rotY = 0.35;
    this.targetRotX = 0.45;
    this.targetRotY = 0.35;
    
    this.isAutoTargeting = false;
    this.activeNodeId = null;

    // Compact Organic Radius
    this.baseRadius = 170;

    // Real-Time VPS Telemetry Reactive State
    this.vpsCpu = 4.0;
    this.vpsRam = 32.0;
    this.vpsLatency = 0.05;

    this.isThinking = false;
    this.isSpeaking = false;
    this.activeCategory = null;
    this.activeSkillKeys = new Set();
    this.activeSkillLabel = '';
    this.activeSkillTimer = null;

    this.mouse = { isDown: false, lastX: 0, lastY: 0 };
    this.lastProjectedNodes = [];
    this.skillsManifest = [];

    this.resize();
    this.initQuantumPlasma();
    this.loadManifestAndBuildSphere();
    this.bindEvents();
    this.startVpsTelemetryPolling();
    this.startSynapseEventsPolling();
    this.connectRustBridge();
    this.animate();
  }

  resize() {
    const parent = this.canvas.parentElement;
    const rect = parent ? parent.getBoundingClientRect() : { width: 800, height: 460 };
    
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    const cssWidth = Math.max(340, rect.width || 800);
    const cssHeight = Math.max(360, rect.height || 460);

    this.canvas.width = cssWidth * dpr;
    this.canvas.height = cssHeight * dpr;
    this.canvas.style.width = cssWidth + 'px';
    this.canvas.style.height = cssHeight + 'px';

    this.ctx.scale(dpr, dpr);

    this.width = cssWidth;
    this.height = cssHeight;
    this.centerX = this.width / 2;
    this.centerY = this.height / 2;
    this.baseRadius = Math.min(this.width, this.height) * 0.35;
    this.repelForce = 160;
    this.linkLength = 90;
  }

  setPhysics(repel, linkLen) {
    this.repelForce = repel;
    this.linkLength = linkLen;
    this.baseRadius = Math.max(100, Math.min(320, repel * 1.15));
    if (this.nodes && this.nodes.length > 0) {
      // Re-scale orbital radii of clusters
      for (let n of this.nodes) {
        if (!n.isHub && n.id !== 'CORE') {
          const factor = (this.linkLength / 90);
          n.x *= (1 + (factor - 1) * 0.05);
          n.y *= (1 + (factor - 1) * 0.05);
          n.z *= (1 + (factor - 1) * 0.05);
        }
      }
    }
  }

  initQuantumPlasma() {
    this.particles = [];
    for (let i = 0; i < 50; i++) {
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = (this.baseRadius * 0.9) + (Math.random() - 0.5) * 50;

      this.particles.push({
        x: r * Math.sin(phi) * Math.cos(theta),
        y: r * Math.sin(phi) * Math.sin(theta),
        z: r * Math.cos(phi),
        baseSpeed: 0.0010 + Math.random() * 0.0012,
        theta,
        phi,
        r,
        radius: 1.0 + Math.random() * 1.4,
        color: Math.random() > 0.5 ? '#00f0ff' : '#00ff9f',
        alpha: 0.12 + Math.random() * 0.2
      });
    }
  }

  async loadManifestAndBuildSphere() {
    try {
      const res = await fetch('/skills_manifest.json?' + Date.now());
      if (res.ok) {
        this.skillsManifest = await res.json();
      }
    } catch (e) {}

    this.buildCompactDenseSkillsSphere();
  }

  // ── BUILD 1:1 RIGOROUS COMPACT SKILLS MATRIX ─────────────────────
  buildCompactDenseSkillsSphere() {
    this.nodes = [];
    this.connections = [];
    this.pulses = [];

    // Central CEREBRO Arc Reactor Core
    this.nodes.push({
      id: 'CORE',
      key: 'core',
      x: 0, y: 0, z: 0,
      radius: 18.0,
      color: '#00f0ff',
      glow: '#00ff9f',
      label: 'CEREBRO CORE',
      category: 'CORE',
      isHub: true,
      description: 'Master Core & Singularità Quantica di Regia AI (120 FPS)',
      command: 'JARVIS, stato generale del sistema'
    });

    // 8 Macro Lobi con mappatura 1:1 delle 39 skill reali
    const systemLobes = [
      {
        name: 'BUSINESS_SGOMBERI',
        label: '🚛 TRASLOCHI & BIZ',
        color: '#00ff9f',
        glow: '#05ffa1',
        skills: [
          { id: 'leads_and_quotes_tracker', label: 'Leads Tracker Live', desc: 'Monitoraggio lead in tempo reale da PietroTraslochi & BadrExpress', cmd: 'JARVIS, quanti preventivi oggi?' },
          { id: 'auto_invoice_pdf_generator', label: 'Fattura PDF Gen', desc: 'Generatore fatture elettroniche e PDF con archiviazione SQLite', cmd: 'JARVIS, genera fattura di prova' },
          { id: 'autonomous_email_triage', label: 'Email Vault Triage', desc: 'Triage FTS5 SQLite e categorizzazione automatica posta in arrivo', cmd: 'JARVIS, spulcia le email recenti' },
          { id: 'real_smtp_mailer', label: 'SMTP SSL 465 Mailer', desc: 'Motore di invio certificato SMTP SSL con allegati professionali', cmd: 'JARVIS, invia email di test' },
          { id: 'logistics_maps_route_optimizer', label: 'Route Logistics Calc', desc: 'Ottimizzatore tratte, chilometraggio e pedaggi per sgomberi', cmd: 'JARVIS, calcola percorso Imola Bologna' },
          { id: 'sgomberi_smart_classifier', label: 'Sgomberi Classifier', desc: 'Classificazione volume arredi, discarica e recupero eco', cmd: 'JARVIS, calcola preventivo per 80 mq al 3 piano' }
        ]
      },
      {
        name: 'GAME_DEV',
        label: '🎮 GAME DEV UE5',
        color: '#ff2a6d',
        glow: '#ff007f',
        skills: [
          { id: 'ue5_game_ops', label: 'UE 5.8 GameOps', desc: 'Automazione compilazione C++, cooking asset e build EBGS.uproject', cmd: 'JARVIS, stato build Unreal Engine 5.8' },
          { id: 'steamworks_sdk_pipeline', label: 'Steam AppID 2886940', desc: 'Deploy automatico su Steamworks per il gioco Survival MMO', cmd: 'JARVIS, prepara release Steamworks' },
          { id: 'gaea_blender_terrain_bridge', label: 'Gaea & Blender Forge', desc: 'Generazione mappe procedurali 8K e bridge asset 3D', cmd: 'JARVIS, bridge blender terreni' },
          { id: 'unreal_dedicated_server_ops', label: 'Dedicated Server Ops', desc: 'Gestione server dedicati autoritativi a 60 tick/s', cmd: 'JARVIS, stato server dedicato UE5' },
          { id: 'pbr_material_forge', label: 'PBR Shaders Forge', desc: 'Compilazione shader custom e ottimizzazione Nanite/Lumen', cmd: 'JARVIS, ottimizza shader Nanite' }
        ]
      },
      {
        name: 'LTM_MEMORY',
        label: '🧠 LTM VAULT',
        color: '#ffb703',
        glow: '#ffd166',
        skills: [
          { id: 'hermes_memory', label: 'Holographic Memory', desc: 'Archivio a lungo termine contestuale con iniezione dinamica nei prompt', cmd: 'JARVIS, memorie recenti nel vault' },
          { id: 'mail_vault_db', label: 'Mail Vault SQLite', desc: 'Database FTS5 con indicizzazione semantica per email e contratti', cmd: 'JARVIS, cerca email nel vault' },
          { id: 'sqlite_fts5_memory_vault', label: 'FTS5 Memory Search', desc: 'Ricerca full-text istantanea in 0.05ms su tutta la conoscenza', cmd: 'JARVIS, recall memoria' },
          { id: 'checkpoint_conversation_graph', label: 'Conversation Graph', desc: 'Mappa delle conversazioni storiche con ripristino istantaneo', cmd: 'JARVIS, snapshot conversazione' },
          { id: 'semantic_vector_cache', label: 'Semantic Vector Cache', desc: 'Cache neurale in RAM per embedding e recall ultra-rapido', cmd: 'JARVIS, cache status' }
        ]
      },
      {
        name: 'API_INFRASTRUCTURE',
        label: '⚡ CLOUD VPS & N8N',
        color: '#00d4ff',
        glow: '#00f0ff',
        skills: [
          { id: 'oracle_vps_monitor', label: 'Oracle VPS Ubuntu', desc: 'Telemetria real-time di CPU, RAM e dischi su 92.4.233.42', cmd: 'JARVIS, telemetria VPS Oracle' },
          { id: 'n8n_workflows_engine', label: 'n8n 15+ Workflows', desc: 'Orchestrazione flussi grafici, intake preventivi e trigger Telegram', cmd: 'JARVIS, stato flussi n8n' },
          { id: 'cloudflare_named_tunnels', label: 'Cloudflare ZeroTrust', desc: 'Named Tunnels SSL per eb.badrexpress.com e n8n/AgentZero', cmd: 'JARVIS, tunnel attivi' },
          { id: 'fastmcp_universal_gateway', label: 'FastMCP Gateway', desc: 'Protocollo Model Context Protocol universale per tool remoti', cmd: 'JARVIS, lista tool MCP' },
          { id: 'docker_swarm_health', label: 'Docker Swarm Health', desc: 'Monitoraggio container Open-WebUI, n8n e Agente Zero', cmd: 'JARVIS, stato container docker' }
        ]
      },
      {
        name: 'VOICE_DEVOPS',
        label: '🎙️ VOICE & IOT',
        color: '#c084fc',
        glow: '#a855f7',
        skills: [
          { id: 'phone_call_and_whatsapp_dispatcher', label: 'Phone & WhatsApp Call', desc: 'Avvio chiamate telefoniche e messaggi WhatsApp con un comando vocale', cmd: 'JARVIS, fai squillare il mio cellulare' },
          { id: 'faster_whisper_voice_engine', label: 'Groq Whisper V3 STT', desc: 'Trascrizione vocale istantanea a bassissima latenza (0.2s)', cmd: 'JARVIS, ascolto vocale' },
          { id: 'elevenlabs_neural_tts', label: 'ElevenLabs Voice', desc: 'Sintesi vocale ad alta fedeltà con timbro British elegante', cmd: 'JARVIS, parla' },
          { id: 'audio_oscilloscope_dsp', label: '24-Band Audio DSP', desc: 'Equalizzatore di frequenza e analizzatore decibel in tempo reale', cmd: 'JARVIS, audio monitor' },
          { id: 'kde_connect_bridge', label: 'KDE Connect Linux', desc: 'Integrazione bidirezionale con smartphone per SMS, clip e ringer', cmd: 'JARVIS, dov\'è il mio telefono?' }
        ]
      },
      {
        name: 'MARKETPLACE',
        label: '🏷️ FB MARKETPLACE',
        color: '#38bdf8',
        glow: '#0284c7',
        skills: [
          { id: 'marketplace_seller_and_evaluator', label: 'Price Evaluator AI', desc: 'Stima accurata prezzi di mercato e creazione schede persuasive', cmd: 'JARVIS, valuta e vendi una PS5 usata' },
          { id: 'facebook_marketplace_messenger_bot', label: 'FB Messenger Bot', desc: 'Risposte automatiche ai clienti di Facebook Marketplace', cmd: 'JARVIS, controlla messaggi marketplace' },
          { id: 'subito_crawler_price_radar', label: 'Subito.it Price Radar', desc: 'Analisi dei prezzi medi per articoli usati su Subito.it', cmd: 'JARVIS, stima prezzo' },
          { id: 'persuasive_copywriter_ai', label: 'Persuasive Copywriter', desc: 'Generatore di annunci di vendita con ganci di conversione', cmd: 'JARVIS, genera annuncio di vendita' }
        ]
      },
      {
        name: 'WEB_RESEARCH',
        label: '🌐 LIVE WEB AI',
        color: '#2dd4bf',
        glow: '#14b8a6',
        skills: [
          { id: 'autonomous_web_browser', label: 'Crawl4AI Live Scraper', desc: 'Navigazione web e scraping in tempo reale con Playwright', cmd: 'JARVIS, naviga su internet e dimmi le ultime novità tech' },
          { id: 'meteo_and_traffic_intelligence', label: 'Meteo & Traffic Radar', desc: 'Previsioni meteo in diretta e traffico satellitare tratte', cmd: 'JARVIS, che tempo fa a Imola e c\'è traffico?' },
          { id: 'duckduckgo_deep_search', label: 'DuckDuckGo Radar', desc: 'Ricerca deep-web per notizie, documentazioni e prezzi', cmd: 'JARVIS, cerca su internet notizie Unreal 5.8' },
          { id: 'docling_pdf_extractor', label: 'Docling PDF Extractor', desc: 'Estrazione strutturata di tabelle e testi da documenti e fatture', cmd: 'JARVIS, analizza pdf' }
        ]
      },
      {
        name: 'AUTONOMOUS_FLEET',
        label: '🤖 AGENTE ZERO',
        color: '#f43f5e',
        glow: '#e11d48',
        skills: [
          { id: 'agent_fleet_dispatcher', label: 'Agente Zero Core', desc: 'Console autonoma Level 5 per esecuzione task in background', cmd: 'JARVIS, stato della flotta agenti' },
          { id: 'hermes_level5_dag_kanban', label: 'Hermes Level 5 DAG', desc: 'Gestione a grafo aciclico delle task con auto-risoluzione', cmd: 'JARVIS, apri kanban' },
          { id: 'rust_tokio_bridge_120fps', label: 'Rust Tokio Bus 120fps', desc: 'Micro-bus nativo compilato in Rust con latenza inferiore a 1ms', cmd: 'JARVIS, telemetria rust bus' },
          { id: 'smart_git_multi_sync', label: 'Git Multi-Sync Repo', desc: 'Commit, backup DB e snapshot git automatico dell\'ecosistema', cmd: 'JARVIS, sync repository e backup' }
        ]
      }
    ];

    const numLobes = systemLobes.length;
    const goldenRatio = (1 + Math.sqrt(5)) / 2;

    systemLobes.forEach((lobe, i) => {
      const theta = 2 * Math.PI * i / goldenRatio;
      const phi = Math.acos(1 - 2 * (i + 0.5) / numLobes);

      const hx = (this.baseRadius * 0.75) * Math.sin(phi) * Math.cos(theta);
      const hy = (this.baseRadius * 0.75) * Math.sin(phi) * Math.sin(theta);
      const hz = (this.baseRadius * 0.75) * Math.cos(phi);

      const hubIdx = this.nodes.length;
      this.nodes.push({
        id: `HUB_${lobe.name}`,
        key: lobe.name.toLowerCase(),
        x: hx, y: hy, z: hz,
        radius: 10.5,
        color: lobe.color,
        glow: lobe.glow,
        label: lobe.label,
        category: lobe.name,
        isHub: true,
        description: `Lobo Master: ${lobe.label} (${lobe.skills.length} Skill Reali collegate)`,
        command: `JARVIS, apri modulo ${lobe.label}`,
        theta,
        phi
      });

      // Highway Axon Cable to Core
      this.connections.push({
        from: 0,
        to: hubIdx,
        alpha: 0.85,
        isHighway: true,
        category: lobe.name
      });

      // Individual Real Skill & Tool Orbs
      lobe.skills.forEach((skill, s) => {
        const satDist = 24 + (s % 3) * 12;
        const satAngle1 = (s / lobe.skills.length) * Math.PI * 2 + (i * 0.4);
        const satAngle2 = (s % 3) * 0.7 + 0.35;

        const sx = hx + satDist * Math.sin(satAngle2) * Math.cos(satAngle1);
        const sy = hy + satDist * Math.sin(satAngle2) * Math.sin(satAngle1);
        const sz = hz + satDist * Math.cos(satAngle2);

        const satIdx = this.nodes.length;
        this.nodes.push({
          id: skill.id,
          key: skill.id,
          x: sx, y: sy, z: sz,
          radius: 5.2 + (s % 3) * 1.0,
          color: lobe.color,
          glow: lobe.glow,
          label: skill.label,
          category: lobe.name,
          isHub: false,
          description: skill.desc || `Skill ufficiale ${skill.label}`,
          command: skill.cmd || `JARVIS, esegui ${skill.label}`
        });

        // Axon connection to Hub
        this.connections.push({
          from: hubIdx,
          to: satIdx,
          alpha: 0.45,
          isHighway: false,
          category: lobe.name
        });

        // Inter-skill connecting mesh
        if (s > 0 && s % 2 === 0) {
          this.connections.push({
            from: satIdx - 1,
            to: satIdx,
            alpha: 0.25,
            isHighway: false,
            category: lobe.name
          });
        }
      });
    });

    for (let i = 1; i <= numLobes; i++) {
      const nextLobe = (i % numLobes) + 1;
      this.connections.push({
        from: i * 7,
        to: nextLobe * 7,
        alpha: 0.22,
        isHighway: false,
        category: 'SHELL'
      });
    }
  }

  startVpsTelemetryPolling() {
    setInterval(async () => {
      try {
        const res = await fetch('/api/telemetry/vps');
        if (res.ok) {
          const data = await res.json();
          if (data && data.cpu_usage !== undefined) {
            this.vpsCpu = data.cpu_usage;
            this.vpsRam = data.ram_usage;
            this.vpsLatency = data.latency_ms;
          }
        }
      } catch (e) {}
    }, 2500);
  }

  startSynapseEventsPolling() {
    setInterval(async () => {
      try {
        const res = await fetch('/api/synapse/events');
        if (res.ok) {
          const data = await res.json();
          if (data && data.events && data.events.length > 0) {
            data.events.forEach(ev => {
              this.igniteSkill(ev.skill, ev.category);
            });
          }
        }
      } catch (e) {}
    }, 1200);
  }

  connectRustBridge() {
    try {
      const ws = new WebSocket('ws://' + window.location.hostname + ':9000/ws');
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data && data.event === 'SYNAPSE_PULSE') {
            this.igniteSkill(data.skill, data.category);
          }
        } catch (e) {}
      };
    } catch (e) {}
  }

  bindEvents() {
    window.addEventListener('resize', () => { this.resize(); });

    let touchStartTime = 0;
    let touchMoved = false;

    const handleStart = (clientX, clientY) => {
      this.mouse.isDown = true;
      this.mouse.lastX = clientX;
      this.mouse.lastY = clientY;
      this.isAutoTargeting = false;
      if (this.activeSkillTimer) clearTimeout(this.activeSkillTimer);
      touchStartTime = Date.now();
      touchMoved = false;
    };

    const handleMove = (clientX, clientY) => {
      if (this.mouse.isDown) {
        const dx = clientX - this.mouse.lastX;
        const dy = clientY - this.mouse.lastY;
        if (Math.abs(dx) > 4 || Math.abs(dy) > 4) touchMoved = true;
        this.rotY += dx * 0.005;
        this.rotX -= dy * 0.005;
        this.mouse.lastX = clientX;
        this.mouse.lastY = clientY;
      }
    };

    const handleEnd = (clientX, clientY) => {
      this.mouse.isDown = false;
      const duration = Date.now() - touchStartTime;
      
      // Tap or Click detected
      if (!touchMoved && duration < 350 && clientX !== undefined && clientY !== undefined) {
        const rect = this.canvas.getBoundingClientRect();
        const tapX = clientX - rect.left;
        const tapY = clientY - rect.top;

        if (this.lastProjectedNodes) {
          let closestNode = null;
          let minDist = 35;

          for (const pn of this.lastProjectedNodes) {
            const dist = Math.hypot(pn.px - tapX, pn.py - tapY);
            if (dist < minDist) {
              minDist = dist;
              closestNode = pn.orig;
            }
          }

          if (closestNode) {
            // Open Skill Inspector HUD Modal
            this.openSkillInspectorModal(closestNode);
            this.igniteSkill(closestNode.key || closestNode.id, closestNode.category);
          }
        }
      }
    };

    this.canvas.addEventListener('mousedown', (e) => handleStart(e.clientX, e.clientY));
    window.addEventListener('mousemove', (e) => handleMove(e.clientX, e.clientY));
    window.addEventListener('mouseup', (e) => handleEnd(e.clientX, e.clientY));

    this.canvas.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) handleStart(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (e.touches.length === 1) handleMove(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });

    window.addEventListener('touchend', (e) => {
      const touch = e.changedTouches[0];
      if (touch) handleEnd(touch.clientX, touch.clientY);
      else handleEnd();
    });
  }

  // ── OPEN SKILL INSPECTOR HUD MODAL ──────────────────────────────
  openSkillInspectorModal(node) {
    if (window.showSkillDetailModal) {
      window.showSkillDetailModal(node);
    }
  }

  // ── 3/4 ISOMETRIC PROFILE LOCK ON ACTIVE TOOL ────────────────────
  igniteSkill(skillKey = null, category = null) {
    if (!category && skillKey) {
      const found = this.nodes.find(n => n.key === skillKey || (n.label && n.label.toLowerCase().includes(skillKey.toLowerCase())));
      if (found) category = found.category;
    }

    this.activeCategory = category;
    this.activeSkillKeys.clear();
    this.activeNodeId = null;

    let targetNode = null;
    if (skillKey) {
      this.activeSkillKeys.add(skillKey.toLowerCase());
      targetNode = this.nodes.find(n => n.key === skillKey.toLowerCase() || (n.label && n.label.toLowerCase().includes(skillKey.toLowerCase())));
    }
    if (!targetNode && category) {
      targetNode = this.nodes.find(n => n.isHub && n.category === category);
    }

    if (targetNode) {
      this.activeNodeId = targetNode.id;
      this.activeSkillLabel = targetNode.label || targetNode.key;

      // ── 3/4 ISOMETRIC PROFILE LOCK (Reveals 3D Axon Depth) ──
      const azimuth = Math.atan2(targetNode.x, targetNode.z);
      this.targetRotY = azimuth + 0.62; 
      this.targetRotX = 0.42;

      this.isAutoTargeting = true;
      this.targetZoom = 1.85;
      this.targetCamX = 0;
      this.targetCamY = 0;
    }

    this.isThinking = true;

    // High energy laser plasma pulse barrage along the active highway
    const activeConns = this.connections.filter(c => c.category === category || c.isHighway);
    for (let i = 0; i < 35; i++) {
      const conn = (activeConns.length > 0) ? activeConns[Math.floor(Math.random() * activeConns.length)] : this.connections[0];
      if (conn) {
        this.pulses.push({
          from: conn.from,
          to: conn.to,
          progress: Math.random() * 0.2,
          speed: 0.038 + Math.random() * 0.035,
          color: (conn.category === category) ? '#00ff9f' : '#00f0ff',
          glow: (conn.category === category) ? '#00ff9f' : '#00f0ff',
          size: 7.0,
          tailLength: 0.32
        });
      }
    }

    if (this.activeSkillTimer) clearTimeout(this.activeSkillTimer);
    this.activeSkillTimer = setTimeout(() => {
      // Gentle return to calm slow idle rotation
      this.targetZoom = 1.0;
      this.isAutoTargeting = false;
      this.activeCategory = null;
      this.activeSkillKeys.clear();
      this.activeNodeId = null;
      this.isThinking = false;
    }, 7500);
  }

  setThinking(val) {
    this.isThinking = val;
    if (val && this.activeCategory) this.igniteSkill(null, this.activeCategory);
  }

  setSpeaking(val) {
    this.isSpeaking = val;
    if (val) {
      this.targetZoom = 1.6;
      this.isAutoTargeting = true; // Lock view still while speaking!
    } else {
      // Return to calm idle rotation after speaking
      this.targetZoom = 1.0;
      this.isAutoTargeting = false;
    }
  }

  // ── DRAW 3D VOLUMETRIC ORB (DORMANT SOFFUSO VS PULSANTE ATTIVO) ──
  drawVolumetricOrb(px, py, r, color, glow, isHub, isLobeActive, isSkillActive, scale) {
    const isLit = isLobeActive || isSkillActive;

    this.ctx.save();
    
    if (isLit) {
      // 🌟 ACCESO / ATTIVO: High-intensity living breathing neon flash bloom
      const pulseMod = 1.0 + Math.sin(this.time * 8.5) * 0.22;
      const rLit = r * (isSkillActive ? 1.45 : 1.2) * pulseMod;

      this.ctx.shadowColor = isSkillActive ? '#00ff9f' : (glow || color);
      this.ctx.shadowBlur = isSkillActive ? 38 : (isHub ? 28 : 18);

      // Expanding Ripple Wave
      const rippleR = r * 1.8 + ((this.time * 24) % 22);
      const rippleAlpha = Math.max(0, 1.0 - (rippleR - r * 1.8) / 22);
      this.ctx.strokeStyle = isSkillActive ? `rgba(0, 255, 159, ${rippleAlpha * 0.7})` : `rgba(0, 240, 255, ${rippleAlpha * 0.5})`;
      this.ctx.lineWidth = 1.5;
      this.ctx.beginPath();
      this.ctx.arc(px, py, rippleR, 0, Math.PI * 2);
      this.ctx.stroke();

      const grad = this.ctx.createRadialGradient(
        px - rLit * 0.35, py - rLit * 0.35, rLit * 0.08,
        px, py, rLit
      );
      grad.addColorStop(0.0, '#ffffff');
      grad.addColorStop(0.3, isSkillActive ? '#00ff9f' : color);
      grad.addColorStop(0.8, isSkillActive ? '#00ff9f' : color);
      grad.addColorStop(1.0, '#011018');

      this.ctx.fillStyle = grad;
      this.ctx.beginPath();
      this.ctx.arc(px, py, rLit, 0, Math.PI * 2);
      this.ctx.fill();

      // Hub Fresnel Corona
      if (isHub) {
        this.ctx.strokeStyle = 'rgba(0, 255, 159, 0.95)';
        this.ctx.lineWidth = 2.0 * scale;
        this.ctx.beginPath();
        this.ctx.arc(px, py, r * 1.6 + Math.sin(this.time * 4) * 3, 0, Math.PI * 2);
        this.ctx.stroke();
      }
    } else {
      // 🌑 DORMANT / SOFFUSO: Soft dark translucent glass orb
      this.ctx.shadowBlur = 0;
      this.ctx.globalAlpha = isHub ? 0.38 : 0.22;

      const grad = this.ctx.createRadialGradient(
        px - r * 0.35, py - r * 0.35, r * 0.1,
        px, py, r
      );
      grad.addColorStop(0.0, 'rgba(255, 255, 255, 0.4)');
      grad.addColorStop(0.35, color);
      grad.addColorStop(0.9, '#021824');
      grad.addColorStop(1.0, '#01080e');

      this.ctx.fillStyle = grad;
      this.ctx.beginPath();
      this.ctx.arc(px, py, r * 0.88, 0, Math.PI * 2);
      this.ctx.fill();
    }

    this.ctx.restore();
    this.ctx.shadowBlur = 0;
    this.ctx.globalAlpha = 1.0;
  }

  // ── DRAW HUD CALLOUT PIN FOR ACTIVE TOOL ─────────────────────────
  drawActiveToolCallout(px, py, label, color) {
    this.ctx.save();

    const pinLenX = 35;
    const pinLenY = -28;
    const boxW = Math.max(120, label.length * 7.5 + 24);
    const boxH = 22;

    const cornerX = px + pinLenX;
    const cornerY = py + pinLenY;

    // Laser Callout Leader Line
    this.ctx.strokeStyle = '#00ff9f';
    this.ctx.lineWidth = 1.5;
    this.ctx.shadowColor = '#00ff9f';
    this.ctx.shadowBlur = 10;
    
    this.ctx.beginPath();
    this.ctx.moveTo(px, py);
    this.ctx.lineTo(cornerX, cornerY);
    this.ctx.lineTo(cornerX + boxW, cornerY);
    this.ctx.stroke();

    // Callout Box Glass Badge
    this.ctx.fillStyle = 'rgba(2, 12, 24, 0.88)';
    this.ctx.strokeStyle = '#00ff9f';
    this.ctx.lineWidth = 1.0;
    this.ctx.beginPath();
    this.ctx.roundRect(cornerX, cornerY - boxH, boxW, boxH, 4);
    this.ctx.fill();
    this.ctx.stroke();

    // Text Label inside HUD Badge
    this.ctx.font = `bold 10px "Orbitron", sans-serif`;
    this.ctx.fillStyle = '#00ff9f';
    this.ctx.textAlign = 'left';
    this.ctx.fillText(`⚡ ${label}`, cornerX + 8, cornerY - 7);

    this.ctx.restore();
  }

  // ── DRAW CENTRAL SINGULARITY ARC CORE ────────────────────────────
  drawCoreSingularity(coreProj) {
    const cx = coreProj.px;
    const cy = coreProj.py;
    const scale = coreProj.scale;
    const rCore = 18 * scale;

    this.ctx.save();
    this.ctx.translate(cx, cy);

    // 1. Triple Holographic Orbit Rings
    this.ctx.strokeStyle = this.isThinking ? '#ff007f' : '#00f0ff';
    this.ctx.lineWidth = 1.8 * scale;
    this.ctx.shadowColor = this.isThinking ? '#ff007f' : '#00f0ff';
    this.ctx.shadowBlur = 20;
    this.ctx.beginPath();
    this.ctx.arc(0, 0, rCore * 1.9 + Math.sin(this.time * 3) * 2.5, 0, Math.PI * 2);
    this.ctx.stroke();

    // 2. Slow Calm Rotating Blades
    const spinSpeed = 1.2;
    this.ctx.strokeStyle = '#00ff9f';
    this.ctx.lineWidth = 2.4 * scale;
    this.ctx.shadowColor = '#00ff9f';
    this.ctx.shadowBlur = 16;

    this.ctx.beginPath();
    this.ctx.arc(0, 0, rCore * 1.4, this.time * spinSpeed, this.time * spinSpeed + Math.PI * 1.2);
    this.ctx.stroke();

    this.ctx.beginPath();
    this.ctx.arc(0, 0, rCore * 1.4, -this.time * spinSpeed, -this.time * spinSpeed + Math.PI * 1.2);
    this.ctx.stroke();

    // 3. Volumetric Plasma Singularity Sphere
    const grad = this.ctx.createRadialGradient(
      -rCore * 0.3, -rCore * 0.3, rCore * 0.1,
      0, 0, rCore
    );
    grad.addColorStop(0.0, '#ffffff');
    grad.addColorStop(0.3, '#00f0ff');
    grad.addColorStop(0.7, '#00ff9f');
    grad.addColorStop(1.0, '#011a14');

    this.ctx.fillStyle = grad;
    this.ctx.beginPath();
    this.ctx.arc(0, 0, rCore, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.restore();
    this.ctx.shadowBlur = 0;

    // Glowing Holographic Label
    this.ctx.font = `900 ${Math.max(10, Math.round(11 * scale))}px "Orbitron", sans-serif`;
    this.ctx.fillStyle = '#00ff9f';
    this.ctx.textAlign = 'center';
    this.ctx.fillText('CEREBRO', cx, cy + rCore + 14);
  }

  animate() {
    this.time += 0.016;

    // Smooth Camera Interpolation
    this.zoomScale += (this.targetZoom - this.zoomScale) * 0.06;
    this.camX += (this.targetCamX - this.camX) * 0.07;
    this.camY += (this.targetCamY - this.camY) * 0.07;
    
    if (this.isAutoTargeting || this.isThinking || this.isSpeaking) {
      // FREEZE ON ISOMETRIC 3/4 PROFILE VIEW (Zero erratic spinning while speaking!)
      this.rotY += (this.targetRotY - this.rotY) * 0.06;
      this.rotX += (this.targetRotX - this.rotX) * 0.06;
    } else if (!this.mouse.isDown) {
      // CALM, SLOW & GENTLE IDLE ROTATION
      this.rotY += 0.0010;
    }

    this.ctx.clearRect(0, 0, this.width, this.height);

    // Ambient floating quantum particles
    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];
      p.theta += p.baseSpeed;
      const px = p.r * Math.sin(p.phi) * Math.cos(p.theta);
      const py = p.r * Math.sin(p.phi) * Math.sin(p.theta);
      const pz = p.r * Math.cos(p.phi);

      const fov = 480;
      const cosY = Math.cos(this.rotY), sinY = Math.sin(this.rotY);
      const cosX = Math.cos(this.rotX), sinX = Math.sin(this.rotX);

      let x1 = px * cosY - pz * sinY;
      let z1 = pz * cosY + px * sinY;
      let y2 = py * cosX - z1 * sinX;
      let z2 = z1 * cosX + py * sinX;

      const scale = (fov / (fov + z2 + 250)) * this.zoomScale;
      const pAlpha = p.alpha * (Math.sin(this.time * 2.0 + i) * 0.3 + 0.7);

      this.ctx.fillStyle = p.color;
      this.ctx.globalAlpha = Math.max(0.06, pAlpha);
      this.ctx.beginPath();
      this.ctx.arc(this.centerX + (x1 + this.camX) * scale, this.centerY + (y2 + this.camY) * scale, p.radius * scale, 0, Math.PI * 2);
      this.ctx.fill();
    }
    this.ctx.globalAlpha = 1.0;

    // Continuous Active Plasma Stream on the active highway
    if (this.activeCategory) {
      if (Math.random() < 0.75) {
        const activeConns = this.connections.filter(c => c.category === this.activeCategory);
        if (activeConns.length > 0) {
          const conn = activeConns[Math.floor(Math.random() * activeConns.length)];
          this.pulses.push({
            from: conn.from,
            to: conn.to,
            progress: 0,
            speed: 0.038 + Math.random() * 0.03,
            color: '#00ff9f',
            glow: '#00ff9f',
            size: 6.8,
            tailLength: 0.32
          });
        }
      }
    } else if (Math.random() < 0.25 && this.connections.length > 0) {
      const conn = this.connections[Math.floor(Math.random() * this.connections.length)];
      this.pulses.push({
        from: conn.from,
        to: conn.to,
        progress: 0,
        speed: 0.020 + Math.random() * 0.02,
        color: '#ffffff',
        glow: '#00d4ff',
        size: 3.8,
        tailLength: 0.15
      });
    }

    // 3D Projection Matrix (FOV 480)
    const fov = 480;
    const projectedNodes = [];

    const cosY = Math.cos(this.rotY), sinY = Math.sin(this.rotY);
    const cosX = Math.cos(this.rotX), sinX = Math.sin(this.rotX);

    for (let i = 0; i < this.nodes.length; i++) {
      const n = this.nodes[i];

      let x1 = n.x * cosY - n.z * sinY;
      let z1 = n.z * cosY + n.x * sinY;

      let y2 = n.y * cosX - z1 * sinX;
      let z2 = z1 * cosX + n.y * sinX;

      const scale = (fov / (fov + z2 + 250)) * this.zoomScale;
      const projX = this.centerX + (x1 + this.camX) * scale;
      const projY = this.centerY + (y2 + this.camY) * scale;

      projectedNodes.push({
        orig: n,
        px: projX,
        py: projY,
        pz: z2,
        scale,
        alpha: Math.max(0.3, Math.min(1.0, (z2 + 260) / 400))
      });
    }

    this.lastProjectedNodes = projectedNodes;

    // 1. Draw Synapse Axons
    for (let i = 0; i < this.connections.length; i++) {
      const c = this.connections[i];
      const p1 = projectedNodes[c.from];
      const p2 = projectedNodes[c.to];

      if (p1 && p2) {
        const isMatch = this.activeCategory && (c.category === this.activeCategory);
        
        if (isMatch) {
          this.ctx.lineWidth = (c.isHighway ? 3.0 : 1.8) * ((p1.scale + p2.scale) / 2);
          this.ctx.strokeStyle = `rgba(0, 255, 159, ${0.95 * ((p1.alpha + p2.alpha) / 2)})`;
          this.ctx.shadowColor = '#00ff9f';
          this.ctx.shadowBlur = 14;
        } else {
          this.ctx.lineWidth = (c.isHighway ? 1.2 : 0.7) * ((p1.scale + p2.scale) / 2);
          this.ctx.strokeStyle = `rgba(0, 212, 255, ${0.12 * ((p1.alpha + p2.alpha) / 2)})`;
          this.ctx.shadowBlur = 0;
        }
        
        this.ctx.beginPath();
        this.ctx.moveTo(p1.px, p1.py);
        this.ctx.lineTo(p2.px, p2.py);
        this.ctx.stroke();
        this.ctx.shadowBlur = 0;
      }
    }

    // 2. Draw Data Sparks with Laser Plasma Tail
    for (let i = this.pulses.length - 1; i >= 0; i--) {
      const pulse = this.pulses[i];
      pulse.progress += pulse.speed;

      if (pulse.progress >= 1.0) {
        this.pulses.splice(i, 1);
        continue;
      }

      const p1 = projectedNodes[pulse.from];
      const p2 = projectedNodes[pulse.to];
      if (p1 && p2) {
        const headX = p1.px + (p2.px - p1.px) * pulse.progress;
        const headY = p1.py + (p2.py - p1.py) * pulse.progress;

        const tailProg = Math.max(0, pulse.progress - (pulse.tailLength || 0.2));
        const tailX = p1.px + (p2.px - p1.px) * tailProg;
        const tailY = p1.py + (p2.py - p1.py) * tailProg;

        const pScale = (p1.scale + p2.scale) / 2;

        const grad = this.ctx.createLinearGradient(tailX, tailY, headX, headY);
        grad.addColorStop(0, 'rgba(0, 240, 255, 0)');
        grad.addColorStop(1, pulse.glow || '#00ff9f');

        this.ctx.lineWidth = 2.6 * pScale;
        this.ctx.strokeStyle = grad;
        this.ctx.beginPath();
        this.ctx.moveTo(tailX, tailY);
        this.ctx.lineTo(headX, headY);
        this.ctx.stroke();

        this.ctx.fillStyle = '#ffffff';
        this.ctx.shadowColor = pulse.glow || '#00ff9f';
        this.ctx.shadowBlur = 18;
        this.ctx.beginPath();
        this.ctx.arc(headX, headY, pulse.size * pScale, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.shadowBlur = 0;
      }
    }

    // 3. Draw CEREBRO Singularity Core
    const coreProj = projectedNodes[0];
    if (coreProj) {
      this.drawCoreSingularity(coreProj);
    }

    // 4. Draw Dense 3D Skill Orbs sorted by Z depth
    const sortedNodes = projectedNodes.slice(1).sort((a, b) => b.pz - a.pz);
    let activeCalloutTarget = null;

    for (let i = 0; i < sortedNodes.length; i++) {
      const pn = sortedNodes[i];
      const n = pn.orig;
      const r = n.radius * pn.scale;

      const isLobeActive = this.activeCategory && (n.category === this.activeCategory);
      const isSkillActive = n.key && (this.activeSkillKeys.has(n.key.toLowerCase()) || this.activeSkillKeys.has(n.label.toLowerCase()));

      if (isSkillActive || (isLobeActive && n.isHub && !activeCalloutTarget)) {
        activeCalloutTarget = { px: pn.px, py: pn.py, label: n.label, color: n.color };
      }

      // Draw Volumetric Orb
      this.drawVolumetricOrb(pn.px, pn.py, r, n.color, n.glow, n.isHub, isLobeActive, isSkillActive, pn.scale);

      // Hub Dormant Label
      if (n.isHub && !isLobeActive && pn.scale > 0.6) {
        this.ctx.font = `bold 9.5px "Orbitron", sans-serif`;
        this.ctx.fillStyle = 'rgba(248, 250, 252, 0.35)';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(n.label, pn.px, pn.py - r - 5);
      }
    }

    // 5. Draw HUD Callout Pin for the Active Tool in Isometric Profile
    if (activeCalloutTarget) {
      this.drawActiveToolCallout(
        activeCalloutTarget.px,
        activeCalloutTarget.py,
        activeCalloutTarget.label,
        activeCalloutTarget.color
      );
    }

    requestAnimationFrame(() => this.animate());
  }

  // ── FRESHNESS SENTINEL — Apply Neon vs Pale Dimmed to nodes ──────────────
  applyFreshnessMatrix(matrix) {
    if (!matrix || !this.nodes) return;
    for (const node of this.nodes) {
      const sid = node.id || node.key;
      const data = matrix[sid];
      if (!data) continue;
      const score = data.freshness_score || 1.0;
      if (score > 0.7) {
        // VIBRANT NEON — skill is fresh
        node._freshnessColor = null; // use default bright color
        node._freshnessAlpha = 1.0;
        node._freshnessGlow = true;
      } else {
        // PALE DIMMED — skill is stale
        const paleness = 0.3 + score * 0.5; // 0.3..0.65
        node._freshnessColor = `rgba(120, 130, 110, ${paleness})`;
        node._freshnessAlpha = paleness;
        node._freshnessGlow = false;
      }
      node._freshnessScore = score;
      node._freshnessStatus = data.status;
      node._freshnessLastUpdated = data.last_updated_hours_ago;
    }
  }

  // ── NUCLEUS SHOCKWAVE PULSE (Tap-to-Talk feedback) ───────────────────────
  emitNucleusShockwave() {
    // Add a transient shockwave particle from center
    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 2;
      this.particles.push({
        x: 0, y: 0, z: 0,
        vx: Math.cos(angle) * 4,
        vy: Math.sin(angle) * 4,
        vz: (Math.random() - 0.5) * 3,
        life: 1.0,
        decay: 0.04,
        color: '#00ff9f',
        size: 3.5,
        isShockwave: true
      });
    }
  }

  // ── DYNAMIC EVOLUTION SCALE & TACHYON FLUX REACTIVITY ─────────────────
  setEvolutionScale(scale = 1.0, flux = 90.0) {
    this.evolutionScale = Math.max(0.8, Math.min(1.8, scale));
    this.tachyonFlux = Math.max(50.0, Math.min(100.0, flux));
    
    // Scale base radius smoothly based on E.B. cognitive level
    const targetRad = Math.min(this.width, this.height) * 0.35 * this.evolutionScale;
    this.baseRadius = targetRad;

    // Adjust particle generation rate based on flux
    if (this.particles && this.particles.length < 35 && Math.random() < (this.tachyonFlux / 150.0)) {
      const ang = Math.random() * Math.PI * 2;
      const dist = 40 + Math.random() * (this.baseRadius * 0.8);
      this.particles.push({
        x: Math.cos(ang) * dist,
        y: Math.sin(ang) * dist,
        z: (Math.random() - 0.5) * 60,
        vx: (Math.random() - 0.5) * 1.5,
        vy: (Math.random() - 0.5) * 1.5,
        vz: (Math.random() - 0.5) * 1.5,
        life: 1.0,
        decay: 0.015,
        color: Math.random() > 0.4 ? '#00ff9f' : '#00f0ff',
        size: 2.0 + Math.random() * 2.0
      });
    }
  }

  // ── DYNAMIC PERSONALITY & HUD THEME MORPHING ──────────────────────────

  setPersonalityTheme(theme = 'jarvis') {
    this.personalityTheme = theme;
    const colors = {
      'jarvis': { primary: '#00f0ff', secondary: '#00ff9f', glow: 'rgba(0,240,255,0.4)', name: 'J.A.R.V.I.S.' },
      'military': { primary: '#f59e0b', secondary: '#ef4444', glow: 'rgba(245,158,11,0.4)', name: 'MILITARY TACTICAL' },
      'architect': { primary: '#00ff9f', secondary: '#06b6d4', glow: 'rgba(0,255,159,0.4)', name: 'SENIOR ARCHITECT' },
      'friendly': { primary: '#a855f7', secondary: '#ec4899', glow: 'rgba(168,85,247,0.4)', name: 'FRIENDLY COMPANION' }
    };
    this.themePalette = colors[theme] || colors['jarvis'];
    this.emitNucleusShockwave();
  }

  // ── AUDIO-REACTIVE 3D VOICE RESONANCE (FFT a 60 FPS) ──────────────────
  setAudioLevel(level = 0.0) {
    this.audioLevel = Math.max(0.0, Math.min(1.0, level));
    if (this.audioLevel > 0.3) {
      // Add acoustic resonance ripple
      for (let i = 0; i < 3; i++) {
        const ang = Math.random() * Math.PI * 2;
        this.particles.push({
          x: Math.cos(ang) * (this.baseRadius * 0.4),
          y: Math.sin(ang) * (this.baseRadius * 0.4),
          z: (Math.random() - 0.5) * 40,
          vx: Math.cos(ang) * 2.5,
          vy: Math.sin(ang) * 2.5,
          vz: (Math.random() - 0.5) * 2.0,
          life: 0.8,
          decay: 0.03,
          color: this.themePalette ? this.themePalette.primary : '#00ff9f',
          size: 2.0 + this.audioLevel * 3.0
        });
      }
    }
  }
}



// Global Singleton Initializer
window.SupremeBioNeuralCortex = SupremeBioNeuralCortex;
window.initBioNeuralCortex = function(canvasId = 'synapseCanvas') {
  if (!window.bioCortexInstance) {
    window.bioCortexInstance = new SupremeBioNeuralCortex(canvasId);
  }
  return window.bioCortexInstance;
};

