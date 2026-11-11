"""Hydralink wordmark generator - dragon-headed Hydra y.

The word is set in Sora SemiBold and converted to outlines (the SVGs need no font).
The y is replaced by a custom glyph - two dragon necks meeting in one body with a
spade-tipped tail - drawn in a design space where the x-height is 1000 and y points
up, then scaled to the font's x-height and stem weight.

Usage:  pip install fonttools && python3 tools/archive/generate_illustrative.py
Fonts in tools/fonts are SIL Open Font License (see the *-LICENSE.txt files).
"""
import math, os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

GREEN, AMBER, PAPER = "#0F3D2E", "#F2A93B", "#F6F3EA"


# ---------- small geometry helpers ----------
def bez(p0, p1, p2, p3, n=48):
    out = []
    for i in range(n + 1):
        t = i / n; m = 1 - t
        out.append((m**3*p0[0] + 3*m*m*t*p1[0] + 3*m*t*t*p2[0] + t**3*p3[0],
                    m**3*p0[1] + 3*m*m*t*p1[1] + 3*m*t*t*p2[1] + t**3*p3[1]))
    return out


def line(p0, p1, n=24):
    return [(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n) for i in range(n + 1)]


def resample(pts, step):
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = d[-1]; n = max(2, round(total / step)); out = []; j = 0
    for i in range(n + 1):
        s = total * i / n
        while j < len(d) - 2 and d[j + 1] < s: j += 1
        k = (s - d[j]) / ((d[j + 1] - d[j]) or 1)
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * k, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * k))
    return out, total


def ribbon(pts, half, step=8.0):
    """Polygon around a centre line; half(s, total) gives the half-width at distance s."""
    pts, total = resample(pts, step)
    L, R = [], []
    for i, p in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; n = math.hypot(tx, ty)
        nx, ny = -ty / n, tx / n
        h = half(total * i / (len(pts) - 1), total)
        L.append((p[0] + nx * h, p[1] + ny * h)); R.append((p[0] - nx * h, p[1] - ny * h))
    return L + R[::-1]


def unit(deg):  # degrees from +y (up), clockwise
    return math.sin(math.radians(deg)), math.cos(math.radians(deg))


def place(poly, origin, deg, k=1.0, mirror=False):
    """Local (x forward, y to the left of forward) -> world, heading deg from +y clockwise."""
    fx, fy = unit(deg); nx, ny = -fy, fx
    out = []
    for x, y in poly:
        if mirror: y = -y
        out.append((origin[0] + (x * fx + y * nx) * k, origin[1] + (x * fy + y * ny) * k))
    return out


# ---------- the dragon ----------
# Head in profile, drawn for a neck of width 250. x = forward (snout), y = top of skull.
def head_poly(h):
    """Dragon head in profile. x = forward (snout), y = top of skull, h = half neck width (local units)."""
    return [(-80, h), (-10, h),
            (-128, h + 96), (58, h + 46),             # rear horn, swept back along the neck
            (-12, h + 150), (150, h + 56),            # front horn
            (212, h + 66), (250, h + 28),             # brow ridge
            (452, 92), (488, 106), (540, 80), (562, 40), (548, 10),   # snout, nostril, hooked nose
            (300, -26),                                # corner of the mouth
            (516, -36), (490, -70),                    # lower jaw tip, chin
            (245, -h - 4), (150, -h - 58), (165, -h + 2), (-80, -h)]   # jaw line + cheek spike


EYE = [(200, 86), (300, 116), (284, 68)]
SPADE = [(-30, 0), (10, 105), (230, 0), (10, -105)]   # arrow tip of the tail


