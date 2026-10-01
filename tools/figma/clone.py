#!/usr/bin/env python3
"""clone.py — Figma файл хооронд node хуулах (bridge-ээр). Plugin API өөр файл руу шууд хуулж чаддаггүй тул:
эх файлд node-ийг JSON болгож (frame/text/auto-layout/fill/stroke/effect), vector-ыг SVG, зургийг bytes-аар уншаад
зорилтот файлд яг хэвээр нь дахин угсарна. --component бол top-level бүрийг Component болгоно.

  python clone.py --src "Full charts" --ids 1:2,1:3 --dst "Untitled" --page "🧩 Components" --section "Charts · source" [--component]
  python clone.py --src "Full charts" --children-of 12:34 ...   (тухайн frame-ийн шууд хүүхдүүдийг тус тусад нь)
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent

SER = r"""
const IDS=__IDS__, CHILDREN_OF=__CH__;
const b64=u=>figma.base64Encode(u);
const SKIP=[];const wt=(p,ms,tag)=>Promise.race([p,new Promise(r=>setTimeout(()=>{SKIP.push(tag);r(null)},ms))]);
const imgCache={};
async function paints(ps){if(!ps||ps===figma.mixed)return [];const out=[];for(const p of ps){if(p.visible===false)continue;const q=JSON.parse(JSON.stringify(p));delete q.boundVariables;
  if(p.type==='IMAGE'&&p.imageHash){if(!imgCache[p.imageHash]){const im=figma.getImageByHash(p.imageHash);const by=im?await wt(im.getBytesAsync(),8000,'img'):null;imgCache[p.imageHash]=by?b64(by):null}q.__img=p.imageHash}out.push(q)}return out}
const GEOM=new Set(['VECTOR','BOOLEAN_OPERATION','STAR','POLYGON','LINE','ELLIPSE']);
async function ser(n,depth=0){if(n.visible===false)return null;
  const o={type:n.type,name:n.name,x:n.x,y:n.y,w:n.width,h:n.height,opacity:n.opacity,rot:n.rotation||0};
  if('blendMode' in n)o.blend=n.blendMode;
  if('effects' in n)o.effects=JSON.parse(JSON.stringify(n.effects||[]));
  // group→SVG дүрэм хасагдсан (зурагтай node-ийн export plugin-ийг гацаадаг)
  if((GEOM.has(n.type)&&!(Array.isArray(n.fills)&&n.fills.some(f=>f.type==='IMAGE')))||(n.type==='RECTANGLE'&&n.fills!==figma.mixed&&(n.fills||[]).some(f=>f.type==='IMAGE')===false&&n.cornerRadius===figma.mixed)){
    try{const sv=await wt(n.exportAsync({format:'SVG_STRING',svgOutlineText:false}),20000,'svg '+n.name);if(sv){o.svg=sv;o.type='SVG';return o}}catch(e){}}
  if(n.type==='TEXT'){const segs=n.getStyledTextSegments(['fontName','fontSize','fills','lineHeight','letterSpacing','textDecoration','textCase']);
    o.text={chars:n.characters,align:n.textAlignHorizontal,valign:n.textAlignVertical,auto:n.textAutoResize,segs:await Promise.all(segs.map(async s=>({start:s.start,end:s.end,font:s.fontName,size:s.fontSize,fills:await paints(s.fills),lh:s.lineHeight,ls:s.letterSpacing,dec:s.textDecoration,cs:s.textCase})))};return o}
  if('fills' in n)o.fills=await paints(n.fills);if('strokes' in n){o.strokes=await paints(n.strokes);o.sw=n.strokeWeight===figma.mixed?1:n.strokeWeight;o.salign=n.strokeAlign;o.dash=n.dashPattern}
  if('cornerRadius' in n){o.r=n.cornerRadius===figma.mixed?[n.topLeftRadius,n.topRightRadius,n.bottomRightRadius,n.bottomLeftRadius]:n.cornerRadius}
  if('clipsContent' in n)o.clip=n.clipsContent;
  if('layoutMode' in n&&n.layoutMode!=='NONE'){o.al={mode:n.layoutMode,gap:n.itemSpacing,cgap:n.counterAxisSpacing,wrap:n.layoutWrap,pl:n.paddingLeft,pr:n.paddingRight,pt:n.paddingTop,pb:n.paddingBottom,pa:n.primaryAxisAlignItems,ca:n.counterAxisAlignItems,ps:n.primaryAxisSizingMode,cs:n.counterAxisSizingMode}}
  if('layoutAlign' in n){o.la=n.layoutAlign;o.lg=n.layoutGrow;o.lp=n.layoutPositioning}
  if('children' in n){o.kids=[];for(const c of n.children){const s=await ser(c,depth+1);if(s)o.kids.push(s)}}
  if(n.type==='GROUP'&&o.kids){for(const k of o.kids){k.x-=n.x;k.y-=n.y}o.clip=false;o.fills=[];o.strokes=[]}
  return o}
