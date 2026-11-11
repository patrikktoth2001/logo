"""Hydralink - geometric concept directions ("Draco" and "Nexus").

The word is set in Geist SemiBold and converted to outlines; the y is a custom glyph
drawn from straight strokes and polygons in a design space where the x-height is 1000,
y points up and W is the font's stem weight, so it always matches the letters around it.

Usage:  pip install fonttools && python3 tools/archive/generate_concepts.py
"""
import math, os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen

GREEN, AMBER, PAPER = "#0F3D2E", "#F2A93B", "#F6F3EA"


def unit(deg):
    return math.sin(math.radians(deg)), math.cos(math.radians(deg))


def heading(p0, p1):
    return math.degrees(math.atan2(p1[0] - p0[0], p1[1] - p0[1]))


def place(poly, origin, deg, k=1.0):
    """Local (x forward, y to the left of forward) -> world."""
    fx, fy = unit(deg); nx, ny = -fy, fx
    return [(origin[0] + (x * fx + y * nx) * k, origin[1] + (x * fy + y * ny) * k) for x, y in poly]


def stroke(p0, p1, w):
    d = heading(p0, p1); L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    return place([(0, w / 2), (L, w / 2), (L, -w / 2), (0, -w / 2)], p0, d)


def circle(c, r, n=72):
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def sym(upper):
    """Mirror the upper half (y>0, listed base -> tip) of a head to a closed polygon."""
    return upper + [(x, -y) for x, y in reversed(upper)]


# ---------------- "Nexus" - the y as three linked nodes ----------------
def nexus_y(W, P):
    out = []
    ro, ri, rp = P["ro"] * W, P["ri"] * W, P["rp"] * W
    J = (0, P["jy"])
    cy = P["top"] - ro
    nodes = {-1: (-P["a"], cy), 1: (P["a"], cy)}
    dr = heading(J, nodes[1]); fx, fy = unit(dr)
    tail = (J[0] - fx * P["tail"], J[1] - fy * P["tail"])
    for side, c in nodes.items():
        d = heading(J, c); ux, uy = unit(d)
        end = (c[0] - ux * ro * 0.78, c[1] - uy * ro * 0.78)
        start = J if side == -1 else (tail[0] + fx * ro * 0.78, tail[1] + fy * ro * 0.78)
        out.append((stroke(start, end, W), "fg"))
    for key, c in list(nodes.items()) + [("t", tail)]:
        out.append(((circle(c, ro), circle(c, ri)), "ring"))
        if key == P.get("lit", -1):
            out.append((circle(c, rp), "accent"))
    return out


# ---------------- "Draco" - straight monoline y, faceted dragon heads in profile ----------------
def draco_head(h):
    return [(-90, h), (-10, h), (-132, h + 100), (60, h + 46), (-8, h + 158), (156, h + 58),   # two horns
            (232, h + 62), (264, h + 20),                                                    # brow
            (470, 96), (546, 62), (550, 12),                                                 # snout
            (300, -26), (512, -36), (486, -72),                                              # mouth, lower jaw
            (250, -h), (-90, -h)]


def draco_y(W, P):
    out = []; h = W / 2
    k = P["head"] * W / 250; hl = h / k
    J = (0, P["jy"])
    for side in (-1, 1):
        nx, ny = unit(side * P["neck_ang"])
        probe = [(x, y * side) for x, y in draco_head(hl)]
        top0 = max(p[1] for p in place(probe, (0, 0), side * P["head_ang"], k))
        n_len = (P["top"] - top0 - J[1]) / ny
        E = (J[0] + nx * n_len, J[1] + ny * n_len)
        role = "accent" if (P.get("two_tone") and side == -1) else "fg"
        start = J
        if side == 1:
            t = P["tail"]; c = P["tail_point"] * W
            start = (J[0] - nx * t, J[1] - ny * t)
            d = heading(start, E); L = math.hypot(E[0] - start[0], E[1] - start[1])
            out.append((place([(-c, h), (L, h), (L, -h), (0, -h)], start, d), role))
        else:
            out.append((stroke(start, E, W), role))
        out.append((circle(E, h), role))
        out.append((place(probe, E, side * P["head_ang"], k), role))
        eye = [(206, 96 * side), (306, 124 * side), (288, 76 * side)]
        out.append((place(eye, E, side * P["head_ang"], k), "eye_on_accent" if role == "accent" else "eye"))
    out.sort(key=lambda t: 0 if t[1] == "accent" else 1)
    return out


