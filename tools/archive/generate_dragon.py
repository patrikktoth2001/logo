"""Hydralink wordmark generator.

"Hydralink" is set in Sora SemiBold and converted to outlines (the SVGs need no font).
The y is a custom glyph: a two-headed hydra - two dragon necks rising from one body that
tapers into a spade-tipped tail. It is drawn in a design space where the x-height is 1000
and y points up, then scaled to the font's x-height and stem weight.

Usage:  pip install fonttools shapely && python3 tools/archive/generate_dragon.py
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
# Dragon head in profile for a neck 240 wide. x = forward (snout), y = up (top of the skull).
HEAD = [
    (-70, 120, "s"), (-28, 138, "s"), (-18, 186, "s"),            # nape
    (-60, 214, "s"), (-150, 256, "s"), (-235, 262, "c"),          # horn, curving back
    (-150, 292, "s"), (-50, 290, "s"), (50, 262, "s"),
    (120, 244, "s"), (200, 240, "s"),                             # skull, brow ridge
    (255, 216, "s"), (310, 178, "s"),
    (390, 152, "s"), (470, 142, "s"), (522, 148, "s"),            # snout, nostril bump
    (562, 126, "s"), (580, 90, "s"), (570, 58, "s"),
    (548, 38, "c"),                                               # hooked tip of the upper lip
    (522, 54, "c"), (506, 16, "c"), (488, 52, "c"),               # fang
    (440, 46, "c"), (428, 22, "c"), (412, 42, "c"),               # second tooth
    (340, 26, "s"), (270, 8, "c"),                                # corner of the mouth
    (340, 4, "s"), (412, 0, "c"), (426, 24, "c"), (440, -2, "c"),        # lower tooth
    (486, -6, "s"), (520, -18, "s"), (514, -50, "s"),             # lower jaw
    (466, -80, "s"), (412, -94, "c"), (394, -126, "c"), (374, -98, "c"),  # chin spike
    (300, -114, "s"), (225, -136, "s"), (175, -152, "c"),
    (112, -204, "c"), (126, -148, "c"), (58, -180, "c"), (72, -124, "c"),  # jaw frill
    (-70, -120, "s"),
]
EYE = [(218, 178, "c"), (250, 200, "s"), (300, 178, "c"), (262, 162, "s")]
NOSTRIL = [(520, 118, "c"), (540, 128, "s"), (556, 112, "c"), (538, 108, "s")]
SPADE = [(-40, 0, "c"), (-10, 60, "s"), (20, 118, "c"), (120, 70, "s"), (250, 0, "c"),
         (120, -70, "s"), (20, -118, "c"), (-10, -60, "s")]
HEAD_NECK = 120.0      # half neck width the head is drawn for


def hydra_y(W, P):
    """Returns [(shapely geometry, role)], roles: left / right / eye_l / eye_r."""
    k = (W * P["neck_tip"] / 2) / HEAD_NECK * P["head"]
    J = (P["jx"], P["jy"])
    geoms = {}; eyes = {}; solid = {}
    for side in (-1, 1):
        na, ha = side * P["neck_ang"], side * P["head_ang"]
        nx, ny = unit(na); hx, hy = unit(ha)
        n1 = (J[0] + nx * P["neck_len"], J[1] + ny * P["neck_len"])
        base = (J[0] + side * P["base_x"], P["base_y"])
        centre = line(J, n1) + bez(n1, (n1[0] + nx * P["bend"], n1[1] + ny * P["bend"]),
                                   (base[0] - hx * P["bend"], base[1] - hy * P["bend"]), base)[1:]
        if side == 1:   # the right neck runs on through the junction into body and tail
            ux, uy = -nx, -ny
            p1 = (J[0] + ux * P["body_len"], J[1] + uy * P["body_len"])
            t1, t2, t3 = P["tail"]
            tail = line(J, p1)[1:] + bez(p1, (p1[0] + ux * P["tail_h"], p1[1] + uy * P["tail_h"]), t1, t2)[1:]
            tail += bez(t2, (2 * t2[0] - t1[0], 2 * t2[1] - t1[1]), t3[0], t3[1])[1:]
            centre = tail[::-1] + centre
        path = Path(centre)
        tail_len = path.total - Path(centre[-(len(centre) - (len(tail) if side == 1 else 0)):]).total if side == 1 else 0.0
        neck_len = path.total - tail_len

        def half(s, tail_len=tail_len, neck_len=neck_len, total=path.total):
            if s >= tail_len:                       # neck: slims towards the head
                q = (s - tail_len) / neck_len
                return (W / 2) * (1 - (1 - P["neck_tip"]) * q ** 1.3)
            q = max(0.0, (tail_len - P["taper_after"] - s)) / (tail_len - P["taper_after"])
            return (W / 2) * (1 - (1 - P["tail_tip"]) * (1 - (1 - q) ** 1.5))

        dorsal = side          # which side of the travel direction the back is on (+1 = left)
        parts = [path.ribbon(half)]
        parts.append(Polygon(place(spline(HEAD), base, ha, k, mirror=(side == -1))).buffer(0))
        # dorsal spines down the back of the neck, shrinking away from the head
        s = path.total - P["spine_start"]; hgt = P["spine"]; i = 0
        while s > tail_len + neck_len * (1 - P["spine_reach"]) and hgt > 12:
            p, t, n = path.at(s); h = half(s); b = hgt * 0.62
            e = (p[0] + dorsal * n[0] * (h - 6), p[1] + dorsal * n[1] * (h - 6))
            tip = (e[0] + dorsal * n[0] * (hgt + 6) - t[0] * hgt * 0.75, e[1] + dorsal * n[1] * (hgt + 6) - t[1] * hgt * 0.75)
            parts.append(Polygon([(e[0] - t[0] * b, e[1] - t[1] * b), tip, (e[0] + t[0] * b, e[1] + t[1] * b)]))
            s -= hgt * 1.75; hgt *= P["spine_decay"]; i += 1
        if side == 1:   # spade at the tip of the tail
            p, t, n = path.at(0)
            ang = math.degrees(math.atan2(-t[0], -t[1]))
            parts.append(Polygon(place(spline(SPADE), p, ang, W / 250 * P["spade"])).buffer(0))
        g = unary_union(parts)
        r = P["soften"]
        g = g.buffer(r).buffer(-2 * r).buffer(r)          # soften corners a touch
        solid[side] = g
        # belly plates: fine cuts across the throat side of the neck
        cuts = [Polygon(place(spline(NOSTRIL), base, ha, k, mirror=(side == -1)))]
        s = path.total - P["scute_start"]
        while s > tail_len + neck_len * (1 - P["scute_reach"]):
            p, t, n = path.at(s); h = half(s); v = -dorsal
            a = (p[0] + v * n[0] * (h + 8), p[1] + v * n[1] * (h + 8))
            b = (p[0] + v * n[0] * h * (1 - P["scute_depth"]) + t[0] * 26, p[1] + v * n[1] * h * (1 - P["scute_depth"]) + t[1] * 26)
            w = P["scute_w"] / 2
            cuts.append(Polygon([(a[0] - t[0] * w, a[1] - t[1] * w), (a[0] + t[0] * w, a[1] + t[1] * w),
                                 (b[0] + t[0] * w * .3, b[1] + t[1] * w * .3), (b[0] - t[0] * w * .3, b[1] - t[1] * w * .3)]))
            s -= P["scute_gap"]
        geoms[side] = g.difference(unary_union(cuts))
        eyes[side] = Polygon(place(spline(EYE), base, ha, k, mirror=(side == -1)))
    out = [(geoms[-1].difference(solid[1]), "left"), (geoms[1], "right"), (eyes[-1], "eye_l"), (eyes[1], "eye_r")]
    return out


DEFAULTS = dict(jx=25, jy=40, neck_ang=23, head_ang=58, neck_len=380, base_x=320, base_y=660, bend=160,
                head=1.0, neck_tip=0.78, body_len=120, tail_h=190,
                tail=((-150, -300), (-255, -300), ((-345, -300), (-395, -235))),
                taper_after=40, tail_tip=0.20, spade=0.62, soften=4,
                spine=56, spine_start=60, spine_decay=0.86, spine_reach=0.46,
                scute_start=70, scute_gap=56, scute_reach=0.80, scute_depth=0.40, scute_w=8,
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
        self.shapes = [(g.simplify(0.6), role) for g, role in hydra_y(self.stem / self.u, self.P)]
        b = unary_union([g for g, _ in self.shapes]).bounds
        self.ext = b   # minx, miny, maxx, maxy in design space

    def bounds(self, ch):
        bp = BoundsPen(self.gs); self.gs[self.cmap[ord(ch)]].draw(bp); return bp.bounds

    def colors(self, fg, accent, eye_dark):
        two = self.P["two_tone"]
        return {"left": accent if two else fg, "right": fg, "eye_l": eye_dark if two else accent, "eye_r": accent}

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
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "..", "logo", "archive", "04-dragon")
    fpath = os.environ.get("HL_FONT", os.path.join(here, "..", "fonts", "sora-latin-600-normal.woff"))
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
