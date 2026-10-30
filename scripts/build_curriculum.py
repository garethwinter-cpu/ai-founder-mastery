#!/usr/bin/env python3
"""Build curriculum.html from data/curriculum-sessions.json, the Airtable snapshot.

    python3 scripts/build_curriculum.py

The snapshot holds what students see: each session's date, type, title, teachers and the
customer description from the Lessons table. Refresh it from Airtable, then rebuild.
"""
import html, json, pathlib, re
from datetime import datetime
from zoneinfo import ZoneInfo

R = pathlib.Path(__file__).resolve().parents[1]
DATA = json.loads((R / 'data/curriculum-sessions.json').read_text())
PT, LON = ZoneInfo('America/Los_Angeles'), ZoneInfo('Europe/London')
TYPE = {'Lesson': 'Lesson', 'Workshop': 'Lab', 'Bonus': 'Bonus', 'Graduation': 'Graduation'}
e = html.escape


def slug(name):
    return re.sub(r'[^a-z]+', '-', name.lower()).strip('-')


def clock(dt):
    h = dt.strftime('%I').lstrip('0')
    return h + ('' if dt.minute == 0 else dt.strftime(':%M')) + dt.strftime('%p').lower()


def when(s):
    if not s.get('start_utc'):
        return 'Watch any time before week 1'
    utc = datetime.fromisoformat(s['start_utc'].replace('Z', '+00:00'))
    pt, lon = utc.astimezone(PT), utc.astimezone(LON)
    day = pt.strftime('%a %-d %b')
    if s.get('prerecorded'):
        return f'Ready from {day}'
    return f'{day} · {clock(pt)} PT / {clock(lon)} London'


def title(s):
    return re.sub(r'^\[Pre-recorded\]\s*|\s*\(pre-recorded\)', '', s['title'], flags=re.I)  # the tag already says it


def body(text):
    para, _, rest = text.partition('\n\n')
    head, _, items = rest.partition('\n')
    bullets = ''.join(f'<li>{e(b[2:])}</li>' for b in items.splitlines() if b.startswith('- '))
    return f'<p>{e(para)}</p><h4>{e(head.rstrip(":"))}</h4><ul>{bullets}</ul>'


def faces(names):
    imgs = ''.join(f'<img src="authors/{slug(n)}.jpg" alt="" width="36" height="36" loading="lazy">' for n in names)
    label = ' and '.join(names) if len(names) == 2 else ', '.join(names)
    return f'<div class="who"><span class="faces">{imgs}</span>{e(label)}</div>'


def card(s):
    kind = TYPE[s['type']]
    tag = 'Pre-recorded' if s.get('prerecorded') else 'Live bonus' if kind == 'Bonus' else kind
    mod = f'<span class="modtag">{e(s["module"])}</span>' if s.get('module') else ''
    m = mod_num(s)
    return (f'<article class="card {kind.lower()} mod-{m}"><div class="meta"><span class="tag">{tag}</span>'
            f'<span class="when">{when(s)}</span>{mod}</div><h3>{e(title(s))}</h3>{faces(s["teachers"])}'
            f'<div class="desc">{body(s["description"])}</div></article>')


def first_day(items):
    dated = [s['start_utc'] for s in items if s.get('start_utc')]
    return datetime.fromisoformat(min(dated).replace('Z', '+00:00')).astimezone(PT) if dated else None


def mod_num(s):
    m = re.match(r'Module (\d+)', s.get('module') or '')
    return int(m.group(1)) if m else 0   # 0 is the Bonus group, before week 1