def hydra_y(W, P):
    """Returns list of (polygon, role) in design space (x-height 1000). role: fg / accent / eye_l / eye_r."""
    k = W / 250 * P["head"]
    J = (P["jx"], P["jy"])
    shapes = []
    necks = {}
    for side in (-1, 1):
        na = side * P["neck_ang"]; ha = side * P["head_ang"]
        nx, ny = unit(na); hx, hy = unit(ha)
        n1 = (J[0] + nx * P["neck_len"], J[1] + ny * P["neck_len"])
        base = (J[0] + side * P["base_x"], P["base_y"])
        c = line(J, n1) + bez(n1, (n1[0] + nx * P["bend"], n1[1] + ny * P["bend"]),
                              (base[0] - hx * P["bend"], base[1] - hy * P["bend"]), base)[1:]
        necks[side] = c
        # head: for the right head (side=1) skull is to the left of forward (towards the top)
        hp = place(head_poly(W * P["neck_tip"] / 2 / k), base, ha, k, mirror=(side == -1))
        ep = place(EYE, base, ha, k, mirror=(side == -1))
        shapes.append((side, hp, ep))
    # body + tail continue the right neck through the junction
    ux, uy = unit(P["neck_ang"]); ux, uy = -ux, -uy
    p1 = (J[0] + ux * P["body_len"], J[1] + uy * P["body_len"])
    t1, t2, t3 = P["tail"]
    tail = line(J, p1)[1:] + bez(p1, (p1[0] + ux * P["tail_h"], p1[1] + uy * P["tail_h"]), t1, t2)[1:]
    tail += bez(t2, (2 * t2[0] - t1[0], 2 * t2[1] - t1[1]), t3[0], t3[1])[1:]
    body_c = necks[1][::-1] + tail
    neck_total = resample(necks[1], 8)[1]

    def neck_half(s, total):          # s measured from the junction up to the head
        q = min(1, s / total)
        return (W / 2) * (1 - (1 - P["neck_tip"]) * q ** 1.3)

    def body_half(s, total):
        s0 = neck_total + P["taper_after"]
        if s < neck_total: return neck_half(neck_total - s, neck_total)
        if s < s0: return W / 2
        q = (s - s0) / (total - s0)
        return (W / 2) * (1 - (1 - P["tail_tip"]) * (1 - (1 - q) ** 1.5))

    out = []
    left_role = "accent" if P.get("two_tone", True) else "fg"
    out.append((ribbon(necks[-1], neck_half), left_role))
    out.append((ribbon(body_c, body_half), "fg"))
    # tail spade
    e0, e1 = tail[-4], tail[-1]
    ang = math.degrees(math.atan2(e1[0] - e0[0], e1[1] - e0[1]))
    out.append((place(SPADE, e1, ang, W / 250 * P["spade"]), "fg"))
    for side, hp, ep in shapes:
        out.append((hp, left_role if side == -1 else "fg"))
        out.append((ep, "eye_l" if side == -1 else "eye_r"))
    return out


DEFAULTS = dict(jx=25, jy=40, neck_ang=23, head_ang=58, neck_len=400, base_x=295, base_y=690, bend=150,
                head=0.84, neck_tip=0.80, body_len=120, tail_h=190,
                tail=((-150, -300), (-255, -300), ((-345, -300), (-395, -235))),
                taper_after=40, tail_tip=0.20, spade=0.60, two_tone=True, lsb=70, rsb=58)


