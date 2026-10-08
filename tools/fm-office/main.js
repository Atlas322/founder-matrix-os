// FM Office — vault = барилга, давхар = PARA, өрөө = төсөл (дотор нь stage), хүн = агент сешн.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { CSS2DRenderer, CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";

const C = {
  paper: 0xe9dcc3, ink: 0x1d1a16, char: 0x2b2723, char2: 0x3a342d, ochre: 0xc8892f, amber: 0xf2b45a,
  wood: 0x9a6b3c, woodL: 0xc49a66, blue: 0x1b5cff, green: 0x2e9b55, grey: 0x9b958b, cream: 0xf3ead6,
};
const STAGE_COL = { "Brief": "#c8892f", "Бэлтгэл": "#8a6d3b", "Дизайн": "#b5462b", "Хөгжүүлэлт": "#1B5CFF", "Контент": "#2e9b55" };
const FLOOR_ORDER = ["archive", "business", "resources", "areas", "projects"]; // доороос дээш
const RW = 6, RD = 5, FH = 3.4, WALL = 0.35, LVL = FH * 2; // давхруудыг «задалсан» зайтай — дээд хавтан дотрыг халхлахгүй
const CLOTHES = [0x3d5a80, 0x8d5a3b, 0x5b7553, 0xa23b3b, 0x6b5b95, 0x2f4858, 0xd08c3a, 0x4a4a4a];
const SKIN = [0xe8c4a0, 0xd9a77c, 0xc08a5e, 0xf0d0b0];
const HAIR = [0x1d1a16, 0x3b2a1e, 0x5a3d26, 0x2b2b2b];

// ---------- renderer / scene ----------
const host = document.getElementById("stage");
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.setClearColor(C.paper);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
host.appendChild(renderer.domElement);
const labels = new CSS2DRenderer();
labels.setSize(innerWidth, innerHeight);
Object.assign(labels.domElement.style, { position: "absolute", top: "0", pointerEvents: "none" });
host.appendChild(labels.domElement);

const scene = new THREE.Scene();
scene.add(new THREE.HemisphereLight(0xfff1d6, 0x6b5638, 0.9));
const sun = new THREE.DirectionalLight(0xffd59a, 1.5);
sun.position.set(30, 50, 25);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -45, right: 45, top: 45, bottom: -45, far: 160 });
scene.add(sun);

const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 500);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.maxPolarAngle = Math.PI / 2.05;
controls.screenSpacePanning = true;
let viewSize = 30;

function resize() {
  const a = innerWidth / innerHeight;
  camera.left = -viewSize * a / 2; camera.right = viewSize * a / 2;
  camera.top = viewSize / 2; camera.bottom = -viewSize / 2;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  labels.setSize(innerWidth, innerHeight);
}
addEventListener("resize", resize);

function resetView(target = new THREE.Vector3(0, 7, 0), size) {
  const yaw = THREE.MathUtils.degToRad(45), pitch = THREE.MathUtils.degToRad(35), d = 120;
  camera.position.set(target.x + d * Math.cos(pitch) * Math.sin(yaw), target.y + d * Math.sin(pitch), target.z + d * Math.cos(pitch) * Math.cos(yaw));
  controls.target.copy(target);
  camera.zoom = 1;
  if (size) viewSize = size;
  resize();
  controls.update();
}

// ---------- helpers ----------
const matCache = new Map();
function mat(color, opts = {}) {
  const k = color + JSON.stringify(opts);
  if (!opts.unique && matCache.has(k)) return matCache.get(k);
  const m = new THREE.MeshLambertMaterial({ color, flatShading: true, ...opts });
  delete m.unique;
  if (!opts.unique) matCache.set(k, m);
  return m;
}
function box(w, h, d, color, x = 0, y = 0, z = 0, opts) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), opts?.isMaterial ? opts : mat(color, opts));
  m.position.set(x, y + h / 2, z);
  m.castShadow = m.receiveShadow = true;
  return m;
}
function label(html, cls = "lbl") {
  const el = document.createElement("div");
  el.className = cls;
  el.innerHTML = html;
  return new CSS2DObject(el);
}
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const hash = s => [...String(s)].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7);

