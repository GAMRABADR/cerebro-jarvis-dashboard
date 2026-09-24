// ═══════════════════════════════════════════════════════════════════════════════
//  E.B.J. J.A.R.V.I.S. · 3D QUANTUM NEURAL COSMOS & ARC REACTOR HUD
//  Ispirato al sistema GPT-6 Astra / JARVIS 3D Knowledge Constellation
// ═══════════════════════════════════════════════════════════════════════════════

(function () {
  const container = document.getElementById('cosmos-3d-container');
  if (!container) return;

  // ── THREE.JS SETUP ────────────────────────────────────────────────────────
  let scene, camera, renderer, controls;
  let nodeObjects = [];
  let lineSegments = [];
  let particleSystem;
  let raycaster, mouse;
  let hoveredNode = null;
  let selectedNode = null;
  let isTransitioningCamera = false;
  let targetCamPos = null;
  let targetControlsTarget = null;
  let currentLayout = 'constellation'; // 'constellation', 'cube', 'sphere', 'ring'

  // Cluster Definition
  const CLUSTERS = [
    {
      id: 'traslochi',
      name: 'Pietro Traslochi & Leads',
      color: 0x10b981, // Emerald Green
      pos: new THREE.Vector3(-140, 40, 20),
      nodes: [
        { name: 'Lead Radar 2026', type: 'scanner', status: 'ACTIVE', notes: 'Facebook & Local Inbound Harvester' },
        { name: 'pietrotraslochi.com', type: 'domain', status: 'ONLINE', notes: 'Next.js Production Landing (SSL)' },
        { name: 'Preventivo Instant', type: 'calculator', status: 'ONLINE', notes: 'Quantum dynamic pricing < 8s' },
        { name: 'WhatsApp Handshake', type: 'messaging', status: 'READY', notes: '1-tap direct pre-filled chat' },
        { name: 'Luhn P.IVA Filter', type: 'rust', status: 'SHIELDED', notes: 'Agenzia Entrate MOD10 verification' },
        { name: 'Bologna Centro Hub', type: 'geo', status: 'ACTIVE', notes: 'Mazzini, Saragozza, Bolognina' },
        { name: 'Imola Metropolitan', type: 'geo', status: 'ACTIVE', notes: 'Autostrada A14 28km corridor' },
        { name: 'Casalecchio Hub', type: 'geo', status: 'ACTIVE', notes: 'Reno & Valsamoggia coverage' },
        { name: 'San Lazzaro Hub', type: 'geo', status: 'ACTIVE', notes: 'Savena & Romagna bypass' },
        { name: '3D Cargo Packing', type: 'optimizer', status: 'READY', notes: 'Ducato & Daily 35C binpacker' },
        { name: 'Clienti Certificati', type: 'database', status: 'SYNCED', notes: 'mail_vault.db verified_leads' }
      ]
    },
    {
      id: 'rust',
      name: 'Rust Tokio Superpowers',
      color: 0xff7700, // Rust Orange
      pos: new THREE.Vector3(120, 80, -30),
      nodes: [
        { name: 'jarvis-bridge :9000', type: 'core', status: 'ACTIVE', notes: 'Tokio Async Micro-Bridge Native' },
        { name: 'GDI Screen Engine', type: 'native', status: 'STREAMING', notes: '1440p @ 5 FPS OpenInputDesktop' },
        { name: 'Active Window Tracker', type: 'win32', status: 'ONLINE', notes: 'user32.dll Win32 FFI < 1µs' },
        { name: 'Dual Polarity Engine', type: 'nlp', status: 'ACTIVE', notes: 'Aho-Corasick semantic classifier' },
        { name: 'Geo-Route Matrix', type: 'math', status: 'ACTIVE', notes: '46 Comuni Emilia Haversine' },
        { name: 'Bloom Lead Dedup', type: 'algorithm', status: 'ACTIVE', notes: 'Sub-millisecond duplicate killer' },
        { name: 'SIMD Vector Memory', type: 'memory', status: 'ONLINE', notes: 'AVX2 accelerated embeddings' },
        { name: 'Terminal Tokio Runner', type: 'runner', status: 'ONLINE', notes: 'Subprocess execution engine' }
      ]
    },
    {
      id: 'cloud',
      name: 'Oracle VPS 24GB Cloud',
      color: 0x00f0ff, // Electric Cyan
      pos: new THREE.Vector3(-40, -120, 80),
      nodes: [
        { name: 'Host 92.4.233.42', type: 'vps', status: 'ONLINE', notes: '4 OCPU Ampere A1, 24GB RAM' },
        { name: 'n8n Workflows :5678', type: 'automation', status: 'ONLINE', notes: '34 active DAG pipelines' },
        { name: 'FastAPI Backend :8000', type: 'api', status: 'ONLINE', notes: 'Uvicorn unified leads router' },
        { name: 'Agent Zero :50080', type: 'agent', status: 'STANDBY', notes: 'Multi-agent orchestration' },
        { name: 'Nginx SSL Cluster', type: 'proxy', status: 'ONLINE', notes: 'TLS 1.3 Reverse Proxy' },
        { name: 'PostgreSQL Database', type: 'db', status: 'HEALTHY', notes: 'Relational storage cluster' },
        { name: 'Redis Cache Bus', type: 'cache', status: 'ONLINE', notes: 'In-memory pub/sub engine' },
        { name: 'Cloudflare Tunnel', type: 'ingress', status: 'ONLINE', notes: 'eb.badrexpress.com zero-trust' }
      ]
    },
    {
      id: 'ai',
      name: 'AI & Cognitive Connectome',
      color: 0xa855f7, // Royal Purple
      pos: new THREE.Vector3(140, -60, 60),
      nodes: [
        { name: 'Qwen 27B Local GPU', type: 'llm', status: 'STANDBY', notes: 'Unsloth local inference :61517' },
        { name: 'Cerebro Synapse Engine', type: 'neural', status: 'ONLINE', notes: 'Real-time state & pulse matrix' },
        { name: 'Hermes LTM Memory', type: 'db', status: 'ONLINE', notes: 'hermes_ltm_memory.db long-term' },
        { name: 'NVIDIA NIM Relay', type: 'cloud_ai', status: 'ACTIVE', notes: 'Cloud LLM acceleration fallback' },
        { name: 'ElevenLabs TTS Voice', type: 'voice', status: 'ONLINE', notes: 'Badr custom neural voice pipeline' },
        { name: 'Sentinel Self-Heal', type: 'watchdog', status: 'ACTIVE', notes: 'Zero-downtime auto-respawn' }
      ]
    },
    {
      id: 'vault',
      name: 'Project & Asset Vaults',
      color: 0xeab308, // Gold
      pos: new THREE.Vector3(0, 150, -80),
      nodes: [
        { name: 'EBGStudio Master', type: 'project', status: 'ACTIVE', notes: 'Game Studio & Software Lab' },
        { name: 'UE 5.8 Game Dev', type: 'engine', status: 'STANDBY', notes: 'Unreal Engine 5.8 Blueprints' },
        { name: 'Steamworks #2886940', type: 'release', status: 'READY', notes: 'Steam build & distribution' },
        { name: 'BustePaghe Vault', type: 'docs', status: 'SECURED', notes: 'Encrypted payroll records' },
        { name: 'Hermes Master Kanban', type: 'kanban', status: 'ONLINE', notes: 'Task DAG & visual workflow' }
      ]
    },
    {
      id: 'kali',
      name: 'Kali Security Hardening',
      color: 0xef4444, // Crimson Red
      pos: new THREE.Vector3(-120, -50, -120),
      nodes: [
        { name: 'Audit Matrix Engine', type: 'sec', status: 'ACTIVE', notes: 'Automated vulnerability scanner' },
        { name: 'Port Scanner Recon', type: 'sec', status: 'IDLE', notes: 'VPS exposure verifier' },
        { name: 'SSH Sentinel Keyring', type: 'sec', status: 'ARMED', notes: 'ECDSA/RSA key vault' }
      ]
    }
  ];

  function init() {
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || (window.innerHeight - 56);

    // Scene & Fog
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x02060d, 0.0018);

    // Camera
    camera = new THREE.PerspectiveCamera(55, width / height, 1, 3000);
    camera.position.set(0, 80, 420);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // OrbitControls
    if (window.THREE && window.THREE.OrbitControls) {
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;
      controls.maxDistance = 1200;
      controls.minDistance = 60;
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.4;
    }

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x00f0ff, 1.2);
    dirLight1.position.set(200, 300, 200);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xa855f7, 0.8);
    dirLight2.position.set(-200, -200, -200);
    scene.add(dirLight2);

    // Build Constellation Universe
    buildUniverse();
    buildStarfield();
    setupRaycaster();
    setupHUD();

    window.addEventListener('resize', onWindowResize);
    animate();
  }

  // ── BUILD UNIVERSE & NODES ────────────────────────────────────────────────
  function buildUniverse() {
    const sphereGeo = new THREE.SphereGeometry(1, 24, 24);
    const lineMat = new THREE.LineBasicMaterial({
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.22,
      blending: THREE.AdditiveBlending
    });

    const linesPositions = [];

    CLUSTERS.forEach(cluster => {
      // Cluster Core Node (Larger, glowing)
      const coreMat = new THREE.MeshStandardMaterial({
        color: cluster.color,
        emissive: cluster.color,
        emissiveIntensity: 0.6,
        roughness: 0.2,
        metalness: 0.8
      });

      const coreMesh = new THREE.Mesh(sphereGeo, coreMat);
      coreMesh.position.copy(cluster.pos);
      coreMesh.scale.setScalar(9.0);
      coreMesh.userData = {
        name: cluster.name,
        type: 'CLUSTER HUB',
        status: 'PRIMARY',
        notes: `Cluster centrale contenente ${cluster.nodes.length} nodi operativi`,
        color: cluster.color,
        isHub: true
      };
      scene.add(coreMesh);
      nodeObjects.push(coreMesh);

      // Create Satellite Nodes
      cluster.nodes.forEach((item, idx) => {
        const phi = Math.acos(-1 + (2 * idx) / cluster.nodes.length);
        const theta = Math.sqrt(cluster.nodes.length * Math.PI) * phi;
        const radius = 32 + Math.random() * 26;

        const offset = new THREE.Vector3(
          radius * Math.cos(theta) * Math.sin(phi),
          radius * Math.sin(theta) * Math.sin(phi),
          radius * Math.cos(phi)
        );

        const nodePos = cluster.pos.clone().add(offset);

        const nodeMat = new THREE.MeshStandardMaterial({
          color: cluster.color,
          emissive: cluster.color,
          emissiveIntensity: 0.35,
          roughness: 0.3,
          metalness: 0.7
        });

        const nodeMesh = new THREE.Mesh(sphereGeo, nodeMat);
        nodeMesh.position.copy(nodePos);
        const nodeSize = 3.5 + Math.random() * 2.2;
        nodeMesh.scale.setScalar(nodeSize);

        nodeMesh.userData = {
          name: item.name,
          type: item.type,
          status: item.status,
          notes: item.notes,
          clusterName: cluster.name,
          color: cluster.color,
          origPos: nodePos.clone()
        };

        scene.add(nodeMesh);
        nodeObjects.push(nodeMesh);

        // Add line connecting satellite to its cluster hub
        linesPositions.push(
          cluster.pos.x, cluster.pos.y, cluster.pos.z,
          nodePos.x, nodePos.y, nodePos.z
        );

        // Add intra-cluster connections between adjacent satellites
        if (idx > 0 && Math.random() > 0.4) {
          const prevNode = nodeObjects[nodeObjects.length - 2];
          linesPositions.push(
            prevNode.position.x, prevNode.position.y, prevNode.position.z,
            nodePos.x, nodePos.y, nodePos.z
          );
        }
      });
    });

    // Inter-cluster highways (links between cluster hubs)
    for (let i = 0; i < CLUSTERS.length; i++) {
      for (let j = i + 1; j < CLUSTERS.length; j++) {
        linesPositions.push(
          CLUSTERS[i].pos.x, CLUSTERS[i].pos.y, CLUSTERS[i].pos.z,
          CLUSTERS[j].pos.x, CLUSTERS[j].pos.y, CLUSTERS[j].pos.z
        );
      }
    }

    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(linesPositions, 3));
    const linesMesh = new THREE.LineSegments(lineGeo, lineMat);
    scene.add(linesMesh);
  }

  // ── STARFIELD BACKGROUND ──────────────────────────────────────────────────
  function buildStarfield() {
    const starCount = 1800;
    const starGeo = new THREE.BufferGeometry();
    const starPositions = [];
    const starColors = [];

    for (let i = 0; i < starCount; i++) {
      const x = (Math.random() - 0.5) * 2000;
      const y = (Math.random() - 0.5) * 2000;
      const z = (Math.random() - 0.5) * 2000;
      starPositions.push(x, y, z);

      const colorChoice = Math.random();
      if (colorChoice > 0.7) starColors.push(0, 0.94, 1.0); // Cyan
      else if (colorChoice > 0.4) starColors.push(0.66, 0.33, 0.97); // Purple
      else starColors.push(0.8, 0.9, 1.0); // Soft Blue
    }

    starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));
    starGeo.setAttribute('color', new THREE.Float32BufferAttribute(starColors, 3));

    const starMat = new THREE.PointsMaterial({
      size: 2.2,
      vertexColors: true,
      transparent: true,
      opacity: 0.65
    });

    particleSystem = new THREE.Points(starGeo, starMat);
    scene.add(particleSystem);
  }

  // ── RAYCASTER & INTERACTION ───────────────────────────────────────────────
  function setupRaycaster() {
    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();

    const tooltip = document.getElementById('cosmos-tooltip');

    window.addEventListener('mousemove', e => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      if (tooltip) {
        tooltip.style.left = (e.clientX + 16) + 'px';
        tooltip.style.top = (e.clientY + 16) + 'px';
      }
    });

    window.addEventListener('click', e => {
      // Ignora click se proviene da HUD laterale o menu
      if (e.target.closest('#cosmos-arc-reactor') || e.target.closest('#cosmos-inspector-drawer')) return;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(nodeObjects);

      if (intersects.length > 0) {
        const clicked = intersects[0].object;
        focusOnNode(clicked);
      }
    });
  }

  function focusOnNode(node) {
    selectedNode = node;
    const pos = node.position;

    // Smooth camera fly-to target
    targetCamPos = pos.clone().add(new THREE.Vector3(0, 20, 65));
    targetControlsTarget = pos.clone();
    isTransitioningCamera = true;

    if (controls) controls.autoRotate = false;

    // Aggiorna drawer dettagli
    const drawer = document.getElementById('cosmos-inspector-drawer');
    if (drawer) {
      drawer.style.display = 'block';
      const u = node.userData;
      drawer.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(0,240,255,0.25); padding-bottom:10px; margin-bottom:12px;">
          <div>
            <span style="font-size:10px; color:#00f0ff; letter-spacing:1px; text-transform:uppercase;">${u.type || 'NODE'}</span>
            <h3 style="margin:2px 0 0 0; color:#fff; font-size:18px; font-family:'Outfit', sans-serif;">${u.name}</h3>
          </div>
          <span style="font-size:10px; background:rgba(16,185,129,0.2); color:#10b981; border:1px solid #10b981; padding:3px 8px; border-radius:12px; font-weight:bold;">${u.status}</span>
        </div>
        <p style="font-size:12px; color:#cbd5e1; line-height:1.6; font-family:'JetBrains Mono', monospace;">${u.notes}</p>
        ${u.clusterName ? `<p style="font-size:11px; color:#94a3b8;">Cluster: <strong style="color:#00ff9f;">${u.clusterName}</strong></p>` : ''}
        <div style="margin-top:16px; display:flex; gap:8px;">
          <button onclick="window.pingCosmosNode('${u.name}')" style="flex:1; background:rgba(0,240,255,0.18); border:1px solid #00f0ff; color:#00f0ff; padding:8px 12px; border-radius:8px; cursor:pointer; font-weight:bold; font-size:11px;">⚡ TEST RESPONSE</button>
          <button onclick="window.resetCosmosCamera()" style="background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.2); color:#fff; padding:8px 12px; border-radius:8px; cursor:pointer; font-size:11px;">RESET</button>
        </div>
      `;
    }
  }

  window.resetCosmosCamera = function () {
    targetCamPos = new THREE.Vector3(0, 80, 420);
    targetControlsTarget = new THREE.Vector3(0, 0, 0);
    isTransitioningCamera = true;
    if (controls) controls.autoRotate = true;
  };

  window.pingCosmosNode = function (name) {
    const t = (Math.random() * 0.8 + 0.1).toFixed(2);
    alert(`⚡ [JARVIS NEURAL BUS] Nodo "${name}" attivo e reattivo: latenza ${t} ms.`);
  };

  // ── HUD REACTOR SETUP ─────────────────────────────────────────────────────
  function setupHUD() {
    window.setCosmosLayout = function (layout) {
      currentLayout = layout;
      document.querySelectorAll('.cosmos-btn-mode').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById('btn-layout-' + layout);
      if (activeBtn) activeBtn.classList.add('active');

      const count = nodeObjects.length;

      nodeObjects.forEach((node, i) => {
        let target;
        if (layout === 'cube') {
          const side = Math.ceil(Math.cbrt(count));
          const ix = i % side;
          const iy = Math.floor((i / side) % side);
          const iz = Math.floor(i / (side * side));
          const step = 65;
          target = new THREE.Vector3(
            (ix - side / 2) * step,
            (iy - side / 2) * step,
            (iz - side / 2) * step
          );
        } else if (layout === 'sphere') {
          const phi = Math.acos(-1 + (2 * i) / count);
          const theta = Math.sqrt(count * Math.PI) * phi;
          const r = 160;
          target = new THREE.Vector3(
            r * Math.cos(theta) * Math.sin(phi),
            r * Math.sin(theta) * Math.sin(phi),
            r * Math.cos(phi)
          );
        } else if (layout === 'ring') {
          const angle = (i / count) * Math.PI * 2;
          const r = 180;
          target = new THREE.Vector3(Math.cos(angle) * r, (Math.sin(angle * 3) * 25), Math.sin(angle) * r);
        } else {
          // Constellation (default organic)
          target = node.userData.origPos || node.position;
        }

        // Tween graduale verso il nuovo layout
        gsapAnimatePos(node, target);
      });
    };
  }

  function gsapAnimatePos(node, target) {
    const start = node.position.clone();
    let p = 0;
    const duration = 60; // frame
    function step() {
      p++;
      const progress = p / duration;
      const ease = 0.5 - Math.cos(progress * Math.PI) / 2;
      node.position.lerpVectors(start, target, ease);
      if (p < duration) requestAnimationFrame(step);
    }
    step();
  }

  // ── RESIZE ────────────────────────────────────────────────────────────────
  function onWindowResize() {
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || (window.innerHeight - 56);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  }

  // ── ANIMATE LOOP ──────────────────────────────────────────────────────────
  function animate() {
    if (document.hidden || !container || container.offsetParent === null || container.clientWidth === 0) {
      setTimeout(() => requestAnimationFrame(animate), 400);
      return;
    }
    requestAnimationFrame(animate);

    if (controls) controls.update();

    if (particleSystem) {
      particleSystem.rotation.y += 0.0003;
      particleSystem.rotation.x += 0.0001;
    }

    // Camera fly-to interpolation
    if (isTransitioningCamera && targetCamPos && targetControlsTarget) {
      camera.position.lerp(targetCamPos, 0.06);
      if (controls) controls.target.lerp(targetControlsTarget, 0.06);

      if (camera.position.distanceTo(targetCamPos) < 1.0) {
        isTransitioningCamera = false;
      }
    }

    // Raycast hover check
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(nodeObjects);
    const tooltip = document.getElementById('cosmos-tooltip');

    if (intersects.length > 0) {
      const obj = intersects[0].object;
      if (hoveredNode !== obj) {
        if (hoveredNode) hoveredNode.scale.setScalar(hoveredNode.userData.isHub ? 9.0 : 4.0);
        hoveredNode = obj;
        hoveredNode.scale.setScalar(hoveredNode.userData.isHub ? 11.5 : 6.0);
      }

      if (tooltip) {
        tooltip.style.display = 'block';
        const u = obj.userData;
        tooltip.innerHTML = `
          <div style="font-weight:bold; color:#fff; font-size:12px;">${u.name}</div>
          <div style="font-size:10px; color:#00f0ff; margin-top:2px;">${u.type} · ${u.status}</div>
          <div style="font-size:9px; color:#94a3b8; margin-top:3px;">${u.notes || 'Click to focus'}</div>
        `;
      }
      container.style.cursor = 'pointer';
    } else {
      if (hoveredNode) {
        hoveredNode.scale.setScalar(hoveredNode.userData.isHub ? 9.0 : 4.0);
        hoveredNode = null;
      }
      if (tooltip) tooltip.style.display = 'none';
      container.style.cursor = 'default';
    }

    renderer.render(scene, camera);
  }

  // Inizializza non appena il DOM è pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
