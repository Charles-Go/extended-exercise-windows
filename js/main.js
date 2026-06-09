// ---------------------------------------------------------------------------
// Navigateur 3D — 14 rue du Cherche-Midi
// ---------------------------------------------------------------------------
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { APT, ROOMS, WALLS, TOUR, roomAt, roomCenter } from "./data.js";
import { makeMaterials } from "./textures.js";
import { buildApartment } from "./builder.js";
import { buildFurniture, buildLighting } from "./furniture.js";

// --- scène -------------------------------------------------------------------
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
document.getElementById("viewport").appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(68, innerWidth / innerHeight, 0.05, 200);

const M = makeMaterials();
const { colliders, ceilGroup } = buildApartment(scene, M);
buildFurniture(scene, M, colliders);
const { lamps } = buildLighting(scene, M);

// environnement IBL discret pour les métaux, miroirs et vitrages
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.traverse(o => { if (o.isMesh && o.material && "envMapIntensity" in o.material) o.material.envMapIntensity = 0.35; });

// --- éclairage ----------------------------------------------------------------
const hemi = new THREE.HemisphereLight(0xdfeaff, 0x8a7a60, 0.85);
scene.add(hemi);
const amb = new THREE.AmbientLight(0xfff4e2, 0.55);
scene.add(amb);
const sun = new THREE.DirectionalLight(0xfff2dd, 2.6);
sun.position.set(6, 14, -12); // sud = rue (z négatif)
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -16; sun.shadow.camera.right = 16;
sun.shadow.camera.top = 16; sun.shadow.camera.bottom = -16;
sun.shadow.bias = -0.0004;
const sunTarget = new THREE.Object3D();
sunTarget.position.set(9.4, 0, 5.2);
scene.add(sunTarget); sun.target = sunTarget;
scene.add(sun);

const lampLights = [];
for (const l of lamps) {
  const pl = new THREE.PointLight(0xffd9a0, 0, l.dist, 1.8);
  pl.position.set(l.x, l.y, l.z);
  pl.userData.base = l.intensity;
  scene.add(pl);
  lampLights.push(pl);
}

let night = false;
function applyDayNight() {
  if (night) {
    scene.background = new THREE.Color(0x0c1020);
    scene.fog = new THREE.Fog(0x0c1020, 30, 90);
    hemi.intensity = 0.12; amb.intensity = 0.06; sun.intensity = 0.0;
    for (const pl of lampLights) pl.intensity = pl.userData.base;
    renderer.toneMappingExposure = 1.15;
  } else {
    scene.background = new THREE.Color(0xbcd2e0);
    scene.fog = new THREE.Fog(0xbcd2e0, 40, 120);
    hemi.intensity = 1.05; amb.intensity = 0.55; sun.intensity = 2.6;
    for (const pl of lampLights) pl.intensity = pl.userData.base * 0.45;
    renderer.toneMappingExposure = 1.12;
  }
}
applyDayNight();

// --- modes de navigation ---------------------------------------------------------
const EYE = 1.62, RADIUS = 0.26;
let mode = "walk"; // walk | orbit | plan
const player = { x: 2.3, z: 8.6, yaw: 0, pitch: 0 }; // départ : entrée, regard vers l'enfilade
const keys = {};

const orbit = new OrbitControls(camera, renderer.domElement);
orbit.target.set(APT.width / 2, 0, APT.depth / 2);
orbit.maxPolarAngle = Math.PI / 2.05;
orbit.enabled = false;

function setMode(m) {
  mode = m;
  document.querySelectorAll("#modes button").forEach(b => b.classList.toggle("active", b.dataset.mode === m));
  orbit.enabled = (m === "orbit");
  ceilGroup.visible = (m === "walk");
  if (m === "orbit") {
    camera.position.set(APT.width / 2 - 9, 13, APT.depth / 2 + 11);
    orbit.target.set(APT.width / 2, 0, APT.depth / 2);
    camera.fov = 50;
  } else if (m === "plan") {
    camera.fov = 38;
  } else {
    camera.fov = 68;
    document.getElementById("viewport").focus?.();
  }
  camera.updateProjectionMatrix();
  document.getElementById("hint").textContent =
    m === "walk" ? "Cliquez sur la vue pour capturer la souris — ZQSD/WASD ou flèches pour marcher, Maj pour courir." :
    m === "orbit" ? "Glisser : orbiter — molette : zoom — clic droit : déplacer." :
    "Vue en plan. Cliquez une pièce de la maquette ou de la mini-carte pour vous y téléporter.";
}

