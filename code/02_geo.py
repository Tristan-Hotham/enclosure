"""Geography: the Wikidata gazetteer cleaned to one row per place in England and Wales with a historic county, rebuilt
historic county shapes, and the England and Wales outline.

Gazetteer. raw/uk_places_wikidata.tsv has one row per item and value, so items repeat; I keep one row per item, with all
its types and its first historic county (P7959). About 3,400 rows have no historic county. Most are Cornish villages
(Wikidata gives Cornwall's places no P7959): those inside the modern county of Cornwall get Cornwall, which matches
the historic county closely. Others get the historic county of the majority of their five nearest neighbours within 15
km that have one. Scotland and Northern Ireland are dropped.

Historic county shapes. There is no historic county boundary file in the inputs, so I rebuild approximate ones: a
Voronoi cell around every gazetteer place, merged by historic county and clipped to the coast of England and Wales
(modern county outlines). With some 40,000 places the shapes follow the real boundaries to within a parish or so;
they are used for the choropleth and for areas (km2, British National Grid). Yorkshire is one county here (Wikidata
does not split it into ridings)."""
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping, Point, MultiPoint, box
from shapely.ops import unary_union, transform as stransform
from shapely.prepared import prep
from shapely import voronoi_polygons
from scipy.spatial import cKDTree
from pyproj import Transformer
from common import *

TO_BNG = Transformer.from_crs(4326, 27700, always_xy=True)
TO_LL = Transformer.from_crs(27700, 4326, always_xy=True)

g = pd.read_csv(f"{RAW}/uk_places_wikidata.tsv", sep="\t", dtype=str, keep_default_na=False, quoting=3)
g.columns = ["item", "label", "coord", "type", "hc", "adm"]
strip = lambda s: re.sub(r'^"(.*)"@en$', r"\1", s)
for c in ("label", "type", "hc", "adm"):
    g[c] = g[c].map(strip)
g["item"] = g.item.str.extract(r"(Q\d+)")[0]
xy = g.coord.str.extract(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)").astype(float)
g["lon"], g["lat"] = xy[0], xy[1]
chk = {"gaz_rows": len(g), "gaz_items": int(g.item.nunique())}
G = g.groupby("item").agg(label=("label", "first"), lon=("lon", "first"), lat=("lat", "first"),
                          types=("type", lambda s: sorted(set(x for x in s if x))), hc=("hc", lambda s: next((x for x in s if x), "")),
                          adm=("adm", lambda s: next((x for x in s if x), ""))).reset_index()
G = G[G.label.str.len() > 0].copy()

# England and Wales outline (modern counties, which follow the coast)
CU = jload(f"{GEO}/counties_uk.geojson")
ew = unary_union([shape(f["geometry"]).buffer(0) for f in CU["features"] if f["properties"]["nation"] in ("England", "Wales")]).buffer(0)
corn = unary_union([shape(f["geometry"]).buffer(0) for f in CU["features"] if f["properties"]["county"] == "Cornwall"]).buffer(0)
pew, pcorn = prep(ew.buffer(0.02)), prep(corn.buffer(0.01))
G["in_ew"] = [pew.contains(Point(x, y)) for x, y in zip(G.lon, G.lat)]
chk["gaz_no_hc"] = int((G.hc == "").sum())

# fill in missing historic counties
miss = (G.hc == "") & G.in_ew
G.loc[miss & np.array([pcorn.contains(Point(x, y)) for x, y in zip(G.lon, G.lat)]), "hc"] = "Cornwall"
lab = G[G.hc.isin(COUNTIES)]
bx, by = TO_BNG.transform(lab.lon.values, lab.lat.values)
tree = cKDTree(np.column_stack([bx, by]))
miss = (G.hc == "") & G.in_ew
mx, my = TO_BNG.transform(G.loc[miss, "lon"].values, G.loc[miss, "lat"].values)
d, ix = tree.query(np.column_stack([mx, my]), k=5, distance_upper_bound=15000)
fill = []
for dd, ii in zip(d, ix):
    c = [lab.hc.values[i] for dist, i in zip(dd, ii) if np.isfinite(dist)]
    fill.append(max(set(c), key=c.count) if c else "")