let nodes=[];for(const id of IDS){const n=await figma.getNodeByIdAsync(id);if(n)nodes.push(n)}
for(const id of CHILDREN_OF){const n=await figma.getNodeByIdAsync(id);if(n&&'children' in n)nodes.push(...n.children)}
const out=[];for(const n of nodes){const s=await ser(n);if(s)out.push(s)}
return JSON.stringify({nodes:out,images:imgCache,skipped:SKIP});
"""

BUILD = r"""
const D=__DATA__, PAGE=__PAGE__, SECTION=__SECTION__, AS_COMP=__COMP__;
const page=figma.root.children.find(p=>p.name===PAGE)||figma.currentPage;await figma.setCurrentPageAsync(page);
page.children.filter(n=>n.name===SECTION).forEach(n=>n.remove());
const ERR=[];const safe=(f,tag)=>{try{f()}catch(e){if(ERR.length<20)ERR.push(tag+': '+String(e).slice(0,90))}};const hashes={};for(const [h,b] of Object.entries(D.images)){if(b)hashes[h]=figma.createImage(figma.base64Decode(b)).hash}
const loaded=new Set();async function font(f){const k=f.family+'|'+f.style;if(loaded.has(k))return f;try{await figma.loadFontAsync(f);loaded.add(k);return f}catch(e){const fb={family:'Inter',style:/Bold|Semi|Medium|Heavy|Black/.test(f.style)?(f.style.includes('Semi')?'Semi Bold':f.style.includes('Medium')?'Medium':'Bold'):'Regular'};await figma.loadFontAsync(fb);return fb}}
function fixPaints(ps){return (ps||[]).map(p=>{const q={...p};if(q.__img){q.imageHash=hashes[q.__img];delete q.__img;if(!q.imageHash)return null}return q}).filter(Boolean)}
async function build(o,parent,top){try{return await build0(o,parent,top)}catch(e){if(ERR.length<30)ERR.push('FAIL '+o.type+' '+o.name+': '+String(e&&e.message||e).slice(0,120));return null}}
async function build0(o,parent,top){let n;
  if(o.type==='SVG'){try{n=figma.createNodeFromSvg(o.svg)}catch(e){ERR.push('svg '+o.name);n=figma.createFrame();n.fills=[]}n.name=o.name}
  else if(o.type==='TEXT'){n=figma.createText();const f0=await font(o.text.segs[0]?o.text.segs[0].font:{family:'Inter',style:'Regular'});n.fontName=f0;n.characters=o.text.chars;
    for(const s of o.text.segs){const f=await font(s.font);n.setRangeFontName(s.start,s.end,f);n.setRangeFontSize(s.start,s.end,s.size);n.setRangeFills(s.start,s.end,fixPaints(s.fills));try{n.setRangeLineHeight(s.start,s.end,s.lh);n.setRangeLetterSpacing(s.start,s.end,s.ls);n.setRangeTextDecoration(s.start,s.end,s.dec);n.setRangeTextCase(s.start,s.end,s.cs)}catch(e){}}
    n.textAlignHorizontal=o.text.align;n.textAlignVertical=o.text.valign;n.textAutoResize=o.text.auto==='TRUNCATE'?'NONE':o.text.auto;if(o.text.auto!=='WIDTH_AND_HEIGHT')n.resize(Math.max(o.w,1),Math.max(o.h,1))}
  else if(o.type==='RECTANGLE'){n=figma.createRectangle()}
  else{n=((top&&AS_COMP)||o.type==='COMPONENT')?figma.createComponent():figma.createFrame()}
  safe(()=>{n.name=o.name},'name');
  if(o.type!=='SVG'&&o.type!=='TEXT'){safe(()=>n.resize(Math.max(o.w,.01),Math.max(o.h,.01)),'resize');if(o.fills)safe(()=>n.fills=fixPaints(o.fills),'fills '+o.name);if(o.strokes){safe(()=>{n.strokes=fixPaints(o.strokes);n.strokeWeight=o.sw;if(o.salign)n.strokeAlign=o.salign;if(o.dash)n.dashPattern=o.dash},'strokes')}
    if(o.r!==undefined)safe(()=>{if(Array.isArray(o.r)){[n.topLeftRadius,n.topRightRadius,n.bottomRightRadius,n.bottomLeftRadius]=o.r}else n.cornerRadius=o.r},'radius');
    if('clip' in o)safe(()=>{n.clipsContent=o.clip},'clip')}
  if(o.effects&&'effects' in n)safe(()=>{n.effects=o.effects.map(e=>{const q={...e};delete q.boundVariables;return q})},'effects')
  safe(()=>{n.opacity=(typeof o.opacity==='number')?o.opacity:1},'opacity');safe(()=>{if(o.blend&&o.blend!=='PASS_THROUGH')n.blendMode=o.blend},'blend');
  try{parent.appendChild(n)}catch(e){ERR.push('append '+o.name+': '+String(e).slice(0,80));return n}
  if(o.al&&'layoutMode' in n)safe(()=>{const a=o.al;n.layoutMode=a.mode;n.itemSpacing=a.gap;if(a.wrap)n.layoutWrap=a.wrap;if(a.wrap==='WRAP')n.counterAxisSpacing=a.cgap||0;n.paddingLeft=a.pl;n.paddingRight=a.pr;n.paddingTop=a.pt;n.paddingBottom=a.pb;n.primaryAxisAlignItems=a.pa;n.counterAxisAlignItems=a.ca},'layout');
  if(o.kids)for(const k of o.kids)await build(k,n,false);
  if(o.al&&'layoutMode' in n)safe(()=>{n.primaryAxisSizingMode=o.al.ps;n.counterAxisSizingMode=o.al.cs;if(o.al.ps==='FIXED'||o.al.cs==='FIXED')n.resize(Math.max(o.w,.01),Math.max(o.h,.01))},'sizing');
  const inAL=parent.layoutMode&&parent.layoutMode!=='NONE';
  safe(()=>{if(inAL){if(o.lp==='ABSOLUTE'){n.layoutPositioning='ABSOLUTE';n.x=o.x;n.y=o.y}else{if(o.la)n.layoutAlign=o.la;if(o.lg)n.layoutGrow=o.lg}}else if(!top){n.x=o.x;n.y=o.y}},'pos');
  if(o.rot&&!inAL)safe(()=>n.rotation=o.rot,'rot');
  if(o.type==='SVG'&&!inAL){n.resize(Math.max(o.w,.01),Math.max(o.h,.01))}
  return n}
