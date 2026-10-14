// FM Office-ийн хуудсуудын (office2d, calendar, 3D) нийтлэг туслахууд — нэг газар (GitNexus 2026-10-14: esc 3 файлд давхардсан байв).
export const $ = id => document.getElementById(id);
export const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
export const STAGE_COL = { "Brief": "var(--ka-brief)", "Бэлтгэл": "var(--ka-beltgel)", "Дизайн": "var(--ka-dizain)", "Хөгжүүлэлт": "var(--ka-hugjuulelt)", "Контент": "var(--ka-kontent)" };