// ---------- room interiors (stage → тавилга) ----------
function interior(g, room) {
  const z0 = -RD / 2 + 0.6; // арын хэсэг
  const st = room.kind === "workshop" ? room.stage : room.stage;
  if (room.kind === "vault") {
    g.add(box(2.4, 2.2, 1.2, C.char2, 0, 0, z0 + 0.3));
    const door = box(1.6, 1.6, 0.1, 0x7a7068, 0, 0.3, z0 + 0.95);
    g.add(door);
    const wheel = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.07, 6, 12), mat(C.amber, { emissive: 0x5a3a00 }));
    wheel.position.set(0, 1.1, z0 + 1.05); g.add(wheel);
    g.add(box(0.5, 0.6, 0.3, C.ochre, 1.5, 0, z0 + 0.6)); // цоож
    return;
  }
  if (room.kind === "library") {
    for (let i = -2; i <= 2; i++) {
      g.add(box(1, 2.4, 0.45, C.wood, i * 1.05, 0, z0));
      for (let s = 0; s < 4; s++) g.add(box(0.85, 0.42, 0.3, [C.ochre, 0x6b5b95, 0x3d5a80, 0xa23b3b][(i + s + 4) % 4], i * 1.05, 0.15 + s * 0.55, z0 + 0.05));
    }
    g.add(box(1.8, 0.75, 0.9, C.woodL, 0, 0, 0.6));
    return;
  }
  if (room.kind === "hq") {
    g.add(box(1.2, 1.1, 0.6, C.char2, -2.2, 0, z0)); // кофе машин
    g.add(box(0.5, 1.4, 0.5, C.green, 2.4, 0, z0)); // ургамал
    return;
  }
  if (room.kind === "archive") {
    for (let i = -2; i <= 2; i++) g.add(box(0.9, 1.0 + (hash(room.id + i) % 3) * 0.4, 0.8, 0x4a443c, i * 1.1, 0, z0 + (i % 2) * 0.4));
    return;
  }
  switch (st) {
    case "Brief": {
      g.add(box(2.6, 0.75, 1.2, C.woodL, 0, 0, 0.2));
      for (let i = 0; i < 4; i++) g.add(box(0.4, 0.45, 0.4, C.char2, -1 + i * 0.66, 0, 1.1));
      for (let i = 0; i < 12; i++) g.add(box(0.35, 0.35, 0.03, [0xf6d55c, 0xf28f6b, 0x8fd1c2, 0xf6d55c][i % 4], -1.8 + (i % 6) * 0.7, 0.9 + Math.floor(i / 6) * 0.5, -RD / 2 + 0.05));
      break;
    }
    case "Бэлтгэл": {
      for (let i = -1; i <= 1; i++) {
        g.add(box(1.4, 2.2, 0.4, C.wood, i * 1.6, 0, z0));
        for (let s = 0; s < 3; s++) for (let b = 0; b < 4; b++) g.add(box(0.22, 0.5, 0.3, [C.ochre, 0x3d5a80, 0xa23b3b, 0x5b7553][(b + s) % 4], i * 1.6 - 0.45 + b * 0.3, 0.2 + s * 0.7, z0 + 0.05));
      }
      g.add(box(2.2, 0.8, 1, C.woodL, 0, 0, 0.6));
      g.add(box(0.5, 0.15, 0.4, C.cream, -0.5, 0.8, 0.6)); g.add(box(0.5, 0.3, 0.4, C.cream, 0.4, 0.8, 0.6));
      break;
    }
    case "Дизайн": {
      g.add(box(4.4, 2, 0.08, C.cream, 0, 0.5, -RD / 2 + 0.06));
      for (let i = 0; i < 10; i++) g.add(box(0.7, 0.5 + (i % 3) * 0.15, 0.03, [0xb5462b, 0xc8892f, 0x2b2723, 0x8fd1c2, 0xe0b0a0][i % 5], -1.8 + (i % 5) * 0.9, 0.7 + Math.floor(i / 5) * 0.9, -RD / 2 + 0.12));
      g.add(box(2, 0.75, 0.9, C.woodL, 0, 0, z0 + 0.9));
      g.add(box(1.6, 0.95, 0.08, C.ink, 0, 0.8, z0 + 0.6, { emissive: 0x0b2a80 }));
      break;
    }
    case "Хөгжүүлэлт": {
      g.add(box(0.9, 2.3, 0.9, C.ink, 2.3, 0, z0 + 0.1));
      for (let i = 0; i < 6; i++) g.add(box(0.75, 0.05, 0.02, i % 2 ? C.green : C.amber, 2.3, 0.3 + i * 0.32, z0 + 0.56, { emissive: i % 2 ? 0x1a6b35 : 0x7a4a00 }));
      g.add(box(3, 0.75, 0.9, C.woodL, -0.6, 0, z0 + 0.3));
      for (let i = 0; i < 3; i++) g.add(box(0.8, 0.55, 0.06, C.ink, -1.6 + i * 1, 0.8, z0 + 0.15, { emissive: 0x0b2a80 }));
      break;
    }
    case "Контент": {
      const tri = new THREE.Group();
      for (let i = 0; i < 3; i++) { const l = box(0.05, 1.5, 0.05, C.ink); l.rotation.z = (i - 1) * 0.3; l.position.x = (i - 1) * 0.2; tri.add(l); }
      tri.add(box(0.5, 0.35, 0.35, C.char2, 0, 1.5, 0));
      tri.position.set(-1.5, 0, 0.3); g.add(tri);
      for (const x of [0.6, 2.2]) {
        g.add(box(0.05, 1.8, 0.05, C.ink, x, 0, z0 + 0.3));
        const sb = box(0.8, 0.8, 0.3, C.cream, x, 1.6, z0 + 0.4, { emissive: 0x806a40 }); g.add(sb);
      }
      g.add(box(1.4, 0.75, 0.7, C.woodL, 1.4, 0, 1));
      g.add(box(0.12, 0.35, 0.12, C.ink, 1.4, 0.75, 1));
      break;
    }
    default:
      g.add(box(1, 0.5, 1, C.grey, 0, 0, z0 + 0.4)); // хоосон саарал өрөө — ганц хайрцаг
  }
  if (room.kind === "workshop") { // ачаалал = төслийн тоо → хайрцагны овоо
    for (let i = 0; i < room.load; i++) g.add(box(0.55, 0.45, 0.55, C.ochre, -2.3 + (i % 3) * 0.6, Math.floor(i / 3) * 0.45, 1.6));
  }
}

