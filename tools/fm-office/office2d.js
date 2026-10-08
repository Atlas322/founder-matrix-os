// FM Office 2.5D — батлагдсан зурагтай барилга / өрөө / оффис. /api/state-ийг (3D-тэй ижил) ашиглана.
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const STAGE_COL = { "Brief": "#c8892f", "Бэлтгэл": "#8a6d3b", "Дизайн": "#b5462b", "Хөгжүүлэлт": "#1B5CFF", "Контент": "#2e9b55" };
const STATUS = { active: "идэвхтэй", planning: "төлөвлөж буй", "on-hold": "түр зогссон", someday: "хэзээ нэгэн цагт", archived: "архив", workshop: "Key Activity цех", locked: "түгжээтэй", area: "хүрээ", resource: "лавлагаа" };
const TYPE_ICON = { "✅": "✅", "🙋": "🙋", "itge.e": "🙂", "Discord": "💬", "send_message": "📨" };
const FLOOR_SUB = { projects: "Төсөл бүр = өрөө · дотор нь одоогийн шат", areas: "Key Activity цех · ачаалал", resources: "Wiki · Research", business: "Сейф · түгжээтэй", archive: "Дууссан төслүүд" };

let S = null, H = null, view = "building", openRoom = null, showParked = true, sig = "";

// ---------- туслах ----------
const agentsIn = id => S.agents.filter(a => a.room === id);
const agentById = id => S.agents.find(a => a.id === id);
const roomById = id => S.rooms.find(r => r.id === id);
function imgKey(r) {
  if (r.kind === "project" || r.kind === "workshop") return r.stage ? H.stage_image[r.stage] : H.kind_image.none;
  return H.kind_image[r.kind] || H.kind_image.none;
}
const imgUrl = key => `/assets/img/${H.rooms[key]?.img || key + ".webp"}`;
function chip(r) {
  if (r.kind === "vault") return `<span class="chip" style="background:#1d1a16">🔒 түгжээтэй</span>`;
  if (r.kind === "workshop") return `<span class="chip" style="background:${STAGE_COL[r.stage]}">${r.load} төсөл</span>`;
  if (r.stage) return `<span class="chip" style="background:${STAGE_COL[r.stage]}">${esc(r.stage)}</span>`;
  if (r.kind === "project") return `<span class="chip" style="background:#8a8378">шатгүй</span>`;
  return `<span class="chip" style="background:#6f6556">${esc(STATUS[r.status] || r.status)}</span>`;
}
const convOf = ids => (S.conversations || []).filter(c => ids.has(c.from) || ids.has(c.to));
const nameOf = (id, fb) => agentById(id)?.name || fb || "";

// ---------- Барилга ----------
function tile(r) {
  const ags = agentsIn(r.id);
  const cls = ["tile", r.kind === "archive" ? "dark" : (r.kind === "project" && (!r.stage || r.parked)) ? "grey" : "", r.parked ? "small" : ""].join(" ");
  return `<div class="${cls}" tabindex="0" role="button" data-room="${esc(r.id)}" aria-label="${esc(r.project)}">
    <div class="im" style="background-image:url('${imgUrl(imgKey(r))}')"></div>
    ${r.kind === "vault" ? '<div class="lock">🔒</div>' : ""}
    <div class="dots">${ags.filter(a => !a.human).slice(0, 6).map(a => `<span class="dot ${a.state === "working" ? "w" : ""}" title="${esc(a.device)} ${esc(a.name)}"></span>`).join("")}</div>
    <div class="cap"><div class="nm">${esc(r.kind === "workshop" ? "⚙️ " + r.project : r.project)}</div>${chip(r)}</div></div>`;
}
function renderBuilding() {
  const html = S.floors.map(f => {
    const rooms = S.rooms.filter(r => r.floor === f.id);
    const main = rooms.filter(r => !r.parked), parked = rooms.filter(r => r.parked);
    return `<div class="floor ${f.id}"><div><h2>${esc(f.label)}</h2><div class="sub">${esc(FLOOR_SUB[f.id] || "")}</div></div>
      <div class="tiles">${main.map(tile).join("")}
      ${parked.length && showParked ? `<div class="group">Шатгүй / Зогссон · ${parked.length}</div>${parked.map(tile).join("")}` : ""}</div></div>`;
  }).join("");
  $("building").innerHTML = html;
  $("building").querySelectorAll("[data-room]").forEach(el => {
    el.onclick = () => enterRoom(el.dataset.room);
    el.onkeydown = e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); enterRoom(el.dataset.room); } };
  });
}

