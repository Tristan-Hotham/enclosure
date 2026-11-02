"""r/dataisbeautiful collage for enclosure: 2400 x 3200 px, light background. Numbers from data/results.json.
Map notes sit on open sea with a halo and are checked against the land (England, Wales and the neighbouring coasts);
no leader lines."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import Patch, Rectangle
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from shapely.geometry import Polygon as SPoly, box as sbox
from shapely.ops import unary_union
from shapely.prepared import prep as _prep

R = jload(f"{DATA}/results.json")
BGc = "#F7F4EC"; SEAc = "#E6EDEF"; LANDc = "#E4DDCB"
pk, er, src, g, C, W = R["peaks"], R["eras"], R["source"], R["geo"], R["counties"], R["waves"]
W0, W1 = R["meta"]["war"]
Y = pd.DataFrame(R["years"]).set_index("y")
PTS, ACTS = places()
X, Yp = P(PTS[:, 0], PTS[:, 1])
DB = np.array([dec_bin(int(y)) for y in PTS[:, 2]])

fig = plt.figure(figsize=(12, 16.0), dpi=200, facecolor=BGc)
fig.text(.045, .985, "Fencing the commons", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(.045, .937, f"Every Act of Parliament that enclosed open fields, commons or wastes in England and Wales, as Parliament's\n"
         f"chronological tables list them: {src['n_all']:,} Acts naming {g['places']:,} places. Each dot is a place, coloured by the decade of its Act.",
         fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.45)

# ---- map
ext = (-30000, 790000, -60000, 690000)
ax = fig.add_axes([.0, .405, .70, .49])
ew(ax, land=LANDc, sea=SEAc, ext=ext, cty_lw=.45)
o = np.argsort(PTS[:, 2], kind="stable")
ax.scatter(X[o], Yp[o], s=5.5, c=[DECC[k] for k in DB[o]], lw=0, alpha=.92, zorder=4)
# land mask for label checks (England and Wales plus neighbouring land), with a margin
LAND_MARGIN = 6000
_land = [SPoly(p).buffer(0) for _, p in EW + OTHER if len(p) > 3]
LANDP = _prep(unary_union(_land).buffer(LAND_MARGIN))
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
NOTES = [
    (600000, 375000, "left", f"Norfolk and Suffolk:\n{W['w1']['eastanglia_pct']:.0f}% of Acts in 1750 to 1779,\n{W['war']['eastanglia_pct']:.0f}% in the war years"),
    (575000, 480000, "left", f"Yorkshire: {C['Yorkshire']['private']} private Acts,\nthe most of any county"),
    (560000, 600000, "left", f"Northamptonshire:\n{C['Northamptonshire']['private']} private Acts,\n{C['Northamptonshire']['per100_private']:.1f} per 100 km², the densest"),
    (-25000, 190000, "left", f"Wales: {R['wales']['all']} Acts,\n{R['wales']['war_pct']:.0f}% of the private\nones in the war years"),
    (-25000, -25000, "left", f"Cornwall: {C['Cornwall']['private']} Act.\nDevon: {C['Devon']['private']}. Kent: {C['Kent']['private']}.\nEnclosed early"),
]
fig.canvas.draw()
inv = ax.transData.inverted()
PLACED = []
for x, y, ha, t in NOTES:          # (x, y) is the preferred spot; the note moves to the nearest open sea that fits
    tt = ax.text(0, 0, t, ha=ha, va="center", fontsize=10, color=FG, path_effects=HALO, zorder=8, linespacing=1.35)
    bb = tt.get_window_extent(renderer=fig.canvas.get_renderer()).expanded(1.03, 1.08)
    (x0, y0), (x1, y1) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    w, h, dx0 = x1 - x0, y1 - y0, x0
    cands = sorted(((cx, cy) for cx in range(ext[0], ext[1], 5000) for cy in range(ext[2], ext[3], 5000)), key=lambda c: (c[0] - x) ** 2 + (c[1] - y) ** 2)
    for cx, cy in cands:
        b = sbox(cx + dx0, cy - h / 2, cx + dx0 + w, cy + h / 2)
        if ext[0] < b.bounds[0] and b.bounds[2] < ext[1] and ext[2] < b.bounds[1] and b.bounds[3] < ext[3] and not LANDP.intersects(b) and not any(b.intersects(o) for o in PLACED):
            tt.set_position((cx, cy)); PLACED.append(b); break
    else:
        raise AssertionError("no sea for " + t)
    print("NOTE", t[:12], cx, cy, round(w), round(h)) if os.environ.get("DBG") else None
    assert np.hypot(cx - x, cy - y) < 120000 or os.environ.get("DBG"), t       # stays near the place it describes
# decade legend on the paper to the right of the map
lg = fig.add_axes([.705, .43, .28, .46]); lg.axis("off"); lg.set_xlim(0, 1); lg.set_ylim(len(DECADES) - .4, -1.6)
lg.text(0, -1.1, "Decade of the Act", fontsize=12, color=FG, fontweight="medium", va="center")
cnt = np.bincount(DB, minlength=len(DECADES))
for k, (d, lab) in enumerate(DECADES):
    lg.scatter([.05], [k], s=120, c=DECC[k], lw=0)
    lg.text(.13, k, lab, fontsize=11, color=FG, va="center")
    lg.text(.62, k, f"{cnt[k]:,}", fontsize=10.5, color=MUT, va="center")
lg.text(0, len(DECADES) - .1, "places per decade", fontsize=9.5, color=MUT, va="center")

# ---- years
a2 = fig.add_axes([.075, .225, .885, .155]); a2.set_facecolor(BGc)
a2.axvspan(W0 - .5, W1 + .5, color=WARC, alpha=.10, lw=0)
a2.bar(Y.index, Y.private, color=PRIV, width=.85); a2.bar(Y.index, Y.local, bottom=Y.private, color=LOCC, width=.85)
a2.set_xlim(1700, 1850); a2.set_ylim(0, 150); spines(a2); a2.grid(axis="y", color=RULE, lw=.7); a2.set_axisbelow(True); a2.tick_params(labelsize=10)
a2.text((W0 + W1) / 2, 140, f"War with France, {W0} to {W1}", ha="center", fontsize=10.5, color=WARC, fontweight="medium")
a2.text(pk["first_wave_year"], pk["first_wave_n"] + 4, f"{pk['first_wave_year']}: {pk['first_wave_n']}", ha="center", fontsize=10, color=FG)
a2.text(pk["all_year"] + 1.5, pk["all_n"] - 4, f"{pk['all_year']}: {pk['all_n']}", ha="left", fontsize=10, color=FG)
a2.text(1702, 120, f"Enclosure Acts per year\n{er['all']['war_pct']:.0f}% came in the {er['war_years']} war years", fontsize=12, color=FG, va="top", linespacing=1.4)
a2.legend(handles=[Patch(color=PRIV, label="private Acts"), Patch(color=LOCC, label="local Acts")], loc="upper left", bbox_to_anchor=(0, .62), frameon=False, fontsize=10)

# ---- counties: choropleth and ranking
BOUNDS = [0, .5, 1, 2, 3, 4, 5, 6, 8]
CMAP = LinearSegmentedColormap.from_list("hedge", ["#F3EEDC", "#D9D3A3", "#A9B66E", "#6E9447", "#3F6B2E", "#24431E"])
NORM = BoundaryNorm(BOUNDS, CMAP.N)
a3 = fig.add_axes([.03, .035, .27, .165]); ew(a3, land=LANDc, sea=BGc, counties=False, other=False, ext=(130000, 660000, 5000, 660000))
for c, p in CTYS:
    a3.add_patch(plt.Polygon(p, closed=True, fc=CMAP(NORM(C[c]["per100_private"])), ec="#FFFFFF", lw=.35, zorder=2))
a4 = fig.add_axes([.63, .035, .33, .165]); a4.set_facecolor(BGc)
CR = R["county_rank"]; rows = CR[:7] + [None] + CR[-4:]
for i, r in enumerate(rows):
    yy = len(rows) - 1 - i
    if r is None:
        a4.text(0, yy, "...", fontsize=11, color=MUT, va="center"); continue
    a4.barh(yy, r["per100"], color=CMAP(NORM(r["per100"])), height=.72, ec="#B5AE98" if r["per100"] < 1 else "none", lw=.5)
    a4.text(r["per100"] + .1, yy, f"{r['per100']:.1f}" if r["per100"] >= 1 else f"{r['per100']:.2f}", va="center", fontsize=9.5, color=FG)
    a4.text(-.12, yy, r["name"], va="center", ha="right", fontsize=10, color=FG)
a4.set_xlim(0, 8.6); a4.set_ylim(-.6, len(rows) - .4); a4.axis("off")
fig.text(.30, .19, "Private enclosure Acts\nper 100 km², by\nhistoric county", fontsize=11.5, color=FG, va="top", linespacing=1.35)
fig.text(.30, .125, f"A Midland belt of twelve\ncounties, {R['belt']['area_pct']:.0f}% of England,\nhad {R['belt']['acts_pct']:.0f}% of its Acts", fontsize=10.2, color=MUT, va="top", linespacing=1.35)
fig.text(.045, .012, "Source: Chronological Tables of Private and of Local Acts, legislation.gov.uk (Open Government Licence v3.0); places from Wikidata (CC0).\n"
         f"{g['rate']:.0f}% of named places located; county shapes rebuilt from Wikidata. Dr Tristan Hotham, Independent researcher. maps.tristanhotham.com/enclosure",
         fontsize=8.6, color=MUT, linespacing=1.4)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "every_enclosure_act.png")
fig.savefig(out, facecolor=BGc, dpi=200)
print("collage", out)
