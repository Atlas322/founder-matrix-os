#!/usr/bin/env python3
"""nt — Just.Notion CLI (BD · Inai). Албан ёсны Notion API, гадны сангүй.

Нэвтрэлт: `ntn login` (албан ёсны Notion CLI) — эсвэл NOTION_TOKEN.
Token (сонголт): Notion → Settings → Connections → Develop integrations → internal integration.
       Just.Notion хуудсыг «… → Connections»-оор тэр integration-д холбоно.
       Дараа нь:  setx NOTION_TOKEN "<token>"   (шинэ terminal нээнэ)

Командууд:
  nt setup                     баазуудыг олж schema-г nt.config.json-д хадгална
  nt ls                        холбогдсон баазууд
  nt pin task <data-source-id> богино нэрийг тодорхой баазад холбоно
  nt tasks [--overdue|--week|--today|--all]   таскууд (анхдагч: нээлттэй)
  nt add task "Нэр" [--due 2026-09-30] [--status "Next"]
  nt add note "Гарчиг" [--body "текст"]
  nt add meeting "Нэр" --due 2026-09-28T14:00
  nt done <page-id>            таскийг дууссан болгоно
  nt pull <бааз> [--out <хавтас>]   баазыг vault руу .md болгож татна (зөвхөн унших)
"""
import json, os, sys, re, datetime as dt, urllib.request, urllib.error, argparse, pathlib

API = 'https://api.notion.com/v1'
VER = '2025-09-03'  # data sources API (ntn-тэй ижил)
HERE = pathlib.Path(__file__).parent
CFG = HERE / 'nt.config.json'
ROOT_PAGE = 'YOUR_NOTION_ROOT_PAGE_ID'  # 🍀 Just.Notion
# Хэрэглэгчийн өдөр тутмын нэрс → Notion бааз (setup олсон нэрээр таарна)
ALIASES = {'task': ['Tasks', 'Weekly GTD', 'Getting Things Done'], 'note': ['Notes'], 'meeting': ['Events', 'Meetings', 'Reminder'],
           'project': ['Projects'], 'ref': ['References', 'Resources']}
DONE_WORDS = ['Done', 'Completed', 'Дууссан', 'Complete']


def die(msg):
    print('✗ ' + msg, file=sys.stderr); sys.exit(1)


def token():
    return os.environ.get('NOTION_TOKEN') or os.environ.get('NOTION_API_TOKEN')


def via_ntn(method, path, body):
    """Token байхгүй бол албан ёсны `ntn api`-аар (ntn login-ийн нэвтрэлт) дуудна."""
    import subprocess, shutil
    exe = shutil.which('ntn')
    if not exe:
        die('NOTION_TOKEN ч, ntn ч алга. `npm install -g ntn` → `ntn login`.')
    cmd = [exe, 'api', '/v1/' + path.lstrip('/'), '-X', method]
    if body is not None:
        cmd += ['-d', '@-']
    kw = {'input': json.dumps(body)} if body is not None else {'stdin': subprocess.DEVNULL}
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf8', timeout=120, **kw)
    if r.returncode != 0:
        hint = ' — `ntn login` хийсэн үү? Just.Notion-д хандах эрхтэй юу?'
        die('ntn api: ' + (r.stderr.strip() or r.stdout.strip())[:400] + hint)
    return json.loads(r.stdout)


def call(method, path, body=None):
    if not token():
        return via_ntn(method, path, body)
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + token(), 'Notion-Version': VER, 'Content-Type': 'application/json'})
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        err = json.loads(e.read() or b'{}')
        hint = ' — Just.Notion хуудсыг integration-д Connections-оор холбосон уу?' if e.code in (403, 404) else ''
        die(f'Notion {e.code}: {err.get("message", e.reason)}{hint}')


def paged(method, path, body=None):
    body = dict(body or {}); out = []
    while True:
        r = call(method, path, body)
        out += r.get('results', [])
        if not r.get('has_more'):
            return out
        body['start_cursor'] = r['next_cursor']


def load_cfg():
    if not CFG.exists():
        die('Эхлээд:  nt setup')
    return json.loads(CFG.read_text(encoding='utf8'))


def plain(rt):
    return ''.join(x.get('plain_text', '') for x in rt or [])


def title_of(db):
    return plain(db.get('title')) or '(нэргүй)'