// ---------- people ----------
function person(a) {
  const h = hash(a.name);
  const g = new THREE.Group();
  const clothes = mat(CLOTHES[h % CLOTHES.length]);
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.22, 0.45, 3, 8), clothes);
  body.position.y = 0.55; body.castShadow = true; g.add(body);
  const legs = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 0.35, 3, 8), mat(0x2f3440));
  legs.position.y = 0.2; g.add(legs);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.2, 12, 10), mat(SKIN[h % SKIN.length]));
  head.position.y = 1.08; head.castShadow = true; g.add(head);
  const hair = new THREE.Mesh(new THREE.SphereGeometry(0.215, 12, 8, 0, Math.PI * 2, 0, Math.PI * (h % 2 ? 0.55 : 0.42)), mat(HAIR[h % HAIR.length]));
  hair.position.y = 1.1; hair.rotation.x = -0.25; g.add(hair);
  g.userData.head = head;
  return g;
}

function deskSlot(a) {
  const g = new THREE.Group();
  g.add(box(1.0, 0.7, 0.55, C.woodL, 0, 0, 0));
  const monMat = new THREE.MeshLambertMaterial({ color: C.ink, flatShading: true });
  const mon = box(0.6, 0.38, 0.05, null, 0, 0.78, -0.12, monMat);
  g.add(mon);
  const lampMat = new THREE.MeshLambertMaterial({ color: 0x5a4a30 });
  const lamp = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.15, 8, 1, true), lampMat);
  lamp.position.set(0.38, 0.98, 0); g.add(lamp);
  g.add(box(0.03, 0.3, 0.03, C.ink, 0.38, 0.7, 0));
  const chair = box(0.4, 0.42, 0.4, C.char2, 0, 0, 0.5); g.add(chair);
  const p = person(a); g.add(p);
  const working = a.state === "working";
  if (working) {
    monMat.emissive.setHex(C.blue); monMat.color.setHex(C.blue);
    lampMat.emissive.setHex(C.amber); lampMat.color.setHex(C.amber);
    p.position.set(0, 0.25, 0.5); p.scale.setScalar(0.92); // суугаа
  } else {
    p.position.set(0.75, 0, 0.45); p.rotation.y = -0.6; // зогсож буй
    p.traverse(o => { if (o.isMesh) { o.material = o.material.clone(); o.material.color.multiplyScalar(0.7); } });
  }
  const lb = label(`${esc(a.device)} ${esc(a.name)}`, "alb");
  lb.position.set(p.position.x, 1.55, p.position.z);
  g.add(lb);
  g.userData = { pick: { type: "agent", id: a.id }, person: p };
  return g;
}

