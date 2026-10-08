// 📅 Цаглабар — хуанли (Өдөр / 7 хоног / Сар), огноогүй тавиур, чирж товлох (баталгаажуулалттай, буцаах боломжтой).
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const STAGE_COL = { "Brief": "var(--ka-brief)", "Бэлтгэл": "var(--ka-beltgel)", "Дизайн": "var(--ka-dizain)", "Хөгжүүлэлт": "var(--ka-hugjuulelt)", "Контент": "var(--ka-kontent)" };
const DOW = ["НЯ", "ДА", "МЯ", "ЛХ", "ПҮ", "БА", "БЯ"];
const STATUS = { "next-action": "дараагийн алхам", waiting: "хүлээж буй", inbox: "inbox", someday: "хэзээ нэгэн цагт", completed: "дууссан", done: "дууссан", cancelled: "цуцалсан", scheduled: "товлосон" };
const H0 = 8, H1 = 21, ROW = 52;

let view = "week", anchor = new Date(), D = null, focusProject = null;
const undoStack = [];

// ---------- огноо ----------
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const parse = s => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const monday = d => addDays(d, -((d.getDay() + 6) % 7));
const todayIso = () => iso(new Date());
function rangeOf() {
  if (view === "day") return [anchor, anchor];
  if (view === "week") { const a = monday(anchor); return [a, addDays(a, 6)]; }
  const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1), a = monday(first);
  return [a, addDays(a, 41)];
}
const shortDate = s => { const d = parse(s); return `${d.getMonth() + 1}/${d.getDate()}`; };

