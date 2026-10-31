"""Bundle a static invitation folder into ONE self-contained HTML (CSS, JS, fonts, images, audio embedded).
Usage: python3 bundle.py <site_dir> <out.html>"""
import base64, re, os, sys
SRC, OUT = sys.argv[1].rstrip('/') + '/', sys.argv[2]
MIME = {'webp': 'image/webp', 'jpg': 'image/jpeg', 'png': 'image/png', 'svg': 'image/svg+xml', 'woff2': 'font/woff2', 'mp3': 'audio/mpeg'}
cache = {}
def uri(rel):
    rel = rel.split('?')[0].lstrip('./')
    if rel not in cache:
        cache[rel] = f"data:{MIME[rel.rsplit('.', 1)[1].lower()]};base64," + base64.b64encode(open(SRC + rel, 'rb').read()).decode()
    return cache[rel]
ASSET = r'((?:img|fonts|audio)/[A-Za-z0-9._/-]+\.(?:webp|jpg|png|svg|woff2|mp3)|og\.jpg|favicon\.svg)'
html = open(SRC + 'index.html').read()
def css_inline(m):
    css = open(SRC + m.group(1).split('?')[0]).read()
    css = re.sub(r'url\((["\']?)' + ASSET + r'\1\)', lambda k: 'url(' + uri(k.group(2)) + ')', css)
    return '<style>\n' + css + '\n</style>'
html = re.sub(r'<link rel="preload"[^>]*>\n?', '', html)
html = re.sub(r'<link rel="stylesheet" href="([^"]+)">', css_inline, html)
def js_inline(m):
    js = open(SRC + m.group(1).split('?')[0]).read()
    js = re.sub(r"(['\"`])" + ASSET + r"\1", lambda k: k.group(1) + uri(k.group(2)) + k.group(1), js)
    return '<script>\n' + js + '\n</script>'
html = re.sub(r'<script src="([^"]+)"[^>]*></script>', js_inline, html)
# src / href / srcset / inline style url() in the markup (absolute og:/twitter: URLs are left alone)
html = re.sub(r'(src|href)="' + ASSET + r'"', lambda k: f'{k.group(1)}="{uri(k.group(2))}"', html)
html = re.sub(r'srcset="([^"]+)"', lambda k: 'srcset="' + ', '.join(uri(p.strip().split(' ')[0]) + ('' if len(p.strip().split(' ')) < 2 else ' ' + p.strip().split(' ')[1]) for p in k.group(1).split(',')) + '"', html)
html = re.sub(r'url\(' + ASSET + r'\)', lambda k: 'url(' + uri(k.group(1)) + ')', html)
left = re.findall(r'(?:src|href|srcset)="(?!data:|https?:|#|mailto:)([^"]+)"', html)
assert not left, left
open(OUT, 'w').write(html)
print(OUT, round(len(html) / 1e6, 1), 'MB,', len(cache), 'assets embedded')
