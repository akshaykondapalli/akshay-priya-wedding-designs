"""Generates the muggu (sikku kolam via mirror-curve method) and a linear mango-leaf thoranam as SVG markup."""
import numpy as np, itertools, json

rng = np.random.default_rng(2111)


def trace(m, n, mirrors):
    # midpoints: vertical edges (x even, y odd), horizontal edges (x odd, y even) in [0,2m]x[0,2n]
    def is_mirror(x, y):
        if x == 0 or x == 2 * m or y == 0 or y == 2 * n: return True
        return (x, y) in mirrors
    states = set()
    for x in range(0, 2 * m + 1):
        for y in range(0, 2 * n + 1):
            if (x + y) % 2 == 1:
                for dx, dy in itertools.product((1, -1), (1, -1)):
                    states.add((x, y, dx, dy))
    loops = []; segs = set()
    for s0 in sorted(states):
        x, y, dx, dy = s0
        nx, ny = x + dx, y + dy
        if not (0 <= nx <= 2 * m and 0 <= ny <= 2 * n): continue
        if frozenset(((x, y), (nx, ny))) in segs: continue
        pts = []; s = s0; guard = 0
        while guard < 100000:
            guard += 1
            x, y, dx, dy = s
            pts.append((x, y))
            nx, ny = x + dx, y + dy
            segs.add(frozenset(((x, y), (nx, ny))))
            dx2 = -dx if (nx % 2 == 0 and is_mirror(nx, ny)) else dx
            dy2 = -dy if (ny % 2 == 0 and is_mirror(nx, ny)) else dy
            s = (nx, ny, dx2, dy2)
            if s == s0: break
        loops.append(pts)
    return loops


def find_single(m, n, tries=4000):
    internal = [(x, y) for x in range(1, 2 * m) for y in range(1, 2 * n) if (x + y) % 2 == 1]
    best = None
    for t in range(tries):
        k = rng.integers(1, len(internal) // 4)
        sel = set()
        # 4-fold symmetric mirror placement
        for (x, y) in [internal[i] for i in rng.choice(len(internal), k, replace=False)]:
            for (a, b) in [(x, y), (2 * n - y, x), (2 * m - x, 2 * n - y), (y, 2 * m - x)]:
                if (a + b) % 2 == 1 and 0 < a < 2 * m and 0 < b < 2 * n: sel.add((a, b))
        loops = trace(m, n, sel)
        if len(loops) == 1 and len(sel) > 2:
            if best is None or abs(len(sel) - len(internal) * .2) < abs(len(best[1]) - len(internal) * .2):
                best = (loops, sel)
            if t > 400: break
    return best


def smooth_path(pts, scale, ox, oy):
    # closed Catmull-Rom -> cubic bezier
    P = [(ox + x * scale, oy + y * scale) for x, y in pts]
    n = len(P); d = []
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        if i == 0: d.append(f'M{p1[0]:.1f} {p1[1]:.1f}')
        d.append(f'C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}')
    return ''.join(d) + 'Z'


m = n = 5
loops, mirrors = find_single(m, n)
sc = 40; ox = oy = 0
path = smooth_path(loops[0], sc, ox, oy)
dots = ''.join(f'<circle cx="{(2*i+1)*sc}" cy="{(2*j+1)*sc}" r="3.2"/>' for i in range(m) for j in range(n))
size = 2 * m * sc
muggu = (f'<svg class="muggu" viewBox="{-20} {-20} {size+40} {size+40}" role="img" aria-label="A muggu: a single continuous line drawn around a grid of dots">'
         f'<g class="muggu-dots">{dots}</g>'
         f'<path class="muggu-line" pathLength="1" d="{path}"/></svg>')

# thoranam: cord with hanging mango leaves + small marigold circles
W = 1200; leaves = []; mar = []
N = 15
cord = f'M0 18 Q{W/2} 46 {W} 18'
for i in range(N):
    t = (i + .5) / N
    x = W * t
    y = (1 - t) ** 2 * 18 + 2 * (1 - t) * t * 46 + t ** 2 * 18
    L = 104 if i % 2 == 0 else 84
    w = 24 if i % 2 == 0 else 19
    # pointed leaf hanging down
    leaves.append(f'<path d="M{x:.1f} {y:.1f} C{x+w:.1f} {y+L*.3:.1f} {x+w*.7:.1f} {y+L*.75:.1f} {x:.1f} {y+L:.1f} '
                  f'C{x-w*.9:.1f} {y+L*.7:.1f} {x-w*.8:.1f} {y+L*.25:.1f} {x:.1f} {y:.1f}Z M{x:.1f} {y+4:.1f} L{x:.1f} {y+L-6:.1f}"/>')
    if i < N - 1:
        t2 = (i + 1) / N; x2 = W * t2
        y2 = (1 - t2) ** 2 * 18 + 2 * (1 - t2) * t2 * 46 + t2 ** 2 * 18
        mar.append(f'<circle cx="{x2:.1f}" cy="{y2+9:.1f}" r="6"/>')
thoranam = (f'<svg class="thoranam" viewBox="0 0 {W} 150" preserveAspectRatio="xMidYMin meet" role="img" '
            f'aria-label="A thoranam of mango leaves and marigolds, drawn as a single fine line">'
            f'<path class="th-cord" d="{cord}"/><g class="th-leaves">{"".join(leaves)}</g><g class="th-mar">{"".join(mar)}</g></svg>')

json.dump({'muggu': muggu, 'thoranam': thoranam}, open('/home/claude/tools/editorial/motifs.json', 'w'))
print(len(loops[0]), len(mirrors), len(muggu), len(thoranam))
