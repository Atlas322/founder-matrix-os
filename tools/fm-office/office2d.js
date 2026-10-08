// FM Office 2.5D — батлагдсан зурагтай барилга / өрөө / оффис. /api/state-ийг (3D-тэй ижил) ашиглана.
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const STAGE_COL = { "Brief": "var(--ka-brief)", "Бэлтгэл": "var(--ka-beltgel)", "Дизайн": "var(--ka-dizain)", "Хөгжүүлэлт": "var(--ka-hugjuulelt)", "Контент": "var(--ka-kontent)" };
const FLOOR_NUM = { projects: "03", areas: "04", resources: "05", business: "B", archive: "99" };
const FLOOR_NAME = { projects: "Projects", areas: "Areas", resources: "Resources", business: "Business", archive: "Archive" };
const VIEW_TXT = {
  building: ["Оффис · Барилга.", "Vault = барилга · давхар = PARA · төсөл бүр өөрийн өрөө · тохижилт = шат"],
  office: ["Оффис.", "Агент бүр нэг ширээ · өрөө = vault-ийн хавтас · шууд төлөв"],
};
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
// Inai tag: дөрвөлжин, 1px хүрээ, өнгөт цэг
const tagHtml = (txt, col, cls = "") => `<span class="tag ${cls}" style="--c:${col || "var(--text-2)"};--tagc:${col || "var(--text-2)"}"><i></i>${esc(txt)}</span>`;
function chip(r) {
  if (r.kind === "vault") return tagHtml("🔒 Сейф", "var(--text)");
  if (r.kind === "workshop") return tagHtml(`${r.load} төсөл`, STAGE_COL[r.stage]);
  if (r.stage) return tagHtml(r.stage, STAGE_COL[r.stage]);
  if (r.kind === "project") return tagHtml(r.status === "on-hold" ? "зогссон" : "шатгүй", "var(--text-2)");
  if (r.kind === "archive") return tagHtml("хаагдсан", "var(--text-2)");
  if (r.kind === "library") return tagHtml("Номын сан", "var(--ka-beltgel)");
  return tagHtml(STATUS[r.status] || r.status, "var(--link)");
}
const convOf = ids => (S.conversations || []).filter(c => ids.has(c.from) || ids.has(c.to));
const nameOf = (id, fb) => agentById(id)?.name || fb || "";

