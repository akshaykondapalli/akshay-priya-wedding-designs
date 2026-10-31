import numpy as np
from wc import leaf_poly, petal_poly, bezier, RNG
import wc

GREEN = '#7c9c55'
GREEN_D = '#4f7344'
SAP = '#93ad5c'
ROSE = '#dd7f95'
ROSE_D = '#b84e6e'
CERU = '#74aed0'
OCHRE = '#dcab58'
INDIGO = '#55618a'
SIENNA = '#bd7550'
GREY = '#c4cad6'
MARI = '#ee9d34'
MARI_D = '#d9702a'


def r(a, b):
    return wc.RNG.uniform(a, b)


def jasmine_flower(cv, cx, cy, size, ang0=None, petals=None):
    petals = petals or int(r(5, 7))
    ang0 = r(0, 6.28) if ang0 is None else ang0
    ps = []
    for i in range(petals):
        a = ang0 + i * 2 * np.pi / petals + r(-0.12, 0.12)
        ps.append(petal_poly(cx, cy, size * r(0.9, 1.1), size * 0.62, a))
    m = cv.polys(ps)
    # cool shadow glaze — gives the white petals form via wet edges
    cv.wash(m, GREY, opacity=0.16, bleed=1.2, soft=0.6, edge=1.6, mottle=0.5, gran=0.3, edge_width=2.2)
    # a second, smaller glaze on half the petals for lighting
    half = [p for k, p in enumerate(ps) if k % 2 == 0]
    cv.wash(cv.polys(half), '#b9c2cf', opacity=0.10, bleed=1.0, soft=1.5, edge=0.8, gran=0.2)
    c = cv.ellipse(cx, cy, size * 0.16, size * 0.16)
    cv.wash(c, '#c9c25c', opacity=0.65, bleed=0.6, soft=0.6, edge=0.4)


def jasmine_bud(cv, x, y, length, ang):
    p = petal_poly(x, y, length, length * 0.32, ang)
    m = cv.poly(p)
    cv.wash(m, '#cfd3d6', opacity=0.20, bleed=0.8, soft=0.6, edge=1.2)
    # pink blush on bud tip — real jasmine buds are tinged pink
    tip = petal_poly(x + np.cos(ang) * length * 0.5, y + np.sin(ang) * length * 0.5, length * 0.5, length * 0.28, ang)
    cv.wash(cv.poly(tip), ROSE, opacity=0.28, bleed=0.8, soft=1.0, edge=0.6)


def leaf(cv, x, y, length, width, ang, col=GREEN, op=0.55, curve=0.12):
    p = leaf_poly(x, y, length, width, ang, curve=curve)
    m = cv.poly(p)
    cv.wash(m, col, opacity=op, bleed=1.6, soft=0.8, edge=0.9, mottle=0.5, gran=0.5,
            blooms=1 if length > 60 else 0, bloom_size=length * 0.18)
    # second glaze on one half, darker, for the fold
    c, s = np.cos(ang), np.sin(ang)
    half = leaf_poly(x, y, length, width * 0.5, ang, curve=curve)
    shift = [(px - s * width * 0.18, py + c * width * 0.18) for px, py in half]
    cv.wash(cv.poly(shift), GREEN_D, opacity=op * 0.45, bleed=1.2, soft=1.0, edge=0.7)
    # vein lift
    vein = [(x + c * t * length - s * curve * length * np.sin(np.pi * t),
             y + s * t * length + c * curve * length * np.sin(np.pi * t)) for t in np.linspace(0.05, 0.9, 20)]
    cv.lift(cv.stroke(vein, 1.2), amount=0.35, soft=0.6)


def stem(cv, pts, w=3, col=GREEN_D, op=0.5):
    cv.wash(cv.stroke(pts, w), col, opacity=op, bleed=0.8, soft=0.6, edge=0.5)