def schema(db):
    props = db['properties']; s = {'title': None, 'date': None, 'status': None, 'status_type': None, 'status_options': [], 'checkbox': None}
    for name, p in props.items():
        t = p['type']
        if t == 'title': s['title'] = name
        elif t == 'date' and (s['date'] is None or re.search(r'due|date|огноо|хугацаа|when|do date', name, re.I)): s['date'] = s['date'] if s['date'] and not re.search(r'due|хугацаа', name, re.I) else name
        elif t in ('status', 'select') and (s['status'] is None or re.search(r'status|төлөв', name, re.I)):
            if s['status'] is None or t == 'status' or re.search(r'status|төлөв', name, re.I):
                s['status'], s['status_type'] = name, t
                s['status_options'] = [o['name'] for o in p[t].get('options', [])]
        elif t == 'checkbox' and re.search(r'done|complete|дууссан', name, re.I): s['checkbox'] = name
    return s


# ── commands
def cmd_setup(a):
    dbs = paged('POST', '/search', {'filter': {'property': 'object', 'value': 'data_source'}, 'page_size': 100})
    if not dbs:
        die('Нэг ч бааз харагдсангүй. Just.Notion хуудсыг integration-д «Connections»-оор холбоно уу.')
    cfg = {'root': ROOT_PAGE, 'databases': {}}
    for db in dbs:
        n = title_of(db)
        cfg['databases'][n] = {'id': db['id'], 'url': db.get('url'), 'schema': schema(db)}
    for k, names in ALIASES.items():
        hit = next((n for want in names for n in cfg['databases'] if n.lower() == want.lower()), None)
        if hit: cfg.setdefault('aliases', {})[k] = hit
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding='utf8')
    print(f'✓ {len(dbs)} бааз олдлоо → {CFG.name}')
    for k, v in cfg.get('aliases', {}).items(): print(f'  {k:8} → {v}')
    missing = [k for k in ALIASES if k not in cfg.get('aliases', {})]
    if missing: print('  ⚠ таараагүй:', ', '.join(missing), '— nt.config.json-ийн "aliases"-д гараар бичнэ үү')


def cmd_pin(a):
    """Богино нэрийг data source ID-д шууд холбоно (ижил нэртэй олон бааз байвал)."""
    cfg = load_cfg(); ds = call('GET', f'/data_sources/{a.id}')
    n = title_of(ds); key = f'{n} · {ds["id"][:8]}'
    cfg['databases'][key] = {'id': ds['id'], 'url': ds.get('url'), 'schema': schema(ds)}
    cfg.setdefault('aliases', {})[a.alias] = key
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding='utf8')
    sc = cfg['databases'][key]['schema']
    print(f'✓ {a.alias} → {key}  (гарчиг={sc["title"]}, огноо={sc["date"]}, төлөв={sc["status"]} {sc["status_options"]})')


def cmd_ls(a):
    cfg = load_cfg(); al = {v: k for k, v in cfg.get('aliases', {}).items()}
    for n, d in sorted(cfg['databases'].items()):
        s = d['schema']; print(f'{("["+al[n]+"]") if n in al else "":10} {n:32} огноо={s["date"] or "—"}  төлөв={s["status"] or "—"}')


def db_of(cfg, key):
    name = cfg.get('aliases', {}).get(key, key)
    if name not in cfg['databases']: die(f'«{key}» бааз алга. nt ls-ээр шалгана уу.')
    return name, cfg['databases'][name]


def row(pg, s):
    p = pg['properties']
    t = plain(p.get(s['title'], {}).get('title')) if s['title'] else ''
    d = ((p.get(s['date']) or {}).get('date') or {}).get('start') if s['date'] else None
    st = None
    if s['status']:
        v = (p.get(s['status']) or {}).get(s['status_type']) or {}
        st = v.get('name')
    return t, d, st


def is_done(st, pg, s):
    if s.get('checkbox') and pg['properties'].get(s['checkbox'], {}).get('checkbox'): return True
    return bool(st) and any(w.lower() in st.lower() for w in DONE_WORDS)


def cmd_tasks(a):
    cfg = load_cfg(); name, db = db_of(cfg, 'task'); s = db['schema']
    pages = paged('POST', f'/data_sources/{db["id"]}/query', {'page_size': 100})
    today = dt.date.today().isoformat(); wk = (dt.date.today() + dt.timedelta(days=7)).isoformat()
    rows = []
    for pg in pages:
        t, d, st = row(pg, s); done = is_done(st, pg, s)
        if not a.all and (done or any(v.get('type') == 'checkbox' and v.get('checkbox') and re.search(r'archiv', k, re.I) for k, v in pg['properties'].items())): continue
        if a.overdue and not (d and d[:10] < today): continue
        if a.today and not (d and d[:10] == today): continue
        if a.week and not (d and today <= d[:10] <= wk): continue
        rows.append((d or '9999', t, st, pg['id'], done))
    rows.sort()
    for d, t, st, pid, done in rows:
        mark = '✓' if done else ('!' if d != '9999' and d[:10] < today else '·')
        print(f'{mark} {("—" if d == "9999" else d[:10]):10}  {(st or "")[:12]:12}  {t[:60]:60}  {pid[:8]}')
    print(f'— {len(rows)} мөр · {name}')


