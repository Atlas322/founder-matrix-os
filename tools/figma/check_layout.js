// Давхцал шалгагч: TEXT node-ууд хоорондоо эсвэл frame-ийн ирмэгээс хальсныг илрүүлнэ.
const page=figma.root.children.find(p=>p.name.includes('Foundations')); await page.loadAsync();
const sec=page.children.find(n=>n.name.startsWith('6 · MCP carousel'));
const slides=sec.children.filter(c=>c.type==='FRAME' && c.name.indexOf('_')!==0);
const rep=[];
for(const s of slides){
  const sb=s.absoluteBoundingBox;
  const texts=s.findAll(n=>n.type==='TEXT' && n.visible && n.opacity>0.05).map(n=>({n:n.name,b:n.absoluteBoundingBox,h:Math.round(n.height)}));
  const hits=[];
  for(let i=0;i<texts.length;i++) for(let j=i+1;j<texts.length;j++){
    const a=texts[i].b,b=texts[j].b; if(!a||!b) continue;
    const ox=Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x);
    const oy=Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y);
    if(ox>2 && oy>2) hits.push(texts[i].n+' ✕ '+texts[j].n+' ('+Math.round(ox)+'×'+Math.round(oy)+')');
  }
  const out=[];
  for(const t of texts){ const b=t.b; if(!b) continue;
    if(b.y+b.height > sb.y+1260+8) out.push(t.n+' доошоо '+Math.round(b.y+b.height-sb.y-1260)+'px');
    if(b.x < sb.x+88) out.push(t.n+' зүүн хязгаараас '+Math.round(sb.x+88-b.x)+'px');
    if(b.x+b.width > sb.x+992) out.push(t.n+' баруун хязгаараас '+Math.round(b.x+b.width-sb.x-992)+'px');
  }
  if(hits.length||out.length) rep.push({slide:s.name, overlap:hits, outside:out});
}
return {slides:slides.length, problems:rep};