// pointer lock pour la marche
const vp = renderer.domElement;
vp.addEventListener("click", (e) => {
  if (mode === "walk" && document.pointerLockElement !== vp) vp.requestPointerLock();
  else if (mode === "plan") teleportFromScreen(e);
});
document.addEventListener("mousemove", (e) => {
  if (mode === "walk" && document.pointerLockElement === vp) {
    player.yaw -= e.movementX * 0.0023;
    player.pitch = Math.max(-1.45, Math.min(1.45, player.pitch - e.movementY * 0.0023));
  }
});
addEventListener("keydown", (e) => {
  keys[e.code] = true;
  if (e.code === "KeyV") setMode(mode === "walk" ? "orbit" : mode === "orbit" ? "plan" : "walk");
  if (e.code === "KeyN") { night = !night; applyDayNight(); document.getElementById("dayNight").textContent = night ? "☀ Jour" : "🌙 Nuit"; }
  if (e.code === "KeyT") toggleTour();
  if (e.code === "KeyH") document.getElementById("help").classList.toggle("hidden");
});
addEventListener("keyup", (e) => keys[e.code] = false);

function collide(nx, nz) {
  for (const c of colliders) {
    const cx = Math.max(c.x0, Math.min(nx, c.x1));
    const cz = Math.max(c.z0, Math.min(nz, c.z1));
    const dx = nx - cx, dz = nz - cz;
    if (dx * dx + dz * dz < RADIUS * RADIUS) return true;
  }
  return false;
}

// point libre le plus proche (évite d'atterrir dans un meuble)
function freeSpot(x, z) {
  if (!collide(x, z)) return { x, z };
  for (let r = 0.25; r <= 2.6; r += 0.25)
    for (let a = 0; a < Math.PI * 2; a += Math.PI / 10) {
      const nx = x + Math.cos(a) * r, nz = z + Math.sin(a) * r;
      if (!collide(nx, nz) && roomAt(nx, nz)) return { x: nx, z: nz };
    }
  return { x, z };
}

function walkUpdate(dt) {
  const run = keys["ShiftLeft"] || keys["ShiftRight"] ? 2.2 : 1;
  const sp = 2.1 * run * dt;
  let fx = 0, fz = 0;
  const f = [(keys["KeyW"] || keys["KeyZ"] || keys["ArrowUp"]) ? 1 : 0, (keys["KeyS"] || keys["ArrowDown"]) ? 1 : 0,
             (keys["KeyA"] || keys["KeyQ"] || keys["ArrowLeft"]) ? 1 : 0, (keys["KeyD"] || keys["ArrowRight"]) ? 1 : 0];
  const sin = Math.sin(player.yaw), cos = Math.cos(player.yaw);
  fx += (f[0] - f[1]) * -sin + (f[3] - f[2]) * cos;
  fz += (f[0] - f[1]) * -cos + (f[3] - f[2]) * -sin;
  const len = Math.hypot(fx, fz);
  if (len > 0.001) {
    fx = fx / len * sp; fz = fz / len * sp;
    if (!collide(player.x + fx, player.z)) player.x += fx;
    if (!collide(player.x, player.z + fz)) player.z += fz;
  }
  camera.position.set(player.x, EYE, player.z);
  camera.rotation.order = "YXZ";
  camera.rotation.y = player.yaw;
  camera.rotation.x = player.pitch;
}

// --- vue plan + téléportation -------------------------------------------------------
const ray = new THREE.Raycaster();
function teleportFromScreen(e) {
  const r = vp.getBoundingClientRect();
  const p = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(p, camera);
  const t = -ray.ray.origin.y / ray.ray.direction.y;
  if (t > 0) {
    const hit = ray.ray.origin.clone().addScaledVector(ray.ray.direction, t);
    if (roomAt(hit.x, hit.z)) { const sp = freeSpot(hit.x, hit.z); player.x = sp.x; player.z = sp.z; setMode("walk"); }
  }
}

