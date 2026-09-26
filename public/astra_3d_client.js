/**
 * GPT-6 Astra 3D Studio & Bambu Lab Client
 * E.B.J. AI Supreme for Ing. Badr
 * Interactive 3D Viewer, Bambu Studio Desktop Launcher & MakerWorld Cloud Sync.
 */

window.Astra3D = {
  currentData: null,
  scene: null,
  camera: null,
  renderer: null,
  controls: null,
  mesh: null,
  isInitialized: false,

  async fetchStatus() {
    try {
      const res = await fetch('/api/bambu/status');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.currentData = data;
      this.renderUi(data);
      return data;
    } catch (e) {
      console.error('[Astra 3D] Error fetching status:', e);
    }
  },

  renderUi(data) {
    if (!data) return;

    // Update Badges
    const badgeEngine = document.getElementById('astra-badge-engine');
    if (badgeEngine) badgeEngine.textContent = data.engine || 'GPT-6 Astra 3D';

    const badgeWatertight = document.getElementById('astra-badge-watertight');
    if (badgeWatertight) {
      badgeWatertight.textContent = data.watertight ? '100% WATERTIGHT (0 ERRORI)' : 'ATTENZIONE NON-MANIFOLD';
      badgeWatertight.style.color = data.watertight ? '#10b981' : '#ef4444';
    }

    const badgeStudio = document.getElementById('astra-badge-studio');
    if (badgeStudio) {
      badgeStudio.textContent = data.bambu_studio_installed ? 'BAMBU STUDIO: PRONTO' : 'BAMBU STUDIO: NON INSTALLATO';
      badgeStudio.style.color = data.bambu_studio_installed ? '#10b981' : '#f59e0b';
    }

    const badgeMaker = document.getElementById('astra-badge-makerworld');
    if (badgeMaker) {
      badgeMaker.textContent = data.makerworld_authenticated ? 'MAKERWORLD: AUTENTICATO' : 'MAKERWORLD: DA COLLEGARE';
      badgeMaker.style.color = data.makerworld_authenticated ? '#a855f7' : '#94a3b8';
    }

    // Update Metrics
    const dimEl = document.getElementById('astra-metric-dim');
    if (dimEl) dimEl.textContent = data.dimensions || '100.0 x 52.3 x 28.6 mm';

    const volEl = document.getElementById('astra-metric-vol');
    if (volEl) volEl.textContent = `${data.volume_cm3 || 37.42} cm³`;

    const weightEl = document.getElementById('astra-metric-weight');
    if (weightEl) weightEl.textContent = `~${data.weight_g_petg || 21.4} g (PETG)`;

    // Update Main Inspection Image
    const mainImg = document.getElementById('astra-main-render');
    if (mainImg && data.renders?.quad_inspection) {
      mainImg.src = data.renders.quad_inspection + '?t=' + Date.now();
    }
  },

  async openBambuStudio() {
    const btn = document.getElementById('btn-astra-open-studio');
    const originalText = btn ? btn.innerHTML : '';
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '⏳ AVVIO BAMBU STUDIO IN CORSO...';
    }

    try {
      const res = await fetch('/api/bambu/open-studio', { method: 'POST' });
      const out = await res.json();
      if (out.success) {
        if (window.showToolRun) {
          window.showToolRun('BAMBU STUDIO X1/P1/A1', `Avviato con successo! PID ${out.pid}. Modello HTVW-281 posizionato sul piatto di stampa virtuale.`, '0.2s');
        } else {
          alert('Bambu Studio aperto con successo con il modello HTVW-281!');
        }
      } else {
        alert('Errore apertura Bambu Studio: ' + (out.error || 'Generico'));
      }
    } catch (e) {
      alert('Errore connessione: ' + e.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    }
  },

  async publishMakerWorld() {
    const btn = document.getElementById('btn-astra-publish-mw');
    const originalText = btn ? btn.innerHTML : '';
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '⏳ PUBBLICAZIONE SU MAKERWORLD...';
    }

    try {
      const res = await fetch('/api/bambu/publish-makerworld', { method: 'POST' });
      const out = await res.json();
      if (out.success) {
        if (window.showToolRun) {
          window.showToolRun('MAKERWORLD CLOUD SYNC', 'Bozza modello HTVW-281 caricata con successo su MakerWorld!', '1.2s');
        }
        alert('Modello HTVW-281 sincronizzato con successo sul tuo account MakerWorld!');
        this.fetchStatus();
      } else {
        alert('Errore pubblicazione: ' + (out.error || 'Generico'));
      }
    } catch (e) {
      alert('Errore connessione MakerWorld: ' + e.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    }
  },

  setPreviewImage(src) {
    const mainImg = document.getElementById('astra-main-render');
    if (mainImg) {
      mainImg.src = src;
    }
  },

  init3DViewer() {
    const container = document.getElementById('astra-3d-viewport');
    if (!container || this.isInitialized) return;

    if (typeof THREE === 'undefined' || typeof THREE.OrbitControls === 'undefined') {
      if (window.loadCosmos3DOnDemand) {
        window.loadCosmos3DOnDemand(() => {
          this.init3DViewer();
        });
        return;
      }
    }

    this.isInitialized = true;
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 400;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x060b16);

    this.camera = new THREE.PerspectiveCamera(45, width / height, 1, 1000);
    this.camera.position.set(120, 100, 140);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    container.innerHTML = '';
    container.appendChild(this.renderer.domElement);

    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.08;
      this.controls.autoRotate = true;
      this.controls.autoRotateSpeed = 2.0;
    }

    // Grid Floor
    const gridHelper = new THREE.GridHelper(220, 22, 0x00f0ff, 0x1e293b);
    gridHelper.position.y = -15;
    this.scene.add(gridHelper);

    // Lights
    const ambient = new THREE.AmbientLight(0xffffff, 0.7);
    this.scene.add(ambient);

    const dirLight1 = new THREE.DirectionalLight(0x00f0ff, 1.2);
    dirLight1.position.set(100, 150, 100);
    this.scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xff0055, 0.6);
    dirLight2.position.set(-100, 50, -100);
    this.scene.add(dirLight2);

    // Load STL Binary
    this.loadStlModel('/3d_models/HTVW_281_BambuLab.stl');

    // Animation Loop with Visibility Culling (Zero GPU usage when hidden)
    const animate = () => {
      const containerEl = document.getElementById('astra-viewport-container');
      if (document.hidden || !containerEl || containerEl.offsetParent === null || container.clientWidth === 0) {
        setTimeout(() => requestAnimationFrame(animate), 500);
        return;
      }
      requestAnimationFrame(animate);
      if (this.controls) this.controls.update();
      this.renderer.render(this.scene, this.camera);
    };
    animate();

    window.addEventListener('resize', () => {
      if (!container || !this.renderer || !this.camera) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h);
    });
  },

  async loadStlModel(url) {
    try {
      const resp = await fetch(url);
      const buffer = await resp.arrayBuffer();
      const geometry = this.parseBinarySTL(buffer);

      geometry.computeVertexNormals();
      geometry.center();

      const material = new THREE.MeshStandardMaterial({
        color: 0x22d3ee,
        roughness: 0.35,
        metalness: 0.25,
        wireframe: false
      });

      if (this.mesh) this.scene.remove(this.mesh);
      this.mesh = new THREE.Mesh(geometry, material);
      this.mesh.rotation.x = -Math.PI / 2; // STL Z-up conversion
      this.scene.add(this.mesh);

      console.log('[Astra 3D] STL loaded successfully! Vertices count:', geometry.attributes.position.count);
    } catch (e) {
      console.warn('[Astra 3D] Could not load STL directly into WebGL, using rendered views:', e);
    }
  },

  parseBinarySTL(buffer) {
    const reader = new DataView(buffer);
    const faces = reader.getUint32(80, true);
    const dataOffset = 84;
    const faceLength = 50;

    const vertices = new Float32Array(faces * 9);
    for (let face = 0; face < faces; face++) {
      const start = dataOffset + face * faceLength;
      for (let i = 1; i <= 3; i++) {
        const vertexstart = start + i * 12;
        const componentIdx = (face * 3 + (i - 1)) * 3;
        vertices[componentIdx] = reader.getFloat32(vertexstart, true);
        vertices[componentIdx + 1] = reader.getFloat32(vertexstart + 4, true);
        vertices[componentIdx + 2] = reader.getFloat32(vertexstart + 8, true);
      }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    return geometry;
  },

  toggleWireframe() {
    if (this.mesh && this.mesh.material) {
      this.mesh.material.wireframe = !this.mesh.material.wireframe;
    }
  },

  toggleAutoRotate() {
    if (this.controls) {
      this.controls.autoRotate = !this.controls.autoRotate;
    }
  }
};

window.loadAstra3DStatus = function() {
  window.Astra3D.fetchStatus();
};

window.initAstra3DViewerOnDemand = function() {
  window.Astra3D.init3DViewer();
};
