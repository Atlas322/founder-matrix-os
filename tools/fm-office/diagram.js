// FM Office — axonometric диаграмын дизайн систем (бүх 3D хуудас нэг хэлтэй).
// Цагаан бөөн хэлбэр + нимгэн хар зураас + ганц улаан accent (= утга: идэвх, анхаарал, сонголт).
// Шийдвэр: vault «2026-10-18 - FM Office - axonometric диаграм хэв маяг».
import * as THREE from 'three';

export const C = {
  paper: 0xf3f2ee, mass: 0xffffff, ground: 0xe9e7e1, path: 0xdedbd3, line: 0x1a1a1a,
  accent: 0xd6453d, green: 0xc9d6bf, ochre: 0xecd9a8, water: 0xd5e2e6, shadow: 0x000000,
};
export const CSS = { paper: '#F3F2EE', line: '#1A1A1A', accent: '#D6453D', muted: '#7a776f' };

const mats = {};
export const matOf = (c = C.mass) => mats[c] ??= new THREE.MeshLambertMaterial({ color: c });
const lineMat = new THREE.LineBasicMaterial({ color: C.line });
const accentLine = new THREE.LineBasicMaterial({ color: C.accent });

// Сцен: цаасан дэвсгэр, хоёр гэрэл (дээрээс сүүдэртэй + зөөлөн орчин) → дээд тал цагаан, хажуу нь цайвар саарал.
export function setupScene(renderer) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(C.paper);
  scene.add(new THREE.HemisphereLight(0xffffff, 0xe4e1da, 2.5));
  const sun = new THREE.DirectionalLight(0xffffff, 0.95); sun.position.set(-40, 80, 30);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.radius = 4; sun.shadow.bias = -0.0004;
  Object.assign(sun.shadow.camera, { left: -60, right: 60, top: 60, bottom: -60, near: 1, far: 220 });
  scene.add(sun);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setClearColor(C.paper);
  return { scene, sun };
}

// Axonometric (ортографик) камер: 45° эргэлт, ~35° хазайлт. zoom-оор ойртоно.
export function axoCamera(w, h, span = 70) {
  const a = w / h, cam = new THREE.OrthographicCamera(-span * a / 2, span * a / 2, span / 2, -span / 2, -500, 500);
  cam.position.set(100, 82, 100); cam.lookAt(0, 0, 0); cam.userData.span = span;
  return cam;
}
export function resizeAxo(cam, w, h) {
  const s = cam.userData.span, a = w / h;
  Object.assign(cam, { left: -s * a / 2, right: s * a / 2, top: s / 2, bottom: -s / 2 }); cam.updateProjectionMatrix();
}

// Бөөн хэлбэр + хар ирмэг. accent=true бол ирмэг улаан.
export function outline(mesh, accent = false, threshold = 25) {
  const e = new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry, threshold), accent ? accentLine : lineMat);
  e.raycast = () => {}; mesh.add(e); return e;
}
export function block(parent, w, h, d, x = 0, y = 0, z = 0, color = C.mass, edges = true) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), matOf(color));
  m.position.set(x, y + h / 2, z); m.castShadow = m.receiveShadow = true; parent.add(m);
  if (edges) outline(m); return m;
}
export function slab(parent, w, d, x, z, color = C.ground, y = 0, h = .2) {      // хавтгай (зам, талбай)
  const m = block(parent, w, h, d, x, y, z, color); m.castShadow = false; return m;
}
// Хоёр налуу дээвэртэй байшин
export function gable(parent, w, h, d, roofH, x = 0, z = 0, color = C.mass) {
  const g = new THREE.Group(); g.position.set(x, 0, z); parent.add(g);
  block(g, w, h, d, 0, 0, 0, color);
  const s = new THREE.Shape(); s.moveTo(-w / 2, 0); s.lineTo(0, roofH); s.lineTo(w / 2, 0); s.closePath();
  const geo = new THREE.ExtrudeGeometry(s, { depth: d, bevelEnabled: false }); geo.translate(0, 0, -d / 2);
  const r = new THREE.Mesh(geo, matOf(color)); r.position.y = h; r.castShadow = r.receiveShadow = true; g.add(r); outline(r);
  return g;
}
// Цонхны эгнээ: хананы нүүрэнд нимгэн тэгш өнцөгтүүд (зураасаар)
export function windows(parent, face, cols, rows, w, h, x0, y0, z, accentIdx = []) {
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const i = r * cols + c, m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), matOf(accentIdx.includes(i) ? C.accent : 0xf7f6f2));
    m.position.set(x0 + c * w * 1.7, y0 + r * h * 1.6, z); if (face === 'x') m.rotation.y = Math.PI / 2;
    parent.add(m); outline(m);
  }
}
// Цагаан «lollipop» мод (лавлагааны навчгүй/цагаан мод шиг): нэг их бие + бөмбөрцөг титэм, зураастай
export function tree(parent, x, z, s = 1) {
  const g = new THREE.Group(); g.position.set(x, 0, z); g.scale.setScalar(s); parent.add(g);
  const t = new THREE.Mesh(new THREE.CylinderGeometry(.12, .16, 1.6, 6), matOf(0x8a857b)); t.position.y = .8; t.castShadow = true; g.add(t);
  const c = new THREE.Mesh(new THREE.IcosahedronGeometry(1.15, 0), matOf(C.mass)); c.position.y = 2.4; c.castShadow = true; g.add(c); outline(c, false, 1);
  return g;
}
// Жижиг хүмүүс: InstancedMesh (нэг draw call), зарим нь accent
export function people(parent, n) {
  const geo = new THREE.CapsuleGeometry(.16, .5, 2, 6); geo.translate(0, .41, 0);
  const im = new THREE.InstancedMesh(geo, new THREE.MeshLambertMaterial({ color: 0xffffff }), n);
  im.castShadow = true; parent.add(im);
  const dark = new THREE.Color(0x3a3833), red = new THREE.Color(C.accent);
  for (let i = 0; i < n; i++) im.setColorAt(i, dark); im.instanceColor.needsUpdate = true;
  im.userData = { dark, red, n }; return im;
}
// Хаяг (label): цагаан хайрцаг + нимгэн зураас + доошоо заагч шугам (CSS2D-д)
export const LABEL_CSS = `
  .dlbl { font:500 12px/1.25 "Inter Tight", Inter, system-ui, sans-serif; color:#1A1A1A; background:#fff; border:1px solid #1A1A1A; padding:4px 9px;
    white-space:nowrap; pointer-events:auto; cursor:pointer; position:relative; transform:translateY(-8px); }
  .dlbl::after { content:""; position:absolute; left:50%; top:100%; width:1px; height:14px; background:#1A1A1A; }
  .dlbl small { display:block; color:#7a776f; font-size:10.5px; }
  .dlbl:hover, .dlbl.on { background:#D6453D; border-color:#D6453D; color:#fff; } .dlbl:hover small, .dlbl.on small { color:#ffe1dc; }
  .dlbl:hover::after, .dlbl.on::after { background:#D6453D; }`;