def jasmine_spray(cv, base, tip, n_flowers=6, size=24, leaves=6, bend=0.25):
    bx, by = base
    tx, ty = tip
    mx, my = (bx + tx) / 2, (by + ty) / 2
    nx, ny = -(ty - by), (tx - bx)
    p1 = (bx + (mx - bx) * 0.6 + nx * bend * 0.6, by + (my - by) * 0.6 + ny * bend * 0.6)
    p2 = (mx + (tx - mx) * 0.4 + nx * bend, my + (ty - my) * 0.4 + ny * bend)
    path = bezier(base, p1, p2, tip, 60)
    stem(cv, path, w=np.linspace(4, 1.5, len(path)))
    for k in range(leaves):
        i = int(len(path) * (0.12 + 0.8 * k / max(1, leaves)))
        x, y = path[i]
        dx, dy = path[min(i + 1, len(path) - 1)] - path[i]
        a = np.arctan2(dy, dx) + (0.9 if k % 2 else -0.9) + r(-0.2, 0.2)
        L = size * r(2.0, 2.8)
        leaf(cv, x, y, L, L * 0.42, a, col=GREEN if k % 3 else SAP)
    tx_, ty_ = path[-1]
    for j in range(3):
        a = r(0, 6.28)
        jasmine_flower(cv, tx_ + np.cos(a) * size * 0.9, ty_ + np.sin(a) * size * 0.9, size * r(0.9, 1.1))
    jasmine_bud(cv, tx_, ty_ - size * 0.4, size * 1.2, -np.pi / 2 + r(-0.5, 0.5))
    for k in range(n_flowers):
        i = int(len(path) * (0.35 + 0.65 * k / max(1, n_flowers - 1)))
        i = min(i, len(path) - 1)
        x, y = path[i]
        off = r(-1, 1) * size * 1.2
        fx, fy = x + off, y + r(-1, 1) * size * 0.8
        stem(cv, [(x, y), (fx, fy)], w=1.2, op=0.35)
        if k % 3 == 2:
            jasmine_bud(cv, fx, fy, size * 1.1, r(-3.1, 0))
        else:
            jasmine_flower(cv, fx, fy, size * r(0.85, 1.1))


def lotus(cv, cx, cy, size, open_=1.0):
    """Pink lotus seen from the side; petals painted back to front."""
    layers = [  # (count, spread, length, width, tint)
        (5, 1.9 * open_, 1.00, 0.42, 0.32),
        (4, 1.3 * open_, 1.05, 0.46, 0.40),
        (3, 0.7 * open_, 1.00, 0.50, 0.50),
    ]
    for count, spread, L, W, tint in layers:
        for i in range(count):
            t = (i / max(1, count - 1) - 0.5)
            a = -np.pi / 2 + t * spread * 1.1
            p = petal_poly(cx, cy, size * L, size * W, a, tip=0.6)
            m = cv.poly(p)
            cv.wash(m, '#e895a8', opacity=tint * 0.6, bleed=1.4, soft=0.8, edge=1.1, mottle=0.45, gran=0.5)
            tipp = petal_poly(cx + np.cos(a) * size * L * 0.45, cy + np.sin(a) * size * L * 0.45,
                              size * L * 0.55, size * W * 0.75, a, tip=0.6)
            cv.wash(cv.poly(tipp), '#cf5f80', opacity=tint * 0.42, bleed=1.6, soft=2.0, edge=0.6, gran=0.6)
    # pale glow at the heart
    cv.lift(cv.ellipse(cx, cy - size * 0.35, size * 0.18, size * 0.22), amount=0.25, soft=4)


def lotus_pad(cv, cx, cy, rx, ry, rot=0.0):
    t = np.linspace(0, 2 * np.pi, 80)
    notch = np.abs(((t - rot) % (2 * np.pi)) - 0.0) < 0.18
    rr = np.where(notch, 0.25, 1.0)
    pts = [(cx + rx * rr[i] * np.cos(t[i]), cy + ry * rr[i] * np.sin(t[i])) for i in range(len(t))]
    m = cv.poly(pts)
    field = cv.gradient_field([(0, '#86b38e'), (0.5, SAP), (1, '#6f9f8a')], axis='x', warp=20)
    cv.wash(m, field, opacity=0.5, bleed=2.5, soft=1, edge=0.9, mottle=0.6, gran=0.7, blooms=1, bloom_size=rx * 0.25)
    # radial veins lifted
    vs = []
    for k in range(9):
        a = rot + 0.4 + k * (2 * np.pi - 0.8) / 8
        vs.append(([(cx, cy), (cx + rx * 0.9 * np.cos(a), cy + ry * 0.9 * np.sin(a))], 1.4))
    cv.lift(cv.strokes(vs), amount=0.25, soft=0.8)