// --- visite guidée -----------------------------------------------------------------
let tour = null;
function toggleTour() {
  if (tour) { tour = null; document.getElementById("tourBtn").classList.remove("active"); return; }
  document.getElementById("tourBtn").classList.add("active");
  tour = { idx: -1, t: 1, from: { ...player }, to: { ...player }, hold: 0 };
  nextTourStop();
}
function nextTourStop() {
  tour.idx = (tour.idx + 1) % TOUR.length;
  const room = ROOMS.find(r => r.id === TOUR[tour.idx]);
  const c = roomCenter(room);
  const spot = freeSpot(c.x, c.y);
  tour.from = { x: player.x, z: player.z, yaw: player.yaw };
  tour.to = { x: spot.x, z: spot.z, yaw: player.yaw + Math.PI * 0.6 };
  tour.t = 0; tour.hold = 0;
  showRoomCard(room, true);
}
function tourUpdate(dt) {
  if (tour.t < 1) {
    tour.t = Math.min(1, tour.t + dt / 3.2);
    const e = tour.t < 0.5 ? 2 * tour.t * tour.t : 1 - Math.pow(-2 * tour.t + 2, 2) / 2;
    player.x = tour.from.x + (tour.to.x - tour.from.x) * e;
    player.z = tour.from.z + (tour.to.z - tour.from.z) * e;
    player.yaw = tour.from.yaw + (tour.to.yaw - tour.from.yaw) * e;
  } else {
    player.yaw += dt * 0.28; // panoramique
    tour.hold += dt;
    if (tour.hold > 5) nextTourStop();
  }
  camera.position.set(player.x, EYE, player.z);
  camera.rotation.order = "YXZ";
  camera.rotation.y = player.yaw;
  camera.rotation.x = -0.03;
}

function goToRoom(id) {
  if (tour) toggleTour();
  const room = ROOMS.find(r => r.id === id);
  const c = roomCenter(room);
  const spot = freeSpot(c.x, c.y);
  player.x = spot.x; player.z = spot.z;
  if (mode !== "walk") setMode("walk");
  showRoomCard(room, true);
}

// --- interface ------------------------------------------------------------------------
const roomList = document.getElementById("roomList");
for (const r of ROOMS) {
  const li = document.createElement("li");
  li.innerHTML = `<b>${r.name}</b><span>${r.area}</span>`;
  li.addEventListener("click", () => goToRoom(r.id));
  li.dataset.id = r.id;
  roomList.appendChild(li);
}

let cardTimer = null;
function showRoomCard(r, sticky = false) {
  const el = document.getElementById("roomCard");
  el.innerHTML = `<h2>${r.name}</h2>
    <div class="meta">${r.area} &nbsp;·&nbsp; HSP ${(r.hsp / 100).toFixed(2).replace(".", ",")} m</div>
    <p>${r.desc}</p>`;
  el.classList.remove("hidden");
  if (cardTimer) clearTimeout(cardTimer);
  if (sticky) cardTimer = setTimeout(() => el.classList.add("compact"), 4000);
}

let lastRoom = null;
function updateRoomHUD() {
  const r = roomAt(player.x, player.z);
  if (r && r !== lastRoom) {
    lastRoom = r;
    document.getElementById("roomCard").classList.remove("compact");
    showRoomCard(r, true);
    document.querySelectorAll("#roomList li").forEach(li => li.classList.toggle("active", li.dataset.id === r.id));
  }
}

document.querySelectorAll("#modes button").forEach(b => b.addEventListener("click", () => setMode(b.dataset.mode)));
document.getElementById("dayNight").addEventListener("click", () => {
  night = !night; applyDayNight();
  document.getElementById("dayNight").textContent = night ? "☀ Jour" : "🌙 Nuit";
});
document.getElementById("tourBtn").addEventListener("click", toggleTour);
document.getElementById("helpBtn").addEventListener("click", () => document.getElementById("help").classList.toggle("hidden"));
document.getElementById("help").addEventListener("click", (e) => { if (e.target.id === "help") e.target.classList.add("hidden"); });

