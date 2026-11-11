"""Hydralink wordmark generator.

"Hydralink" is set in Sora SemiBold and converted to outlines (the SVGs need no font).
The y is a custom glyph: a two-headed hydra drawn as a water serpent - two sinuous necks
rising from one thick trunk that tapers into a pointed tail. The heads are serpentine
(flat skull, rows of teeth, slit-pupil eye, swept-back crest instead of horns) and
deliberately not mirror images: one flicks a forked tongue, the other hisses.
Detail is layered so it only shows as the logo gets larger: belly plates in the other
brand colour, scale marks on the flanks, fin rays, facial creases, spines down the tail.
It is drawn in a design space where the x-height is 1000 and y points up, then scaled
to the font's x-height and stem weight.

Usage:  pip install fonttools shapely && python3 tools/generate_logo.py
Fonts in tools/fonts are SIL Open Font License (see the *-LICENSE.txt files).
"""
import math, os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from shapely.geometry import Polygon
from shapely.ops import unary_union

GREEN, AMBER, PAPER = "#0F3D2E", "#F2A93B", "#F6F3EA"


# ---------- geometry helpers ----------
def bez(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n; m = 1 - t
        out.append((m**3*p0[0] + 3*m*m*t*p1[0] + 3*m*t*t*p2[0] + t**3*p3[0],
                    m**3*p0[1] + 3*m*m*t*p1[1] + 3*m*t*t*p2[1] + t**3*p3[1]))
    return out


def line(p0, p1, n=20):
    return [(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n) for i in range(n + 1)]


def spline(pts, n=10):
    """Closed outline through (x, y, kind) points; kind 's' = smooth, 'c' = sharp corner."""
    N = len(pts); out = []
    for i in range(N):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % N], pts[(i + 2) % N]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6) if p1[2] == "s" else p1
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6) if p2[2] == "s" else p2
        out += bez(p1, c1, c2, p2, n)[:-1]
    return out