// ---------- building ----------
let building = null, pickables = [], roomTiles = new Map(), agentNodes = new Map(), floorGroups = new Map();
let STATE = null, sig = "", activeFloor = "all";

function roomColor(r) {
  if (r.kind === "archive") return 0x3a352f;
  if (r.kind === "vault") return 0x4a443c;
  if (r.kind === "project" && !r.stage) return 0xb9b2a5;
  if (r.kind === "workshop") return 0xd8c39a;
  return 0xe6d6b4;
}

function build(state) {
  if (building) { building.traverse(o => { if (o.isCSS2DObject) o.removeFromParent(); }); scene.remove(building); }
  building = new THREE.Group(); scene.add(building);
  pickables = []; roomTiles.clear(); agentNodes.clear(); floorGroups.clear();
  const byFloor = Object.fromEntries(FLOOR_ORDER.map(f => [f, state.rooms.filter(r => r.floor === f)]));
  const rowsOf = f => (byFloor[f].length > 8 ? 2 : 1);
  const colsOf = f => Math.max(1, Math.ceil(byFloor[f].length / rowsOf(f)));
  const maxCols = Math.max(...FLOOR_ORDER.map(colsOf));
  const W = maxCols * RW, D = 2 * RD;
  const agentsByRoom = {};
  for (const a of state.agents) (agentsByRoom[a.room] ||= []).push(a);

  // газар
  const ground = box(W + 8, 0.2, D + 8, 0xd7c6a5, 0, -0.2, 0); ground.receiveShadow = true; building.add(ground);

  FLOOR_ORDER.forEach((fid, level) => {
    const fg = new THREE.Group(); fg.position.y = level * LVL; building.add(fg); floorGroups.set(fid, fg);
    const fl = state.floors.find(f => f.id === fid);
    fg.add(box(W + WALL * 2, 0.18, D + WALL * 2, C.char, 0, -0.18, 0));
    // зузаан хар гадна хана (ар, зүүн) — урд/баруун нээлттэй тул дотор харагдана
    fg.add(box(W + WALL * 2, FH - 0.2, WALL, C.ink, 0, 0, -D / 2 - WALL / 2));
    fg.add(box(WALL, FH - 0.2, D + WALL, C.ink, -W / 2 - WALL / 2, 0, WALL / 2 - WALL / 2));
    const fLbl = label(`<b>${esc(fl?.label || fid)}</b>`); fLbl.position.set(-W / 2 - 1.2, 1.2, D / 2); fg.add(fLbl);
    const rooms = byFloor[fid], rows = rowsOf(fid), cols = colsOf(fid);
    const rw = W / cols, rd = D / rows;
    rooms.forEach((r, i) => {
      const cx = -W / 2 + rw * (i % cols) + rw / 2, cz = -D / 2 + rd * Math.floor(i / cols) + rd / 2;
      const rg = new THREE.Group(); rg.position.set(cx, 0, cz); fg.add(rg);
      const tile = box(rw - 0.08, 0.04, rd - 0.08, null, 0, 0, 0, new THREE.MeshLambertMaterial({ color: roomColor(r) }));
      tile.userData.pick = { type: "room", id: r.id }; rg.add(tile); pickables.push(tile); roomTiles.set(r.id, tile);
      // шилэн хана
      const glass = new THREE.Mesh(new THREE.BoxGeometry(0.06, FH - 0.6, rd - 0.1), new THREE.MeshLambertMaterial({ color: 0xbfd6e0, transparent: true, opacity: 0.22 }));
      glass.position.set(rw / 2, (FH - 0.6) / 2, 0); rg.add(glass);
      if (rows > 1 && Math.floor(i / cols) === 0) {
        const g2 = new THREE.Mesh(new THREE.BoxGeometry(rw - 0.1, FH - 0.6, 0.06), glass.material); g2.position.set(0, (FH - 0.6) / 2, rd / 2); rg.add(g2);
      }
      const ig = new THREE.Group(); ig.scale.setScalar(Math.min(1, rw / RW, rd / RD)); rg.add(ig);
      interior(ig, r);
      // агентуудын ширээ
      const ags = agentsByRoom[r.id] || [];
      const perRow = r.kind === "hq" ? 4 : 3;
      ags.forEach((a, k) => {
        const d = deskSlot(a);
        const sc = Math.min(1, rw / RW) * (ags.length > 6 ? 0.8 : 1);
        d.scale.setScalar(sc);
        d.position.set((-rw / 2 + 0.9 + (k % perRow) * (rw - 1.4) / Math.max(1, perRow - 1)) * 0.95, 0.02, rd / 2 - 0.9 - Math.floor(k / perRow) * 1.25 * sc);
        rg.add(d);
        d.traverse(o => { if (o.isMesh) { o.userData.pick = d.userData.pick; pickables.push(o); } });
        agentNodes.set(a.id, d);
      });
      // шошго
      let chip = "";
      if (r.kind === "vault") chip = `<span class="chip" style="background:#1d1a16">🔒 түгжээтэй</span>`;
      else if (r.kind === "workshop") chip = `<span class="chip" style="background:${STAGE_COL[r.stage] || "#777"}">${r.load} төсөл</span>`;
      else if (r.stage) chip = `<span class="chip" style="background:${STAGE_COL[r.stage] || "#777"}">${esc(r.stage)}</span>`;
      else if (r.kind === "project") chip = `<span class="chip" style="background:#8a8378">stage алга</span>`;
      const lb = label(`${esc(r.kind === "workshop" ? "⚙️ " + r.project : r.project)}${chip}`, "lbl" + (r.kind === "archive" || r.status === "on-hold" ? " dim" : ""));
      lb.position.set(0, FH - 0.4, 0); rg.add(lb);
      rg.userData.room = r;
      if (r.kind === "archive") rg.add(box(rw - 0.1, FH - 0.4, 0.05, 0x1d1a16, 0, 0, rd / 2 - 0.05, { transparent: true, opacity: 0.35 }));
    });
  });
  building.userData.size = { W, D, H: (FLOOR_ORDER.length - 1) * LVL + FH };
  applyFloor(activeFloor);
}

