"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json."""
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import Patch, Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from figstyle import *

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
Y = pd.DataFrame(R["years"]).set_index("y")
PTS, ACTS = places()
X, Yp = P(PTS[:, 0], PTS[:, 1])
DB = np.array([dec_bin(int(y)) for y in PTS[:, 2]])
HALO = [pe.withStroke(linewidth=3.5, foreground=BG)]
HALOS = [pe.withStroke(linewidth=3.5, foreground=SEA)]
pk, er, src, g = R["peaks"], R["eras"], R["source"], R["geo"]
W0, W1 = R["meta"]["war"]


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def dots(ax, idx=None, s=6, alpha=.9, col=None, z=4):
    idx = np.arange(len(PTS)) if idx is None else idx
    o = idx[np.argsort(PTS[idx, 2], kind="stable")]
    c = [DECC[k] for k in DB[o]] if col is None else col
    ax.scatter(X[o], Yp[o], s=s, c=c, lw=0, alpha=alpha, zorder=z)


# ---------- the map, coloured by decade ----------
fig = plt.figure(figsize=(12, 10.2), facecolor=BG)
ax = fig.add_axes([.0, .0, .64, .965]); ew(ax, other=True)
dots(ax, s=7)
fig.text(.02, .975, f"{g['matched']:,} places named in {g['acts_located']:,} enclosure Acts, England and Wales, coloured by the decade of the Act", fontsize=11, color=FG, va="top")
lx = .67
fig.text(lx, .9, "Decade of the Act", fontsize=11.5, color=FG, fontweight="medium")
cnt = np.bincount(DB, minlength=len(DECADES))
lg = fig.add_axes([lx, .27, .3, .6]); lg.set_xlim(0, 1); lg.set_ylim(len(DECADES) - .5, -.5); lg.axis("off")
for k, (d, lab) in enumerate(DECADES):
    lg.scatter([.04], [k], s=150, c=DECC[k], lw=0)
    lg.text(.12, k, lab, fontsize=10.5, color=FG, va="center")
    lg.text(.6, k, f"{cnt[k]:,} places", fontsize=10, color=MUT, va="center")
fig.text(lx, .24, f"One dot per place, so an Act naming\nthree townships has three dots.\n{g['rate']:.0f}% of named places were found in the\nWikidata gazetteer; the rest are listed\nin the data files.\n\nSource: Chronological Tables of Private\nand of Local Acts, legislation.gov.uk\n(Open Government Licence v3.0);\nWikidata (CC0).", fontsize=9.5, color=MUT, va="top", linespacing=1.4)
both(fig, "map")

# ---------- acts per year ----------
def years_chart(ax, lab=True, small=False):
    ys = Y.index.values
    ax.axvspan(W0 - .5, W1 + .5, color=WARC, alpha=.09, lw=0, zorder=0)
    ax.bar(ys, Y.private, color=PRIV, width=.85, zorder=2, label="private Acts")
    ax.bar(ys, Y.local, bottom=Y.private, color=LOCC, width=.85, zorder=2, label="local Acts")
    ax.set_xlim(1700, 1850); ax.set_ylim(0, 150); spines(ax)
    if lab:
        ax.text((W0 + W1) / 2, 142, f"War with France, {W0} to {W1}", ha="center", fontsize=10 if not small else 8.5, color=WARC, fontweight="medium")
        ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True)


fig = plt.figure(figsize=(12, 5.6), facecolor=BG); ax = fig.add_axes([.065, .1, .92, .74]); ax.set_facecolor(BG)
years_chart(ax)
for y, v, t, ha, dy in ((pk["first_wave_year"], int(Y.loc[pk["first_wave_year"]].n), f"{pk['first_wave_year']}: {pk['first_wave_n']}, first wave peak", "center", 3),
                        (pk["private_year"], int(Y.loc[pk["private_year"]].n), f"{pk['private_year']}: {pk['private_n']} private (+{int(Y.loc[pk['private_year']].local)} local)", "right", -4),
                        (pk["all_year"], pk["all_n"], f"{pk['all_year']}: {pk['all_n']} in all", "left", 1)):
    ax.text(y + (-1.2 if ha == "right" else 1.2 if ha == "left" else 0), v + dy, t, ha=ha, va="bottom", fontsize=10, color=FG, path_effects=HALO, zorder=5)
for y in (1802, 1803):
    ax.text(y, int(Y.loc[y].n) + 1.5, "*", ha="center", va="bottom", fontsize=12, color=FG, zorder=5)
