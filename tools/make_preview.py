"""Builds the preview board as HTML; screenshot it to get preview.png.

Usage:  python3 tools/make_preview.py /tmp/preview.html
        then render it 2000 px wide at 1.5x (e.g. Playwright, full page) into preview.png
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_logo as g

here = os.path.dirname(os.path.abspath(__file__))
font = os.environ.get("HL_FONT", os.path.join(here, "fonts", "sora-latin-600-normal.woff"))
main, mono = g.Wordmark(font), g.Wordmark(font, two_tone=False)
PALETTE = [("Hydra Green", "#0F3D2E", "elsődleges", 1), ("Amber", "#F2A93B", "kiemelő", 0),
           ("Green 900", "#0A2A20", "sötét háttér", 1), ("Green 500", "#1F6B50", "linkek", 1),
           ("Green 100", "#DCE8E1", "halvány felület", 0), ("Amber 600", "#C97F14", "hover", 0),
           ("Amber 100", "#FBE8C4", "kiemelés háttér", 0), ("Paper", "#F6F3EA", "oldalháttér", 0),
           ("Ink", "#14211C", "szöveg", 1)]


def box(svg, w):
    return f'<div style="width:{w}px">{svg}</div>'


sw = "".join(f'<div class="sw" style="background:{h};color:{"#F6F3EA" if d else "#0F3D2E"}"><b>{n}</b>{h}<br>{r}</div>'
             for n, h, r, d in PALETTE)
html = f"""<!doctype html><meta charset="utf-8"><style>
body{{margin:0;padding:37px;width:1926px;background:#E9E4D8;font:15px/1.5 Inter,"Helvetica Neue",Arial,sans-serif;color:#6B6F66}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
.card{{background:#F6F3EA;border-radius:28px;padding:20px 30px 30px;position:relative;display:flex;flex-direction:column}}
.card>span{{font-weight:600;font-size:17px}} .mid{{flex:1;display:flex;align-items:center;justify-content:center;gap:40px;flex-wrap:wrap}}
.dark{{background:#0F3D2E;color:#B9C7BF}} .white{{background:#fff}}
.pal{{display:grid;grid-template-columns:repeat(9,1fr);gap:14px}} h3{{font-size:19px;margin:44px 0 22px}}
.sw{{border-radius:18px;height:160px;box-sizing:border-box;padding:70px 17px 0;font-weight:500;border:1px solid #0001}} .sw b{{display:block;font-size:17px}}
</style><div class="grid">
<div class="card" style="height:274px"><span>Elsődleges · világos háttér</span><div class="mid">{box(main.build(), 800)}</div></div>
<div class="card dark"><span>Elsődleges · sötét háttér</span><div class="mid">{box(main.build(fg=g.PAPER), 800)}</div></div>
<div class="card" style="grid-row:span 2;height:828px"><span>Az Y közelről</span><div class="mid">{box(main.build(text="y"), 760)}</div></div>
<div class="card white"><span>Egyszínű változat (borostyán has, szem és nyelv)</span><div class="mid">{box(mono.build(), 800)}</div></div>
<div class="card"><span>Ikon · kis méretek</span><div class="mid">{box(main.icon(), 186)}{box(main.icon(), 74)}{box(main.icon(), 38)}
{box(main.build(), 350)}<div style="flex-basis:100%;height:0"></div>{box(main.build(), 200)}</div></div>
</div><h3>Színpaletta</h3><div class="pal">{sw}</div>"""
with open(sys.argv[1], "w") as f:
    f.write(html)
