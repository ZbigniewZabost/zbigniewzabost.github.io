#!/usr/bin/env python3
"""Build the static GitHub Pages site.

Inlines the content (src/content.json), the logos it uses (assets/icons) and the fonts
(assets/fonts) into src/page.html, adds a plain-HTML copy of the finished career run
for visitors without JavaScript, and writes docs/index.html (GitHub Pages publishes only
docs/). The published page makes no third-party requests (no Google Fonts, no CDN), so
visitors' IPs go only to the host.

    python3 build.py                                  # writes docs/index.html
    python3 build.py --site-url https://you.github.io # absolute og:image / og:url for link previews
"""
import base64, html as htmlmod, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(ROOT, 'assets', 'icons')
FONTS = os.path.join(ROOT, 'assets', 'fonts')
# family, file, weight (range for variable fonts). All three are SIL Open Font License.
FONT_FACES = [
    ('Space Grotesk', 'space-grotesk-var.woff2', '300 700'),
    ('Inter', 'inter-var.woff2', '100 900'),
    ('IBM Plex Mono', 'ibm-plex-mono-400.woff2', '400'),
    ('IBM Plex Mono', 'ibm-plex-mono-500.woff2', '500'),
]


def font_css():
    out = []
    for family, fn, weight in FONT_FACES:
        b64 = base64.b64encode(open(os.path.join(FONTS, fn), 'rb').read()).decode()
        out.append(f"@font-face {{ font-family: '{family}'; font-style: normal; font-weight: {weight}; font-display: swap; "
                   f"src: url(data:font/woff2;base64,{b64}) format('woff2'); }}")
    return '\n'.join(out)


def clean_svg(svg):
    svg = re.sub(r'<\?xml.*?\?>|<!DOCTYPE.*?>|<!--.*?-->|<title>.*?</title>', '', svg, flags=re.S)
    svg = re.sub(r'\s(width|height)="[^"]*"', '', svg[:svg.index('>') + 1], count=2) + svg[svg.index('>') + 1:]
    svg = re.sub(r'\s(id|x|y|enable-background|xml:space|version|xmlns:xlink)="[^"]*"', '', svg[:svg.index('>') + 1]) + svg[svg.index('>') + 1:]
    return re.sub(r'>\s+<', '><', svg.replace('\n', ' ').replace('\t', ' ')).strip()


def norm(t):
    return re.sub(r'[^a-z0-9]', '', t.lower().replace('+', 'plus').replace('.', 'dot').replace('&', 'and'))


def load_icons(page):
    # embed only logos the page refers to (as a quoted slug), so nothing unused ships in the source
    used = set(re.findall(r"'([a-z0-9]+)'", page))
    data = json.load(open(os.path.join(ICONS, 'simple-icons-data.json')))['icons']
    meta = {(e.get('slug') or norm(e['title'])): e for e in data}
    out = {}
    for folder in ('tools',):
        for fn in sorted(os.listdir(os.path.join(ICONS, folder))):
            slug = fn[:-4]
            if slug not in used:
                continue
            key = slug
            if fn.endswith('.png'):  # raster logo: wrap it in an SVG so it renders like the others
                b64 = base64.b64encode(open(os.path.join(ICONS, folder, fn), 'rb').read()).decode()
                out[key] = {'t': slug, 'svg': f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><image width="128" height="128" href="data:image/png;base64,{b64}"/></svg>'}
                continue
            svg = open(os.path.join(ICONS, folder, fn)).read()
            e = meta.get(slug)
            path = re.findall(r'<path[^>]*\sd="([^"]+)"', svg)
            if e and len(path) == 1 and 'viewBox="0 0 24 24"' in svg:  # Simple Icons: one path, brand hex
                out[key] = {'t': e['title'], 'h': e['hex'], 'p': path[0]}
            else:  # multi-colour logos (Devicon, company marks): keep the SVG
                svg = clean_svg(svg)
                svg = svg.replace('#252f3e', 'currentColor')  # AWS wordmark text
                out[key] = {'t': slug, 'svg': svg}
    return out


def static_html(c):
    """Plain-HTML version of the page's finished state, for search engines, link scrapers and
    visitors without JavaScript. The page's script replaces it on load."""
    esc = htmlmod.escape
    stages = []
    for i, s in enumerate(c['STAGES']):
        fam = {}
        for r in c['ROLES']:
            if s['a'] - 0.01 <= r['a'] < s['b']:
                fam[r['g']] = r['t']
        titles = ', '.join(dict.fromkeys(fam.values()))
        skills = sorted((n for n in c['TREE'] if next(k for k, st in enumerate(c['STAGES']) if n[4] < st['b']) == i), key=lambda n: n[4])
        end = 'today' if s['b'] > 2050 else int(s['b'])
        stages.append(f'<div class="st done"><h3>{esc(s["label"])}</h3><div class="yrs">{int(s["a"])}–{end}</div>'
                      f'<div class="titles">{esc(titles)}</div><p class="titles">{esc(" · ".join(n[2] for n in skills))}</p></div>')
    camel = lambda t: re.sub(r'[^A-Za-z0-9]+(.)?', lambda m: m.group(1).upper() if m.group(1) else '', t)
    ways = ''.join(f'<span class="way"><b>#{esc(camel(w[0]))}</b>{" <span>" + esc(w[1]) + "</span>" if w[1] else ""}</span>' for w in c['WAYS'])
    tags = ''.join(f'<span class="tg">#{esc(t[0])}</span>' for t in c['TAGS'])
    cur = max(c['ROLES'], key=lambda r: r['a'])['t']
    strip = (f'<div class="chip now">now<b>{esc(cur)}</b></div><div class="chip">skills picked up<b>{len(c["TREE"])}</b></div>'
             f'<div class="chip">on-call<b>since 2016</b></div>')
    return {'STATIC_STAGES': ''.join(stages), 'STATIC_WAYS': ways, 'STATIC_TAGS': tags, 'STATIC_STRIP': strip}


def main():
    page = open(os.path.join(ROOT, 'src', 'page.html')).read()
    content = json.load(open(os.path.join(ROOT, 'src', 'content.json')))
    # a logo counts as used if the page or the content mentions its slug in quotes
    used_text = page + json.dumps(content).replace('"', "'")
    icons = 'const ICONS = ' + json.dumps(load_icons(used_text), separators=(',', ':')) + ';'
    body_json = json.dumps({k: v for k, v in content.items() if not k.startswith('_')}, ensure_ascii=False).replace('</', '<\\/')
    html = page.replace('/*CONTENT*/', body_json).replace('/*ICONS*/', icons).replace('/*FONTS*/', font_css())
    for key, value in static_html(content).items():
        html = html.replace(f'<!--{key}-->', value)
    if '--site-url' in sys.argv:
        url = sys.argv[sys.argv.index('--site-url') + 1].rstrip('/')
        html = html.replace('content="og-image.png"', f'content="{url}/og-image.png"')
        html = html.replace('<meta property="og:type"', f'<meta property="og:url" content="{url}/">\n<meta property="og:type"')
    # GitHub Pages publishes only docs/, so sources and tooling are not served as web pages
    open(os.path.join(ROOT, 'docs', 'index.html'), 'w').write(html)
    print('docs/index.html', len(html) // 1024, 'KB')

if __name__ == '__main__':
    main()