// ---------- өгөгдөл ----------
async function load() {
  const [a, b] = rangeOf();
  const isPhone = innerWidth <= 700;
  const from = isPhone ? new Date() : a, to = isPhone ? addDays(new Date(), 13) : b;
  try {
    const r = await fetch(`/api/calendar?from=${iso(from)}&to=${iso(to)}`, { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    D = await r.json(); $("err").textContent = "";
    render();
  } catch (e) { $("err").textContent = "Өгөгдөл татаж чадсангүй: " + e.message; }
}
const agent = id => D.agents.find(a => a.id === id);

// ---------- блок ----------
function chipHtml(it) {
  const a = it.agent && agent(it.agent);
  if (!a) return it.owner ? `<span class="chip"><i>·</i>${esc(it.owner)}</span>` : "";
  const w = it.state === "working";
  return `<span class="chip ${w ? "w" : ""}"><i>${a.human ? "🙂" : esc((a.name || "?").trim().slice(0, 2))}</i>${esc(a.human ? "itge.e" : a.name.replace(/^\S+\s/, ""))}${a.device_name ? " · " + esc(a.device_name) : ""}</span>`;
}
function blockHtml(it, extra = "") {
  const col = it.kind === "event" ? "var(--link)" : (STAGE_COL[it.stage] || "var(--text-2)");
  const cls = ["blk", it.kind === "event" ? "ev" : "", it.state === "done" ? "done" : it.state === "working" ? "working" : "sched",
    focusProject && it.project === focusProject ? "hl" : ""].join(" ");
  const drag = it.kind === "task" && it.state !== "done";
  const icon = it.state === "done" ? "✅ " : it.state === "working" ? "🟢 " : "";
  return `<div class="${cls}" style="--c:${col}" ${extra} data-path="${esc(it.path)}" ${drag ? 'draggable="true"' : ""} tabindex="0">
    ${it.time ? `<div class="tm">${esc(it.time)}</div>` : ""}<div class="tt">${icon}${esc(it.title)}</div>
    ${it.project ? `<div class="tm">${esc(it.project)}${it.stage ? " · " + esc(it.stage) : ""}</div>` : ""}${chipHtml(it)}</div>`;
}
const itemsOn = d => D.items.filter(i => i.date === d);
const msOn = d => D.milestones.filter(m => m.date === d);
const msHtml = m => `<div class="ms ${m.done ? "done" : ""}" style="--c:${STAGE_COL[m.stage] || "var(--accent)"}" data-room="${esc(m.room || "")}" title="${esc(m.project)}"><b></b>${esc(m.label)}</div>`;

// ---------- view-үүд ----------
function renderWeek(days) {
  const t = todayIso();
  let h = `<div class="cols" style="--n:${days.length}"><div class="corner"></div>`;
  h += days.map(d => { const dt = parse(d); return `<div class="dh ${d === t ? "today" : ""}">${DOW[dt.getDay()]} ${dt.getDate()}${D.daily.includes(d) ? '<span class="dd" title="өдрийн тэмдэглэл"></span>' : ""}</div>`; }).join("");
  h += `<div class="alllbl">өдөр</div>`;
  h += days.map(d => `<div class="allday drop" data-date="${d}">${msOn(d).map(msHtml).join("")}${itemsOn(d).filter(i => !i.time).map(i => blockHtml(i)).join("")}</div>`).join("");
  h += `<div>${Array.from({ length: H1 - H0 }, (_, k) => `<div class="tl">${String(H0 + k).padStart(2, "0")}:00</div>`).join("")}</div>`;
  h += days.map(d => {
    const timed = itemsOn(d).filter(i => i.time).map(i => {
      const [hh, mm] = i.time.split(":").map(Number); const top = Math.max(0, (hh - H0) * ROW + mm / 60 * ROW);
      return blockHtml(i, `style="--c:${i.kind === "event" ? "var(--link)" : STAGE_COL[i.stage] || "var(--text-2)"};top:${top}px;min-height:${ROW - 6}px" data-timed="1"`).replace('class="blk', 'class="blk timed');
    }).join("");
    const now = new Date(); const nowLine = d === t && now.getHours() >= H0 && now.getHours() < H1 ? `<div class="now" style="top:${(now.getHours() - H0) * ROW + now.getMinutes() / 60 * ROW}px"></div>` : "";
    return `<div class="hours drop" data-date="${d}">${Array.from({ length: H1 - H0 }, () => '<div class="hl"></div>').join("")}${timed}${nowLine}</div>`;
  }).join("");
  $("grid").innerHTML = h + "</div>";
}
function renderMonth(a) {
  const t = todayIso(), m = anchor.getMonth();
  let h = `<div class="mhead">${["ДА", "МЯ", "ЛХ", "ПҮ", "БА", "БЯ", "НЯ"].map(x => `<div>${x}</div>`).join("")}</div><div class="month">`;
  for (let k = 0; k < 42; k++) {
    const dt = addDays(a, k), d = iso(dt), its = itemsOn(d);
    h += `<div class="mcell drop ${d === t ? "today" : ""} ${dt.getMonth() !== m ? "out" : ""}" data-date="${d}"><span class="n">${dt.getDate()}${D.daily.includes(d) ? " ·" : ""}</span>
      ${msOn(d).map(msHtml).join("")}${its.slice(0, 3).map(i => blockHtml(i)).join("")}${its.length > 3 ? `<span class="mute mono">+${its.length - 3}</span>` : ""}</div>`;
  }
  $("grid").innerHTML = h + "</div>";
}
function renderAgenda() {
  const t = todayIso();
  const days = Array.from({ length: 14 }, (_, k) => iso(addDays(new Date(), k)));
  const late = D.items.filter(i => i.date < t && i.state !== "done");
  $("agenda").innerHTML = `<div class="label" style="margin-bottom:6px">${esc(new Date().toLocaleDateString("mn-MN", { weekday: "long", month: "long", day: "numeric" }))}</div>
    <h2 style="font:400 var(--t-h2)/1.1 var(--font-display);letter-spacing:-1px;margin:0 0 14px">Өнөөдрийн хуваарь.</h2>
    ${late.length ? `<div class="ag-day"><h4>Хоцорсон · ${late.length}</h4>${late.map(i => blockHtml(i)).join("")}</div>` : ""}` +
    days.map(d => { const its = itemsOn(d), ms = msOn(d); if (!its.length && !ms.length && d !== t) return ""; const dt = parse(d);
      return `<div class="ag-day ${d === t ? "today" : ""}"><h4>${d === t ? "Өнөөдөр" : DOW[dt.getDay()]} · ${dt.getMonth() + 1}/${dt.getDate()}</h4>${ms.map(msHtml).join("")}${its.map(i => blockHtml(i)).join("") || '<p class="mute">Товлосон зүйл алга.</p>'}</div>`; }).join("");
}
function renderShelf() {
  const n = D.shelf.reduce((s, g) => s + g.tasks.length, 0);
  $("shelfN").textContent = n;
  $("shelf").innerHTML = D.shelf.map(g => `<h4 style="--c:${STAGE_COL[g.stage] || "var(--text-2)"}"><i></i>${esc(g.project)} · ${g.tasks.length}</h4>${g.tasks.map(i => blockHtml(i)).join("")}`).join("") || '<p class="mute">Огноогүй next-action алга.</p>';
}
function renderWho() {
  const ag = D.agents.filter(a => !a.human).sort((a, b) => (b.state === "working") - (a.state === "working") || String(b.last_seen || "").localeCompare(String(a.last_seen || "")));
  $("who").innerHTML = ag.slice(0, 8).map(a => `<li><span class="st ${a.state === "working" ? "w" : ""}"></span><span><b>${esc(a.name)}</b> <span class="mute mono">${esc(a.device_name)}</span><small>${a.state === "working" ? "ажиллаж" : "сул"}</small></span><span class="t">${esc(a.last_seen ? a.last_seen.slice(5) : "—")}</span></li>`).join("");
}
function render() {
  const [a, b] = rangeOf();
  const T = { day: ["Өдөр · Агенттай.", "Өнөөдрийн блокууд · агентын chip"], week: ["Долоо хоног · Агенттай.", "Блок бүр агентын chip-тэй · task-ийг өдөр рүү чирж оноох"], month: ["Сар · Агенттай.", "Сарын тойм · task-ийг өдөр рүү чирж оноох"] }[view];
  $("vTitle").textContent = T[0]; $("vSub").textContent = T[1];
  $("range").textContent = view === "day" ? shortDate(iso(a)) : `${shortDate(iso(a))} – ${shortDate(iso(b))}`;
  document.querySelectorAll(".seg [data-v]").forEach(x => x.classList.toggle("on", x.dataset.v === view));
  if (innerWidth <= 700) renderAgenda();
  else if (view === "month") renderMonth(a);
  else renderWeek(view === "day" ? [iso(a)] : Array.from({ length: 7 }, (_, k) => iso(addDays(a, k))));
  renderShelf(); renderWho(); wire();
  if (view !== "month") { const now = document.querySelector(".now"); if (now) now.scrollIntoView({ block: "center" }); }
}

// ---------- харилцаа: дарах, чирэх ----------
const findItem = p => D.items.find(i => i.path === p) || D.shelf.flatMap(g => g.tasks).find(i => i.path === p);
function wire() {
  document.querySelectorAll(".blk").forEach(el => {
    el.onclick = () => showCard(findItem(el.dataset.path));
    el.onkeydown = e => { if (e.key === "Enter") showCard(findItem(el.dataset.path)); };
    el.ondragstart = e => { e.dataTransfer.setData("text/plain", el.dataset.path); e.dataTransfer.effectAllowed = "move"; };
  });
  document.querySelectorAll(".ms[data-room]").forEach(el => el.onclick = () => { if (el.dataset.room) location.href = "/#room=" + encodeURIComponent(el.dataset.room); });
  document.querySelectorAll(".drop").forEach(z => {
    z.ondragover = e => { e.preventDefault(); z.classList.add("drop-on"); };
    z.ondragleave = () => z.classList.remove("drop-on");
    z.ondrop = e => { e.preventDefault(); z.classList.remove("drop-on"); const p = e.dataTransfer.getData("text/plain"); const it = findItem(p); if (it && it.date !== z.dataset.date) askSchedule(it, z.dataset.date); };
  });
}
function showCard(it) {
  if (!it) return;
  const a = it.agent && agent(it.agent);
  const obs = `obsidian://open?vault=${encodeURIComponent(D.vault_name)}&file=${encodeURIComponent(it.path.replace(/\.md$/, ""))}`;
  $("card").hidden = false;
  $("card").innerHTML = `<div class="strip"><span class="label">${it.kind === "event" ? "Үйл явдал" : "Task"}</span><button id="cardX" aria-label="Хаах" style="padding:2px 8px">×</button></div><div class="body">
    <h3>${esc(it.title)}</h3>
    <dl><dt>Огноо</dt><dd class="mono">${esc(it.date || "огноогүй")}${it.time ? " " + esc(it.time) : ""}</dd>
    <dt>Төсөл</dt><dd>${esc(it.project || "—")}</dd><dt>Шат</dt><dd>${esc(it.stage || "—")}</dd>
    <dt>Төлөв</dt><dd>${esc(STATUS[it.status] || it.status)} · ${it.state === "working" ? "🟢 ажиллаж" : it.state === "done" ? "✅ дууссан" : "товлосон"}</dd>
    <dt>Эзэн</dt><dd>${a ? esc(a.human ? "itge.e" : a.name) + (a.device_name ? ` <span class="mute mono">${esc(a.device_name)}</span>` : "") : esc(it.owner || "—")}</dd>
    ${it.priority ? `<dt>Ач холбогдол</dt><dd>${esc(it.priority)}</dd>` : ""}</dl>
    <div class="acts"><a class="ghost" href="${obs}"><span>Obsidian-д нээх</span><i>↗</i></a>${it.room ? `<a class="ghost" href="/#room=${encodeURIComponent(it.room)}"><span>Оффис дахь өрөө</span><i>↗</i></a>` : ""}</div></div>`;
  $("cardX").onclick = () => { $("card").hidden = true; };
}
// баталгаажуулалт → POST /api/schedule (зөвхөн due: мөр)
function askSchedule(it, date) {
  $("cfT").textContent = `«${it.title}» → ${shortDate(date)} товлох уу?`;
  $("cfS").textContent = `Зөвхөн task файлын «due:» мөр ${it.due_raw || it.date || "(хоосон)"} → ${date} болно. Бусад нь өөрчлөгдөхгүй.`;
  $("cfOk").textContent = "Товлох";
  $("confirm").showModal();
  $("cfNo").onclick = () => $("confirm").close();
  $("cfOk").onclick = async () => { $("confirm").close(); await schedule(it.path, date, it.title, true); };
}
async function schedule(path, due, title, pushUndo) {
  try {
    const r = await fetch("/api/schedule", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ task_path: path, due, confirm: true }) });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || r.status);
    if (pushUndo) undoStack.push({ path, prev: j.previous, title });
    toast(pushUndo ? `«${title}» → ${due ? shortDate(due) : "огноогүй"} товлогдлоо.` : `Буцаалаа: «${title}».`, pushUndo);
    await load();
  } catch (e) { toast("✖ " + e.message, false); }
}
function toast(msg, canUndo) {
  $("toastT").textContent = msg; $("undo").hidden = !canUndo || !undoStack.length; $("toast").classList.add("show");
  clearTimeout(toast.t); toast.t = setTimeout(() => $("toast").classList.remove("show"), 8000);
}
$("undo").onclick = async () => { const u = undoStack.pop(); if (!u) return; $("toast").classList.remove("show"); await schedule(u.path, u.prev, u.title, false); };

