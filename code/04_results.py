"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv) and the page data
(data/site.json, data/places.json).

Definitions:
  * enclosing act: a title classed "enclosure" or "agreement" in 01_parse.py (amendments, Inclosure Commissioners'
    order confirmations and passing mentions are kept apart). Acts for Irish counties are left out.
  * private Acts: from the Chronological Table of Private and Personal Acts; local Acts: from the Chronological Table of
    Local Acts. Every count is given for each source; "all" is their sum. The headline figures are the private Acts.
  * year: the first calendar year of the parliamentary session;
  * the French wars: 1793 to 1815 inclusive; before = to 1792; after = from 1816;
  * county of an act: the first county in its title; for an act without one, the county of its first located place;
  * located act: at least one of its places was geocoded; an act's position is the mean of its located places;
  * centroid by decade: the mean position (British National Grid) of located acts, each act counted once;
  * a place enclosed twice: one gazetteer place named in two or more enclosing acts of different years."""
import numpy as np, pandas as pd
from pyproj import Transformer
from common import *

A0 = pd.read_pickle(f"{WORK}/acts.pkl")
P0 = pd.read_pickle(f"{WORK}/places.pkl")
E = pd.read_pickle(f"{WORK}/gaz_keyed.pkl")
CP, CG = jload(f"{WORK}/checks_parse.json"), jload(f"{WORK}/checks_geo.json")
CTY = {f["properties"]["county"]: f["properties"] for f in jload(f"{DATA}/historic_counties.geojson")["features"]}
TO_LL = Transformer.from_crs(27700, 4326, always_xy=True)
pc = lambda a, b: round(100 * a / b, 2) if b else None
R = {}

A = A0[A0.kind.isin(["enclosure", "agreement"]) & ~A0.nation.isin(["Ireland", "Scotland"])].copy()
A["session"] = A.session.str.strip().str.rstrip(".").str.strip()
P = P0[P0.act.isin(A.id)].copy()
loc = P[P.gi.notna()]
pos = loc.groupby("act").agg(x=("g_x", "mean"), y=("g_y", "mean"), n_loc=("gi", "size"), cty1=("g_hc", "first"))
A = A.join(pos, on="id")
A["located"] = A.x.notna()
A["cty"] = A.county.where(A.county.isin(COUNTIES), A.cty1)
A["era"] = np.where(A.year < WAR[0], "before", np.where(A.year <= WAR[1], "war", "after"))
A["dec"] = A.year // 10 * 10
lon, lat = TO_LL.transform(A.x.fillna(0).values, A.y.fillna(0).values)
A["lon"], A["lat"] = np.where(A.located, lon, np.nan), np.where(A.located, lat, np.nan)
SRC = ("private", "local")
S = {s: A[A.source == s] for s in SRC}
S["all"] = A

# ---------- source ----------
R["source"] = {"private_rows": CP["private"]["rows"], "private_pages": CP["private"]["pages"], "private_titles": CP["private_acts_all"],
               "private_mention_rows": CP["private_rows_mentioning"], "local_pages": CP["local"]["pages"], "local_pages_total": 187,
               "local_rows": CP["local_acts_listed"], "local_missing": "1802 to 1803 and 1841",
               "kinds_private": CP["kinds_private"], "kinds_local": CP["kinds_local"], "ireland": CP["ireland_private"],
               "n_private": len(S["private"]), "n_local": len(S["local"]), "n_all": len(A),
               "n_private_mentions": int((A0.source == "private").sum()), "n_local_mentions": int((A0.source == "local").sum()),
               "amend_private": int(((A0.source == "private") & (A0.kind == "amendment")).sum()),
               "agree_private": int(((A0.source == "private") & (A0.kind == "agreement")).sum()),
               "orders_local": int(((A0.source == "local") & (A0.kind == "order")).sum()),
               "other_private": int(((A0.source == "private") & (A0.kind == "other")).sum()),
               "allotment_only": CP["allotment_only_private"],
               "first_year": int(A.year.min()), "last_year": int(A.year.max())}
src = R["source"]
assert src["n_private"] + src["n_local"] == src["n_all"]
assert 3500 < src["n_private"] < 3800 and 3600 < src["private_mention_rows"] < 3800
assert src["local_pages"] == 185

# ---------- geocoding ----------
for s in SRC:
    p = P[P.act.isin(S[s].id)]
    R.setdefault("geo", {})[s] = {"places": len(p), "matched": int(p.gi.notna().sum()), "rate": pc(p.gi.notna().sum(), len(p)),
                                  "acts_located": int(S[s].located.sum()), "acts_rate": pc(S[s].located.sum(), len(S[s]))}
g = R["geo"]
g["places"] = len(P); g["matched"] = int(P.gi.notna().sum()); g["rate"] = pc(g["matched"], g["places"])
g["acts_located"] = int(A.located.sum()); g["acts_rate"] = pc(g["acts_located"], len(A))
g["how"] = P.how.value_counts().to_dict()
g["unique_places"] = int(P.gi.nunique())
g["gaz_ew"] = CG["gaz_ew"]; g["gaz_items"] = CG["gaz_items"]
g["wales_rate"] = pc(P[P.act.isin(A[A.cty.isin(WALES)].id)].gi.notna().sum(), len(P[P.act.isin(A[A.cty.isin(WALES)].id)]))
g["england_rate"] = pc(P[P.act.isin(A[A.cty.isin(ENGLAND)].id)].gi.notna().sum(), len(P[P.act.isin(A[A.cty.isin(ENGLAND)].id)]))
assert g["rate"] > 75

# ---------- years ----------
YRS = list(range(1700, 1850))
yr = []
for y in YRS:
    row = {"y": y}
    for s in SRC:
        row[s] = int((S[s].year == y).sum())
    row["n"] = row["private"] + row["local"]
    yr.append(row)
R["years"] = yr
Y = pd.DataFrame(yr).set_index("y")
R["early"] = {"before1700": int((A.year < 1700).sum()), "after1849": int((A.year > 1849).sum())}
assert int(Y.n.sum()) + R["early"]["before1700"] + R["early"]["after1849"] == len(A)
pk = {}
for s in ("private", "n"):
    nm = "all" if s == "n" else s
    pk[nm + "_year"] = int(Y[s].idxmax()); pk[nm + "_n"] = int(Y[s].max())
w1 = Y.loc[1750:1792]; w2 = Y.loc[1793:1815]
pk["first_wave_year"] = int(w1.private.idxmax()); pk["first_wave_n"] = int(w1.private.max())
pk["war_year"] = int(w2.n.idxmax()); pk["war_n"] = int(w2.n.max())
pk["war_private_year"] = int(w2.private.idxmax()); pk["war_private_n"] = int(w2.private.max())
pk["trough_year"] = int(Y.loc[1780:1792].private.idxmin()); pk["trough_n"] = int(Y.loc[1780:1792].private.min())
pk["y1760s"] = int(Y.loc[1760:1769].private.sum()); pk["y1770s"] = int(Y.loc[1770:1779].private.sum())
pk["y1750s"] = int(Y.loc[1750:1759].private.sum()); pk["y1780s"] = int(Y.loc[1780:1789].private.sum())
pk["y1760_79"] = pk["y1760s"] + pk["y1770s"]
pk["y1800s_all"] = int(Y.loc[1800:1809].n.sum()); pk["y1810s_all"] = int(Y.loc[1810:1819].n.sum())
pk["y1800s_private"] = int(Y.loc[1800:1809].private.sum()); pk["y1810s_private"] = int(Y.loc[1810:1819].private.sum())
pk["y1793_1815_all"] = int(w2.n.sum()); pk["y1793_1815_private"] = int(w2.private.sum()); pk["y1793_1815_local"] = int(w2.local.sum())
pk["y1793_1815_per_year"] = round(w2.n.sum() / len(w2), 1)
pk["y1760_79_per_year"] = round(pk["y1760_79"] / 20, 1)
pk["years_over_100"] = [int(y) for y in Y.index[Y.n >= 100]]
pk["years_over_100_private"] = [int(y) for y in Y.index[Y.private >= 100]]
pk["y1801"] = int(Y.loc[1801].n); pk["y1811"] = int(Y.loc[1811].n); pk["y1813"] = int(Y.loc[1813].n)
pk["y1816"] = int(Y.loc[1816].n); pk["y1815"] = int(Y.loc[1815].n); pk["y1814"] = int(Y.loc[1814].n)
dec = A.groupby("dec").size(); pk["dec_all"] = int(dec.idxmax()); pk["dec_all_n"] = int(dec.max())
decp = S["private"].groupby("dec").size(); pk["dec_private"] = int(decp.idxmax()); pk["dec_private_n"] = int(decp.max())
loc_y = S["local"].year
pk["local_1798_1815"] = int(((loc_y >= 1798) & (loc_y <= 1815)).sum()); pk["local_first"] = int(loc_y.min())
pk["local_after1815"] = int((loc_y > 1815).sum())
pk["local_share_1798_1815"] = pc(pk["local_1798_1815"], int(((A.year >= 1798) & (A.year <= 1815)).sum()))
pk["local_share_1811_14"] = pc(int(Y.loc[1811:1814].local.sum()), int(Y.loc[1811:1814].n.sum()))
R["peaks"] = pk

# eras
er = {}
for s in ("private", "local", "all"):
    d = S[s]; n = len(d)
    er[s] = {"before": int((d.era == "before").sum()), "war": int((d.era == "war").sum()), "after": int((d.era == "after").sum()), "n": n}
    for k in ("before", "war", "after"):
        er[s][k + "_pct"] = pc(er[s][k], n)
er["war_years"] = WAR[1] - WAR[0] + 1
er["war_share_of_years"] = pc(er["war_years"], src["last_year"] - src["first_year"] + 1)
R["eras"] = er

# ---------- counties ----------
ct = []
for c in COUNTIES:
    rowc = {"county": c, "name": SHORT.get(c, c), "nation": NATION[c], "area_km2": CTY[c]["area_km2"]}
    for s in SRC:
        d = S[s][S[s].cty == c]
        rowc[s] = len(d)
    rowc["all"] = rowc["private"] + rowc["local"]
    d = A[A.cty == c]
    rowc["per100_private"] = round(100 * rowc["private"] / rowc["area_km2"], 3)
    rowc["per100_all"] = round(100 * rowc["all"] / rowc["area_km2"], 3)
    rowc["first"] = int(d.year.min()) if len(d) else None
    rowc["last"] = int(d.year.max()) if len(d) else None
    rowc["median_year"] = int(d.year.median()) if len(d) else None
    rowc["peak_dec"] = int(d.groupby("dec").size().idxmax()) if len(d) else None
    rowc["before_pct"] = pc((d.era == "before").sum(), len(d)); rowc["war_pct"] = pc((d.era == "war").sum(), len(d))
    rowc["places"] = int(P[P.act.isin(d.id)].shape[0])
    ct.append(rowc)
CT = pd.DataFrame(ct).sort_values("per100_private", ascending=False).reset_index(drop=True)
CT["rank"] = CT.index + 1
R["counties"] = {r["county"]: r for r in CT.to_dict("records")}
R["county_rank"] = [{"county": r.county, "name": r.name, "per100": r.per100_private, "n": int(r.private), "all": int(r.all)} for r in CT.itertuples()]
cr = {r["county"]: r for r in R["counties"].values()}
MID = ["Northamptonshire", "Leicestershire", "Oxfordshire", "Cambridgeshire", "Huntingdonshire", "Bedfordshire", "Buckinghamshire", "Warwickshire", "Rutland", "Nottinghamshire", "Lincolnshire", "Berkshire"]
LIGHT = ["Kent", "Devon", "Cornwall"]
mid = CT[CT.county.isin(MID)]; mid_area = mid.area_km2.sum()
eng = CT[CT.nation == "England"]
R["belt"] = {"counties": MID, "n": int(mid.private.sum()), "area": round(mid_area), "per100": round(100 * mid.private.sum() / mid_area, 2),
             "area_pct": pc(mid_area, eng.area_km2.sum()), "acts_pct": pc(mid.private.sum(), eng.private.sum()),
             "eng_per100": round(100 * eng.private.sum() / eng.area_km2.sum(), 2), "eng_n": int(eng.private.sum()), "eng_area": round(eng.area_km2.sum())}
top = CT.head(8)
R["top8"] = [r.county for r in top.itertuples()]
R["light"] = {c: {"n": cr[c]["private"], "all": cr[c]["all"], "per100": cr[c]["per100_private"], "rank": int(CT.index[CT.county == c][0]) + 1} for c in LIGHT + ["Middlesex", "Essex", "Sussex", "Surrey", "Herefordshire", "Shropshire", "Lancashire"]}
R["n_counties"] = len(COUNTIES); R["n_eng"] = len(ENGLAND); R["n_wales"] = len(WALES)
R["wales"] = {"private": int(CT[CT.nation == "Wales"].private.sum()), "all": int(CT[CT.nation == "Wales"]["all"].sum()),
              "per100": round(100 * CT[CT.nation == "Wales"].private.sum() / CT[CT.nation == "Wales"].area_km2.sum(), 2),
              "war_pct": pc(((A.cty.isin(WALES)) & (A.era == "war") & (A.source == "private")).sum(), ((A.cty.isin(WALES)) & (A.source == "private")).sum()),
              "first": int(A[A.cty.isin(WALES)].year.min())}
R["no_county_private"] = int(S["private"].cty.isna().sum()); R["no_county_all"] = int(A.cty.isna().sum())
mostc = CT.sort_values("private", ascending=False)
R["most_acts"] = [{"county": r.county, "name": r.name, "n": int(r.private), "all": int(r.all)} for r in mostc.head(10).itertuples()]
CT.drop(columns=["rank"]).to_csv(f"{DATA}/acts_by_county.csv", index=False)

# ---------- first and last ----------
pv = S["private"].sort_values(["year", "row"])
std = pv[pv.title.str.contains(r"\([^)]*\)\s*(?:in|en)closures?\b", case=False, regex=True)]
f0 = pv.iloc[0]; fs = std.iloc[0]; last = pv.iloc[-1]; lastl = S["local"].sort_values(["year", "row"]).iloc[-1]
R["first"] = {"year": int(f0.year), "title": f0.title, "chapter": f0.chapter, "session": f0.session,
              "std_year": int(fs.year), "std_title": fs.title, "std_session": fs.session, "std_chapter": fs.chapter,
              "n_before1700": int((pv.year < 1700).sum()), "n_before1750": int((pv.year < 1750).sum()), "n_1720s_on": int((pv.year >= 1720).sum())}
R["last"] = {"year": int(last.year), "title": last.title, "chapter": last.chapter, "local_year": int(lastl.year), "local_title": lastl.title,
             "n_after1845": int((A.year > 1845).sum()), "n_1840s": int(((A.year >= 1840) & (A.year <= 1849)).sum())}
fl = []
for r in CT.itertuples():
    fl.append({"county": r.county, "first": r.first, "last": r.last, "median": r.median_year})
R["county_first_last"] = fl
early = CT.sort_values("median_year").head(6); late = CT.sort_values("median_year", ascending=False).head(6)
R["earliest_counties"] = [{"county": r.county, "median": r.median_year, "n": int(r.all)} for r in early.itertuples()]
R["latest_counties"] = [{"county": r.county, "median": r.median_year, "n": int(r.all)} for r in late.itertuples()]

# ---------- centroid over time ----------
Lc = A[A.located]
cen = []
for d0, d1, lab in [(1700, 1749, "before 1750"), (1750, 1759, "1750s"), (1760, 1769, "1760s"), (1770, 1779, "1770s"), (1780, 1789, "1780s"),
                    (1790, 1799, "1790s"), (1800, 1809, "1800s"), (1810, 1819, "1810s"), (1820, 1829, "1820s"), (1830, 1849, "1830s and 1840s")]:
    d = Lc[(Lc.year >= d0) & (Lc.year <= d1)]
    x, y = d.x.mean(), d.y.mean(); lo, la = TO_LL.transform(x, y)
    cen.append({"label": lab, "d0": d0, "d1": d1, "n": len(d), "x": round(x), "y": round(y), "lon": round(lo, 4), "lat": round(la, 4),
                "north_pct": pc((d.lat > 53.0).sum(), len(d))})
R["centroid"] = cen
cd = {c["label"]: c for c in cen}
dx = cd["1810s"]["x"] - cd["1760s"]["x"]; dy = cd["1810s"]["y"] - cd["1760s"]["y"]
R["centroid_move"] = {"km": round(float(np.hypot(dx, dy)) / 1000), "dx_km": round(dx / 1000), "dy_km": round(dy / 1000),
                      "first_km": round(float(np.hypot(cd["1830s and 1840s"]["x"] - cd["1760s"]["x"], cd["1830s and 1840s"]["y"] - cd["1760s"]["y"])) / 1000), "south_km": round(-dy / 1000), "west_km": round(-dx / 1000)}
assert R["centroid_move"]["south_km"] > 0 and R["centroid_move"]["west_km"] > 0
# nearest town to each centroid (gazetteer towns)
T = E[E.types.map(lambda t: bool({"town", "city", "big city"} & set(t)))]
for c in cen:
    dd = np.hypot(T.x - c["x"], T.y - c["y"]); i = dd.idxmin()
    c["near"] = T.label[i]; c["near_km"] = round(float(dd[i]) / 1000, 1); c["near_county"] = T.hc[i]

# ---------- the second wave: where and what ----------
UP = ["Cumberland", "Westmorland", "Northumberland", "County Durham", "Yorkshire", "Lancashire", "Derbyshire", "Cheshire"] + WALES
WASTE = r"\b(?:commons?|wastes?|waste lands?|moors?|heaths?|forest|chase|fens?|marsh(?:es)?|carrs?|downs?|hills?|mountains?|warrens?|greens?)\b"
FIELDS = r"\b(?:open fields?|common fields?|fields?|infield|ings|meadows?)\b"
sw = {}
for nm, (a0, a1) in {"w1": (1750, 1779), "war": WAR, "after": (1816, 1849)}.items():
    d = A[(A.year >= a0) & (A.year <= a1)]
    dp = d[d.source == "private"]
    sw[nm] = {"n": len(d), "up_pct": pc(d.cty.isin(UP).sum(), d.cty.notna().sum()), "wales_pct": pc(d.cty.isin(WALES).sum(), d.cty.notna().sum()),
              "waste_pct": pc(d.title.str.contains(WASTE, case=False, regex=True).sum(), len(d)),
              "fields_pct": pc(d.title.str.contains(FIELDS, case=False, regex=True).sum(), len(d)),
              "mid_pct": pc(d.cty.isin(MID).sum(), d.cty.notna().sum()),
              "mean_lat": round(float(d.lat.mean()), 2), "lat53_pct": pc((d.lat > 53.0).sum(), d.lat.notna().sum()),
              "west_pct": pc((d.lon < -2.0).sum(), d.lon.notna().sum()),
              "multi_pct": pc((d.n_places > 1).sum(), len(d)), "drain_pct": pc(d.title.str.contains(r"drain|embank", case=False, regex=True).sum(), len(d)),
              "tithe_pct": pc(dp.title.str.contains(r"tithe|tythe", case=False, regex=True).sum(), len(dp))}
R["waves"] = sw
REG = {"belt": MID, "eastanglia": ["Norfolk", "Suffolk"], "wales": WALES,
       "north": ["Northumberland", "Cumberland", "Westmorland", "County Durham", "Yorkshire", "Lancashire"],
       "southwest": ["Cornwall", "Devon", "Somerset", "Dorset", "Wiltshire", "Hampshire", "Gloucestershire", "Herefordshire", "Shropshire", "Worcestershire"],
       "southeast": ["Kent", "Sussex", "Surrey", "Middlesex", "Essex", "Hertfordshire"]}
for nm, (a0, a1) in {"w1": (1750, 1779), "war": WAR, "after": (1816, 1849)}.items():
    d = A[(A.year >= a0) & (A.year <= a1) & A.cty.notna()]
    for rg, cs in REG.items():
        sw[nm][rg + "_pct"] = pc(d.cty.isin(cs).sum(), len(d)); sw[nm][rg + "_n"] = int(d.cty.isin(cs).sum())
R["regions"] = REG
assert sw["war"]["mid_pct"] < sw["w1"]["mid_pct"] and sw["war"]["wales_pct"] > sw["w1"]["wales_pct"] and sw["war"]["west_pct"] > sw["w1"]["west_pct"]
assert sw["war"]["eastanglia_pct"] > sw["w1"]["eastanglia_pct"] and sw["war"]["southwest_pct"] > sw["w1"]["southwest_pct"]
assert sw["war"]["north_pct"] < sw["w1"]["north_pct"]          # the north's share did not grow
print("WAVES", {k: {kk: v[kk] for kk in v if kk.endswith("_pct")} for k, v in sw.items()})

# ---------- striking cases ----------
big = A.sort_values(["n_places", "year"], ascending=[False, True]).iloc[0]
R["biggest"] = {"title": big.title, "year": int(big.year), "n_places": int(big.n_places), "county": big.cty, "source": big.source, "chapter": big.chapter,
                "located": int(P[(P.act == big.id) & P.gi.notna()].shape[0])}
R["multi"] = {"n_multi": int((A.n_places > 1).sum()), "multi_pct": pc((A.n_places > 1).sum(), len(A)), "n5": int((A.n_places >= 5).sum()),
              "places_per_act": round(float(A.n_places.mean()), 2)}
tw = loc.merge(A[["id", "year", "title", "source", "chapter"]], left_on="act", right_on="id")
cnt = tw.groupby("gi").agg(n=("act", "nunique"), years=("year", lambda s: sorted(set(s)))).reset_index()
cnt["ny"] = cnt.years.map(len)
twice = cnt[cnt.ny >= 2]
R["twice"] = {"n": len(twice), "pct": pc(len(twice), cnt.shape[0]), "three": int((cnt.ny >= 3).sum()), "max": int(cnt.ny.max())}
mx = cnt.sort_values(["ny", "n"], ascending=False).head(12)
R["twice_top"] = [{"place": E.label[int(r.gi)], "county": E.hc[int(r.gi)], "n": int(r.n), "years": [int(y) for y in r.years]} for r in mx.itertuples()]
gaps = twice.assign(gap=twice.years.map(lambda ys: ys[-1] - ys[0])).sort_values("gap", ascending=False)
R["twice_gap"] = [{"place": E.label[int(r.gi)], "county": E.hc[int(r.gi)], "years": [int(y) for y in r.years], "gap": int(r.gap)} for r in gaps.head(6).itertuples()]
# Plumstead Marsh, the earliest: how many acts mention it
R["plumstead"] = {"n": int(A.title.str.contains("Plumstead").sum()), "years": sorted(int(y) for y in A[A.title.str.contains("Plumstead")].year)}
kn = A[A.title.str.contains("Knaresborough")]
R["knaresborough"] = {"n": len(kn), "years": sorted(int(y) for y in kn.year)}
R["wording"] = {"drain_pct": pc(A.title.str.contains(r"drain|embank", case=False, regex=True).sum(), len(A)),
                "tithe_pct": pc(S["private"].title.str.contains(r"tithe|tythe", case=False, regex=True).sum(), len(S["private"])),
                "waste_pct": pc(A.title.str.contains(WASTE, case=False, regex=True).sum(), len(A))}

# ---------- meta ----------
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG, "war": list(WAR), "leg": LEG_URL, "loc": LOC_URL}

# ---------- clean data out ----------
out = A.copy()
out["places_text"] = out.places.map(lambda ps: "; ".join(n for n, _ in ps))
out["counties_text"] = out.counties.map(lambda cs: "; ".join(cs))
out.sort_values(["year", "source", "row"])[["source", "year", "session", "chapter", "title", "kind", "counties_text", "riding", "cty", "n_places", "places_text", "located", "lat", "lon", "era"]] \
    .rename(columns={"counties_text": "counties_in_title", "cty": "county_used", "places_text": "places", "lat": "mean_lat", "lon": "mean_lon"}) \
    .round({"mean_lat": 4, "mean_lon": 4}).to_csv(f"{DATA}/enclosure_acts.csv", index=False)
po = P.merge(A[["id", "source", "year", "session", "chapter", "title"]], left_on="act", right_on="id")
po.sort_values(["year", "act", "j"])[["source", "year", "session", "chapter", "title", "place", "alts", "county_given", "how", "g_label", "g_item", "g_hc", "g_type", "g_lat", "g_lon"]] \
    .rename(columns={"alts": "alternative_spellings", "how": "match", "g_label": "gazetteer_name", "g_item": "wikidata", "g_hc": "gazetteer_county", "g_type": "gazetteer_type", "g_lat": "lat", "g_lon": "lon"}) \
    .to_csv(f"{DATA}/enclosed_places.csv", index=False)
po[po.gi.isna()].sort_values(["year", "act", "j"])[["source", "year", "chapter", "title", "place", "alts", "county_given", "how", "ncand"]] \
    .rename(columns={"how": "reason", "ncand": "candidates"}).replace({"reason": {"none": "no gazetteer match", "ambiguous": "several places of this name"}}) \
    .to_csv(f"{DATA}/unmatched_places.csv", index=False)
Y.reset_index().rename(columns={"y": "year", "n": "all"}).to_csv(f"{DATA}/acts_by_year.csv", index=False)
others = A0[~A0.id.isin(A.id)]
others.sort_values(["year", "row"])[["source", "year", "session", "chapter", "title", "kind", "nation"]].to_csv(f"{DATA}/other_inclosure_titles.csv", index=False)

# ---------- page data ----------
ACT_I = {aid: k for k, aid in enumerate(A.sort_values(["year", "source", "row"]).id)}
AS = A.set_index("id")
acts = []
for aid in sorted(ACT_I, key=ACT_I.get):
    r = AS.loc[aid]
    acts.append([int(r.year), r.session if isinstance(r.session, str) else "", str(r.chapter), r.title, r.cty if isinstance(r.cty, str) else "", 0 if r.source == "private" else 1, int(r.n_places), 1 if r.kind == "agreement" else 0])
pts = []
for r in loc.sort_values(["act", "j"]).itertuples():
    a = AS.loc[r.act]
    pts.append([round(float(r.g_lon), 4), round(float(r.g_lat), 4), int(a.year), ACT_I[r.act], r.place if r.place == r.g_label else f"{r.place}|{r.g_label}"])
jsave({"cols": ["year", "session", "chapter", "title", "county", "local", "n_places", "agreement"], "acts": acts,
       "pcols": ["lon", "lat", "year", "act", "place"], "points": pts}, f"{DATA}/places.json")
cent = [[c["lon"], c["lat"], c["label"], c["n"]] for c in cen]
towns, miss_t = [], []
for rk, lst in TOWNS.items():
    for nm, c in lst:
        cand = E[(E.key == place_key(nm)) & (E.hc == c)].sort_values("tp")
        if not len(cand): cand = E[(E.key == place_key(nm))].sort_values("tp")
        if not len(cand):
            if nm in TOWN_LL:   # a few towns are missing from the gazetteer: label positions entered by hand (to about 1 km)
                towns.append({"name": nm, "lat": TOWN_LL[nm][0], "lon": TOWN_LL[nm][1], "rank": rk, "county": c}); continue
            miss_t.append(nm); continue
        r = cand.iloc[0]; towns.append({"name": nm.replace("Newcastle upon Tyne", "Newcastle").replace("Kingston upon Hull", "Hull"), "lat": round(float(r.lat), 4), "lon": round(float(r.lon), 4), "rank": rk, "county": c})
assert not miss_t, miss_t
site = {"decades": DECADES, "dec_col": DEC_COL, "centroid": cent, "towns": towns}
jsave(site, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print("results ok", {k: os.path.getsize(f"{DATA}/{k}") // 1024 for k in ("site.json", "places.json", "results.json")})
print(json.dumps({k: R[k] for k in ("source", "geo", "peaks", "eras", "belt", "light", "wales", "first", "last", "centroid_move", "waves", "biggest", "multi", "twice", "twice_top", "twice_gap", "wording")}, indent=0, ensure_ascii=False)[:9000])
print(R["county_rank"][:12]); print(R["most_acts"]); print([(c["label"], c["n"], c["near"], c["near_km"], c["lat"], c["lon"]) for c in cen])
print(R["earliest_counties"], R["latest_counties"])