def build():
    """Teaching order, one section per month (Airtable's Month field). Each session is tagged and coloured by its module."""
    sessions, brk = DATA['sessions'], DATA['break']
    names = {mod_num(s): s['module'].split(': ', 1)[-1] for s in sessions if s.get('module')}
    weeks, wk = [], 0
    for s in sessions:  # a week is a Tuesday lesson and its Thursday lab; graduation stands alone
        if s['order'].startswith('0'):
            continue
        if s['type'] in ('Lesson', 'Graduation'):
            wk += 1
            weeks.append({'n': wk, 'month': s['month'], 'mod': mod_num(s), 'grad': s['type'] == 'Graduation', 'items': []})
        weeks[-1]['items'].append(s)
    pre = [s for s in sessions if s['order'].startswith('0')]
    months = sorted({s['month'] for s in sessions if s['month'].startswith('Month')}, key=lambda m: int(m.split()[-1]))

    first = {}   # where each module first appears, for the key at the top
    out = []
    if pre:   # onboarding sits outside the four months, as in Airtable's Pre-Class Bonus
        blocks = []
        for s in pre: first.setdefault(mod_num(s), f'w0-{mod_num(s)}')
        for mn in sorted({mod_num(s) for s in pre}):
            blocks.append(f'<div class="week mod-{mn}" id="w0-{mn}"><div class="wl"><b>Before week 1</b><span>{"Live" if mn == 0 else "Pre-recorded"}</span></div>'
                          f'<div class="cards">{"".join(card(s) for s in pre if mod_num(s) == mn)}</div></div>')
        out.append(f'<section id="m0" class="month"><div class="mh"><span class="eyebrow">Before week 1</span>'
                   f'<h2>{e(pre[0]["month"])}</h2></div>{"".join(blocks)}</section>')
    for i, m in enumerate(months, 1):
        items = [s for s in sessions if s['month'] == m]
        blocks = []
        mw = [w for w in weeks if w['month'] == m]
        for w in mw:
            first.setdefault(w['mod'], f'w{w["n"]}')
            label = 'Graduation' if w['grad'] else f'Week {w["n"]}'
            blocks.append(f'<div class="week mod-{w["mod"]}" id="w{w["n"]}"><div class="wl"><b>{label}</b><span>{first_day(w["items"]).strftime("%-d %b")}</span>'
                          f'<em>{e(names[w["mod"]])}</em></div>'
                          f'<div class="cards">{"".join(card(s) for s in w["items"])}</div></div>')
            if any(s['order'] == brk['after_order'] for s in w['items']):
                blocks.append(f'<div class="break"><b>{e(brk["label"])}</b> {e(brk["dates"])}</div>')
        mods = sorted({mod_num(s) for s in items})
        pills = ''.join(f'<span class="modtag mod-{n}">{e(names[n] if n == 0 else f"Module {n}: {names[n]}")}</span>' for n in mods)
        nums = [w['n'] for w in mw if not w['grad']]
        span = f'Weeks {nums[0]} to {nums[-1]}' + (', then graduation' if any(w['grad'] for w in mw) else '')
        last = max(s['start_utc'] for s in items if s.get('start_utc'))
        last = datetime.fromisoformat(last.replace('Z', '+00:00')).astimezone(PT)
        out.append(f'<section id="m{i}" class="month"><div class="mh"><span class="eyebrow">{span} · {first_day(items).strftime("%-d %b")} to {last.strftime("%-d %b")}</span>'
                   f'<h2>{e(m)}</h2><div class="pills">{pills}</div></div>{"".join(blocks)}</section>')

    chips = ''.join(f'<a class="mod-{n}" href="#{first[n]}">{e(names[n]) if n == 0 else f"{n} · {e(names[n])}"}</a>' for n in sorted(names))
    page = TEMPLATE.replace('__CHIPS__', chips).replace('__BODY__', '\n'.join(out))
    (R / 'curriculum.html').write_text(page)
    print(f'curriculum.html: {len(sessions)} sessions in teaching order, {len(months)} months plus pre-class, {len(names)} module tags, {wk - 1} weeks and a graduation')


TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI for Founders Mastery · Curriculum</title>
<meta name="description" content="AI for Founders Mastery: every live lesson and lab, week by week, with the teacher and what you will build.">
<link rel="icon" type="image/svg+xml" href="favicon-aif.svg"><link rel="alternate icon" type="image/png" sizes="32x32" href="favicon-aif-32.png"><link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon-aif.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{--brand:#1832B4;--brand-bright:#3D63F5;--brand-light:#EEF2FF;--ink:#0F131A;--muted:#595E67;--subtle:#71767F;--border:#DFE1E5;--grey:#F6F7F9;--gold:#946A00;--gold-light:#FBF3DE;--sh1:0 4px 15px 0 rgba(0,0,0,.05);--sh2:0 5px 20px 0 rgba(0,0,0,.10)}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;scroll-padding-top:116px}
body{font-family:"Google Sans","Segoe UI",system-ui,sans-serif;background:#fff;color:var(--ink);font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--brand);text-decoration:none}
.wrap{max-width:960px;margin:0 auto;padding:0 16px}
.top{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.96);backdrop-filter:blur(10px);border-bottom:1px solid var(--border)}
.bar{height:56px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.wm{font-weight:700;font-size:17px;color:var(--ink);white-space:nowrap} .wm span{color:var(--brand)}
.bar nav a{font-size:14px;font-weight:500;color:var(--muted);margin-left:18px} .bar nav a.on{color:var(--brand)}
.chips{display:flex;gap:6px;overflow-x:auto;padding:8px 0 10px;scrollbar-width:none} .chips::-webkit-scrollbar{display:none}
.chips a{flex:0 0 auto;font-size:13px;font-weight:500;color:var(--muted);border:1px solid var(--border);border-radius:128px;padding:5px 12px;background:#fff}
.chips a:hover{color:var(--brand);border-color:var(--brand)}
.hero{padding:44px 0 8px}
h1{font-size:clamp(32px,5vw,48px);font-weight:700;line-height:1.08;letter-spacing:-.02em}
.lede{margin-top:12px;font-size:18px;color:var(--muted);max-width:640px}
.facts{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}
.facts span{border:1px solid var(--border);border-radius:128px;padding:7px 14px;font-size:14px;font-weight:500}
.facts b{color:var(--brand);font-weight:700}
.mod,.month{padding:40px 0 8px}
.mh{margin-bottom:16px}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--brand)}
h2{font-size:28px;font-weight:700;letter-spacing:-.01em;margin-top:2px}
.week{display:grid;grid-template-columns:96px 1fr;gap:16px;padding:16px 0;border-top:1px solid var(--border)}
.wl b{display:block;font-size:15px} .wl span{font-size:13px;color:var(--subtle)}
.cards{display:grid;gap:12px}
.card{border:1px solid var(--border);border-radius:16px;padding:20px;background:#fff;box-shadow:var(--sh1)}
.card.lab{background:var(--grey);box-shadow:none}
.card.graduation{border-color:var(--brand);background:var(--brand-light)}
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;font-size:13px;color:var(--subtle)}
.tag{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;border-radius:128px;padding:3px 10px;background:var(--brand-light);color:var(--brand)}
.lab .tag{background:#fff;color:var(--muted);border:1px solid var(--border)}
.bonus .tag{background:var(--gold-light);color:var(--gold)}
.graduation .tag{background:var(--brand);color:#fff}
h3{font-size:20px;font-weight:700;line-height:1.3;margin-top:10px}
.who{display:flex;align-items:center;gap:10px;margin-top:10px;font-size:14px;font-weight:500;color:var(--muted)}
.faces{display:flex} .faces img{width:36px;height:36px;border-radius:50%;object-fit:cover;object-position:50% 20%;border:2px solid #fff;background:var(--border)}
.faces img+img{margin-left:-10px}
.desc{margin-top:12px;font-size:15px;color:#2B3038}
.desc h4{margin-top:12px;font-size:13px;font-weight:700;color:var(--ink)}
.desc ul{list-style:none;margin-top:6px;display:grid;gap:4px}
.desc li{position:relative;padding-left:18px} .desc li::before{content:"";position:absolute;left:2px;top:.6em;width:7px;height:7px;border-radius:50%;background:var(--brand-bright)}
.lab .desc li::before{background:var(--subtle)}
.break{margin:4px 0 4px 112px;padding:12px 16px;border-radius:16px;background:var(--gold-light);color:#5C4300;font-size:14px}
footer{margin:48px 0 0;padding:24px 0 40px;border-top:1px solid var(--border);font-size:13px;color:var(--subtle)}
.mod-0{--mc:#946A00;--mt:#FBF3DE}.mod-1{--mc:#475467;--mt:#F2F4F7}.mod-2{--mc:#1832B4;--mt:#EEF2FF}.mod-3{--mc:#7A12D4;--mt:#F4EBFC}
.mod-4{--mc:#0F7B4A;--mt:#E8F5EE}.mod-5{--mc:#B54708;--mt:#FEF0E6}.mod-6{--mc:#0E7090;--mt:#E6F4F8}
.month .eyebrow{color:var(--subtle)}
.pills{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.wl em{display:block;font-style:normal;font-size:12px;font-weight:700;color:var(--mc);margin-top:6px;border-left:3px solid var(--mc);padding-left:6px}
.card{border-left:4px solid var(--mc)}
.modtag{font-size:11px;font-weight:700;letter-spacing:.04em;color:var(--mc);background:var(--mt);border-radius:128px;padding:3px 10px}
.chips a{border-color:var(--mc);color:var(--mc)} .chips a:hover{background:var(--mt);color:var(--mc);border-color:var(--mc)}
@media (max-width:640px){.week{grid-template-columns:1fr;gap:8px}.wl{display:flex;gap:8px;align-items:baseline}.break{margin-left:0}.card{padding:16px}h3{font-size:18px}.bar nav a{margin-left:12px}.wm{font-size:15px}.facts{gap:6px}.facts span{font-size:13px;padding:6px 12px}.lede{font-size:17px}}
</style>
</head>
<body>
<header class="top"><div class="wrap"><div class="bar"><a class="wm" href="index.html">AI for <span>Founders</span> Mastery</a>
<nav><a href="index.html">Home</a><a class="on" href="curriculum.html">Curriculum</a></nav></div>
<div class="chips">__CHIPS__</div></div></header>
<main class="wrap">
<section class="hero">
<h1>The curriculum</h1>
<p class="lede">Every Tuesday, a live lesson. Every Thursday, a hands-on lab where you build it for your own business.</p>
<div class="facts"><span>Starts <b>Tue 17 Nov</b></span><span>Live <b>7am PT / 3pm London</b></span><span><b>18 weeks</b> · 4 months</span><span><b>90 min</b> per session</span><span>Graduation <b>Tue 30 Mar</b></span></div>
</section>
__BODY__
<footer>Times are Pacific and London. Teachers and dates may change before the program starts.</footer>
</main>
</body>
</html>
'''

if __name__ == '__main__':
    build()