// ---------- Өрөө ----------
function enterRoom(id) {
  const r = roomById(id); if (!r) return;
  openRoom = id; location.hash = "room=" + encodeURIComponent(id);
  $("roomImg").src = imgUrl(imgKey(r));
  $("roomImg").style.filter = r.kind === "archive" ? "grayscale(1) brightness(.5)" : (r.kind === "project" && !r.stage) ? "grayscale(1)" : "";
  $("room").classList.add("show");
  renderRoom();
}
function renderRoom() {
  const r = roomById(openRoom); if (!r) return closeRoom();
  const scene = $("scene");
  scene.querySelectorAll(".mk,.bub").forEach(n => n.remove());
  const desks = H.rooms[imgKey(r)]?.desks || [[50, 50]];
  const ags = agentsIn(r.id);
  ags.forEach((a, i) => {
    const [x, y] = desks[i % desks.length];
    const off = Math.floor(i / desks.length) * 3;
    const m = document.createElement("div");
    m.className = "mk " + (a.human ? "human w" : a.state === "working" ? "w" : "i");
    m.style.left = x + off + "%"; m.style.top = y + off + "%"; m.dataset.agent = a.id;
    m.innerHTML = `<span class="av">${a.human ? "🙂" : ""}</span><span class="tag">${esc(a.name)} ${esc(a.device_name ? a.device : "")}</span>`;
    m.title = a.last_seen ? "Сүүлд: " + a.last_seen : "";
    m.onclick = () => agentSide(a);
    scene.appendChild(m);
  });
  const ids = new Set(ags.map(a => a.id));
  const conv = convOf(ids).slice(-6);
  const work = r.kind === "workshop" ? S.rooms.filter(x => x.kind === "project" && x.stage === r.stage) : [];
  const disc = ags.find(a => a.channel);
  $("side").innerHTML = `<h2>${esc(r.project)}</h2>${chip(r)}
    <dl><dt>Шат</dt><dd>${esc(r.stage || "—")}</dd><dt>Төлөв</dt><dd>${esc(STATUS[r.status] || r.status)}</dd>
    <dt>Агент</dt><dd>${ags.filter(a => !a.human).length} (${ags.filter(a => a.state === "working" && !a.human).length} ажиллаж)</dd></dl>
    ${r.kind === "vault" ? "<p>🔒 Санхүүгийн өгөгдөл энд харагдахгүй.</p>" : ""}
    ${work.length ? `<h3>Энэ шатанд</h3><ul>${work.map(x => `<li>${esc(x.project)}</li>`).join("")}</ul>` : ""}
    ${ags.length ? `<h3>Агентууд</h3><ul>${ags.map(a => `<li>${esc(a.device_name ? a.device : "🙂")} ${esc(a.name)} — ${a.human ? "itge.e" : a.state === "working" ? "ажиллаж" : "сул"}${a.last_seen ? ` <span style="color:var(--mute)">· ${esc(a.last_seen.slice(5))}</span>` : ""}</li>`).join("")}</ul>` : ""}
    <h3>Сүүлийн яриа</h3>${conv.length ? `<ul>${conv.slice().reverse().map(c => `<li><b>${TYPE_ICON[c.type] || "💬"} ${esc(nameOf(c.from, c.from_label))}${c.to ? " → " + esc(nameOf(c.to, c.to_label)) : ""}</b><br>${esc(c.text)} <span style="color:var(--mute)">${esc(hhmm(c))}</span></li>`).join("")}</ul>` : '<p style="color:var(--mute)">Яриа алга.</p>'}
    ${disc ? `<p><a href="https://discord.com/channels/${esc(disc.guild || "@me")}" target="_blank" rel="noopener">Discord руу → #${esc(disc.channel)}</a></p>` : ""}`;
  // өрөөний яриаг bubble-ээр
  roomBubbles = conv.slice(-3);
}
function agentSide(a) {
  const r = roomById(a.room);
  $("side").innerHTML = `<h2>${esc(a.device_name ? a.device : "🙂")} ${esc(a.name)}</h2>
    <dl><dt>Дүр</dt><dd>${esc(a.role || "—")}</dd><dt>Өрөө</dt><dd>${esc(r?.project || "—")}</dd><dt>Шат</dt><dd>${esc(r?.stage || "—")}</dd>
    <dt>Төхөөрөмж</dt><dd>${esc(a.device_name || "—")}</dd><dt>Төлөв</dt><dd>${a.state === "working" ? "ажиллаж байна" : "сул"}</dd>
    <dt>Сүүлд</dt><dd>${esc(a.last_seen || "тодорхойгүй")}</dd></dl>
    ${a.channel ? `<p><a href="https://discord.com/channels/${esc(a.guild || "@me")}" target="_blank" rel="noopener">Discord руу → #${esc(a.channel)}</a></p>` : ""}
    <p><button id="sideBack">← Өрөөний мэдээлэл</button></p>`;
  $("sideBack").onclick = renderRoom;
}
function closeRoom() {
  openRoom = null; $("room").classList.remove("show");
  if (location.hash.startsWith("#room")) history.replaceState(null, "", location.pathname + (view === "office" ? "#office" : ""));
}
$("back").onclick = closeRoom;
addEventListener("keydown", e => { if (e.key === "Escape") { if (openRoom) closeRoom(); else $("feed").classList.remove("open"); } });
// parallax (хулгана / gyro)
function parallax(dx, dy) { $("scene").style.transform = `translate(${dx * -14}px,${dy * -10}px) scale(1.04)`; }
$("stage").addEventListener("pointermove", e => { const b = $("stage").getBoundingClientRect(); parallax((e.clientX - b.left) / b.width - .5, (e.clientY - b.top) / b.height - .5); });
addEventListener("deviceorientation", e => { if (openRoom && e.gamma != null) parallax(Math.max(-1, Math.min(1, e.gamma / 30)) / 2, Math.max(-1, Math.min(1, (e.beta - 45) / 30)) / 2); });

// ---------- Оффис ----------
let officePos = {};
function renderOffice() {
  const layer = $("oflayer"); layer.innerHTML = ""; officePos = {};
  const z = H.office.zones;
  const zones = [
    ...["Brief", "Бэлтгэл", "Дизайн", "Хөгжүүлэлт", "Контент"].map(st => ({ key: st, room: S.rooms.find(r => r.kind === "workshop" && r.stage === st), label: `⚙️ ${st} · ${S.rooms.find(r => r.kind === "workshop" && r.stage === st)?.load ?? 0}` })),
    { key: "library", room: roomById("wiki"), label: "📚 Номын сан" },
    { key: "hq", room: roomById("hq"), label: "🏢 Төв оффис" },
    { key: "vault", room: roomById("vault"), label: "🔒 Сейф" },
  ];
  zones.forEach(o => {
    if (!o.room || !z[o.key]) return;
    const d = document.createElement("div"); d.className = "zone";
    d.style.left = z[o.key][0] + "%"; d.style.top = z[o.key][1] / 74.7 * 100 + "%";
    d.textContent = o.label; d.onclick = () => enterRoom(o.room.id); layer.appendChild(d);
  });
  // агентуудын цэг: stage-тэй төслийн агент → тэр цехийн бүс, бусад → ширээнүүд
  const desks = H.office.desks; let k = 0; const perZone = {};
  const dots = S.agents.map(a => {
    const r = roomById(a.room);
    let p;
    if (r && r.stage && z[r.stage]) { const n = perZone[r.stage] = (perZone[r.stage] || 0) + 1; p = [z[r.stage][0] + ((n % 4) - 1.5) * 2.4, z[r.stage][1] + 3 + Math.floor(n / 4) * 2.4]; }
    else if (r && r.id === "wiki" || r?.id === "research") { const n = perZone.lib = (perZone.lib || 0) + 1; p = [z.library[0] + (n % 4) * 2.2, z.library[1] + 4 + Math.floor(n / 4) * 2.2]; }
    else p = desks[k++ % desks.length];
    officePos[a.id] = [p[0], p[1] * 0.747];
    return a;
  });
  $("ofsvg").innerHTML = `<g id="arcs"></g>` + dots.map(a => {
    const [x, y] = officePos[a.id];
    const w = a.state === "working" || a.human;
    return `<g class="ag" data-id="${esc(a.id)}" style="cursor:pointer"><title>${esc(a.name)} ${esc(a.device_name || "")}</title>
      ${w ? `<circle cx="${x}" cy="${y}" r="1.6" fill="${a.human ? "#c8892f" : "#2e9b55"}" opacity=".35"/>` : ""}
      <circle cx="${x}" cy="${y}" r=".9" fill="${a.human ? "#c8892f" : w ? "#2e9b55" : "#9b958b"}" stroke="#1d1a16" stroke-width=".3" opacity="${w ? 1 : .7}"/></g>`;
  }).join("");
  $("ofsvg").querySelectorAll(".ag").forEach(g => g.onclick = () => { const a = agentById(g.dataset.id); if (a) { enterRoom(a.room); agentSide(a); } });
}