class Wordmark:
    def __init__(self, font_path, yfunc, **params):
        self.font = TTFont(font_path); self.gs = self.font.getGlyphSet(); self.cmap = self.font.getBestCmap()
        self.yfunc, self.P = yfunc, params
        self.xh = self.bounds("x")[3]
        rp = RecordingPen(); self.gs[self.cmap[ord("H")]].draw(rp)
        xs = sorted({round(p[0]) for _, args in rp.value for p in args})
        self.stem = xs[1] - xs[0]
        self.u = self.xh / 1000.0

    def bounds(self, ch):
        bp = BoundsPen(self.gs); self.gs[self.cmap[ord(ch)]].draw(bp); return bp.bounds

    def ypaths(self, x0, base, k, colors, r):
        parts = []
        for poly, role in self.yfunc(self.stem / self.u * self.P.get("weight", 1.0), self.P):
            col = colors[role]
            subs = poly if role == "ring" else (poly,)
            d = "".join("M" + "L".join(f"{x0 + px * k:.1f} {base - py * k:.1f}" for px, py in sp) + "Z" for sp in subs)
            extra = ' fill-rule="evenodd"' if role == "ring" else ""
            if r and role in ("fg", "accent"):
                extra += f' stroke="{col}" stroke-width="{r:.1f}" stroke-linejoin="round"'
            parts.append(f'<path d="{d}" fill="{col}"{extra}/>')
        return parts

    def extents(self):
        pts = []
        for poly, role in self.yfunc(self.stem / self.u * self.P.get("weight", 1.0), self.P):
            for sp in (poly if role == "ring" else (poly,)): pts += sp
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        return min(xs), max(xs), min(ys), max(ys)

    def colors(self, fg, accent, bg):
        return {"fg": fg, "accent": accent, "ring": fg, "eye": accent, "eye_on_accent": GREEN}

    def build(self, fg=GREEN, accent=AMBER, bg=PAPER, text="Hydralink", pad=None, paint_bg=False):
        u = self.u; track = self.P.get("track", 0) * self.xh
        x0d, x1d, y0d, y1d = self.extents()
        asc = max([self.bounds(c)[3] for c in text if c != "y"] or [0])
        top = max(asc, y1d * u); depth = -y0d * u
        pad = self.xh * 0.14 if pad is None else pad
        r = self.stem * self.P.get("round", 0.0)
        x = pad; base = pad + top; parts = []
        for ch in text:
            if ch == "y":
                gx = x + self.P.get("lsb", 60) * u - x0d * u
                parts += self.ypaths(gx, base, u, self.colors(fg, accent, bg), r)
                x = gx + x1d * u + self.P.get("rsb", 60) * u + track
            else:
                gn = self.cmap[ord(ch)]
                pen = SVGPathPen(self.gs, lambda v: f"{v:.1f}")
                self.gs[gn].draw(TransformPen(pen, (1, 0, 0, -1, x, base)))
                parts.append(f'<path d="{pen.getCommands()}" fill="{fg}"/>')
                x += self.gs[gn].width + track
        Wd = x - track + pad; Ht = base + depth + pad
        rect = f'<rect width="{Wd:.0f}" height="{Ht:.0f}" fill="{bg}"/>' if paint_bg else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {Wd:.0f} {Ht:.0f}" role="img" aria-label="Hydralink">'
                f'<title>Hydralink</title>{rect}\n' + "\n".join(parts) + "\n</svg>\n")

    def icon(self, bg=GREEN, fg=PAPER, accent=AMBER, size=1024, fill=0.64):
        x0, x1, y0, y1 = self.extents()
        k = size * fill / max(x1 - x0, y1 - y0)
        ox = size / 2 - (x0 + x1) / 2 * k; oy = size / 2 + (y0 + y1) / 2 * k
        parts = self.ypaths(ox, oy, k, self.colors(fg, accent, bg), self.stem / self.u * k * self.P.get("round", 0.0))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" role="img" aria-label="Hydralink">'
                f'<title>Hydralink</title><rect width="{size}" height="{size}" rx="{size * .22:.0f}" fill="{bg}"/>\n'
                + "\n".join(parts) + "\n</svg>\n")


DRACO = dict(top=1012, jy=30, neck_ang=24, head_ang=64, head=0.90, tail=420, tail_point=0.9, two_tone=True,
             round=0.05, track=-0.012, lsb=45, rsb=45)
NEXUS = dict(a=330, top=1012, jy=60, tail=430, ro=0.84, ri=0.40, rp=0.20, lit=-1, round=0.0, track=-0.012, lsb=55, rsb=55)

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "..", "logo", "archive")
    f = os.path.join(here, "..", "fonts", "geist-latin-600-normal.woff")
    draco, draco_mono = Wordmark(f, draco_y, **DRACO), Wordmark(f, draco_y, **dict(DRACO, two_tone=False))
    nexus = Wordmark(f, nexus_y, **NEXUS)
    files = {
        "02-draco/hydralink-draco.svg": draco.build(),
        "02-draco/hydralink-draco-on-dark.svg": draco.build(fg=PAPER, bg=GREEN),
        "02-draco/hydralink-draco-mono.svg": draco_mono.build(),
        "02-draco/hydralink-draco-mono-on-dark.svg": draco_mono.build(fg=PAPER, bg=GREEN),
        "02-draco/hydralink-draco-icon.svg": draco.icon(),
        "03-nexus/hydralink-nexus.svg": nexus.build(),
        "03-nexus/hydralink-nexus-on-dark.svg": nexus.build(fg=PAPER, bg=GREEN),
        "03-nexus/hydralink-nexus-lowercase.svg": nexus.build(text="hydralink"),
        "03-nexus/hydralink-nexus-icon.svg": nexus.icon(fill=0.60),
    }
    for name, data in files.items():
        path = os.path.join(out, name); os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(data)
        print("wrote", name, len(data), "bytes")