fig.text(.985, .015, "* local Acts for 1802 and 1803 were not collected (two table pages missing)", ha="right", fontsize=9, color=MUT)
ax.set_ylabel("enclosure Acts per year")
fig.legend(handles=[Patch(color=PRIV, label="private Acts"), Patch(color=LOCC, label="local Acts (from 1799)"), Patch(color=WARC, alpha=.2, label="French wars")],
           loc="upper left", bbox_to_anchor=(.06, .99), ncol=3, frameon=False, fontsize=10.5)
both(fig, "years")

# ---------- counties: choropleth and ranking ----------
CR = R["county_rank"]; CC = R["counties"]
BOUNDS = [0, .5, 1, 2, 3, 4, 5, 6, 8]
CMAP = LinearSegmentedColormap.from_list("hedge", ["#F3EEDC", "#D9D3A3", "#A9B66E", "#6E9447", "#3F6B2E", "#24431E"])
NORM = BoundaryNorm(BOUNDS, CMAP.N)
fig = plt.figure(figsize=(12, 9.4), facecolor=BG)
ax = fig.add_axes([0, 0, .56, .95]); ew(ax, counties=False)
for c, p in CTYS:
    ax.add_patch(plt.Polygon(p, closed=True, fc=CMAP(NORM(CC[c]["per100_private"])), ec="#FFFFFF", lw=.5, zorder=2))
fig.text(.02, .975, "Private enclosure Acts per 100 km², by historic county", fontsize=11.5, color=FG, va="top")
cax = fig.add_axes([.31, .055, .22, .018])
for k in range(len(BOUNDS) - 1):
    cax.add_patch(Rectangle((k, 0), 1, 1, fc=CMAP(NORM((BOUNDS[k] + BOUNDS[k + 1]) / 2)), ec="none"))
cax.set_xlim(0, len(BOUNDS) - 1); cax.set_ylim(0, 1); cax.set_yticks([]); cax.set_xticks(range(len(BOUNDS))); cax.set_xticklabels([str(b) for b in BOUNDS], fontsize=8.5)
for s in cax.spines.values(): s.set_visible(False)
cax.tick_params(length=0)
a2 = fig.add_axes([.73, .07, .25, .86]); a2.set_facecolor(BG)
rows = CR[:14] + [None] + CR[-8:]
yl = list(range(len(rows)))[::-1]
for yy, r in zip(yl, rows):
    if r is None:
        a2.text(0, yy, "...", fontsize=11, color=MUT, va="center"); continue
    a2.barh(yy, r["per100"], color=CMAP(NORM(r["per100"])), height=.72, ec="#B5AE98" if r["per100"] < 1 else "none", lw=.5)
    a2.text(r["per100"] + .12, yy, (f"{r['per100']:.1f}" if r["per100"] >= 1 else f"{r['per100']:.2f}") + f"  ({r['n']})", va="center", fontsize=9, color=FG)
    a2.text(-.15, yy, r["name"], va="center", ha="right", fontsize=9.5, color=FG)
a2.set_xlim(0, 9.8); a2.set_ylim(-.7, len(rows) - .3); a2.set_yticks([]); a2.set_xticks([]); [a2.spines[s].set_visible(False) for s in a2.spines]
a2.set_title("Acts per 100 km² (Acts)", loc="left", fontsize=10.5, color=FG, x=-.6)
both(fig, "counties")

# ---------- two waves, side by side ----------
sw = R["waves"]
fig = plt.figure(figsize=(12, 6.9), facecolor=BG)
for k, ((a0, a1), title, col) in enumerate((((1750, 1779), "First wave, 1750 to 1779", "#B86E22"), ((W0, W1), f"War years, {W0} to {W1}", "#2C7FA6"))):
    ax = fig.add_axes([.005 + k * .335, .005, .33, .885]); ew(ax, cty_lw=.35)
    sel = np.where((PTS[:, 2] >= a0) & (PTS[:, 2] <= a1))[0]
    ax.scatter(X[sel], Yp[sel], s=5, c=col, lw=0, alpha=.85, zorder=4)
    acts_n = sw["w1" if k == 0 else "war"]["n"]
    fig.text(.015 + k * .335, .965, title, fontsize=12.5, color=FG, va="top", fontweight="medium")
    fig.text(.015 + k * .335, .935, f"{acts_n:,} Acts, {len(sel):,} places located", fontsize=9.5, color=MUT, va="top")