// ---------- яриа: дараалал, bubble, нум ----------
const queue = [], seen = new Set(); let busyUntil = 0, roomBubbles = [];
const key = c => c.id || (c.ts + c.text);
const hhmm = c => c.hhmm || (c.ts || "").slice(11, 16);
function play(c) {
  if (openRoom) {
    const fromMk = document.querySelector(`#scene .mk[data-agent="${CSS.escape(c.from || "")}"]`) || document.querySelector(`#scene .mk[data-agent="${CSS.escape(c.to || "")}"]`);
    if (!fromMk) return false;
    bubble($("scene"), fromMk.style.left, fromMk.style.top, c);
    return true;
  }
  if (view !== "office") return false;
  const a = officePos[c.from], b = officePos[c.to];
  if (!a && !b) return false;
  const p = a || b;
  if (a && b) {
    const mx = (a[0] + b[0]) / 2, my = Math.min(a[1], b[1]) - 6 - Math.abs(a[0] - b[0]) * .15;
    const ok = c.type === "✅";
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.innerHTML = `<path class="arc ${ok ? "ok" : ""}" d="M${a[0]},${a[1]} Q${mx},${my} ${b[0]},${b[1]}"/>` + (ok ? `<circle class="pulse" cx="${b[0]}" cy="${b[1]}" r="2"/>` : "");
    $("arcs").appendChild(g); setTimeout(() => g.remove(), 3200);
  }
  bubble($("oflayer"), p[0] + "%", p[1] / 74.7 * 100 + "%", c);
  return true;
}
function bubble(host, left, top, c) {
  const d = document.createElement("div");
  d.className = "bub" + (c.type === "✅" ? " ok" : "");
  d.style.left = left; d.style.top = top;
  d.innerHTML = `<b>${TYPE_ICON[c.type] || "💬"} ${esc(nameOf(c.from, c.from_label))}${c.to ? " → " + esc(nameOf(c.to, c.to_label)) : ""} · ${esc(hhmm(c))}</b>${esc(c.text)}`;
  host.appendChild(d); setTimeout(() => d.remove(), 3000);
}
function pump() {
  const now = performance.now();
  if (now < busyUntil) return;
  if (!queue.length && openRoom && roomBubbles.length) queue.push(roomBubbles.shift());
  while (queue.length) { if (play(queue.shift())) { busyUntil = now + 3300; break; } }
}
setInterval(pump, 300);
function enqueue(list) {
  const first = seen.size === 0;
  const fresh = list.filter(c => !seen.has(key(c)));
  fresh.forEach(c => seen.add(key(c)));
  queue.push(...(first ? fresh.slice(-3) : fresh));
}
function renderFeed() {
  const items = [...(S.conversations || [])].reverse().slice(0, 40);
  $("feedEmpty").style.display = items.length ? "none" : "block";
  $("feedList").innerHTML = items.map((c, i) => `<li data-i="${i}" class="${c.type === "✅" ? "ok" : ""}"><span class="t">${esc(hhmm(c))}${c.channel ? " · #" + esc(c.channel) : ""}</span>
    <b>${TYPE_ICON[c.type] || "💬"} ${esc(nameOf(c.from, c.from_label))}${c.to ? " → " + esc(nameOf(c.to, c.to_label)) : ""}</b><span class="x">${esc(c.text)}</span></li>`).join("");
  $("feedList").querySelectorAll("li").forEach(li => li.onclick = () => focusConv(items[+li.dataset.i]));
}
function focusConv(c) {
  // хоёр агент нэг өрөөнд бол тэр өрөө рүү, үгүй бол Оффис дээр нум зурна
  const ra = agentById(c.from)?.room, rb = agentById(c.to)?.room;
  if (ra && (ra === rb || !rb)) { enterRoom(ra); } else { closeRoom(); setView("office"); }
  queue.unshift(c); busyUntil = 0;
  if (innerWidth <= 700) $("feed").classList.remove("open");
}
$("feedBtn").onclick = () => $("feed").classList.toggle("open");
if (innerWidth <= 700) $("feed").classList.remove("open");