class Wordmark:
    def __init__(self, font_path, **params):
        self.font = TTFont(font_path)
        self.gs = self.font.getGlyphSet()
        self.P = {**DEFAULTS, **params}
        self.xh = self.bounds("x")[3]
        from fontTools.pens.recordingPen import RecordingPen
        rp = RecordingPen(); self.gs[self.glyph_name("H")].draw(rp)
        xs = sorted({round(p[0]) for _, args in rp.value for p in args})
        self.stem = xs[1] - xs[0]
        self.asc = max(self.bounds(c)[3] for c in "Hdlik")
        self.u = self.xh / 1000.0

    def bounds(self, g):
        bp = BoundsPen(self.gs); self.gs[self.glyph_name(g)].draw(bp); return bp.bounds

    def glyph_name(self, ch):
        return self.font.getBestCmap()[ord(ch)]

    def build(self, fg=GREEN, accent=AMBER, track=0, text="Hydralink", pad=None, bg=None, round_px=None):
        u = self.u; W = self.stem / u
        ypolys = hydra_y(W, self.P)
        xs = [p[0] for poly, _ in ypolys for p in poly]; ys = [p[1] for poly, _ in ypolys for p in poly]
        y_left, y_right = min(xs) * u, max(xs) * u
        depth = -min(ys) * u
        top = max(self.asc, max(ys) * u)
        pad = self.xh * 0.12 if pad is None else pad
        r = self.stem * 0.07 if round_px is None else round_px
        colors = {"fg": fg, "accent": accent, "eye_r": accent,
                  "eye_l": (GREEN if self.P["two_tone"] else accent)}
        x = pad; base = pad + top; parts = []
        for ch in text:
            if ch == "y":
                x0 = x + self.P["lsb"] * u - y_left
                for poly, role in ypolys:
                    col = colors[role]
                    d = "M" + "L".join(f"{x0 + px * u:.1f} {base - py * u:.1f}" for px, py in poly) + "Z"
                    extra = "" if role.startswith("eye") else f' stroke="{col}" stroke-width="{r:.1f}" stroke-linejoin="round"'
                    parts.append(f'<path d="{d}" fill="{col}"{extra}/>')
                x = x0 + y_right + self.P["rsb"] * u + track
            else:
                gn = self.glyph_name(ch)
                pen = SVGPathPen(self.gs, lambda v: f"{v:.1f}")
                self.gs[gn].draw(TransformPen(pen, (1, 0, 0, -1, x, base)))
                parts.append(f'<path d="{pen.getCommands()}" fill="{fg}"/>')
                x += self.gs[gn].width + track
        Wd = x - track + pad; Ht = base + depth + pad
        rect = f'<rect width="{Wd:.0f}" height="{Ht:.0f}" fill="{bg}"/>' if bg else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {Wd:.0f} {Ht:.0f}" role="img" aria-label="Hydralink">'
                f'<title>Hydralink</title>{rect}\n' + "\n".join(parts) + "\n</svg>\n")


def icon(wm, bg=GREEN, fg=PAPER, accent=AMBER, size=1024):
    """Square app icon / favicon: the Hydra-y on a rounded tile."""
    polys = hydra_y(wm.stem / wm.u, wm.P)
    xs = [p[0] for poly, _ in polys for p in poly]; ys = [p[1] for poly, _ in polys for p in poly]
    k = size * 0.70 / max(max(xs) - min(xs), max(ys) - min(ys))
    ox = size / 2 - (min(xs) + max(xs)) / 2 * k; oy = size / 2 + (min(ys) + max(ys)) / 2 * k
    colors = {"fg": fg, "accent": accent, "eye_r": accent, "eye_l": bg}
    parts = []
    for poly, role in polys:
        col = colors[role]
        d = "M" + "L".join(f"{ox + px * k:.1f} {oy - py * k:.1f}" for px, py in poly) + "Z"
        extra = "" if role.startswith("eye") else f' stroke="{col}" stroke-width="{size * .008:.1f}" stroke-linejoin="round"'
        parts.append(f'<path d="{d}" fill="{col}"{extra}/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" role="img" aria-label="Hydralink">'
            f'<title>Hydralink</title><rect width="{size}" height="{size}" rx="{size * .22:.0f}" fill="{bg}"/>\n'
            + "\n".join(parts) + "\n</svg>\n")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "..", "logo", "archive", "01-illustrative")
    font = lambda n: os.path.join(here, "..", "fonts", f"{n}-latin-600-normal.woff")
    main = Wordmark(font("sora"))
    mono = Wordmark(font("sora"), two_tone=False)
    files = {
        "hydralink-logo.svg": main.build(),                       # primary, for light backgrounds
        "hydralink-logo-on-dark.svg": main.build(fg=PAPER),       # primary, for dark backgrounds
        "hydralink-logo-alt.svg": mono.build(),                   # quieter: all green, amber eyes only
        "hydralink-logo-alt-on-dark.svg": mono.build(fg=PAPER),
        "hydralink-icon.svg": icon(main),                         # favicon / avatar
        "font-options/hydralink-outfit.svg": Wordmark(font("outfit")).build(),
        "font-options/hydralink-space-grotesk.svg": Wordmark(font("space-grotesk")).build(),
    }
    for name, data in files.items():
        with open(os.path.join(out, name), "w") as f:
            f.write(data)
        print("wrote", name, len(data), "bytes")
