/**
 * ═══════════════════════════════════════════════════════════════════════════════
 *  E.B.J. J.A.R.V.I.S. · FABLE 5.2 3D HOLOGRAPHIC STUDIO
 * ═══════════════════════════════════════════════════════════════════════════════
 *  Ispirato al sistema Fable 5.2 JARVIS di Zubair Trabzada (AI Workshop).
 *  Capacità integrate:
 *    1. Generazione 3D Robot Body / Mechanical Chassis
 *    2. Exploded Views Meccaniche (scomposizione cinematica parti e attuatori)
 *    3. Trasformazione da Planimetria 2D in Ambiente Architettonico 3D
 *    4. AI Landscaping (Cura del verde, prato, alberi e siepi procedurali)
 *    5. Voice-Controlled 3D Manipulation in Tempo Reale
 * ═══════════════════════════════════════════════════════════════════════════════
 */

(function () {
  'use strict';

  const Fable3D = {
    isOpen: false,
    currentMode: 'robot', // 'robot' | 'floorplan'
    isExploded: false,
    explodeProgress: 0,
    targetExplode: 0,
    isWireframe: false,
    hasLandscaping: false,
    isAutoRotating: true,

    // Three.js instances
    scene: null,
    camera: null,
    renderer: null,
    controls: null,
    animationId: null,

    // Scene Groups
    robotGroup: null,
    floorplanGroup: null,
    landscapingGroup: null,
    gridHelper: null,
    arcReactorLight: null,

    // Explodable Parts Registry: { mesh, origPos, explPos }
    explodableParts: [],

    init() {
      const container = document.getElementById('fable-3d-canvas-container');
      if (!container) return;

      // 1. Scene
      this.scene = new THREE.Scene();
      this.scene.background = new THREE.Color(0x020611);
      this.scene.fog = new THREE.FogExp2(0x020611, 0.035);

      // 2. Camera
      const width = container.clientWidth || 800;
      const height = container.clientHeight || 500;
      this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
      this.camera.position.set(0, 3.5, 9);

      // 3. Renderer
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.renderer.shadowMap.enabled = true;
      this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 1.1;
      container.innerHTML = '';
      container.appendChild(this.renderer.domElement);

      // 4. Controls
      if (typeof THREE.OrbitControls !== 'undefined') {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      } else if (typeof OrbitControls !== 'undefined') {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
      } else if (window.OrbitControls) {
        this.controls = new window.OrbitControls(this.camera, this.renderer.domElement);
      }
      if (this.controls) {
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.maxPolarAngle = Math.PI / 2 + 0.05;
        this.controls.minDistance = 2.5;
        this.controls.maxDistance = 25;
        this.controls.target.set(0, 2.0, 0);
      }

      // 5. Lighting
      this.setupLights();

      // 6. Grid & Holographic Floor
      this.setupHoloGrid();

      // 7. Build Robot Body
      this.buildRobotBody();

      // 8. Build Floorplan Environment
      this.buildFloorplanEnvironment();

      // 9. Window Resize Listener
      window.addEventListener('resize', () => this.onResize());

      // 10. Start Animation Loop
      this.animate();
    },

    setupLights() {
      // Soft ambient fill
      const ambient = new THREE.AmbientLight(0x0f172a, 1.2);
      this.scene.add(ambient);

      // Key light (Cyan Stark)
      const keyLight = new THREE.DirectionalLight(0x38bdf8, 2.5);
      keyLight.position.set(6, 10, 8);
      keyLight.castShadow = true;
      keyLight.shadow.mapSize.width = 1024;
      keyLight.shadow.mapSize.height = 1024;
      this.scene.add(keyLight);

      // Rim light (Warm Amber)
      const rimLight = new THREE.DirectionalLight(0xf59e0b, 1.8);
      rimLight.position.set(-8, 6, -6);
      this.scene.add(rimLight);

      // Overhead soft white fill
      const topLight = new THREE.PointLight(0xffffff, 1.0, 20);
      topLight.position.set(0, 8, 2);
      this.scene.add(topLight);

      // Pulsing Arc Reactor Point Light
      this.arcReactorLight = new THREE.PointLight(0x00f0ff, 3.5, 8);
      this.arcReactorLight.position.set(0, 2.6, 0.4);
      this.scene.add(this.arcReactorLight);
    },

    setupHoloGrid() {
      // Holographic floor grid
      const grid = new THREE.GridHelper(20, 20, 0x00f0ff, 0x1e293b);
      grid.position.y = 0;
      this.scene.add(grid);
      this.gridHelper = grid;

      // Concentric Radar Rings
      const ringGeo = new THREE.RingGeometry(2.5, 2.54, 48);
      const ringMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, side: THREE.DoubleSide, transparent: true, opacity: 0.35 });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = -Math.PI / 2;
      ringMesh.position.y = 0.01;
      this.scene.add(ringMesh);

      const ringOuterGeo = new THREE.RingGeometry(5.0, 5.06, 64);
      const ringOuterMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, side: THREE.DoubleSide, transparent: true, opacity: 0.2 });
      const ringOuterMesh = new THREE.Mesh(ringOuterGeo, ringOuterMat);
      ringOuterMesh.rotation.x = -Math.PI / 2;
      ringOuterMesh.position.y = 0.01;
      this.scene.add(ringOuterMesh);
    },

    // ── 1. ROBOT BODY & EXPLODED VIEW ENGINE ────────────────────────────────
    buildRobotBody() {
      this.robotGroup = new THREE.Group();
      this.scene.add(this.robotGroup);
      this.explodableParts = [];

      // Shared Materials
      const darkTitanium = new THREE.MeshStandardMaterial({
        color: 0x1e293b,
        metalness: 0.85,
        roughness: 0.25,
      });

      const armorGold = new THREE.MeshStandardMaterial({
        color: 0xd97706,
        metalness: 0.9,
        roughness: 0.2,
      });

      const armorCyan = new THREE.MeshStandardMaterial({
        color: 0x0284c7,
        metalness: 0.7,
        roughness: 0.3,
      });

      const chromeJoint = new THREE.MeshStandardMaterial({
        color: 0x94a3b8,
        metalness: 0.95,
        roughness: 0.1,
      });

      const emissiveCore = new THREE.MeshStandardMaterial({
        color: 0x00f0ff,
        emissive: 0x00f0ff,
        emissiveIntensity: 1.8,
        roughness: 0.1,
      });

      // Helper to register parts for Exploded View
      const registerPart = (mesh, explOffsetX, explOffsetY, explOffsetZ, name) => {
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        const origPos = mesh.position.clone();
        const explPos = origPos.clone().add(new THREE.Vector3(explOffsetX, explOffsetY, explOffsetZ));
        this.explodableParts.push({ mesh, origPos, explPos, name });
        this.robotGroup.add(mesh);
        return mesh;
      };

      // ── PELVIS & LOWER CHASSIS ──
      const pelvisGeo = new THREE.BoxGeometry(0.8, 0.4, 0.5);
      const pelvis = new THREE.Mesh(pelvisGeo, darkTitanium);
      pelvis.position.set(0, 1.4, 0);
      registerPart(pelvis, 0, -0.3, 0, "Pelvis Core");

      // ── SPINE & INTERNAL VERTEBRAE ──
      for (let i = 0; i < 3; i++) {
        const vertGeo = new THREE.CylinderGeometry(0.12, 0.14, 0.2, 16);
        const vert = new THREE.Mesh(vertGeo, chromeJoint);
        vert.position.set(0, 1.7 + i * 0.25, 0);
        registerPart(vert, 0, 0, 0, `Spine Segment ${i + 1}`);
      }

      // ── TORSO INNER FRAME ──
      const torsoFrameGeo = new THREE.BoxGeometry(1.0, 1.1, 0.6);
      const torsoFrame = new THREE.Mesh(torsoFrameGeo, darkTitanium);
      torsoFrame.position.set(0, 2.5, 0);
      registerPart(torsoFrame, 0, 0, 0, "Torso Main Frame");

      // ── ARC REACTOR CORE ──
      const reactorHousingGeo = new THREE.CylinderGeometry(0.24, 0.24, 0.15, 24);
      reactorHousingGeo.rotateX(Math.PI / 2);
      const reactorHousing = new THREE.Mesh(reactorHousingGeo, chromeJoint);
      reactorHousing.position.set(0, 2.6, 0.32);
      registerPart(reactorHousing, 0, 0, 1.6, "Arc Reactor Housing");

      const coreRingGeo = new THREE.TorusGeometry(0.16, 0.03, 16, 32);
      const coreRing = new THREE.Mesh(coreRingGeo, emissiveCore);
      coreRing.position.set(0, 2.6, 0.38);
      registerPart(coreRing, 0, 0, 2.0, "Arc Reactor Core MK-LV");

      // ── CHEST ARMOR PLATES (Expands Forward) ──
      const chestPlateLeftGeo = new THREE.BoxGeometry(0.48, 0.6, 0.15);
      const chestLeft = new THREE.Mesh(chestPlateLeftGeo, armorCyan);
      chestLeft.position.set(-0.3, 2.65, 0.38);
      registerPart(chestLeft, -0.6, 0.2, 1.8, "Chest Armor Left");

      const chestPlateRightGeo = new THREE.BoxGeometry(0.48, 0.6, 0.15);
      const chestRight = new THREE.Mesh(chestPlateRightGeo, armorCyan);
      chestRight.position.set(0.3, 2.65, 0.38);
      registerPart(chestRight, 0.6, 0.2, 1.8, "Chest Armor Right");

      // ── HEAD & VISOR HUD (Expands Upward) ──
      const headBaseGeo = new THREE.BoxGeometry(0.45, 0.5, 0.45);
      const headBase = new THREE.Mesh(headBaseGeo, darkTitanium);
      headBase.position.set(0, 3.4, 0);
      registerPart(headBase, 0, 1.2, 0, "Neural Cortex Head Base");

      const visorGeo = new THREE.BoxGeometry(0.4, 0.1, 0.1);
      const visor = new THREE.Mesh(visorGeo, emissiveCore);
      visor.position.set(0, 3.45, 0.23);
      registerPart(visor, 0, 1.5, 0.8, "Tactical Visor HUD");

      const helmetPlateGeo = new THREE.ConeGeometry(0.32, 0.25, 4);
      helmetPlateGeo.rotateY(Math.PI / 4);
      const helmetPlate = new THREE.Mesh(helmetPlateGeo, armorGold);
      helmetPlate.position.set(0, 3.72, 0);
      registerPart(helmetPlate, 0, 1.8, 0, "Helmet Crest Armor");

      // ── SHOULDERS & ARMS ──
      [-1, 1].forEach((side) => {
        const sidePrefix = side === -1 ? "Left" : "Right";

        // Shoulder joint
        const sJointGeo = new THREE.SphereGeometry(0.2, 16, 16);
        const sJoint = new THREE.Mesh(sJointGeo, chromeJoint);
        sJoint.position.set(side * 0.75, 2.9, 0);
        registerPart(sJoint, side * 0.8, 0.4, 0, `Shoulder Joint ${sidePrefix}`);

        // Shoulder Armor Pad
        const sArmorGeo = new THREE.CylinderGeometry(0.28, 0.32, 0.35, 16);
        const sArmor = new THREE.Mesh(sArmorGeo, armorGold);
        sArmor.position.set(side * 0.85, 3.0, 0);
        registerPart(sArmor, side * 1.8, 0.6, 0.3, `Shoulder Pauldron ${sidePrefix}`);

        // Bicep
        const bicepGeo = new THREE.CylinderGeometry(0.12, 0.14, 0.6, 16);
        const bicep = new THREE.Mesh(bicepGeo, darkTitanium);
        bicep.position.set(side * 0.8, 2.4, 0);
        registerPart(bicep, side * 1.2, 0, 0, `Bicep Actuator ${sidePrefix}`);

        // Forearm Gauntlet
        const forearmGeo = new THREE.BoxGeometry(0.25, 0.65, 0.25);
        const forearm = new THREE.Mesh(forearmGeo, armorCyan);
        forearm.position.set(side * 0.85, 1.7, 0);
        registerPart(forearm, side * 1.6, -0.2, 0.4, `Forearm Gauntlet ${sidePrefix}`);

        // Hand Repulsor
        const handGeo = new THREE.SphereGeometry(0.1, 12, 12);
        const hand = new THREE.Mesh(handGeo, emissiveCore);
        hand.position.set(side * 0.85, 1.3, 0);
        registerPart(hand, side * 2.0, -0.4, 0.5, `Hand Repulsor ${sidePrefix}`);
      });

      // ── LEGS & HYDRAULICS ──
      [-1, 1].forEach((side) => {
        const sidePrefix = side === -1 ? "Left" : "Right";

        // Hip Ball Joint
        const hipGeo = new THREE.SphereGeometry(0.18, 16, 16);
        const hip = new THREE.Mesh(hipGeo, chromeJoint);
        hip.position.set(side * 0.35, 1.2, 0);
        registerPart(hip, side * 0.4, -0.2, 0, `Hip Joint ${sidePrefix}`);

        // Thigh
        const thighGeo = new THREE.BoxGeometry(0.3, 0.8, 0.3);
        const thigh = new THREE.Mesh(thighGeo, armorCyan);
        thigh.position.set(side * 0.35, 0.75, 0);
        registerPart(thigh, side * 0.8, -0.2, 0.3, `Thigh Armor ${sidePrefix}`);

        // Shin / Hydraulic Calves
        const shinGeo = new THREE.CylinderGeometry(0.12, 0.15, 0.8, 16);
        const shin = new THREE.Mesh(shinGeo, darkTitanium);
        shin.position.set(side * 0.35, 0.05, 0);
        registerPart(shin, side * 0.8, -0.4, 0, `Hydraulic Shin ${sidePrefix}`);

        // Stabilizer Foot
        const footGeo = new THREE.BoxGeometry(0.28, 0.12, 0.55);
        const foot = new THREE.Mesh(footGeo, armorGold);
        foot.position.set(side * 0.35, -0.35, 0.1);
        registerPart(foot, side * 1.0, -0.6, 0.4, `Stabilizer Foot ${sidePrefix}`);
      });
    },

    // ── 2. 2D FLOOR PLAN TO 3D ENVIRONMENT TRANSFORMATION ───────────────────
    buildFloorplanEnvironment() {
      this.floorplanGroup = new THREE.Group();
      this.floorplanGroup.visible = false;
      this.scene.add(this.floorplanGroup);

      // Floor Material (Polished Hardwood / Slate)
      const floorMat = new THREE.MeshStandardMaterial({
        color: 0x334155,
        roughness: 0.3,
        metalness: 0.1,
      });

      const wallMat = new THREE.MeshStandardMaterial({
        color: 0xe2e8f0,
        roughness: 0.6,
        metalness: 0.05,
      });

      const glassMat = new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.45,
        roughness: 0.1,
        metalness: 0.9,
      });

      const deskMat = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        roughness: 0.2,
        metalness: 0.7,
      });

      // ── Main Floor Slab (10x8 meters) ──
      const floorGeo = new THREE.BoxGeometry(10, 0.2, 8);
      const floorMesh = new THREE.Mesh(floorGeo, floorMat);
      floorMesh.position.set(0, -0.1, 0);
      floorMesh.receiveShadow = true;
      this.floorplanGroup.add(floorMesh);

      // ── Perimeter Walls (Extruded from 2D coordinates) ──
      const wallThickness = 0.2;
      const wallHeight = 2.6;

      // Back wall (with large window cutout)
      const backWallGeo = new THREE.BoxGeometry(10, wallHeight, wallThickness);
      const backWall = new THREE.Mesh(backWallGeo, wallMat);
      backWall.position.set(0, wallHeight / 2, -4);
      backWall.castShadow = true;
      this.floorplanGroup.add(backWall);

      // Back Panoramic Glass Window
      const winGeo = new THREE.BoxGeometry(5.0, 1.6, 0.08);
      const winMesh = new THREE.Mesh(winGeo, glassMat);
      winMesh.position.set(0, 1.5, -3.95);
      this.floorplanGroup.add(winMesh);

      // Left Wall
      const leftWallGeo = new THREE.BoxGeometry(wallThickness, wallHeight, 8);
      const leftWall = new THREE.Mesh(leftWallGeo, wallMat);
      leftWall.position.set(-5, wallHeight / 2, 0);
      leftWall.castShadow = true;
      this.floorplanGroup.add(leftWall);

      // Right Wall
      const rightWallGeo = new THREE.BoxGeometry(wallThickness, wallHeight, 8);
      const rightWall = new THREE.Mesh(rightWallGeo, wallMat);
      rightWall.position.set(5, wallHeight / 2, 0);
      rightWall.castShadow = true;
      this.floorplanGroup.add(rightWall);

      // Interior Partition (Separating Office & Logistics Hub)
      const partitionGeo = new THREE.BoxGeometry(wallThickness, wallHeight, 4.5);
      const partition = new THREE.Mesh(partitionGeo, wallMat);
      partition.position.set(0.5, wallHeight / 2, -1.75);
      partition.castShadow = true;
      this.floorplanGroup.add(partition);

      // ── FURNITURE PLACEMENT (Badr Stark Executive Office) ──
      // Executive Glass Desk
      const deskTopGeo = new THREE.BoxGeometry(2.4, 0.08, 1.2);
      const deskTop = new THREE.Mesh(deskTopGeo, glassMat);
      deskTop.position.set(-2.5, 0.8, -2.0);
      this.floorplanGroup.add(deskTop);

      // Desk Legs
      [-1, 1].forEach((dx) => {
        const legGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.8, 16);
        const leg = new THREE.Mesh(legGeo, deskMat);
        leg.position.set(-2.5 + dx * 1.0, 0.4, -2.0);
        this.floorplanGroup.add(leg);
      });

      // Triple Holographic Displays on Desk
      [-0.6, 0, 0.6].forEach((mx, idx) => {
        const monGeo = new THREE.BoxGeometry(0.55, 0.35, 0.02);
        const monMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, wireframe: idx !== 1 });
        const mon = new THREE.Mesh(monGeo, monMat);
        mon.position.set(-2.5 + mx, 1.15, -2.1);
        mon.rotation.y = (idx - 1) * -0.25;
        this.floorplanGroup.add(mon);
      });

      // Server Rack Hub (with pulsing LEDs)
      const rackGeo = new THREE.BoxGeometry(0.8, 2.0, 0.8);
      const rack = new THREE.Mesh(rackGeo, deskMat);
      rack.position.set(3.8, 1.0, -3.0);
      rack.castShadow = true;
      this.floorplanGroup.add(rack);

      for (let l = 0; l < 6; l++) {
        const ledGeo = new THREE.BoxGeometry(0.6, 0.04, 0.02);
        const ledMat = new THREE.MeshBasicMaterial({ color: l % 2 === 0 ? 0x00ff9f : 0x00f0ff });
        const led = new THREE.Mesh(ledGeo, ledMat);
        led.position.set(3.8, 0.3 + l * 0.28, -2.59);
        this.floorplanGroup.add(led);
      }

      // Logistics Crates (BadrExpress / SELEZIONE inventory)
      const crateMat = new THREE.MeshStandardMaterial({ color: 0xb45309, roughness: 0.8 });
      for (let c = 0; c < 3; c++) {
        const crateGeo = new THREE.BoxGeometry(0.7, 0.6, 0.7);
        const crate = new THREE.Mesh(crateGeo, crateMat);
        crate.position.set(2.6 + (c % 2) * 0.8, 0.3 + Math.floor(c / 2) * 0.6, 1.5 + (c % 2) * 0.3);
        crate.castShadow = true;
        this.floorplanGroup.add(crate);
      }
    },

    // ── 3. AI LANDSCAPING & CURA DEL VERDE PROCEDURALE ──────────────────────
    toggleLandscaping() {
      this.hasLandscaping = !this.hasLandscaping;
      const btn = document.getElementById('fable-btn-landscape');
      if (btn) btn.classList.toggle('active', this.hasLandscaping);

      if (this.landscapingGroup) {
        this.scene.remove(this.landscapingGroup);
        this.landscapingGroup = null;
      }

      if (this.hasLandscaping) {
        this.landscapingGroup = new THREE.Group();
        this.scene.add(this.landscapingGroup);

        // Lawn Grass Surface
        const lawnGeo = new THREE.BoxGeometry(18, 0.05, 16);
        const lawnMat = new THREE.MeshStandardMaterial({ color: 0x15803d, roughness: 0.9 });
        const lawn = new THREE.Mesh(lawnGeo, lawnMat);
        lawn.position.set(0, -0.15, 0);
        lawn.receiveShadow = true;
        this.landscapingGroup.add(lawn);

        // Procedural Trees (Trunk + Foliage Cones)
        const treePositions = [
          [-7, 0, -6], [-6, 0, 5], [7, 0, -5], [6, 0, 5], [-8, 0, 0], [8, 0, 1]
        ];

        const trunkMat = new THREE.MeshStandardMaterial({ color: 0x78350f, roughness: 0.9 });
        const foliageMat = new THREE.MeshStandardMaterial({ color: 0x16a34a, roughness: 0.7 });

        treePositions.forEach(([tx, ty, tz]) => {
          const trunkGeo = new THREE.CylinderGeometry(0.15, 0.22, 1.5, 8);
          const trunk = new THREE.Mesh(trunkGeo, trunkMat);
          trunk.position.set(tx, 0.75, tz);
          trunk.castShadow = true;
          this.landscapingGroup.add(trunk);

          for (let f = 0; f < 3; f++) {
            const coneGeo = new THREE.ConeGeometry(1.2 - f * 0.25, 1.4, 8);
            const cone = new THREE.Mesh(coneGeo, foliageMat);
            cone.position.set(tx, 1.8 + f * 0.8, tz);
            cone.castShadow = true;
            this.landscapingGroup.add(cone);
          }
        });

        // Procedural Trimmed Hedges (Alloro / Lauroceraso perimetrale)
        const hedgeMat = new THREE.MeshStandardMaterial({ color: 0x14532d, roughness: 0.8 });
        for (let hx = -6; hx <= 6; hx += 1.8) {
          const hedgeGeo = new THREE.BoxGeometry(1.6, 0.9, 0.6);
          const hedge = new THREE.Mesh(hedgeGeo, hedgeMat);
          hedge.position.set(hx, 0.45, 6.5);
          hedge.castShadow = true;
          this.landscapingGroup.add(hedge);
        }

        if (window.playUiClick) window.playUiClick();
      }
    },

    // ── 4. ANIMATION LOOP & EXPLODED LERP ────────────────────────────────────
    animate() {
      this.animationId = requestAnimationFrame(() => this.animate());

      // Smooth Exploded View Interpolation
      const diff = this.targetExplode - this.explodeProgress;
      if (Math.abs(diff) > 0.001) {
        this.explodeProgress += diff * 0.12;
        this.applyExplodedPositions(this.explodeProgress);
      }

      // Pulsing Arc Reactor Core Light
      if (this.arcReactorLight) {
        const time = Date.now() * 0.004;
        this.arcReactorLight.intensity = 3.0 + Math.sin(time) * 1.2;
      }

      // Auto Rotation
      if (this.isAutoRotating && this.controls && !this.controls.state) {
        if (this.currentMode === 'robot' && this.robotGroup) {
          this.robotGroup.rotation.y += 0.005;
        } else if (this.currentMode === 'floorplan' && this.floorplanGroup) {
          this.floorplanGroup.rotation.y += 0.003;
        }
      }

      if (this.controls) this.controls.update();
      if (this.renderer && this.scene && this.camera) {
        this.renderer.render(this.scene, this.camera);
      }
    },

    applyExplodedPositions(t) {
      this.explodableParts.forEach(({ mesh, origPos, explPos }) => {
        mesh.position.lerpVectors(origPos, explPos, t);
      });
    },

    // ── 5. PUBLIC UI & VOICE CONTROLS ───────────────────────────────────────
    toggleExplodedView() {
      this.isExploded = !this.isExploded;
      this.targetExplode = this.isExploded ? 1.0 : 0.0;

      const btn = document.getElementById('fable-btn-explode');
      if (btn) btn.classList.toggle('active', this.isExploded);

      const label = document.getElementById('fable-status-label');
      if (label) {
        label.textContent = this.isExploded
          ? 'EXPLODED VIEW ACTIVE · DISASSEMBLY NORMAL EXPANSION'
          : 'ASSEMBLED STATE · NOMINAL INTEGRITY';
        label.style.color = this.isExploded ? '#f59e0b' : '#00f0ff';
      }
    },

    setMode(mode) {
      this.currentMode = mode;
      if (mode === 'robot') {
        if (this.robotGroup) this.robotGroup.visible = true;
        if (this.floorplanGroup) this.floorplanGroup.visible = false;
        if (this.camera) this.camera.position.set(0, 3.5, 9);
        if (this.controls) this.controls.target.set(0, 2.0, 0);
      } else {
        if (this.robotGroup) this.robotGroup.visible = false;
        if (this.floorplanGroup) this.floorplanGroup.visible = true;
        if (this.camera) this.camera.position.set(8, 9, 12);
        if (this.controls) this.controls.target.set(0, 1.2, 0);
      }

      document.querySelectorAll('.fable-mode-tab').forEach((tab) => {
        tab.classList.toggle('active', tab.getAttribute('data-mode') === mode);
      });

      const label = document.getElementById('fable-title-mode');
      if (label) {
        label.textContent = mode === 'robot'
          ? 'EBJ MARK ROBOT BODY · PARAMETRIC MECHANICAL CHASSIS'
          : '2D BLUEPRINT TO 3D ARCHITECTURAL ENVIRONMENT';
      }
    },

    toggleWireframe() {
      this.isWireframe = !this.isWireframe;
      const targetGroup = this.currentMode === 'robot' ? this.robotGroup : this.floorplanGroup;
      if (targetGroup) {
        targetGroup.traverse((child) => {
          if (child.isMesh && child.material) {
            child.material.wireframe = this.isWireframe;
          }
        });
      }
      const btn = document.getElementById('fable-btn-wireframe');
      if (btn) btn.classList.toggle('active', this.isWireframe);
    },

    toggleAutoRotate() {
      this.isAutoRotating = !this.isAutoRotating;
      const btn = document.getElementById('fable-btn-rotate');
      if (btn) btn.classList.toggle('active', this.isAutoRotating);
    },

    openStage(defaultMode = 'robot') {
      const modal = document.getElementById('fable-3d-stage-modal');
      if (!modal) return;
      modal.style.display = 'flex';
      this.isOpen = true;

      if (!this.scene) {
        this.init();
      } else {
        this.onResize();
      }

      this.setMode(defaultMode);
      if (window.playUiClick) window.playUiClick();
    },

    closeStage() {
      const modal = document.getElementById('fable-3d-stage-modal');
      if (modal) modal.style.display = 'none';
      this.isOpen = false;
    },

    onResize() {
      const container = document.getElementById('fable-3d-canvas-container');
      if (!container || !this.camera || !this.renderer) return;
      const width = container.clientWidth || 800;
      const height = container.clientHeight || 500;
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(width, height);
    },

    exportBlenderScript() {
      const scriptCode = `# ==============================================================================
# E.B.J. JARVIS · FABLE 5.2 ROBOT BODY & 3D ENVIRONMENT EXPORTER FOR BLENDER 5.2
# ==============================================================================
import bpy
import math

bpy.ops.wm.read_factory_settings(use_empty=True)

# Create Torso Main Frame
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 2.5))
torso = bpy.context.active_object
torso.name = "EBJ_Torso_Frame"

# Create Arc Reactor Core
bpy.ops.mesh.primitive_cylinder_add(radius=0.24, depth=0.15, location=(0, -0.32, 2.6))
reactor = bpy.context.active_object
reactor.rotation_euler = (math.pi/2, 0, 0)
reactor.name = "EBJ_Arc_Reactor_MK_LV"

# Create Head Unit
bpy.ops.mesh.primitive_cube_add(size=0.45, location=(0, 0, 3.4))
head = bpy.context.active_object
head.name = "EBJ_Neural_Cortex_Head"

print("[EBJ Fable 5.2] 3D Model Procedural Assembly Generated Successfully.")
`;

      const blob = new Blob([scriptCode], { type: 'text/x-python' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `ebj_fable52_${this.currentMode}_blender.py`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      if (typeof window.showToastNotification === 'function') {
        window.showToastNotification("Script Python Blender 5.2 scaricato con successo!");
      }
    }
  };

  // Expose to window
  window.Fable3D = Fable3D;

  // Auto initialize on DOMContentLoaded if modal is present
  document.addEventListener('DOMContentLoaded', () => {
    // Stage triggers
    const openBtn = document.getElementById('btn-open-fable-3d');
    if (openBtn) {
      openBtn.addEventListener('click', () => Fable3D.openStage('robot'));
    }
  });
})();