// Demo
const DEMO = [["Discord", "Brief бэлэн, дизайн руу шилжүүлье"], ["🙋", "🙋 авлаа — одоо эхэлж байна"], ["✅", "✅ дууслаа — шалгаад баталъя"], ["itge.e", "Энэ хэр явж байна?"], ["Discord", "Судалгааны дүгнэлтийг атом болгосон"]];
let demoT = null;
$("demo").onclick = () => {
  const on = $("demo").classList.toggle("on"); clearInterval(demoT); if (!on) return;
  const tick = () => {
    const pool = openRoom ? agentsIn(openRoom) : S.agents;
    if (pool.length < 1) return;
    const x = pool[Math.floor(Math.random() * pool.length)];
    const others = S.agents.filter(a => a !== x); const y = (openRoom && pool.length > 1 ? pool.filter(a => a !== x) : others)[Math.floor(Math.random() * (openRoom && pool.length > 1 ? pool.length - 1 : others.length))];
    const [type, text] = DEMO[Math.floor(Math.random() * DEMO.length)];
    queue.push({ from: x.id, to: y?.id, type, text, hhmm: new Date().toTimeString().slice(0, 5) });
  };
  tick(); demoT = setInterval(tick, 3600);
};

// ---------- view ----------
function setView(v) {
  view = v;
  document.querySelectorAll("header [data-v]").forEach(b => b.classList.toggle("on", b.dataset.v === v));
  $("building").classList.toggle("show", v === "building"); $("office").classList.toggle("show", v === "office");
  if (!location.hash.startsWith("#room")) history.replaceState(null, "", location.pathname + (v === "office" ? "#office" : ""));
}
document.querySelectorAll("header [data-v]").forEach(b => b.onclick = () => { closeRoom(); setView(b.dataset.v); });
$("parkedBtn").onclick = () => { showParked = !showParked; $("parkedBtn").classList.toggle("on", showParked); renderBuilding(); };

function counts() {
  const ag = S.agents.filter(a => !a.human);
  $("nWork").textContent = ag.filter(a => a.state === "working").length;
  $("nIdle").textContent = ag.filter(a => a.state !== "working").length;
  $("nTalk").textContent = (S.conversations || []).length;
}

async function poll() {
  try {
    if (!H) H = await (await fetch("/assets/hotspots.json")).json();
    const r = await fetch("/api/state", { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    S = await r.json();
    const ns = JSON.stringify([S.rooms, S.agents.map(a => [a.id, a.room, a.state, a.name])]);
    if (ns !== sig) { sig = ns; renderBuilding(); renderOffice(); if (openRoom) renderRoom(); }
    enqueue(S.conversations || []); renderFeed(); counts(); $("err").textContent = "";
  } catch (e) { $("err").textContent = "Өгөгдөл татаж чадсангүй: " + e.message; }
}
await poll();
setInterval(poll, 30000);
if (location.hash === "#office") setView("office");
const m = location.hash.match(/^#room=(.+)$/); if (m) enterRoom(decodeURIComponent(m[1]));
