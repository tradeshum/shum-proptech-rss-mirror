"""Merge the raw feeds fetched by the workflow into data/items.json (rolling 21 days, de-duplicated by link).

Each item keeps first_seen (UTC date-time of the first run that saw it), so a routine that reads this file twice a week can ask
for 'first_seen in the last N hours' and never miss an item that rolled out of a busy feed between two runs, and never see one twice.
data/health.json records, per feed, the last successful fetch and the item count (a feed that fails keeps its old items)."""
import json, os, re, sys, html
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

RAW = sys.argv[1]; OUT = sys.argv[2]
NOW = datetime.now(timezone.utc); KEEP = timedelta(days=21)
os.makedirs(OUT, exist_ok=True)
ip, hp = os.path.join(OUT, 'items.json'), os.path.join(OUT, 'health.json')
items = json.load(open(ip, encoding='utf-8')) if os.path.exists(ip) else []
health = json.load(open(hp, encoding='utf-8')) if os.path.exists(hp) else {}
have = {i['link']: i for i in items}

def tag(e): return e.tag.split('}')[-1].lower()
def txt(e, *names):
    for c in e:
        if tag(c) in names and (c.text or '').strip(): return c.text.strip()
    return ''
def strip(s): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()
def when(s):
    if not s: return None
    try: d = parsedate_to_datetime(s)
    except Exception:
        try: d = datetime.fromisoformat(s.replace('Z', '+00:00'))
        except Exception: return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

for fn in sorted(os.listdir(RAW)):
    name = fn[:-4]; p = os.path.join(RAW, fn); h = health.setdefault(name, {})
    try:
        root = ET.parse(p).getroot()
        ents = [e for e in root.iter() if tag(e) in ('item', 'entry')]
        if not ents: raise ValueError('no items')
        new = 0
        for e in ents:
            link = txt(e, 'link') or ''
            if not link:
                for c in e:
                    if tag(c) == 'link' and c.get('href'): link = c.get('href'); break
            title = strip(txt(e, 'title'))
            if not link or not title: continue
            d = when(txt(e, 'pubdate', 'published', 'updated', 'date'))
            summ = strip(txt(e, 'description', 'summary', 'encoded', 'content'))[:400]
            cats = [strip(c.text) for c in e if tag(c) == 'category' and c.text][:6]
            if link in have: continue
            it = dict(source=name, title=title, link=link, published=d.isoformat() if d else '', first_seen=NOW.isoformat(timespec='minutes'), summary=summ, categories=cats)
            items.append(it); have[link] = it; new += 1
        h.update(ok=NOW.isoformat(timespec='minutes'), items_in_feed=len(ents), new_items=new, error='')
    except Exception as ex:
        h['error'] = '%s at %s' % (str(ex)[:120], NOW.isoformat(timespec='minutes'))
items = [i for i in items if datetime.fromisoformat(i['first_seen']) > NOW - KEEP]
items.sort(key=lambda i: i['first_seen'], reverse=True)
json.dump(items, open(ip, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
json.dump(health, open(hp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
print(len(items), 'items kept;', sum(1 for v in health.values() if v.get('error')), 'feeds with errors')