// ---------- удирдлага ----------
document.querySelectorAll(".seg [data-v]").forEach(b => b.onclick = () => { view = b.dataset.v; load(); });
$("prev").onclick = () => { anchor = view === "month" ? new Date(anchor.getFullYear(), anchor.getMonth() - 1, 1) : addDays(anchor, view === "day" ? -1 : -7); load(); };
$("next").onclick = () => { anchor = view === "month" ? new Date(anchor.getFullYear(), anchor.getMonth() + 1, 1) : addDays(anchor, view === "day" ? 1 : 7); load(); };
$("today").onclick = () => { anchor = new Date(); load(); };
addEventListener("keydown", e => { if (e.key === "Escape") $("card").hidden = true; });
function applyTheme(th) {
  if (th === "light") document.documentElement.dataset.theme = "light"; else delete document.documentElement.dataset.theme;
  $("themeBtn").textContent = th === "light" ? "☀ Light" : "☾ Dark";
  try { localStorage.setItem("fm-theme", th); } catch (e) { /* хадгалахгүй ч болно */ }
}
applyTheme(document.documentElement.dataset.theme === "light" ? "light" : "dark");
$("themeBtn").onclick = () => applyTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
const m = location.hash.match(/project=([^&]+)/); if (m) focusProject = decodeURIComponent(m[1]);
let lastW = innerWidth; addEventListener("resize", () => { if ((lastW <= 700) !== (innerWidth <= 700)) { lastW = innerWidth; load(); } });
await load();
setInterval(load, 60000);