a3 = fig.add_axes([.8, .13, .18, .72]); a3.set_facecolor(BG)
REGN = [("belt", "Midland belt"), ("north", "The north"), ("southwest", "South-west and\nWelsh border"), ("eastanglia", "Norfolk and\nSuffolk"), ("southeast", "Home counties\nand Kent"), ("wales", "Wales")]
for i, (k, lab) in enumerate(REGN):
    yy = len(REGN) - 1 - i
    a, b = sw["w1"][k + "_pct"], sw["war"][k + "_pct"]
    a3.barh(yy + .18, a, height=.34, color="#B86E22"); a3.barh(yy - .18, b, height=.34, color="#2C7FA6")
    a3.text(a + 1, yy + .18, f"{a:.0f}%", va="center", fontsize=9, color=FG); a3.text(b + 1, yy - .18, f"{b:.0f}%", va="center", fontsize=9, color=FG)
    a3.text(-2, yy, lab, ha="right", va="center", fontsize=9.5, color=FG)
a3.set_xlim(0, 66); a3.set_ylim(-.7, len(REGN) - .3); a3.set_yticks([]); a3.set_xticks([]); [a3.spines[s].set_visible(False) for s in a3.spines]
fig.text(.69, .93, "Share of each wave's Acts, by region", fontsize=10.5, color=FG)
a3.legend(handles=[Patch(color="#B86E22", label="1750 to 1779"), Patch(color="#2C7FA6", label=f"{W0} to {W1}")], loc="upper right", bbox_to_anchor=(1.0, -.02), ncol=2, frameon=False, fontsize=9)
both(fig, "waves")

# ---------- the centre of enclosure, decade by decade ----------
CEN = R["centroid"]
fig = plt.figure(figsize=(12, 7.2), facecolor=BG)
ax = fig.add_axes([0, 0, .62, .93])
ext = (395000, 535000, 235000, 375000)
ew(ax, ext=ext, cty_ec="#FFFFFF", cty_lw=1.2)
sel = np.where((X > ext[0]) & (X < ext[1]) & (Yp > ext[2]) & (Yp < ext[3]))[0]
ax.scatter(X[sel], Yp[sel], s=9, c=[DECC[k] for k in DB[sel]], lw=0, alpha=.32, zorder=3)
cx = np.array([c["x"] for c in CEN]); cy = np.array([c["y"] for c in CEN])
ax.plot(cx[1:], cy[1:], color=FG, lw=1.6, zorder=6)
for i, c in enumerate(CEN):
    k = dec_bin(c["d0"]) if c["d0"] >= 1720 else 0
    ax.scatter([c["x"]], [c["y"]], s=90, c=DECC[min(k, len(DECC) - 1)], ec=FG, lw=1.2, zorder=7)
OFF = {"before 1750": (6000, -3500, "left"), "1750s": (-6000, 4500, "right"), "1760s": (6000, 3500, "left"), "1770s": (6000, 1500, "left"),
       "1780s": (-6000, 0, "right"), "1790s": (-6000, 2500, "right"), "1800s": (6000, 1000, "left"), "1810s": (-6000, -3500, "right"),
       "1820s": (6000, -4000, "left"), "1830s and 1840s": (6000, -2500, "left")}
for c in CEN:
    dx, dy, ha = OFF[c["label"]]
    ax.text(c["x"] + dx, c["y"] + dy, c["label"], ha=ha, va="center", fontsize=10, color=FG, path_effects=[pe.withStroke(linewidth=4, foreground=LAND)], zorder=8)
TOWNS = {"Nottingham": (-1.1505, 52.9536), "Leicester": (-1.1332, 52.6369), "Northampton": (-0.8901, 52.2405), "Coventry": (-1.5197, 52.4068), "Derby": (-1.4746, 52.9225)}
TOFF = {"Nottingham": (-3500, -2500, "right", "top"), "Leicester": (4000, -3000, "left", "top"), "Northampton": (0, -3800, "center", "top"), "Coventry": (0, -3800, "center", "top"), "Derby": (0, -3800, "center", "top")}
for t, (lo, la) in TOWNS.items():
    x, y = P(lo, la); ax.scatter([x], [y], s=16, marker="s", c="#FFFFFF", ec=MUT, lw=.9, zorder=5)
    ox, oy, ha_, va_ = TOFF[t]
    ax.text(x + ox, y + oy, t, ha=ha_, va=va_, fontsize=9, color=MUT, path_effects=[pe.withStroke(linewidth=3, foreground=LAND)], zorder=5, style="italic")