def props_for(s, title, due=None, status=None):
    pr = {s['title']: {'title': [{'text': {'content': title}}]}}
    if due and s['date']: pr[s['date']] = {'date': {'start': due}}
    if status and s['status']: pr[s['status']] = {s['status_type']: {'name': status}}
    return pr


def cmd_add(a):
    cfg = load_cfg(); name, db = db_of(cfg, a.kind); s = db['schema']
    body = {'parent': {'type': 'data_source_id', 'data_source_id': db['id']}, 'properties': props_for(s, a.title, a.due, a.status)}
    if a.body:
        body['children'] = [{'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'text': {'content': a.body[:1900]}}]}}]
    pg = call('POST', '/pages', body)
    print(f'✓ {name}-д нэмэгдлээ: {a.title}  {pg["url"]}')


def cmd_done(a):
    cfg = load_cfg(); name, db = db_of(cfg, 'task'); s = db['schema']
    pid = a.id
    if len(pid) < 32:  # богино id → жагсаалтаас таацуулна
        pages = paged('POST', f'/data_sources/{db["id"]}/query', {'page_size': 100})
        m = [p for p in pages if p['id'].replace('-', '').startswith(pid.replace('-', ''))]
        if len(m) != 1: die(f'«{pid}»-д {len(m)} таск таарлаа. Урт id өгнө үү.')
        pid = m[0]['id']
    if s.get('checkbox'):
        pr = {s['checkbox']: {'checkbox': True}}
    elif s['status']:
        opt = next((o for w in DONE_WORDS for o in s['status_options'] if w.lower() in o.lower()), None)
        if not opt: die(f'«{s["status"]}» талбарт Done төлөв олдсонгүй: {s["status_options"]}')
        pr = {s['status']: {s['status_type']: {'name': opt}}}
    else:
        die('Дууссаныг тэмдэглэх талбар (status/checkbox) олдсонгүй.')
    call('PATCH', f'/pages/{pid}', {'properties': pr}); print('✓ дууссан:', pid[:8])


def cmd_pull(a):
    cfg = load_cfg(); name, db = db_of(cfg, a.db); s = db['schema']
    out = pathlib.Path(a.out or f'00-Inbox/notion/{name}'); out.mkdir(parents=True, exist_ok=True)
    pages = paged('POST', f'/data_sources/{db["id"]}/query', {'page_size': 100}); n = 0
    for pg in pages:
        t, d, st = row(pg, s)
        safe = re.sub(r'[\\/:*?"<>|#^\[\]]', ' ', t or pg['id'][:8]).strip()[:90]
        fm = {'type': 'notion-mirror', 'source': 'notion', 'notion-db': name, 'notion-id': pg['id'], 'notion-url': pg['url'],
              'updated': pg['last_edited_time'][:10], 'status': st, 'due': d, 'ai-first': True}
        lines = ['---'] + [f'{k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, str) else ("null" if v is None else str(v).lower())}' for k, v in fm.items()] + ['---', '', f'# {t}', '']
        (out / f'{safe}.md').write_text('\n'.join(lines), encoding='utf8'); n += 1
    print(f'✓ {n} мөр → {out}  (зөвхөн унших толь, vault-ын үндсэн нотуудыг хөндөхгүй)')


def main():
    p = argparse.ArgumentParser(prog='nt', description='Just.Notion CLI'); sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('setup'); sub.add_parser('ls')
    pn = sub.add_parser('pin'); pn.add_argument('alias'); pn.add_argument('id')
    t = sub.add_parser('tasks'); g = t.add_mutually_exclusive_group()
    for f in ('overdue', 'week', 'today', 'all'): g.add_argument('--' + f, action='store_true')
    ad = sub.add_parser('add'); ad.add_argument('kind', choices=['task', 'note', 'meeting', 'project', 'ref']); ad.add_argument('title')
    ad.add_argument('--due'); ad.add_argument('--status'); ad.add_argument('--body')
    d = sub.add_parser('done'); d.add_argument('id')
    pl = sub.add_parser('pull'); pl.add_argument('db'); pl.add_argument('--out')
    a = p.parse_args()
    {'setup': cmd_setup, 'ls': cmd_ls, 'pin': cmd_pin, 'tasks': cmd_tasks, 'add': cmd_add, 'done': cmd_done, 'pull': cmd_pull}[a.cmd](a)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); sys.stderr.reconfigure(encoding='utf-8')
    main()
