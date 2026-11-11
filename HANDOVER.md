# Hydralink – átadó dokumentum

Utolsó frissítés: a `claude/gallant-wright-ajybgh` ág utolsó commitja.
Ez a fájl annak szól, aki új sessionben folytatja a Hydralink logó munkáját.

## Mi a feladat

Minimalista, csak feliratból álló logó a **Hydralink** nevű AI ügynökségnek.
Az **y** betű egy **kétfejű Hydra** (nem sárkány), vízikígyó-jellegű, két nyak egy
vastag törzsből, hegyes farokkal. A felirat **Sora SemiBold**, outline-olva.
A két szín: **Hydra Green `#0F3D2E`** és **Amber `#F2A93B`**. A színeket később a
weboldalon is használni akarják, ezért van `brand/colors.css`.

A felhasználó magyarul kommunikál. Premium designerként kezeljük: visszafogott,
de kidolgozott. Nem túl animált, nem rajzfilmes, nem túlzott.

## Döntések (ezeket ne írjuk újra)

- **Kétfejű** maradt, háromfejűt elvetettük.
- A **fejek** nem tükörképek: az egyik nyelvet ölt, a másik sziszeg.
- **Szarv helyett** hátrasimuló taraj (hidra, nem sárkány).
- **Nem sárkány**: a sárkányfejes változat (`logo/archive/04-dragon`) már félretéve.
- **Rétegzett részletesség**: kis méretben a sziluett és a hasi csík dolgozik,
  nagyobb méretben jönnek a pikkelyek, fogak, arcvonalak.
- **Betűtípus**: Sora SemiBold (SIL OFL). Két alternatíva (Outfit, Space Grotesk,
  Geist) volt, de Sora maradt.
- Koncepciók **Draco** és **Nexus** (geometrikus) elvetve, archívumban.

## Aktuális állapot

### Elsődleges fájlok (`logo/`)

| Fájl | Mire |
| --- | --- |
| `hydralink-logo.svg` | világos háttérre |
| `hydralink-logo-on-dark.svg` | sötét háttérre |
| `hydralink-logo-mono.svg` / `-mono-on-dark.svg` | egyszínű változat (zöld fejek, borostyán has, szem, nyelv) |
| `hydralink-icon.svg` | ikon / favicon (csak az y, zöld kerekített négyzeten) |
| `preview.png` | előnézeti tábla (logó, sötét, közelkép, mono, ikon, paletta) |

Az SVG-k körvonalazott betűket használnak, nincs szükség font-telepítésre.

### Egyéb

- `brand/colors.css`: a paletta CSS-változókként, sötét szekcióval (`.hl-dark`).
- `README.md`: felhasználói leírás, a részletekről és a fájlokról.

### Archívum

- `logo/archive/01-illustrative/` – első ívelt nyakú sárkány, Sora
- `logo/archive/02-draco/` – geometrikus sárkány (Geist)
- `logo/archive/03-nexus/` – csomópontos y (Geist)
- `logo/archive/04-dragon/` – sárkányfejes, részletes
- `logo/archive/05-hydra-simple/` – egyszerűbb hidra, kis méretekhez
- `tools/archive/` – ezeket előállító szkriptek

## Generálás

```bash
pip install fonttools shapely
python3 tools/generate_logo.py                 # írja a logo/ mappába
HL_FONT=tools/fonts/sora-latin-600-normal.woff python3 tools/generate_logo.py /tmp/out   # tesztkimenet
```

A fő szkript: `tools/generate_logo.py`. Ebben van minden paraméter:
- `NECK_L` / `NECK_R`: a két nyak íve és a fejek dőlése
- `HEAD_TOP`, `JAW`, `EYE`, `HEAD_LINES`, `HEAD_SCALES`: a fej formája és részletei
- `DEFAULTS`: törzs, farok, pikkely, hasi lemezek, tüskék (`fin`, `fin_pitch`, `fin_lean`, ...)

Fontok: `tools/fonts/` (Sora, Outfit, Space Grotesk, Geist; mindegyikhez LICENSE).

## Ismert nyitott pontok

1. **Kis méret**: 140 px alatt a részletek eltűnnek. Ilyenkor az ikon és a
   „kisebb” változat használandó. Nincs külön kis-méret sziluett.
2. **Jobb fej**: kissé az x-magasság fölé nyúlik; a felhasználó még nem döntött.
3. **Egyszínű változat**: a nyelv és a szem a borostyánt használja, de a
   fejek és a törzs zöld; ellenőrizni kell, hogy a hasi csík tényleg olvasható-e.
4. **Tüskesor**: most rendezett, de a koponya és a nyak találkozásánál még lehet
   finomítani. A felhasználó kérte, hogy rendezett legyen, ez teljesült.
5. **Pikkelyek**: a közelképen sok apró részlet; ha a végleges logó túl zsúfolt,
   a `scale_rows` / `scale_r` csökkentésével lehet ritkítani.
6. **Végleges SVG-tisztítás**: a fájlok ~35 KB; érdemes egyszerűsíteni (`simplify`)
   és ellenőrizni, hogy nincs-e hibás path a kivágások után.
7. **Ikon**: a tervezett 1024 px-es forrásból még nincs PNG-export
   (favicon, app-ikon méretek).

## Javasolt következő lépések

1. A `preview.png` alapján a felhasználóval eldönteni: a jelenlegi részletesség
   jó-e, vagy visszább kell venni.
2. Kis méretű ellenőrzés (32, 64, 128 px) és ha kell, külön egyszerűsített ikon.
3. PNG-export (átlátszó háttér, 512/1024 px) és a favicon-készlet.
4. A `brand/colors.css` beillesztése a weboldal stílusába, és a Sora betűtípus
   bekötése.
5. Végső SVG-tisztítás, majd a `logo/` mappa lezárása.

## Git

- Ág: `claude/gallant-wright-ajybgh`
- Nincs PR; a felhasználó nem kérte.
- Commit csak kérésre, a szokásos attribúciós sorokkal.
