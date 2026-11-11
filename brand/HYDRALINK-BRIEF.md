# Hydralink – cég- és arculati összefoglaló a weboldalhoz

Ez a fájl mindent összegyűjt, amit a logómunka során a cégről és az arculatról
rögzítettünk. A weboldalt építő ágra önmagában is átvihető; a logókészítés
folyamatáról szándékosan nem szól.

## A cég

- **Név:** Hydralink (egybeírva, nagy H, a többi kisbetű)
- **Tevékenység:** AI ügynökség
- **Nyelv:** a kommunikáció magyarul folyik

Ennél több a cégről eddig nincs rögzítve – lásd a „Hiányzó információk” részt.

## Hangvétel és stílus

- Prémium, minimalista, visszafogott, de kidolgozott.
- Nem rajzfilmes, nem túlzó, nem túlanimált. A weboldalon is kevés, finom mozgás illik hozzá.
- A részletek „rétegzettek”: távolról tiszta és egyszerű, közelről gazdag.

## A névadó motívum

A logóban az **y** betű egy **kétfejű Hydra**: vízikígyó, két nyak egy vastag
törzsből, hegyes farokkal. Hidra, **nem sárkány** – nincs szarv és szárny, a fejen
hátrasimuló taraj van. A két fej nem tükörkép: az egyik nyelvet ölt, a másik sziszeg.
A weboldal illusztrációi és ikonjai ehhez igazodjanak (kígyószerű, nem sárkányos).

## Színek

A két márkaszín a **Hydra Green** és az **Amber**. Kész CSS-változók: `brand/colors.css`
(sötét szekcióhoz a `.hl-dark` osztály).

| Név | Hex | CSS-változó | Szerep |
| --- | --- | --- | --- |
| Hydra Green | `#0F3D2E` | `--hl-green` | Elsődleges: logó, címsorok, sötét szekciók háttere |
| Amber | `#F2A93B` | `--hl-amber` | Kiemelő: gombok, apró hangsúlyok |
| Green 900 | `#0A2A20` | `--hl-green-900` | Lábléc, sötét mód háttér |
| Green 500 | `#1F6B50` | `--hl-green-500` | Linkek, hover világos háttéren |
| Green 100 | `#DCE8E1` | `--hl-green-100` | Halvány zöld felület: kártyák, címkék |
| Amber 600 | `#C97F14` | `--hl-amber-600` | Borostyán gomb hover / lenyomott állapota |
| Amber 100 | `#FBE8C4` | `--hl-amber-100` | Kiemelés háttere, jelvények |
| Paper | `#F6F3EA` | `--hl-paper` | Meleg törtfehér oldalháttér |
| White | `#FFFFFF` | `--hl-white` | Kártyák a Paper háttéren |
| Ink | `#14211C` | `--hl-ink` | Folyószöveg világos háttéren |

Szabályok:

- A zöld viszi a szöveget és a felületeket, a borostyán a „szikra”.
- A borostyán **kitöltő szín**: világos háttéren szövegnek vagy vékony vonalnak ne
  használd (kontraszt 1,8:1). Sötétzöldön bármire jó (6,1:1).
- Elsődleges gomb: borostyán háttér, sötétzöld szöveg; hover: Amber 600.

## Betűtípus

- **Sora** (SIL Open Font License, szabadon használható a weben is).
- A logó **Sora SemiBold (600)**; címsorokhoz ugyanez ajánlott.
- Folyószöveg-betűtípus még nincs kiválasztva.
- A fontfájl a repóban: `tools/fonts/sora-latin-600-normal.woff` (csak 600-as súly, latin készlet).

## Logófájlok

Az SVG-kben a betűk körvonalak, nem kell hozzájuk font. Mindegyik háttere átlátszó.

| Fájl | Mire |
| --- | --- |
| `logo/hydralink-logo.svg` | Fejléc világos háttéren |
| `logo/hydralink-logo-on-dark.svg` | Sötét háttéren (pl. lábléc, sötét szekció) |
| `logo/hydralink-logo-mono.svg`, `logo/hydralink-logo-mono-on-dark.svg` | Egyszínű változat |
| `logo/hydralink-icon.svg` | Favicon, profilkép, app-ikon (csak az y, zöld kerekített négyzeten) |

Használat:

- Körülbelül 140 px szélesség alatt a rajz részletei eltűnnek; nagyon kis helyre az ikont használd.
- PNG-export és favicon-készlet (16/32/180/512 px) még nincs, az ikon SVG-ből kell előállítani.

## Hiányzó információk

Ezeket a weboldalhoz még meg kell adni, a logómunka során nem kerültek szóba:

- szolgáltatások, célcsoport, referenciák
- szlogen, bemutatkozó szöveg
- elérhetőségek, domain, közösségi profilok
- cégadatok (jogi név, székhely, adószám) az impresszumhoz
- az oldal nyelve(i) és szerkezete