fig.text(.02, .975, "The centre of enclosure: the average position of each decade's Acts", fontsize=11.5, color=FG, va="top")
cm = R["centroid_move"]
fig.text(.65, .85, "Centre of gravity", fontsize=12, color=FG, fontweight="medium", va="top")
fig.text(.65, .8, f"Each circle is the mean position of the\nActs of one decade (all places located).\nPale dots: the places themselves.\n\nFrom the 1760s to the 1810s the centre\nmoved about {cm['km']} km, from near\nNottingham to the country west of\nLeicester: the second wave reached\nsouth and west, while the first had\nleaned north into Yorkshire.\n\nIt never left the East Midlands.", fontsize=9.8, color=FG, va="top", linespacing=1.45)
both(fig, "centroid")

# ---------- enclosed again and again ----------
TT = R["twice_top"][:5] + R["twice_gap"][:3]
seen = set(); TT = [t for t in TT if not (t["place"] in seen or seen.add(t["place"]))]
fig = plt.figure(figsize=(12, 5.4), facecolor=BG); ax = fig.add_axes([.27, .14, .7, .72]); ax.set_facecolor(BG)
ax.axvspan(W0 - .5, W1 + .5, color=WARC, alpha=.09, lw=0)
for i, t in enumerate(TT):
    yy = len(TT) - 1 - i
    ax.plot([min(t["years"]), max(t["years"])], [yy, yy], color=RULE, lw=2, zorder=1)
    ax.scatter(t["years"], [yy] * len(t["years"]), s=70, c=[DECC[dec_bin(y)] for y in t["years"]], ec=FG, lw=.8, zorder=3)
    ax.text(1712, yy, f"{t['place']}, {SHORT.get(t['county'], t['county'])}", ha="right", va="center", fontsize=10, color=FG)
ax.set_xlim(1715, 1850); ax.set_ylim(-.7, len(TT) - .3); ax.set_yticks([]); spines(ax); ax.spines["left"].set_visible(False)
ax.text((W0 + W1) / 2, len(TT) - .45, "French wars", ha="center", fontsize=9, color=WARC)
fig.text(.02, .95, f"Enclosed again: {R['twice']['n']} places are named in enclosure Acts of two or more different years.\nThe most repeated, and the longest gaps. Each dot is an Act, coloured by decade.", fontsize=11, color=FG, va="top", linespacing=1.5)
both(fig, "twice")

# ---------- eras (paper only) ----------
fig = plt.figure(figsize=(11, 2.8), facecolor=BG); ax = fig.add_axes([.14, .28, .83, .6]); ax.set_facecolor(BG)
EC = [("before", f"to {W0 - 1}", "#B86E22"), ("war", f"{W0} to {W1}", WARC), ("after", f"from {W1 + 1}", "#5A4B9E")]
for i, s in enumerate(("private", "local", "all")):
    left = 0
    for k, lab, c in EC:
        v = er[s][k + "_pct"]; ax.barh(2 - i, v, left=left, color=c, height=.6)
        if v > 5: ax.text(left + v / 2, 2 - i, f"{v:.0f}%", ha="center", va="center", color="#fff", fontsize=10)
        left += v
    ax.text(-1, 2 - i, {"private": "private Acts", "local": "local Acts", "all": "all"}[s] + f" ({er[s]['n']:,})", ha="right", va="center", fontsize=10)
ax.set_xlim(0, 100); ax.set_yticks([]); ax.set_xticks([]); [ax.spines[s].set_visible(False) for s in ax.spines]
fig.legend(handles=[Patch(color=c, label=lab) for k, lab, c in EC], loc="lower center", ncol=3, frameon=False, fontsize=9.5, bbox_to_anchor=(.55, 0))
both(fig, "eras", blog=False)

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.56, .0, .44, 1.0]); ew(ax, other=False, cty_lw=.3, sea=BG, ext=(130000, 660000, 5000, 660000))
dots(ax, s=3.2, alpha=.9)
fig.text(.045, .87, "Fencing", fontproperties=DISP, fontsize=62, color=GREEN, va="top")
fig.text(.045, .69, "the commons", fontproperties=DISP, fontsize=62, color=FG, va="top")
fig.text(.045, .48, f"Every enclosure Act in the Chronological Tables:\n{src['n_private']:,} private Acts and {src['n_local']:,} local Acts that fenced\nthe open fields, commons and wastes of England\nand Wales, mapped place by place.", fontproperties=SERP, fontsize=14.5, color=FG, va="top", linespacing=1.4)
a2 = fig.add_axes([.045, .1, .45, .14]); a2.set_facecolor(BG); years_chart(a2, lab=False); a2.set_yticks([]); a2.spines["left"].set_visible(False); a2.tick_params(labelsize=8)
fig.text(.045, .035, "maps.tristanhotham.com/enclosure", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