// ---------- Барилга (13 Оффис · Барилга фрейм) ----------
function tile(r) {
  const ags = agentsIn(r.id).filter(a => !a.human);
  const cls = ["tile", r.kind === "archive" ? "dark" : (r.kind === "project" && (!r.stage || r.parked)) ? "grey" : "", r.parked ? "small" : ""].join(" ");
  return `<div class="${cls}" tabindex="0" role="button" data-room="${esc(r.id)}" aria-label="${esc(r.project)}">
    <div class="im" style="background-image:url('${imgUrl(imgKey(r))}')">${chip(r)}
      ${r.kind === "vault" ? '<div class="lock">🔒</div>' : ""}
      <div class="dots">${ags.slice(0, 6).map(a => `<span class="dot ${a.state === "working" ? "w" : ""}" title="${esc(a.name)} ${esc(a.device_name)}"></span>`).join("")}</div></div>
    <div class="nm">${esc(r.kind === "workshop" ? r.project : r.project)}</div></div>`;
}
function renderBuilding() {
  const floors = S.floors.map(f => {
    const rooms = S.rooms.filter(r => r.floor === f.id);
    const main = rooms.filter(r => !r.parked), parked = rooms.filter(r => r.parked);
    return `<div class="floor ${f.id}"><div class="fl"><div class="label"><b>${FLOOR_NUM[f.id] || ""}</b>${esc(FLOOR_NAME[f.id] || f.label)}</div><p>${esc(FLOOR_SUB[f.id] || "")}</p></div>
      <div class="tiles">${main.map(tile).join("")}
      ${parked.length && showParked ? `<div class="group label mute">Шатгүй / Зогссон · ${parked.length}</div>${parked.map(tile).join("")}` : ""}</div></div>`;
  }).join("");
  $("building").innerHTML = `<div class="panel"><div class="strip"><span class="label">▲ Vault · <b>Second Brain 2.0</b></span><span class="label mute">${S.rooms.filter(r => r.kind === "project").length} төсөл</span></div>${floors}</div>`;
  $("building").querySelectorAll("[data-room]").forEach(el => {
    el.onclick = () => enterRoom(el.dataset.room);
    el.onkeydown = e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); enterRoom(el.dataset.room); } };
  });
}
// баруун хүрээ: Барилга = удирдлагын самбар, Шууд = одоо ажиллаж буй
function renderRail() {
  if (!S) return;
  if (view === "building") {
    const ws = S.rooms.filter(r => r.kind === "workshop");
    $("railPanel").innerHTML = `<div class="strip"><span class="label">Цаглабар = <b>удирдлагын самбар</b></span></div><div class="body">
      <ul class="arrows"><li>Өрөө = төсөл. Өрөөний дотор тал = төслийн одоогийн шат (Key Activity).</li>
      <li>Шат солигдоход өрөөний тохижилт солигдоно (Цаглабараас).</li>
      <li>04 Areas давхарт 5 цех: тэнд хэдэн төсөл байгаа = ачаалал.</li>
      <li>Шат frontmatter-ийн <span class="mono">stage:</span>-ээс уншина.</li>
      <li>Хаагдсан төсөл 99 Archive руу бууж харанхуй болно.</li></ul>
      <div class="label" style="margin-top:14px">Key Activity</div>
      <ul class="legend">${ws.map(w => `<li style="--c:${STAGE_COL[w.stage]}"><i></i>${esc(w.stage)} <span>· ${w.load}</span></li>`).join("")}</ul>
      <div class="note">🔒 Хувийн санхүү барилгад байхгүй</div></div>`;
  } else {
    const ag = S.agents.filter(a => !a.human).slice().sort((a, b) => (b.state === "working") - (a.state === "working") || String(b.last_seen || "").localeCompare(String(a.last_seen || "")));
    $("railPanel").innerHTML = `<div class="strip"><span class="label">Одоо <b>ажиллаж байна</b></span><span class="label mute">${ag.filter(a => a.state === "working").length}/${ag.length}</span></div><div class="body"><ul class="who">${ag.slice(0, 9).map(a => {
      const r = roomById(a.room);
      return `<li data-room="${esc(a.room)}"><span class="st ${a.state === "working" ? "w" : ""}"></span><span><b>${esc(a.name)}</b> <span class="badge">${esc(a.device_name)}</span><small>${esc(r?.project || "")}${r?.stage ? " · " + esc(r.stage) : ""}</small></span><span class="t">${esc(a.last_seen ? a.last_seen.slice(5) : "—")}</span></li>`;
    }).join("")}</ul></div>`;
    $("railPanel").querySelectorAll("[data-room]").forEach(li => li.onclick = () => enterRoom(li.dataset.room));
  }
}