const sec=figma.createSection();sec.name=SECTION;page.appendChild(sec);
const tops=[];let x=64,y=64,rowH=0;const MAXW=4200;
for(const o of D.nodes){const n=await build(o,sec,true);if(!n)continue;if(x+o.w>MAXW){x=64;y+=rowH+64;rowH=0}n.x=x;n.y=y;x+=o.w+48;rowH=Math.max(rowH,o.h);tops.push(n)}
sec.resizeWithoutConstraints(Math.max(...tops.map(t=>t.x+t.width))+64,Math.max(...tops.map(t=>t.y+t.height))+64);
const others=page.children.filter(n=>n!==sec);sec.x=0;sec.y=others.length?Math.max(...others.map(n=>n.y+n.height))+200:0;
figma.viewport.scrollAndZoomIntoView([sec]);return {section:sec.id,count:tops.length,errors:ERR,names:tops.map(t=>t.name).slice(0,60)};
"""


def run(doc, code, t=1800):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(code)
    r = subprocess.run([sys.executable, str(HERE / "fig.py"), "--doc", doc, "run", "-t", str(t), "-f", f.name], capture_output=True, text=True, encoding="utf-8")
    try:
        return json.loads(r.stdout)
    except Exception:
        sys.exit(r.stdout[-2000:] or r.stderr[-2000:])


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--src", required=True); a.add_argument("--dst", required=True)
    a.add_argument("--ids", default=""); a.add_argument("--children-of", default="")
    a.add_argument("--page", default="🧩 Components"); a.add_argument("--section", default="Cloned")
    a.add_argument("--component", action="store_true")
    o = a.parse_args()
    ids = [i for i in o.ids.split(",") if i]; ch = [i for i in o.children_of.split(",") if i]
    data = run(o.src, SER.replace("__IDS__", json.dumps(ids)).replace("__CH__", json.dumps(ch)))
    if isinstance(data, str):
        data = json.loads(data)
    if "error" in data:
        sys.exit(data)
    print("serialized:", len(data["nodes"]), "nodes ·", len(data["images"]), "images · skipped:", len(data.get("skipped", [])), data.get("skipped", [])[:8])
    code = BUILD.replace("__DATA__", json.dumps(data)).replace("__PAGE__", json.dumps(o.page)).replace("__SECTION__", json.dumps(o.section)).replace("__COMP__", "true" if o.component else "false")
    print(json.dumps(run(o.dst, code), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