function setVisible(obj, v) { obj.visible = v; obj.traverse(o => { if (o.isCSS2DObject) o.visible = v; }); }

function applyFloor(fid) {
  activeFloor = fid;
  document.body.classList.toggle("overview", fid === "all");
  for (const [id, g] of floorGroups) setVisible(g, fid === "all" || id === fid);
  document.querySelectorAll("#floors button").forEach(b => b.classList.toggle("on", b.dataset.f === fid));
  const s = building?.userData.size;
  if (!s) return;
  const a = innerWidth / innerHeight, wide = (s.W * 0.78 + s.D) / a; // өргөнөөр ч багтаана (утас)
  if (fid === "all") resetView(new THREE.Vector3(0, s.H / 2 - 1, 0), Math.max(s.H * 1.7, s.W * 0.75, wide));
  else resetView(new THREE.Vector3(0, FLOOR_ORDER.indexOf(fid) * LVL + 1, 0), Math.max(14, s.W * 0.7, wide));
}

// ---------- UI ----------
const $ = id => document.getElementById(id);
function renderFloorButtons(floors) {
  const wrap = $("floors"); wrap.innerHTML = "";
  for (const f of [{ id: "all", label: "Бүгд" }, ...floors]) {
    const b = document.createElement("button"); b.textContent = f.id === "all" ? f.label : f.label.split(" · ")[0]; b.dataset.f = f.id;
    b.onclick = () => applyFloor(f.id); wrap.appendChild(b);
  }
}
function counts() {
  const ag = STATE?.agents || [];
  $("nWork").textContent = ag.filter(a => a.state === "working").length;
  $("nIdle").textContent = ag.filter(a => a.state !== "working").length;
  $("nTalk").textContent = talkCount;
}
function openCard(html) { $("cardBody").innerHTML = html; $("card").classList.add("show"); }
function closeCard() { $("card").classList.remove("show"); }
$("close").onclick = closeCard;
addEventListener("keydown", e => { if (e.key === "Escape") closeCard(); });
$("reset").onclick = () => applyFloor(activeFloor);