def marigold(cv, cx, cy, size):
    for ring, (rr, col, op) in enumerate([(1.0, MARI, 0.55), (0.72, MARI_D, 0.45), (0.42, '#c9561f', 0.45)]):
        m = cv.ellipse(cx, cy, size * rr, size * rr * 0.92)
        cv.wash(m, col, opacity=op, bleed=2.2 * rr + 0.6, soft=0.6, edge=1.0, mottle=0.7, gran=0.6,
                local_warp=(size * 0.12, 1.5))


def mango_leaf(cv, x, y, length, ang):
    leaf(cv, x, y, length, length * 0.24, ang, col='#6e9a48', op=0.6, curve=0.06)


def palm(cv, base_x, base_y, height, lean=0.15, fronds=9, col='#4f6b55', op=0.55, scale=1.0):
    """Coconut palm: curved ringed trunk, crown of arching feathery fronds."""
    top_x = base_x + lean * height
    top_y = base_y - height
    trunk = bezier((base_x, base_y), (base_x + lean * height * 0.05, base_y - height * 0.45),
                   (top_x - lean * height * 0.35, top_y + height * 0.25), (top_x, top_y), 60)
    tw = np.linspace(11 * scale, 6.5 * scale, 60)
    cv.wash(cv.stroke(trunk, tw), '#8f7a62', opacity=op * 0.85, bleed=1, soft=0.6, edge=1.0, gran=0.8)
    # shadow side of the trunk
    cv.wash(cv.stroke(trunk + [2.5 * scale, 0], tw * 0.45), '#5d5068', opacity=op * 0.35, bleed=0.8, soft=0.8)
    # trunk rings — tiny lifts
    for i in range(4, 58, 4):
        x, y = trunk[i]
        cv.lift(cv.stroke([(x - tw[i] * 0.5, y), (x + tw[i] * 0.5, y + 1)], 1.0 * scale), amount=0.35, soft=0.4)
    spines, leaflets = [], []
    for k in range(fronds):
        a = -np.pi / 2 + (k / (fronds - 1) - 0.5) * 4.2 + r(-0.12, 0.12)
        L = height * r(0.30, 0.40) * (1.0 if abs(np.cos(a)) > 0.3 else 0.8)
        lift_ = L * (0.35 if abs(np.cos(a)) < 0.6 else 0.15)
        end = (top_x + np.cos(a) * L, top_y + np.sin(a) * L * 0.45 + L * 0.55 * abs(np.cos(a)) ** 1.5 + L * 0.2)
        c1 = (top_x + np.cos(a) * L * 0.35, top_y + np.sin(a) * L * 0.5 - lift_)
        c2 = (top_x + np.cos(a) * L * 0.75, top_y + np.sin(a) * L * 0.4 - lift_ * 0.4)
        path = bezier((top_x, top_y), c1, c2, end, 44)
        spines.append((path, np.linspace(3.2 * scale, 0.8 * scale, 44)))
        for j in range(3, 43):
            px, py = path[j]
            dx, dy = path[j + 1] - path[j - 1]
            nd = np.hypot(dx, dy) + 1e-6
            dx, dy = dx / nd, dy / nd
            ll = L * 0.22 * np.sin(np.pi * (j / 44) ** 0.8) * r(0.8, 1.1)
            for sgn in (1, -1):
                # leaflet points backwards along the spine and droops with gravity
                ang = np.arctan2(dy, dx) + sgn * 1.0
                qx = px + np.cos(ang) * ll * 0.55 - dx * ll * 0.3
                qy = py + np.sin(ang) * ll * 0.55 + ll * 0.75
                leaflets.append(([(px, py), ((px + qx) / 2, (py + qy) / 2 - ll * 0.08), (qx, qy)],
                                 [2.6 * scale, 2.0 * scale, 0.6 * scale]))
    m = cv.strokes(leaflets + spines)
    cv.wash(m, col, opacity=op, bleed=1.0, soft=0.5, edge=0.8, mottle=0.6, gran=0.5)
    # deeper tone in the crown
    cv.wash(cv.ellipse(top_x, top_y + 6 * scale, 26 * scale, 16 * scale), '#3f4f4a', opacity=op * 0.6, bleed=2, soft=2, edge=0.5)
    # coconuts
    for k in range(4):
        cv.wash(cv.ellipse(top_x + r(-12, 12) * scale, top_y + r(8, 20) * scale, 6 * scale, 6 * scale), '#7a6a3e',
                opacity=op * 0.7, bleed=0.6, soft=0.5, edge=1.0)