G.loc[miss, "hc"] = fill
chk["gaz_cornwall"] = int((G.hc == "Cornwall").sum())
chk["gaz_nn_filled"] = int(sum(1 for x in fill if x))
E = G[G.hc.isin(COUNTIES)].copy()
E["x"], E["y"] = TO_BNG.transform(E.lon.values, E.lat.values)
chk["gaz_ew"] = len(E); chk["gaz_ew_counties"] = int(E.hc.nunique())
assert set(E.hc) == set(COUNTIES), set(COUNTIES) - set(E.hc)
E.to_pickle(f"{WORK}/gaz.pkl")

# rebuilt historic counties: Voronoi cells of the gazetteer points, merged by county, clipped to the coast
ew_b = stransform(lambda x, y: TO_BNG.transform(x, y), ew)
pts = E.drop_duplicates(["x", "y"])
vor = voronoi_polygons(MultiPoint(list(zip(pts.x, pts.y))), extend_to=ew_b.envelope.buffer(50000))
cells = list(vor.geoms)
ctree = cKDTree(np.column_stack([pts.x, pts.y]))
owner = {}
for c in cells:
    p = c.representative_point()
    _, i = ctree.query([p.x, p.y])
    owner.setdefault(pts.hc.values[i], []).append(c)
feats, areas = [], {}
for cty in COUNTIES:
    geom = unary_union(owner[cty]).intersection(ew_b).buffer(0)
    geom = geom.buffer(400).buffer(-400).simplify(300, preserve_topology=True)   # smooth the cell edges a little
    areas[cty] = round(geom.area / 1e6, 1)
    gl = stransform(lambda x, y: TO_LL.transform(x, y), geom)
    gm = mapping(gl)
    rnd = lambda c: [round(c[0], 4), round(c[1], 4)] if isinstance(c[0], float) else [rnd(x) for x in c]
    lp = gl.representative_point() if cty != "Yorkshire" else Point(-1.45, 54.05)
    feats.append({"type": "Feature", "properties": {"county": cty, "nation": NATION[cty], "area_km2": areas[cty], "lx": round(lp.x, 3), "ly": round(lp.y, 3)},
                  "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/historic_counties.geojson")
chk["area_total_km2"] = round(sum(areas.values())); chk["areas"] = areas
# rough checks against well known historic areas (Rutland about 390 km2, Yorkshire about 15,700 km2)
assert 330 < areas["Rutland"] < 460 and 14500 < areas["Yorkshire"] < 16800 and 6300 < areas["Lincolnshire"] < 7600, areas

# outline for the page and figures
ew_s = ew.simplify(0.004, preserve_topology=True)
gm = mapping(ew_s)
rnd = lambda c: [round(c[0], 4), round(c[1], 4)] if isinstance(c[0], float) else [rnd(x) for x in c]
jsave({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "England and Wales"}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}}]}, f"{DATA}/england_wales.geojson")
# neighbouring land (Scotland, Ireland, France) for context in the figures
NE = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
fr = box(-11.5, 49.0, 3.5, 56.5)
oth = []
for f in NE["features"]:
    s = shape(f["geometry"]).intersection(fr)
    if not s.is_empty:
        oth.append(s)
sc = unary_union([shape(f["geometry"]).buffer(0) for f in CU["features"] if f["properties"]["nation"] in ("Scotland", "Northern Ireland")])
land = unary_union(oth + [sc]).difference(ew.buffer(0.01)).simplify(0.01)
gm = mapping(land)
jsave({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}}]}, f"{WORK}/other_land.geojson")
# towns for map labels: towns and cities in the gazetteer
T = E[E.types.map(lambda t: bool({"town", "city", "big city"} & set(t)))].copy()
T["rank"] = T.types.map(lambda t: 2 if "big city" in t else 1 if "city" in t else 0)
jsave([{"name": r.label, "lat": round(r.lat, 4), "lon": round(r.lon, 4), "rank": int(r.rank), "county": r.hc} for r in T.sort_values("rank", ascending=False).itertuples()], f"{WORK}/towns.json")
jsave(chk, f"{WORK}/checks_geo.json", indent=1)
print({k: v for k, v in chk.items() if k != "areas"}); print(sorted(areas.items(), key=lambda kv: -kv[1])[:8], areas["Rutland"])
