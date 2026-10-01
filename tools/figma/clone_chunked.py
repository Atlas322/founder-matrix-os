#!/usr/bin/env python3
"""clone_chunked.py — clone.py-ийн SER/BUILD-ийг ашиглан том frame-ийг ХЭСЭГЛЭН хуулна, явцыг лог руу бичнэ.
Frame бүрийг: (1) бүрхүүл (хүүхэдгүй) → (2) хүүхэд бүрийг тусад нь serialize+build. Хэсэг бүр тусдаа timeout-той,
гацвал алгасаад үргэлжилнэ. Явц: _system/tools/figma/clone_progress.log  (tail -f хийж харна).

  python clone_chunked.py --src Designo --ids 1:933,1:1340 --dst Untitled --page "📱 Templates" --section "Source · Designo LMS"
"""
import argparse, json, sys, time, datetime as dt
from pathlib import Path
import clone

sys.stdout.reconfigure(encoding="utf-8")
LOG = Path(__file__).parent / "clone_progress.log"


def log(msg):
    line = f"{dt.datetime.now():%H:%M:%S}  {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def ser(src, ids, t):
    code = clone.SER.replace("__IDS__", json.dumps(ids)).replace("__CH__", "[]")
    d = clone.run(src, code, t)
    return json.loads(d) if isinstance(d, str) else d


SHELL = r"""
const D=__D__,PAGE=__PAGE__,SECTION=__SECTION__,X=__X__,AS_COMP=false;
const page=figma.root.children.find(p=>p.name===PAGE);await figma.setCurrentPageAsync(page);
let sec=page.children.find(n=>n.name===SECTION&&n.type==='SECTION');
if(!sec){sec=figma.createSection();sec.name=SECTION;page.appendChild(sec);const o=page.children.filter(n=>n!==sec);sec.x=0;sec.y=o.length?Math.max(...o.map(n=>n.y+n.height))+200:0;sec.resizeWithoutConstraints(200,200)}
const o=D.nodes[0];const kids=o.kids;o.kids=[];
__BUILDFN__
const n=await build(o,sec,true);if(!n)return {error:'build: '+ERR.join(' | ')};n.x=X;n.y=64;sec.resizeWithoutConstraints(Math.max(sec.width,X+n.width+64),Math.max(sec.height,n.height+128));
return {id:n.id,al:!!o.al,errors:ERR};
"""

CHILD = r"""
const D=__D__,PARENT=__PARENT__,AS_COMP=false;
const parent=await figma.getNodeByIdAsync(PARENT);
__BUILDFN__
const n=await build(D.nodes[0],parent,false);return {ok:!!n,errors:ERR};
"""


def buildfn(images):
    # clone.BUILD-аас helper-үүдийг (hashes/font/fixPaints/build/build0) авна
    b = clone.BUILD
    start = b.index("const ERR=[]")
    end = b.index("const sec=figma.createSection()")
    return b[start:end].replace("Object.entries(D.images)", "Object.entries(" + json.dumps(images) + ")")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--src", required=True); a.add_argument("--dst", required=True); a.add_argument("--ids", required=True)
    a.add_argument("--page", default="📱 Templates"); a.add_argument("--section", default="Cloned"); a.add_argument("--t", type=int, default=240)
    o = a.parse_args()
    LOG.write_text("", encoding="utf-8")
    x = 64
    for fid in o.ids.split(","):
        # хүүхдүүдийн id жагсаалт
        info = clone.run(o.src, f"const n=await figma.getNodeByIdAsync('{fid}');return JSON.stringify({{name:n.name,kids:n.children.map(c=>[c.id,c.name])}})", 60)
        info = json.loads(info) if isinstance(info, str) else info
        kids = info["kids"]
        log(f"▶ {info['name']} ({fid}) — {len(kids)} хэсэг")
        # бүрхүүл
        t0 = time.time()
        helpers = clone.SER[clone.SER.index("const b64"):clone.SER.index("const GEOM")]
        shell_js = helpers + f"""const f=await figma.getNodeByIdAsync('{fid}');const o={{type:f.type,name:f.name,x:f.x,y:f.y,w:f.width,h:f.height,opacity:f.opacity,rot:0,fills:await paints(f.fills),strokes:await paints(f.strokes),sw:f.strokeWeight===figma.mixed?1:f.strokeWeight,salign:f.strokeAlign,r:f.cornerRadius===figma.mixed?0:f.cornerRadius,clip:f.clipsContent,effects:JSON.parse(JSON.stringify(f.effects||[])),kids:[]}};if(f.layoutMode&&f.layoutMode!=='NONE')o.al={{mode:f.layoutMode,gap:f.itemSpacing,cgap:f.counterAxisSpacing,wrap:f.layoutWrap,pl:f.paddingLeft,pr:f.paddingRight,pt:f.paddingTop,pb:f.paddingBottom,pa:f.primaryAxisAlignItems,ca:f.counterAxisAlignItems,ps:f.primaryAxisSizingMode,cs:f.counterAxisSizingMode}};return JSON.stringify({{nodes:[o],images:imgCache,skipped:SKIP}});"""
        sd = clone.run(o.src, shell_js, 120)
        sd = json.loads(sd) if isinstance(sd, str) else sd
        r = clone.run(o.dst, SHELL.replace("__D__", json.dumps(sd)).replace("__PAGE__", json.dumps(o.page)).replace("__SECTION__", json.dumps(o.section)).replace("__X__", str(x)).replace("__BUILDFN__", buildfn(sd["images"])), 120)
        if "error" in r:
            log(f"  ✗ бүрхүүл: {r['error']}"); continue
        parent = r["id"]
        log(f"  ✓ бүрхүүл {time.time()-t0:.1f}s")
        ok = 0
        for i, (cid, cname) in enumerate(kids, 1):
            t1 = time.time()
            d = ser(o.src, [cid], o.t)
            if "error" in d:
                log(f"  [{i}/{len(kids)}] {cname} — ✗ уншиж чадсангүй ({d['error'][:60]})"); continue
            r = clone.run(o.dst, CHILD.replace("__D__", json.dumps(d)).replace("__PARENT__", json.dumps(parent)).replace("__BUILDFN__", buildfn(d["images"])), o.t)
            sk = len(d.get("skipped", []))
            if "error" in r:
                log(f"  [{i}/{len(kids)}] {cname} — ✗ угсарч чадсангүй ({str(r['error'])[:60]})"); continue
            ok += 1
            log(f"  [{i}/{len(kids)}] {cname} — ✓ {time.time()-t1:.1f}s" + (f" · {sk} алгассан" if sk else "") + (f" · {len(r['errors'])} анхааруулга" if r.get("errors") else ""))
        log(f"■ {info['name']}: {ok}/{len(kids)} хэсэг хуулагдав")
        x += 1400
    log("ДУУСЛАА")


if __name__ == "__main__":
    main()