// ---------- Өрөө (дашбоард: шат · task · сешн удирдлага · яриа · холбоос) ----------
let roomInfo = null;
const GROUP_LBL = { "next-action": "Дараагийн алхам", waiting: "Хүлээж буй", inbox: "Inbox", someday: "Хэзээ нэгэн цагт" };
async function enterRoom(id) {
  const r = roomById(id); if (!r) return;
  openRoom = id; location.hash = "room=" + encodeURIComponent(id);
  $("roomImg").src = imgUrl(imgKey(r));
  $("roomImg").style.filter = r.kind === "archive" ? "grayscale(1) brightness(.5)" : (r.kind === "project" && !r.stage) ? "grayscale(1)" : "";
  $("room").classList.add("show"); $("room").scrollTop = 0;
  roomInfo = null; renderRoom();
  try { const res = await fetch("/api/room?id=" + encodeURIComponent(id), { cache: "no-store" }); if (res.ok && openRoom === id) { roomInfo = await res.json(); renderRoom(); } }
  catch (e) { /* дашбоард хоосон үлдэнэ */ }
}
let secN = 0;
function sec(title, body, cls = "", extra = "") { secN++; return `<section class="card ${cls}"><div class="strip"><span class="label"><b>[0${secN}]</b>&nbsp; ${title}</span><span class="label mute">${extra}</span></div><div class="body">${body}</div></section>`; }
function renderRoom() {
  const r = roomById(openRoom); if (!r) return closeRoom();
  const scene = $("scene");
  scene.querySelectorAll(".mk,.bub").forEach(n => n.remove());
  const desks = H.rooms[imgKey(r)]?.desks || [[50, 50]];
  const ags = agentsIn(r.id);
  ags.forEach((a, i) => {
    const [x, y] = desks[i % desks.length];
    const m = document.createElement("div");
    m.className = "mk " + (a.human ? "human w" : a.state === "working" ? "w" : "i");
    m.style.left = x + "%"; m.style.top = y + "%"; m.dataset.agent = a.id;
    m.innerHTML = `<span class="av">${a.human ? "🙂" : ""}</span>`;
    m.title = `${a.name} ${a.device_name || ""}${a.last_seen ? " · " + a.last_seen : ""}`;
    m.onclick = () => document.querySelector(`.srow[data-id="${CSS.escape(a.id)}"]`)?.scrollIntoView({ behavior: "smooth", block: "center" });
    scene.appendChild(m);
  });
  const I = roomInfo;
  const fl = S.floors.find(f => f.id === r.floor);
  $("rtitle").innerHTML = `<div class="label">[${FLOOR_NUM[r.floor] || ""}] ${esc(fl?.label || "")} · Өрөө</div><h2>${esc(r.project)}.</h2>${chip(r)}
    <div class="meta"><span>Төлөв: <b>${esc(STATUS[r.status] || r.status)}</b></span>${I?.due ? `<span>Дуусах: <b>${esc(I.due)}</b></span>` : ""}
    <span>Агент: <b>${ags.filter(a => !a.human).length}</b> · ажиллаж <b>${ags.filter(a => a.state === "working" && !a.human).length}</b></span>
    ${I?.tasks ? `<span>Нээлттэй task: <b>${I.tasks.open}</b> · энэ 7 хоногт дууссан <b>${I.tasks.done_week}</b></span>` : ""}</div>`;
  const ids = new Set(ags.map(a => a.id));
  const conv = convOf(ids).slice(-12);
  roomBubbles = conv.slice(-3);
  const convHtml = conv.length ? `<ul class="conv">${conv.slice().reverse().map(c => `<li class="${c.type === "✅" ? "ok" : ""}"><span class="t">${esc(hhmm(c))}${c.channel ? " · #" + esc(c.channel) : ""}</span><b>${TYPE_ICON[c.type] || "💬"} ${esc(nameOf(c.from, c.from_label))}${c.to ? " → " + esc(nameOf(c.to, c.to_label)) : ""}</b><span>${esc(c.text)}</span></li>`).join("")}</ul>` : '<p class="mute">Сүүлийн 24 цагт яриа алга.</p>';
  let html = ""; secN = 0;
  if (!I) html = '<p class="mute">Ачаалж байна…</p>';
  else if (r.kind === "project") {
    const cur = I.stages.indexOf(r.stage);
    html += sec("Шат · Key Activity", `<ol class="steps">${I.stages.map((s, i) => `<li class="${i === cur ? "cur" : i < cur ? "past" : ""}" style="--c:${STAGE_COL[s]}"><span>0${i + 1}</span><i></i>${esc(s)}</li>`).join("")}</ol>
      ${cur < 0 ? '<p class="mute">Шат тодорхойгүй — төслийн note-д <code>stage:</code> тавина уу.</p>' : ""}
      ${I.milestones.length ? `<div class="label" style="margin-bottom:4px">Milestone</div><ul class="ms">${I.milestones.map(m => `<li class="${m.done ? "done" : ""}"><span class="ck">${m.done ? "✓" : ""}</span><span class="lb">${esc(m.label)}</span> <span class="mute mono">${esc(m.date || "")}</span></li>`).join("")}</ul>` : '<p class="mute">Milestone алга.</p>'}`, "wide");
    html += sec("Task-ууд", taskGroups(I.tasks), "", `${I.tasks.open} нээлттэй · 7 хоногт ✓ ${I.tasks.done_week}`);
    html += sec("Сешнүүд", sessionsHtml(I));
    html += sec("Сүүлийн яриа", convHtml);
    html += sec("Холбоос", I.links.length ? `<ul class="links">${I.links.map(l => `<li><a class="ghost" href="${esc(l.url)}" target="_blank" rel="noopener"><span>${esc(l.label)}</span><i>↗</i></a></li>`).join("")}</ul>` : '<p class="mute">Холбоос алга.</p>');
  } else if (r.kind === "workshop") {
    html += sec(`Энэ шатанд буй төслүүд`, I.projects.length ? `<ul class="wp">${I.projects.map(p => `<li><a href="#" data-go="${esc(p.id)}">${esc(p.project)}</a> <span class="mute">${esc(STATUS[p.status] || p.status)}</span>
      <div class="tsum">${["next-action", "waiting", "inbox", "someday"].map(g => `<span>${GROUP_LBL[g]}: <b>${p.tasks.groups[g].length}</b></span>`).join("")}<span>7 хоногт ✔ <b>${p.tasks.done_week}</b></span></div></li>`).join("")}</ul>` : '<p class="mute">Энэ шатанд төсөл алга.</p>', "wide");
    html += sec("Сүүлийн яриа", convHtml);
  } else {
    const msg = r.kind === "vault" ? "🔒 Санхүүгийн өгөгдөл энд харагдахгүй." : r.kind === "library" ? "📚 Wiki, Research — лавлагаа, судалгааны сешнүүд." : r.kind === "archive" ? "🗄 Дууссан төсөл." : "🏢 Дүрийн сешнүүд (GTD, Architect, Creative, Portfolio).";
    html += sec("Мэдээлэл", `<p>${msg}</p><ul>${ags.map(a => `<li>${esc(a.device_name ? a.device : "🙂")} ${esc(a.name)} — ${a.human ? "itge.e" : a.state === "working" ? "ажиллаж" : "сул"}</li>`).join("")}</ul>`);
    if (r.kind !== "vault") html += sec("Сүүлийн яриа", convHtml);
  }
  $("dash").innerHTML = html;
  $("dash").querySelectorAll("[data-go]").forEach(a => a.onclick = e => { e.preventDefault(); enterRoom(a.dataset.go); });
  $("dash").querySelectorAll("[data-act]").forEach(b => b.onclick = () => openSend(b));
}
function taskGroups(t) {
  const gs = ["next-action", "waiting", "inbox", "someday"].filter(g => t.groups[g].length);
  if (!gs.length) return '<p class="mute">Нээлттэй task алга.</p>';
  return gs.map(g => `<h4 class="label">${GROUP_LBL[g]} <span class="mute mono">· ${t.groups[g].length}</span></h4><ul class="tasks">${t.groups[g].map(x => `<li><span class="pr">${esc(x.priority || "·")}</span><span class="tt">${esc(x.title)}</span>
    <span class="mute">${x.due ? "⏰ " + esc(x.due) : ""}${x.owner ? " · " + esc(x.owner) : ""}</span></li>`).join("")}</ul>`).join("");
}
function sessionsHtml(I) {
  if (!I.sessions.length) return '<p class="mute">Энэ төсөлд холбогдсон сешн алга.</p>';
  return I.sessions.map(s => `<div class="srow" data-id="${esc(s.id)}">
    <div class="sh"><span class="st ${s.state === "working" ? "w" : ""}"></span><b>${esc(s.name)}</b><span class="badge">${esc(s.device_name)}</span>${s.state === "working" ? '<span class="tag ok">✓ ажиллаж</span>' : ""}
      <span class="mute">${s.state === "working" ? "ажиллаж" : "сул"} · ${esc(s.last_seen || "тодорхойгүй")}${s.bound ? "" : " · дүрийн сешн"}</span></div>
    ${s.baton ? `<div class="bt">${s.baton.stopped ? `<p><b>Хаана зогссон:</b> ${esc(s.baton.stopped)}</p>` : ""}${s.baton.next ? `<p><b>Дараагийн алхам:</b> ${esc(s.baton.next)}</p>` : ""}<p class="mute">baton · ${esc(s.baton.ts)} · ${esc(s.baton.by)}</p></div>` : '<p class="mute">Baton алга.</p>'}
    <div class="acts">${s.channel ? `<a class="cta" href="https://discord.com/channels/${esc(S.agents.find(a => a.guild)?.guild || "@me")}" target="_blank" rel="noopener"><span>Discord руу</span><i>↗</i></a>` : ""}
      ${s.channel && I.send_channels.includes(s.channel) ? `<button data-act="message" data-ch="${esc(s.channel)}" data-id="${esc(s.id)}">Мессеж илгээх</button>` : ""}
      <button data-act="wake" data-ch="gtd" data-id="${esc(s.id)}">Сэрээх</button></div>
    <div class="sendbox" hidden></div></div>`).join("");
}
function openSend(btn) {
  const row = btn.closest(".srow"), box = row.querySelector(".sendbox");
  const kind = btn.dataset.act, ch = btn.dataset.ch, sid = btn.dataset.id;
  const s = roomInfo.sessions.find(x => x.id === sid);
  const target = kind === "wake" ? `#gtd · → ${s.name} @${(s.device_name || "pc").toLowerCase()}` : `#${ch}`;
  box.hidden = false;
  box.innerHTML = `<label>${kind === "wake" ? "Сэрээх мессеж" : "Мессеж"} → <b>${esc(target)}</b></label>
    <textarea maxlength="1500" rows="3" placeholder="${kind === "wake" ? "Юу хийхийг товч бич…" : "Мессеж…"}"></textarea>
    <div class="acts"><button class="go">Илгээх…</button><button class="cancel">Болих</button><span class="res mute"></span></div>`;
  const ta = box.querySelector("textarea"), go = box.querySelector(".go"), res = box.querySelector(".res");
  ta.focus();
  let armed = false;
  box.querySelector(".cancel").onclick = () => { box.hidden = true; box.innerHTML = ""; };
  go.onclick = async () => {
    if (!ta.value.trim()) { res.textContent = "Текст хоосон байна."; return; }
    if (!armed) { armed = true; go.textContent = `Баталгаажуул: ${target} руу илгээх`; go.classList.add("warn"); return; }
    go.disabled = true; res.textContent = "Илгээж байна…";
    try {
      const r = await fetch("/api/send", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ room: openRoom, kind, channel: ch, target: sid, text: ta.value, confirm: true }) });
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || r.status);
      res.textContent = `✔ #${j.channel} руу илгээгдлээ.`; ta.value = ""; go.textContent = "Илгээх…"; go.classList.remove("warn"); armed = false;
    } catch (e) { res.textContent = "✖ " + e.message; armed = false; go.textContent = "Илгээх…"; go.classList.remove("warn"); }
    go.disabled = false;
  };
}
function closeRoom() {
  openRoom = null; roomInfo = null; $("room").classList.remove("show");
  if (location.hash.startsWith("#room")) history.replaceState(null, "", location.pathname + (view === "office" ? "#office" : ""));
}
$("back").onclick = closeRoom;
addEventListener("keydown", e => { if (e.key === "Escape" && !/TEXTAREA/.test(document.activeElement?.tagName)) { if (openRoom) closeRoom(); else $("feed").classList.remove("open"); } });
// parallax (хулгана / gyro) — жижиг зураг дээр бага зэрэг
function parallax(dx, dy) { $("scene").style.transform = `translate(${dx * -6}px,${dy * -4}px) scale(1.05)`; }
$("thumb").addEventListener("pointermove", e => { const b = $("thumb").getBoundingClientRect(); parallax((e.clientX - b.left) / b.width - .5, (e.clientY - b.top) / b.height - .5); });
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
  $("ofsvg").querySelectorAll(".ag").forEach(g => g.onclick = () => { const a = agentById(g.dataset.id); if (a) enterRoom(a.room); });
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
  $("feedCount").textContent = items.length ? `${(S.conversations || []).length} · 24 цаг` : "";
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
  $("vTitle").textContent = VIEW_TXT[v][0]; $("vSub").textContent = VIEW_TXT[v][1];
  renderRail();
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
    if (ns !== sig) { sig = ns; renderBuilding(); renderOffice(); renderRail(); if (openRoom) renderRoom(); }
    enqueue(S.conversations || []); renderFeed(); counts(); $("err").textContent = "";
  } catch (e) { $("err").textContent = "Өгөгдөл татаж чадсангүй: " + e.message; }
}
await poll();
setInterval(poll, 30000);
if (location.hash === "#office") setView("office");
const m = location.hash.match(/^#room=(.+)$/); if (m) enterRoom(decodeURIComponent(m[1]));

// ---------- өнгөний горим (dark үндсэн, light = Inai website) ----------
function applyTheme(th) {
  if (th === "light") document.documentElement.dataset.theme = "light"; else delete document.documentElement.dataset.theme;
  $("themeBtn").textContent = th === "light" ? "☀ Light" : "☾ Dark";
  try { localStorage.setItem("fm-theme", th); } catch (e) { /* хадгалж чадахгүй ч ажиллана */ }
}
applyTheme(document.documentElement.dataset.theme === "light" ? "light" : "dark");
$("themeBtn").onclick = () => applyTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