// --- mini-carte ------------------------------------------------------------------------
const mm = document.getElementById("minimap");
const mctx = mm.getContext("2d");
const MMW = mm.width, MMH = mm.height;
const sc = Math.min((MMW - 16) / APT.width, (MMH - 16) / APT.depth);
const mx = (x) => 8 + x * sc;
const my = (y) => MMH - 8 - y * sc; // rue en bas

function drawMinimap() {
  mctx.clearRect(0, 0, MMW, MMH);
  mctx.fillStyle = "rgba(20,18,14,0.88)";
  mctx.beginPath(); mctx.roundRect(0, 0, MMW, MMH, 10); mctx.fill();
  // pièces
  for (const r of ROOMS) {
    mctx.fillStyle = r === lastRoom ? "rgba(212,175,55,0.45)" : "rgba(235,225,200,0.16)";
    for (const [x0, y0, x1, y1] of r.rects)
      mctx.fillRect(mx(x0), my(y1), (x1 - x0) * sc, (y1 - y0) * sc);
  }
  // murs
  mctx.fillStyle = "rgba(240,235,220,0.85)";
  for (const w of WALLS) {
    const segs = [];
    let cur = w.a;
    for (const o of [...w.openings].sort((p, q) => p.at - q.at)) {
      if (o.sill > 0.2) { continue; }
      segs.push([cur, o.at - o.w / 2]); cur = o.at + o.w / 2;
    }
    segs.push([cur, w.b]);
    for (const [a, b] of segs) {
      if (b - a <= 0.01) continue;
      if (w.dir === "x") mctx.fillRect(mx(a), my(w.c + w.t / 2), (b - a) * sc, w.t * sc);
      else mctx.fillRect(mx(w.c - w.t / 2), my(b), w.t * sc, (b - a) * sc);
    }
  }
  // joueur
  mctx.save();
  mctx.translate(mx(player.x), my(player.z));
  mctx.rotate(-player.yaw); // yaw=0 regarde -z (vers la rue = bas de carte)
  mctx.fillStyle = "#ffd24d";
  mctx.beginPath();
  mctx.moveTo(0, 7); mctx.lineTo(-4.5, -5); mctx.lineTo(0, -2.5); mctx.lineTo(4.5, -5);
  mctx.closePath(); mctx.fill();
  mctx.restore();
  // rue
  mctx.fillStyle = "rgba(240,235,220,0.5)";
  mctx.font = "9px Georgia";
  mctx.fillText("rue du Cherche-Midi", MMW / 2 - 44, MMH - 2);
}

mm.addEventListener("click", (e) => {
  const r = mm.getBoundingClientRect();
  const x = (e.clientX - r.left) * (MMW / r.width), y = (e.clientY - r.top) * (MMH / r.height);
  const wx = (x - 8) / sc, wy = (MMH - 8 - y) / sc;
  if (roomAt(wx, wy)) { if (tour) toggleTour(); const sp = freeSpot(wx, wy); player.x = sp.x; player.z = sp.z; if (mode !== "walk") setMode("walk"); }
});

// --- boucle ---------------------------------------------------------------------------
addEventListener("resize", () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

const clock = new THREE.Clock();
function planUpdate() {
  camera.position.set(APT.width / 2, 26, APT.depth / 2 + 0.01);
  camera.rotation.order = "YXZ";
  camera.rotation.set(-Math.PI / 2, 0, 0);
}

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  if (tour) tourUpdate(dt);
  else if (mode === "walk") walkUpdate(dt);
  else if (mode === "plan") planUpdate();
  else if (mode === "orbit") orbit.update();
  if (mode !== "orbit" || tour) updateRoomHUD(); else updateRoomHUD();
  drawMinimap();
  renderer.render(scene, camera);
}
setMode("walk");
animate();

// petit point d'accès pour tests automatisés
window.__nav = { player, get mode() { return mode; }, get tour() { return tour; }, goToRoom };
