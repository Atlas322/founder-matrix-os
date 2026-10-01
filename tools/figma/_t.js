
const IDS=["1:1241"], CHILDREN_OF=[];
const b64=u=>figma.base64Encode(u);
const SKIP=[];const wt=(p,ms,tag)=>{TR.push('wt '+tag);return Promise.race([p,new Promise(r=>setTimeout(()=>{SKIP.push(tag);r(null)},ms))])};
const imgCache={};
async function paints(ps){if(!ps||ps===figma.mixed)return [];const out=[];for(const p of ps){if(p.visible===false)continue;const q=JSON.parse(JSON.stringify(p));delete q.boundVariables;
  if(p.type==='IMAGE'&&p.imageHash){if(!imgCache[p.imageHash]){const im=figma.getImageByHash(p.imageHash);const by=im?await wt(im.getBytesAsync(),8000,'img'):null;imgCache[p.imageHash]=by?b64(by):null}q.__img=p.imageHash}out.push(q)}return out}
const GEOM=new Set(['VECTOR','BOOLEAN_OPERATION','STAR','POLYGON','LINE','ELLIPSE']);
const TR=[];async function ser(n,depth=0){TR.push('>'+n.type+':'+n.name);if(n.visible===false)return null;
  const o={type:n.type,name:n.name,x:n.x,y:n.y,w:n.width,h:n.height,opacity:n.opacity,rot:n.rotation||0};
  if('blendMode' in n)o.blend=n.blendMode;
  if('effects' in n)o.effects=JSON.parse(JSON.stringify(n.effects||[]));
  if((n.type==='GROUP'||n.type==='FRAME'||n.type==='INSTANCE'||n.type==='BOOLEAN_OPERATION')&&depth>0&&n.width*n.height<250000&&!(Array.isArray(n.fills)&&n.fills.some(f=>f.type==='IMAGE'))&&!n.findOne(x=>x.type==='TEXT'||(('fills' in x)&&Array.isArray(x.fills)&&x.fills.some(f=>f.type==='IMAGE')))&&!(('layoutMode' in n)&&n.layoutMode!=='NONE'&&n.children.length>1)){
    try{const sv=await wt(n.exportAsync({format:'SVG_STRING'}),8000,'svg '+n.name);if(sv){o.svg=sv;o.type='SVG';return o}}catch(e){}}
  if((GEOM.has(n.type)&&!(Array.isArray(n.fills)&&n.fills.some(f=>f.type==='IMAGE')))||(n.type==='RECTANGLE'&&n.fills!==figma.mixed&&(n.fills||[]).some(f=>f.type==='IMAGE')===false&&n.cornerRadius===figma.mixed)){
    try{const sv=await wt(n.exportAsync({format:'SVG_STRING',svgOutlineText:false}),8000,'svg '+n.name);if(sv){o.svg=sv;o.type='SVG';return o}}catch(e){}}
  if(n.type==='TEXT'){const segs=n.getStyledTextSegments(['fontName','fontSize','fills','lineHeight','letterSpacing','textDecoration','textCase']);
    o.text={chars:n.characters,align:n.textAlignHorizontal,valign:n.textAlignVertical,auto:n.textAutoResize,segs:await Promise.all(segs.map(async s=>({start:s.start,end:s.end,font:s.fontName,size:s.fontSize,fills:await paints(s.fills),lh:s.lineHeight,ls:s.letterSpacing,dec:s.textDecoration,cs:s.textCase})))};return o}
  if('fills' in n)o.fills=await paints(n.fills);if('strokes' in n){o.strokes=await paints(n.strokes);o.sw=n.strokeWeight===figma.mixed?1:n.strokeWeight;o.salign=n.strokeAlign;o.dash=n.dashPattern}
  if('cornerRadius' in n){o.r=n.cornerRadius===figma.mixed?[n.topLeftRadius,n.topRightRadius,n.bottomRightRadius,n.bottomLeftRadius]:n.cornerRadius}
  if('clipsContent' in n)o.clip=n.clipsContent;
  if('layoutMode' in n&&n.layoutMode!=='NONE'){o.al={mode:n.layoutMode,gap:n.itemSpacing,cgap:n.counterAxisSpacing,wrap:n.layoutWrap,pl:n.paddingLeft,pr:n.paddingRight,pt:n.paddingTop,pb:n.paddingBottom,pa:n.primaryAxisAlignItems,ca:n.counterAxisAlignItems,ps:n.primaryAxisSizingMode,cs:n.counterAxisSizingMode}}
  if('layoutAlign' in n){o.la=n.layoutAlign;o.lg=n.layoutGrow;o.lp=n.layoutPositioning}
  if('children' in n){o.kids=[];for(const c of n.children){const s=await ser(c,depth+1);if(s)o.kids.push(s)}}
  return o}
const main=async()=>{let nodes=[];for(const id of IDS){const n=await figma.getNodeByIdAsync(id);if(n)nodes.push(n)}
for(const id of CHILDREN_OF){const n=await figma.getNodeByIdAsync(id);if(n&&'children' in n)nodes.push(...n.children)}
const out=[];for(const n of nodes){const s=await ser(n);if(s)out.push(s)}
return 'DONE';
};const r=await Promise.race([main(),new Promise(x=>setTimeout(()=>x('TIMEOUT'),20000))]);return {r,trace:TR.slice(-8),n:TR.length};