function agentCard(a) {
  const room = STATE.rooms.find(r => r.id === a.room);
  const link = a.channel ? `<p><a href="https://discord.com/channels/${esc(a.guild || "@me")}" target="_blank" rel="noopener">Discord руу → #${esc(a.channel)}</a></p>` : "";
  openCard(`<h2>${esc(a.device)} ${esc(a.name)}</h2><dl>
    <dt>Дүр</dt><dd>${esc(a.role || "—")}</dd><dt>Гарчиг</dt><dd>${esc(a.title || "—")}</dd>
    <dt>Төсөл</dt><dd>${esc(room?.project || a.project)}</dd><dt>Stage</dt><dd>${esc(room?.stage || "—")}</dd>
    <dt>Төхөөрөмж</dt><dd>${esc(a.device_name)}</dd><dt>Төлөв</dt><dd>${a.state === "working" ? "ажиллаж байна" : "сул"}</dd>
    <dt>Сүүлд</dt><dd>${esc(a.last_seen || "тодорхойгүй")}</dd></dl>${link}`);
}
function roomCard(r) {
  const ags = STATE.agents.filter(a => a.room === r.id);
  const st = { active: "идэвхтэй", planning: "төлөвлөж буй", "on-hold": "түр зогссон", archived: "архив", workshop: "Key Activity цех", locked: "түгжээтэй" }[r.status] || r.status;
  let extra = "";
  if (r.kind === "vault") extra = "<p>🔒 Санхүүгийн өгөгдөл энд харагдахгүй.</p>";
  if (r.kind === "workshop") extra = `<p>Энэ stage-д буй төсөл: <b>${r.load}</b></p><ul>${STATE.rooms.filter(x => x.kind === "project" && x.stage === r.stage).map(x => `<li>${esc(x.project)}</li>`).join("")}</ul>`;
  openCard(`<h2>${esc(r.project)}</h2><dl><dt>Stage</dt><dd>${esc(r.stage || "—")}</dd><dt>Төлөв</dt><dd>${esc(st)}</dd><dt>Агент</dt><dd>${ags.length}</dd></dl>
    ${ags.length ? `<ul>${ags.map(a => `<li>${esc(a.device)} ${esc(a.name)} — ${a.state === "working" ? "ажиллаж" : "сул"}</li>`).join("")}</ul>` : ""}${extra}`);
}

