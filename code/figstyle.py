"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, and England and Wales in the British National Grid."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#6B655B", "axes.labelcolor": "#26221D",
                     "xtick.color": "#6B655B", "ytick.color": "#6B655B"})
# Hedgerow: pale paper, field green, harvest gold, a deep hawthorn red for the war years
BG, FG, MUT, LAND, RULE, SEA = "#F6F3EA", "#26221D", "#6B655B", "#E6E0D0", "#DDD6C4", "#E8EEEF"
HOT, COOL, GREEN, GOLD, INK = "#A4372A", "#2C6E8F", "#4F7A3A", "#C99A2E", "#2E2A24"
PRIV, LOCC = "#4F7A3A", "#C99A2E"          # private Acts, local Acts
WARC = "#A4372A"
DECC = DEC_COL
BNG = Transformer.from_crs(4326, 27700, always_xy=True)


def P(lon, lat):
    return BNG.transform(np.asarray(lon), np.asarray(lat))


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


def shapes(path, key=None):
    out = []
    for f in jload(path)["features"]:
        for ring in rings(f["geometry"]):
            x, y = P(ring[:, 0], ring[:, 1])
            out.append(((f["properties"].get(key) if key else None), np.column_stack([x, y])))
    return out


EW = shapes(f"{DATA}/england_wales.geojson")
CTYS = shapes(f"{DATA}/historic_counties.geojson", "county")
OTHER = shapes(f"{WORK}/other_land.geojson")
EXT = (120000, 670000, 0, 680000)   # x0, x1, y0, y1 in BNG metres (Land's End to Berwick)


def ew(ax, land=LAND, ec="#FFFFFF", lw=.4, counties=True, cty_ec="#FFFFFF", cty_lw=.5, other=True, ext=EXT, z=1, sea=SEA):
    ax.set_facecolor(sea)
    if other:
        for _, p in OTHER:
            ax.add_patch(MPoly(p, closed=True, fc="#F1F0EC", ec="none", lw=0, zorder=z - .5))
    for _, p in EW:
        ax.add_patch(MPoly(p, closed=True, fc=land, ec="none", lw=0, zorder=z))
    if counties:
        for _, p in CTYS:
            ax.add_patch(MPoly(p, closed=True, fc="none", ec=cty_ec, lw=cty_lw, zorder=z + .2))
    for _, p in EW:
        ax.add_patch(MPoly(p, closed=True, fc="none", ec=ec if ec else land, lw=lw, zorder=z + .3))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def places():
    """Located places: array of lon, lat, year, act index; plus act table."""
    J = jload(f"{DATA}/places.json")
    pts = np.array([[p[0], p[1], p[2], p[3]] for p in J["points"]], float)
    return pts, J["acts"]
