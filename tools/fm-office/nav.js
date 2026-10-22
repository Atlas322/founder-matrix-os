// FM Office — бүх хуудсанд нэг ижил цэс. <script src="/nav.js" defer></script> гэж оруулна.
// Дээд төвд жижиг «шил» товч (☰ + одоогийн хуудас); дарахад бүх модуль, M товч = нээх/хаах, Esc = хаах.
(() => {
  const PAGES = [
    ['/', 'Нүүр', 'Second Brain'],
    ['/home', 'Гэр', 'Second Brain мини хот'],
    ['/khuvsgul', 'Хөвсгөл', 'миний эрэг · Second Brain'],
    ['/garden', 'Цэцэрлэг', 'суугаад ажиллах'],
    ['/gallery', 'Gallery', 'сэдвээр reference'],
    ['/fpv', 'Gallery FPV', 'алхаж үзэх'],
    ['/hall?topics=1', 'POV танхим', 'YouTube · highlight → атом'],
    
    ['/office25d', 'Агентын оффис', '2.5D · алхдаг агентууд'],
    ['/control', 'Удирдлагын өрөө', 'агентууд · agent tree'],
    ['/campus', 'Оффис', 'байгууллагын кампус'],
    ['/map', 'Хот', 'газрын зураг'],
    ['/calendar', 'Цаглабар', 'календарь'],
  ];
  const here = location.pathname, cur = PAGES.find(p => p[0].split('?')[0] === here) || [here, 'FM Office'];
  const css = `
  #fmnav { position:fixed; top:12px; left:50%; transform:translateX(-50%); z-index:9999; font:500 13px/1.3 "Inter Tight", Inter, system-ui, sans-serif; }
  #fmnav > button { display:flex; gap:8px; align-items:center; padding:6px 14px; cursor:pointer; color:#1A1A1A; background:#fff; border:1px solid #1A1A1A; font:inherit; }
  #fmnav > button:hover { background:#1A1A1A; color:#fff; }
  #fmnav > button b { font-weight:600; } #fmnav > button span { opacity:.6; font:600 11px ui-monospace, monospace; letter-spacing:.1em; }
  #fmnav nav { display:none; position:absolute; top:calc(100% + 8px); left:50%; transform:translateX(-50%); width:min(520px, 92vw);
    grid-template-columns:1fr 1fr; gap:0; padding:0; background:#fff; border:1px solid #1A1A1A; }
  #fmnav.open nav { display:grid; }
  #fmnav a { display:block; padding:10px 14px; color:#1A1A1A; text-decoration:none; border-bottom:1px solid #e3e0d8; }
  #fmnav a:hover, #fmnav a:focus-visible { background:#F3F2EE; outline:none; }
  #fmnav a.on { background:#D6453D; color:#fff; } #fmnav a small { display:block; opacity:.65; font-size:11px; margin-top:2px; }
  @media (max-width:600px) { #fmnav nav { grid-template-columns:1fr; } }`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  const box = document.createElement('div'); box.id = 'fmnav';
  box.innerHTML = `<button type="button" aria-expanded="false" aria-controls="fmnav-menu">☰ <b>${cur[1]}</b><span>M</span></button>
    <nav id="fmnav-menu">${PAGES.map(([h, t, s]) => `<a href="${h}" class="${h.split('?')[0] === here ? 'on' : ''}">${t}<small>${s}</small></a>`).join('')}</nav>`;
  document.body.appendChild(box);
  const btn = box.querySelector('button');
  const set = o => { box.classList.toggle('open', o); btn.setAttribute('aria-expanded', o); };
  btn.onclick = e => { e.stopPropagation(); set(!box.classList.contains('open')); };
  document.addEventListener('click', e => { if (!box.contains(e.target)) set(false); });
  addEventListener('keydown', e => {
    if (/INPUT|TEXTAREA/.test(document.activeElement?.tagName)) return;
    if (e.key === 'Escape') set(false);
    if (e.key === 'm' || e.key === 'M') { if (document.pointerLockElement) document.exitPointerLock(); set(!box.classList.contains('open')); }
  });
})();