// ---------- picking ----------
const ray = new THREE.Raycaster(), ptr = new THREE.Vector2();
let hovered = null, downAt = null;
function pickAt(e) {
  ptr.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  ray.setFromCamera(ptr, camera);
  const hit = ray.intersectObjects(pickables.filter(o => isShown(o)), false)[0];
  return hit?.object.userData.pick || null;
}
function isShown(o) { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; }
function setHover(p) {
  if (hovered?.type === p?.type && hovered?.id === p?.id) return;
  if (hovered) highlight(hovered, false);
  hovered = p; if (p) highlight(p, true);
  renderer.domElement.style.cursor = p ? "pointer" : "";
}
function highlight(p, on) {
  if (p.type === "room") { const t = roomTiles.get(p.id); t?.material.emissive.setHex(on ? 0x5a3a10 : 0); }
  else { const n = agentNodes.get(p.id); n?.userData.person.scale.setScalar(on ? 1.15 : (STATE.agents.find(a => a.id === p.id)?.state === "working" ? 0.92 : 1)); }
}
renderer.domElement.addEventListener("pointermove", e => {
  const p = pickAt(e); setHover(p);
  const tip = $("tip");
  if (p) {
    const name = p.type === "room" ? STATE.rooms.find(r => r.id === p.id)?.project : STATE.agents.find(a => a.id === p.id)?.name;
    tip.textContent = name || ""; tip.style.display = "block"; tip.style.left = e.clientX + 12 + "px"; tip.style.top = e.clientY + 12 + "px";
  } else tip.style.display = "none";
});
renderer.domElement.addEventListener("pointerdown", e => { downAt = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener("pointerup", e => {
  if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 5) return;
  const p = pickAt(e);
  if (!p) return closeCard();
  if (p.type === "agent") agentCard(STATE.agents.find(a => a.id === p.id));
  else roomCard(STATE.rooms.find(r => r.id === p.id));
});

// ---------- conversations ----------
const queue = [], seenConv = new Set(), effects = [];
let talkCount = 0, busyUntil = 0;
function headPos(id) {
  const n = agentNodes.get(id); if (!n || !isShown(n)) return null;
  const v = new THREE.Vector3(); n.userData.person.userData.head.getWorldPosition(v); return v;
}
function playConv(c) {
  const a = headPos(c.from), b = c.to ? headPos(c.to) : null;
  if (!a) return false;
  const ok = c.type === "✅";
  const col = ok ? C.green : C.blue;
  if (b) {
    const mid = a.clone().lerp(b, 0.5); mid.y += 2 + a.distanceTo(b) * 0.25;
    const pts = new THREE.QuadraticBezierCurve3(a, mid, b).getPoints(40);
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineDashedMaterial({ color: col, dashSize: 0.3, gapSize: 0.18 }));
    line.computeLineDistances(); scene.add(line);
    effects.push({ obj: line, until: performance.now() + 3200 });
    if (ok) {
      const ring = new THREE.Mesh(new THREE.RingGeometry(0.3, 0.4, 24), new THREE.MeshBasicMaterial({ color: C.green, transparent: true, side: THREE.DoubleSide }));
      ring.rotation.x = -Math.PI / 2; ring.position.copy(b).setY(b.y - 1); scene.add(ring);
      effects.push({ obj: ring, until: performance.now() + 3200, pulse: true, t0: performance.now() });
    }
  }
  const icon = c.type === "send_message" ? "💬" : c.type === "Discord" ? "🎧" : c.type;
  const bub = label(`${icon} <b>${esc(c.from_label || "")}${c.to_label ? " → " + esc(c.to_label) : ""}</b><br>${esc(c.text)}`, "bubble" + (ok ? " ok" : ""));
  bub.position.copy(a).setY(a.y + 0.9); scene.add(bub);
  effects.push({ obj: bub, until: performance.now() + 3000 });
  talkCount++; counts();
  return true;
}
function pump(now) {
  if (now < busyUntil || !queue.length) return;
  const c = queue.shift();
  if (playConv(c)) busyUntil = now + 3300;
}
function enqueueReal(list) {
  const fresh = list.filter(c => !seenConv.has(c.time + c.text));
  fresh.forEach(c => seenConv.add(c.time + c.text));
  queue.push(...(seenConv.size === fresh.length ? fresh.slice(-3) : fresh)); // анх ачаалахад сүүлийн 3
}
const DEMO = [
  ["send_message", "Brief бэлэн, дизайн руу шилжүүлье"], ["🙋", "Figma-ийн эрх хэрэгтэй байна"], ["✅", "Task дууссан — шалгаад баталъя"],
  ["Discord", "#byd-website-д тайлан орлоо"], ["send_message", "Судалгааны дүгнэлтийг атом болгосон"], ["✅", "Deploy амжилттай"],
];
let demoTimer = null;
$("demo").onclick = () => {
  const on = $("demo").classList.toggle("on");
  clearInterval(demoTimer);
  if (!on) return;
  const tick = () => {
    const ag = STATE.agents.filter(a => agentNodes.has(a.id) && isShown(agentNodes.get(a.id)));
    if (ag.length < 2) return;
    const x = ag[Math.floor(Math.random() * ag.length)];
    let y = ag[Math.floor(Math.random() * ag.length)]; if (y === x) y = ag[(ag.indexOf(x) + 1) % ag.length];
    const [type, text] = DEMO[Math.floor(Math.random() * DEMO.length)];
    queue.push({ from: x.id, to: y.id, from_label: x.name, to_label: y.name, type, text });
  };
  tick(); demoTimer = setInterval(tick, 3500);
};

// ---------- data ----------
async function poll() {
  try {
    const r = await fetch("/api/state", { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const s = await r.json();
    const nsig = JSON.stringify([s.rooms, s.agents.map(a => [a.id, a.room, a.state])]);
    const first = !STATE;
    STATE = s;
    if (first) renderFloorButtons(s.floors);
    if (nsig !== sig) { sig = nsig; const keep = activeFloor; build(s); if (!first) applyFloor(keep); }
    enqueueReal(s.conversations || []);
    counts(); $("err").textContent = "";
  } catch (e) { $("err").textContent = "Өгөгдөл татаж чадсангүй: " + e.message; }
}

// ---------- loop ----------
function loop(now) {
  controls.update();
  pump(now);
  for (let i = effects.length - 1; i >= 0; i--) {
    const f = effects[i];
    if (f.pulse) { const k = ((now - f.t0) % 1000) / 1000; f.obj.scale.setScalar(1 + k * 2.5); f.obj.material.opacity = 1 - k; }
    if (now > f.until) { f.obj.removeFromParent(); f.obj.geometry?.dispose(); effects.splice(i, 1); }
  }
  renderer.render(scene, camera);
  labels.render(scene, camera);
  requestAnimationFrame(loop);
}
resize();
await poll();
setInterval(poll, 30000);
requestAnimationFrame(loop);