class Path:
    """A centre line resampled evenly, with position / tangent lookup by distance."""
    def __init__(self, pts, step=6.0):
        d = [0.0]
        for a, b in zip(pts, pts[1:]):
            d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.total = d[-1]; n = max(2, round(self.total / step)); self.pts = []; j = 0
        for i in range(n + 1):
            s = self.total * i / n
            while j < len(d) - 2 and d[j + 1] < s: j += 1
            k = (s - d[j]) / ((d[j + 1] - d[j]) or 1)
            self.pts.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * k, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * k))

    def at(self, s):
        """point, unit tangent, unit normal (to the left of travel) at distance s."""
        f = max(0.0, min(1.0, s / self.total)) * (len(self.pts) - 1)
        i = min(int(f), len(self.pts) - 2); k = f - i
        a, b = self.pts[i], self.pts[i + 1]
        p = (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
        a, b = self.pts[max(i - 2, 0)], self.pts[min(i + 3, len(self.pts) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; n = math.hypot(tx, ty)
        return p, (tx / n, ty / n), (-ty / n, tx / n)

    def ribbon(self, half):
        L, R = [], []
        for i in range(len(self.pts)):
            s = self.total * i / (len(self.pts) - 1)
            p, t, n = self.at(s); h = half(s)
            L.append((p[0] + n[0] * h, p[1] + n[1] * h)); R.append((p[0] - n[0] * h, p[1] - n[1] * h))
        return Polygon(L + R[::-1]).buffer(0)


def unit(deg):  # degrees from +y (up), clockwise
    return math.sin(math.radians(deg)), math.cos(math.radians(deg))


def place(poly, origin, deg, k=1.0, mirror=False):
    """Local (x forward, y to the left of forward) -> world, heading deg from +y clockwise."""
    fx, fy = unit(deg); nx, ny = -fy, fx
    out = []
    for p in poly:
        x, y = p[0], (-p[1] if mirror else p[1])
        out.append((origin[0] + (x * fx + y * nx) * k, origin[1] + (x * fy + y * ny) * k))
    return out


# ---------- the hydra ----------
# Water-serpent head in profile for a neck 240 wide. x = forward (snout), y = up (top of the skull).
HEAD_NECK = 120.0
HEAD_TOP = [
    (-70, 120, "s"), (-20, 128, "s"), (40, 150, "s"),             # back of the skull (the crest is added as a fin)
    (120, 172, "s"), (200, 176, "s"),                             # flat skull, brow ridge over the eye
    (252, 164, "s"), (320, 144, "s"), (420, 128, "s"), (500, 120, "s"),   # deep, blunt snout
    (548, 122, "s"), (586, 102, "s"), (594, 70, "s"),             # nostril bump, blunt nose
    (578, 46, "c"),
    (560, 50, "c"), (552, -8, "c"), (534, 46, "c"),               # long front fang
    (470, 44, "s"),
    (444, 42, "c"), (436, 22, "c"), (424, 40, "c"),               # row of smaller teeth
    (396, 38, "c"), (389, 21, "c"), (379, 36, "c"),
    (350, 34, "c"), (344, 20, "c"), (335, 32, "c"),
    (340, 32, "s"), (250, 20, "s"), (190, 10, "c"),               # corner of the mouth, under the eye
]
JAW = [                                                           # lower jaw, closed pose; hinged at (150, 8)
    (260, 12, "s"), (330, 19, "s"),
    (352, 21, "c"), (361, 37, "c"), (371, 23, "c"),
    (408, 26, "c"), (418, 46, "c"), (430, 26, "c"),               # lower fang
    (480, 30, "s"), (514, 24, "s"), (520, 8, "s"),
    (496, -12, "s"), (430, -32, "s"), (350, -50, "s"),
    (300, -60, "c"), (284, -92, "c"), (266, -64, "c"),            # chin barbel
]
HEAD_BACK = [(200, -100, "s"), (120, -136, "s"), (40, -134, "s"), (-70, -120, "s")]   # jaw hinge, throat
HINGE = (190, 10)
EYE = [(194, 140, "c"), (228, 162, "s"), (268, 140, "c"), (230, 124, "s")]
PUPIL = [(224, 160, "c"), (233, 144, "s"), (238, 126, "c"), (229, 142, "s")]
NOSTRIL = [(536, 86, "c"), (554, 96, "s"), (568, 84, "c"), (552, 80, "s")]
TONGUE = [(300, 16, "c"), (470, 12, "s"), (620, 10, "s"), (668, 30, "s"), (712, 52, "c"),
          (672, 8, "s"), (650, -4, "c"), (676, -22, "s"), (716, -44, "c"),
          (664, -28, "s"), (620, -10, "s"), (470, -2, "s"), (300, 2, "c")]


def _reshape(pts, top=1.0, bottom=1.0):
    out = []
    for x, y, kind in pts:
        if x > 250: x = 250 + (x - 250) * 0.84           # shorter snout
        if y > 100: y *= top                             # higher skull
        if y < 0: y *= bottom                            # deeper lower jaw
        out.append((x, y, kind))
    return out


HEAD_TOP = _reshape(HEAD_TOP, top=1.2)
JAW = _reshape(JAW, bottom=1.35)
NOSTRIL = [(x, y + 16, k_) for x, y, k_ in _reshape(NOSTRIL)]
EYE = [(x, y * 1.2 - 4, k_) for x, y, k_ in EYE]
PUPIL = [(x, y * 1.2 - 4, k_) for x, y, k_ in PUPIL]
TONGUE = _reshape(TONGUE)
HEAD_BACK = [(200, -118, "s"), (120, -142, "s"), (40, -136, "s"), (-70, -120, "s")]


# fine detail on the head, in final head coordinates: (points, width) creases cut out of the silhouette
HEAD_LINES = [
    ([(505, 74), (440, 72), (360, 66), (280, 56), (215, 42)], 7),        # lip line
    ([(186, -2), (160, -26), (142, -58)], 5),                            # jaw crease behind the mouth
    ([(182, 150), (215, 134), (250, 132), (286, 148)], 6),               # eye socket
    ([(472, 118), (410, 128), (340, 148), (296, 166)], 6),               # ridge from nostril to brow
]
# top of the skull behind the brow, in final head coordinates: where the crest stands
SKULL_RAIL = [(168, 210), (130, 207), (95, 198), (60, 187), (25, 174), (-10, 160), (-40, 150)]
HEAD_SCALES = [(128, 84, 22), (78, 50, 22), (150, 30, 20), (96, -6, 22), (40, 4, 20), (48, -70, 20), (10, 70, 18)]


def rot(pts, pivot, deg):
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(pivot[0] + (p[0] - pivot[0]) * c - (p[1] - pivot[1]) * s_,
             pivot[1] + (p[0] - pivot[0]) * s_ + (p[1] - pivot[1]) * c) + tuple(p[2:]) for p in pts]


def head_outline(gape):
    return HEAD_TOP + rot(JAW, HINGE, -gape) + HEAD_BACK


def crease(pts, width):
    """A thin line with tapered ends through the given points."""
    if len(pts) > 2:
        sm = []
        for i in range(len(pts) - 1):
            p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
            sm += bez(p1, (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6),
                      (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6), p2, 10)[:-1]
        pts = sm + [pts[-1]]
    path = Path(pts, step=4.0)
    return path.ribbon(lambda s: (width / 2) * min(1.0, 0.25 + 3.0 * min(s, path.total - s) / path.total))


def crescent(c, facing, r, th):
    """Scale mark: an arc whose rounded edge faces `facing` (unit vector)."""
    base = math.atan2(facing[1], facing[0]); outer, inner = [], []
    for i in range(11):
        a = base + math.radians(-78 + 156 * i / 10)
        w = th * (0.35 + 0.65 * math.sin(math.pi * i / 10))
        outer.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
        inner.append((c[0] + (r - w) * math.cos(a), c[1] + (r - w) * math.sin(a)))
    return Polygon(outer + inner[::-1])


def hydra_y(W, P):
    """Returns [(shapely geometry, role)]."""
    k = (W * P["neck_tip"] / 2) / HEAD_NECK
    J = (P["jx"], P["jy"])
    body, belly, solid, extra = {}, {}, {}, []
    for side in (-1, 1):
        S = P["left"] if side == -1 else P["right"]
        mir = side == -1
        sa, ma, ha = side * S["start_ang"], side * S["mid_ang"], side * S["head_ang"]
        sx, sy = unit(sa); mx, my = unit(ma); hx, hy = unit(ha)
        M = (J[0] + side * S["mid_x"], S["mid_y"])
        base = (J[0] + side * S["base_x"], S["base_y"])
        centre = bez(J, (J[0] + sx * S["h1"], J[1] + sy * S["h1"]), (M[0] - mx * S["h2"], M[1] - my * S["h2"]), M)
        centre += bez(M, (M[0] + mx * S["h3"], M[1] + my * S["h3"]), (base[0] - hx * S["h4"], base[1] - hy * S["h4"]), base)[1:]
        tail_pts = []
        if side == 1:   # the right neck runs on through the junction into body and tail
            ux, uy = -sx, -sy
            p1 = (J[0] + ux * P["body_len"], J[1] + uy * P["body_len"])
            T = P["tail"]
            tail_pts = line(J, p1)[1:] + bez(p1, (p1[0] + ux * P["tail_h"], p1[1] + uy * P["tail_h"]), T[0], T[1])[1:]
            for i in range(1, len(T) - 3, 3):
                tail_pts += bez(T[i], T[i + 1], T[i + 2], T[i + 3])[1:]
            centre = tail_pts[::-1] + centre
        path = Path(centre)
        tail_len = Path([J] + tail_pts).total if tail_pts else 0.0
        neck_len = path.total - tail_len
        total = path.total

        def half(s, tail_len=tail_len, neck_len=neck_len):
            if s >= tail_len:                       # neck: thick trunk at the base, slim towards the head
                q = (s - tail_len) / neck_len
                return (W / 2) * (P["trunk"] - (P["trunk"] - P["neck_tip"]) * q ** P["neck_pow"])
            q = (tail_len - s) / tail_len
            end = min(1.0, s / 40.0) ** 0.6           # pointed tip
            return (W / 2) * (P["trunk"] - (P["trunk"] - P["tail_tip"]) * q ** P["tail_pow"]) * end

        d = side                                    # dorsal side: +1 = left of the travel direction

        def at(s, lat):                             # point at distance s, lat = offset towards the back
            p, t, n = path.at(s)
            return (p[0] + d * n[0] * lat, p[1] + d * n[1] * lat)

        head = Polygon(place(spline(head_outline(S["gape"])), base, ha, k, mirror=mir)).buffer(0)
        parts = [path.ribbon(half), head]
        cuts = [Polygon(place(spline(NOSTRIL), base, ha, k, mirror=mir))]

        # --- fins: evenly graded spines joined by a membrane, one ray per spine
        def fin(rail, height, lean, web, ray_w):
            """rail runs from the head end towards the tail; height(u) for u = 0..1 along it."""
            rp = Path(rail, step=4.0)
            tips = []
            pos = 0.0
            while True:
                hgt = height(min(1.0, pos / rp.total)); step = hgt * P["fin_pitch"]
                if pos + step > rp.total or hgt < 8: break
                c, t, n = rp.at(pos + step / 2)
                o = (-d * n[0], -d * n[1])                       # outwards, away from the body
                b = hgt * P["fin_base"]
                tip = (c[0] + o[0] * hgt * math.cos(lean) + t[0] * hgt * math.sin(lean),
                       c[1] + o[1] * hgt * math.cos(lean) + t[1] * hgt * math.sin(lean))
                front = (c[0] - t[0] * b - o[0] * 8, c[1] - t[1] * b - o[1] * 8)
                back = (c[0] + t[0] * b - o[0] * 8, c[1] + t[1] * b - o[1] * 8)
                tips.append((c, tip, front, back, hgt, o, t))
                pos += step
            for i, (c, tip, front, back, hgt, o, t) in enumerate(tips):
                # the spine itself: slim, with a gently curved trailing edge
                lead_mid = ((tip[0] + front[0]) / 2 - t[0] * hgt * 0.07, (tip[1] + front[1]) / 2 - t[1] * hgt * 0.07)
                trail_mid = ((tip[0] + back[0]) / 2 - t[0] * hgt * 0.09, (tip[1] + back[1]) / 2 - t[1] * hgt * 0.09)
                parts.append(Polygon(spline([front + ("c",), lead_mid + ("s",), tip + ("c",), trail_mid + ("s",), back + ("c",)], 6)).buffer(0))
                if i + 1 < len(tips) and web > 0:                 # scallop of membrane down to the next spine
                    c2, tip2, front2, back2, hgt2, o2, t2 = tips[i + 1]
                    hv = (hgt + hgt2) / 2 * web
                    m = ((c[0] + c2[0]) / 2, (c[1] + c2[1]) / 2)
                    valley = (m[0] + o[0] * hv * math.cos(lean) + t[0] * hv * math.sin(lean),
                              m[1] + o[1] * hv * math.cos(lean) + t[1] * hv * math.sin(lean))
                    top = spline([tip + ("c",), valley + ("s",), tip2 + ("c",),
                                  (c2[0] - o2[0] * 8, c2[1] - o2[1] * 8, "c"), (c[0] - o[0] * 8, c[1] - o[1] * 8, "c")], 8)
                    parts.append(Polygon(top).buffer(0))
            for c, tip, front, back, hgt, o, t in tips:
                if hgt > 40:
                    cuts.append(crease([(c[0] + (tip[0] - c[0]) * 0.20, c[1] + (tip[1] - c[1]) * 0.20),
                                        (c[0] + (tip[0] - c[0]) * 0.80, c[1] + (tip[1] - c[1]) * 0.80)], ray_w))

        lean = math.radians(P["fin_lean"])
        s_end = tail_len + neck_len * (1 - P["fin_reach"])
        rail = place(SKULL_RAIL, base, ha, k, mirror=mir)
        n_ = 40
        rail += [at(total - 46 - (total - 46 - s_end) * i / n_, half(total - 46 - (total - 46 - s_end) * i / n_)) for i in range(n_ + 1)]
        for _ in range(3):                                        # smooth the join between skull and neck
            rail = [rail[0]] + [((a[0] + 2 * b[0] + c[0]) / 4, (a[1] + 2 * b[1] + c[1]) / 4)
                                for a, b, c in zip(rail, rail[1:], rail[2:])] + [rail[-1]]
        H = P["fin"] * W / 261.0

        def crest(u):                                             # low over the brow, tallest behind the skull, fading down the neck
            rise = 0.55 + 0.45 * min(1.0, u / 0.10)
            fall = 1.0 - 0.68 * max(0.0, (u - 0.10) / 0.90) ** 0.85
            return H * rise * fall

        fin(rail, crest, lean, P["fin_web"], 5.0)
        if side == 1:                                             # a low ridge along the back of the tail
            n_ = 40; s0 = tail_len - P["tail_fin_start"]; s1 = P["tail_fin_stop"]
            trail = [at(s0 - (s0 - s1) * i / n_, half(s0 - (s0 - s1) * i / n_)) for i in range(n_ + 1)]
            Ht = P["tail_fin"] * W / 261.0
            fin(trail, lambda u: Ht * (1.0 - 0.62 * u), lean, P["fin_web"], 4.0)

        g = unary_union(parts)
        r = P["soften"]
        g = g.buffer(r).buffer(-2 * r).buffer(r)
        solid[side] = g

        # --- belly: a band of plates along the throat side, in the other colour
        bw = P["belly"]; lo = 46.0; band = []
        s_hi = total - 6
        n_ = int((s_hi - lo) / 8)
        outer, inner = [], []
        for i in range(n_ + 1):
            s = lo + (s_hi - lo) * i / n_; h = half(s)
            f = min(1.0, (s_hi - s) / 90.0) ** 0.7 * min(1.0, (s - lo) / 120.0 + 0.25)   # tapers under the jaw / at the tail
            outer.append(at(s, -(h + 12))); inner.append(at(s, -h + h * bw * f))
        band = Polygon(outer + inner[::-1]).buffer(0).intersection(g.difference(head.buffer(-2))).buffer(-P["belly_rim"])
        plates = []
        s = s_hi - 30
        while s > lo + 20:
            h = half(s)
            a0 = at(s, -(h + 14)); b0 = at(s + h * 0.22, -h + h * bw + 6)
            plates.append(crease([a0, b0], P["plate_w"] * (0.6 + 0.4 * h / (W / 2)) * 2))
            s -= max(22.0, h * P["plate_gap"])
        belly[side] = band.difference(unary_union(plates))

        # --- scales on the flank: staggered crescents, rounded edge towards the tail
        rows = P["scale_rows"]
        s = total - 40; i = 0
        while s > 150:
            p, t, n = path.at(s); h = half(s)
            if h > 46:
                for j, lat in enumerate(rows):
                    ss = s - (h * 0.36 if j % 2 else 0)
                    c = at(ss, h * lat); pp, tt, nn = path.at(ss)
                    cuts.append(crescent(c, (-tt[0], -tt[1]), h * P["scale_r"], max(4.0, h * P["scale_w"])))
            s -= h * 0.72; i += 1
        # --- head detail
        for pts, w in HEAD_LINES:
            cuts.append(crease(place(pts, base, ha, k, mirror=mir), w * k * 1.25))
        back = (-hx, -hy)
        for x, y, rr in HEAD_SCALES:
            c = place([(x, y)], base, ha, k, mirror=mir)[0]
            cuts.append(crescent(c, back, rr * k, 6 * k))
        allcuts = unary_union(cuts).intersection(g.buffer(-P["edge_keep"]))
        body[side] = g.difference(allcuts)
        tag = "l" if side == -1 else "r"
        if S["tongue"]:
            tg = [(HINGE[0] + (x - HINGE[0]) * S["tongue"], y, kind) for x, y, kind in TONGUE]
            tg = rot(tg, HINGE, -S["gape"] * 0.55)
            tongue = Polygon(place(spline(tg), base, ha, k, mirror=mir)).buffer(0)
            extra.append((tongue.difference(g), "tongue_" + tag))
        extra.append((Polygon(place(spline(EYE), base, ha, k, mirror=mir)), "eye_" + tag))
        extra.append((Polygon(place(spline(PUPIL), base, ha, k, mirror=mir)), "pupil_" + tag))
    over = solid[1].buffer(P["overlap_gap"])          # a hairline gap where the left neck passes behind
    return [(body[-1].difference(over), "left"), (belly[-1].difference(over), "belly_l"),
            (body[1], "right"), (belly[1], "belly_r")] + extra


NECK_L = dict(start_ang=27, mid_ang=12, head_ang=66, mid_x=205, mid_y=380, base_x=300, base_y=655,
              h1=130, h2=120, h3=110, h4=110, gape=6, tongue=1.0)
NECK_R = dict(start_ang=25, mid_ang=12, head_ang=56, mid_x=200, mid_y=400, base_x=298, base_y=672,
              h1=130, h2=120, h3=120, h4=110, gape=9, tongue=0.0)
DEFAULTS = dict(jx=25, jy=40, left=NECK_L, right=NECK_R, neck_tip=0.74, trunk=1.04, neck_pow=1.2,
                body_len=110, tail_h=190, tail_tip=0.08, tail_pow=0.85,
                tail=((-150, -300), (-255, -300), (-345, -300), (-405, -255), (-398, -170)),
                soften=1.5, fin=82, fin_pitch=0.84, fin_base=0.31, fin_lean=20, fin_reach=0.56, fin_web=0.0,
                tail_fin=38, tail_fin_start=170, tail_fin_stop=90,
                belly=0.60, belly_rim=5, plate_w=4.5, plate_gap=0.34,
                scale_rows=(0.66, 0.26, -0.12), scale_r=0.22, scale_w=0.055, edge_keep=7, overlap_gap=7,
                two_tone=True, lsb=70, rsb=58)


def geom_path(g, fx, fy):
    polys = [g] if g.geom_type == "Polygon" else [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]
    d = ""
    for p in polys:
        for ring in [p.exterior] + list(p.interiors):
            d += "M" + "L".join(f"{fx(x):.1f} {fy(y):.1f}" for x, y in ring.coords[:-1]) + "Z"
    return d


class Wordmark:
    def __init__(self, font_path, **params):
        self.font = TTFont(font_path); self.gs = self.font.getGlyphSet(); self.cmap = self.font.getBestCmap()
        self.P = {**DEFAULTS, **params}
        self.xh = self.bounds("x")[3]
        rp = RecordingPen(); self.gs[self.cmap[ord("H")]].draw(rp)
        xs = sorted({round(p[0]) for _, args in rp.value for p in args})
        self.stem = xs[1] - xs[0]
        self.u = self.xh / 1000.0
        self.shapes = [(g.simplify(0.5), role) for g, role in hydra_y(self.stem / self.u, self.P)]
        b = unary_union([g for g, _ in self.shapes]).bounds
        self.ext = b   # minx, miny, maxx, maxy in design space

    def bounds(self, ch):
        bp = BoundsPen(self.gs); self.gs[self.cmap[ord(ch)]].draw(bp); return bp.bounds

    def colors(self, fg, accent, eye_dark):
        two = self.P["two_tone"]
        left = accent if two else fg
        return {"left": left, "right": fg, "belly_l": fg if two else accent, "belly_r": accent,
                "eye_l": eye_dark if two else accent, "eye_r": accent,
                "pupil_l": left, "pupil_r": fg, "tongue_l": fg if two else accent, "tongue_r": accent}

    def ypaths(self, ox, oy, k, colors):
        return [f'<path d="{geom_path(g, lambda x: ox + x * k, lambda y: oy - y * k)}" fill="{colors[role]}" fill-rule="evenodd"/>'
                for g, role in self.shapes]

    def build(self, fg=GREEN, accent=AMBER, eye_dark=GREEN, track=0, text="Hydralink", pad=None, bg=None):
        u = self.u
        x0d, y0d, x1d, y1d = self.ext
        asc = max([self.bounds(c)[3] for c in text if c != "y"] or [0])
        top = max(asc, y1d * u); depth = -y0d * u
        pad = self.xh * 0.12 if pad is None else pad
        x = pad; base = pad + top; parts = []
        for ch in text:
            if ch == "y":
                gx = x + self.P["lsb"] * u - x0d * u
                parts += self.ypaths(gx, base, u, self.colors(fg, accent, eye_dark))
                x = gx + x1d * u + self.P["rsb"] * u + track
            else:
                gn = self.cmap[ord(ch)]
                pen = SVGPathPen(self.gs, lambda v: f"{v:.1f}")
                self.gs[gn].draw(TransformPen(pen, (1, 0, 0, -1, x, base)))
                parts.append(f'<path d="{pen.getCommands()}" fill="{fg}"/>')
                x += self.gs[gn].width + track
        Wd = x - track + pad; Ht = base + depth + pad
        rect = f'<rect width="{Wd:.0f}" height="{Ht:.0f}" fill="{bg}"/>' if bg else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {Wd:.0f} {Ht:.0f}" role="img" aria-label="Hydralink">'
                f'<title>Hydralink</title>{rect}\n' + "\n".join(parts) + "\n</svg>\n")

    def icon(self, bg=GREEN, fg=PAPER, accent=AMBER, size=1024, fill=0.72):
        x0, y0, x1, y1 = self.ext
        k = size * fill / max(x1 - x0, y1 - y0)
        ox = size / 2 - (x0 + x1) / 2 * k; oy = size / 2 + (y0 + y1) / 2 * k
        parts = self.ypaths(ox, oy, k, self.colors(fg, accent, bg))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" role="img" aria-label="Hydralink">'
                f'<title>Hydralink</title><rect width="{size}" height="{size}" rx="{size * .22:.0f}" fill="{bg}"/>\n'
                + "\n".join(parts) + "\n</svg>\n")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "logo")
    fpath = os.environ.get("HL_FONT", os.path.join(here, "fonts", "sora-latin-600-normal.woff"))
    main = Wordmark(fpath)
    mono = Wordmark(fpath, two_tone=False)
    files = {
        "hydralink-logo.svg": main.build(),                       # primary, for light backgrounds
        "hydralink-logo-on-dark.svg": main.build(fg=PAPER),       # primary, for dark backgrounds
        "hydralink-logo-mono.svg": mono.build(),                  # single colour, amber eyes only
        "hydralink-logo-mono-on-dark.svg": mono.build(fg=PAPER),
        "hydralink-icon.svg": main.icon(),                        # favicon / avatar
        "_zoom.svg": main.build(text="y", bg=PAPER),
    }
    for name, data in files.items():
        if name.startswith("_") and len(sys.argv) < 2: continue
        with open(os.path.join(out, name), "w") as f:
            f.write(data)
        print("wrote", name, len(data), "bytes")
