"""Geocode every place named in an enclosing act against the Wikidata gazetteer (England and Wales only).

Name keys. Both sides are reduced to a key: accents and punctuation dropped, lower case, Saint/St./S. -> st, King's ->
kings, "upon"/"super" -> on, "juxta"/"near" -> next, "-cum-" and "with" kept as words, "the" dropped, hyphens as spaces,
and a final possessive s dropped (St. Mary's -> st mary).

Steps, in order, for each place of an act whose title names a county (all steps are restricted to that county, or to
any of the counties when the title names two):
  1. exact: the key, or an alternative spelling the title gives ("North Hykeham or Hickham"), matches one gazetteer
     place, or several that are all within 5 km of each other (a parish and its village); civil parishes are preferred.
  2. part: the title names a piece of land in a parish ("Nythen Common in Alresford", "Glusburn Moor in Kildwick"), a
     township joined to another ("Denby-with-Clayton West"), or a name with a field or moor word ("Bonsall Leys"): the
     parish or main name is tried as in step 1.
     A name may also stand for a unique longer one with an "on", "next" or "by" tail (Goring for Goring-on-Thames),
     and "Great X" or "Little X" for X when only X is in the gazetteer.
  3. close: one gazetteer place in the county whose key is very similar (difflib ratio at least 0.88, same first
     letter) and clearly better than the next best: old spellings such as Hucklescote (Hugglescote) or Lockerly
     (Lockerley).
  4. ambiguous names (two Newtons in one county) are settled only if one candidate lies within 20 km of another place
     of the same act that matched; otherwise the place is left unmatched.
  5. other county: no match in the stated county, but exactly one place of that name in all of England and Wales, and
     it lies within 15 km of the stated county (a parish on or across a county boundary, such as Halesowen, or a
     slip in the table). Unique names farther away are rejected, since the gazetteer often lacks the right place.
Places of acts that give no county (most local acts) use steps 1, 2 and 4 against all of England and Wales, and are
accepted only when the name is unique or settled by a neighbour. Nothing else is guessed: everything left over is
listed in data/unmatched_places.csv."""
import difflib, numpy as np, pandas as pd
from common import *

A = pd.read_pickle(f"{WORK}/acts.pkl")
E = pd.read_pickle(f"{WORK}/gaz.pkl").reset_index(drop=True)
TPREF = lambda t: 0 if "civil parish" in t else 1 if "village" in t else 2 if "town" in t or "city" in t else 3


key = place_key


E["key"] = E.label.map(key)
E["tp"] = E.types.map(TPREF)
BY = {}
for i, r in E.iterrows():
    BY.setdefault(r.key, []).append(i)
BYC = {}
for i, r in E.iterrows():
    BYC.setdefault((r.hc, r.key), []).append(i)
KEYS_C = {}
for (c, k) in BYC:
    KEYS_C.setdefault(c, []).append(k)
XY = E[["x", "y"]].values


def collapse(ids):
    """One place if all candidates lie within 5 km (parish and village of one name), preferring the civil parish."""
    if not ids: return None, 0
    ids = sorted(ids, key=lambda i: E.tp[i])
    p = XY[ids]
    if len(ids) == 1 or np.max(np.hypot(*(p - p[0]).T)) <= 5000:
        return ids[0], 1
    return None, len(ids)


LAND = r"(?:common|commons|moor|moors|heath|marsh|marshes|fen|fens|forest|chase|green|greens|waste|wastes|field|fields|infield|park|wood|leys|carr|carrs|down|downs|hill|hills|ings|meadows?|pastures?|lands?|hay|warren|lammas|cow pasture|in the clay)"


def variants(nm):
    """Simpler names to try in step 2."""
    out = []
    m = re.match(r"^(.*?)\s+(?:in|of|near|within)\s+(?:the\s+)?(?:parish\s+of\s+)?(.+)$", nm, re.I)
    if m:
        out += [m.group(2), m.group(1)]
    for sep in (r"-?\bcum\b-?", r"-?\bwith\b-?", r"\s+and\s+"):
        if re.search(sep, nm, re.I):
            out += [x.strip(" -") for x in re.split(sep, nm, flags=re.I) if x.strip(" -")]
    s = re.sub(r"\s+" + LAND + r"$", "", nm, flags=re.I)
    if s != nm: out.append(s)
    s = re.sub(r"^(?:the\s+)?" + LAND + r"\s+(?:of|in)\s+", "", nm, flags=re.I)
    if s != nm: out.append(s)
    out.append(re.sub(r"\s*\b(?:parish|township|manor|hamlet|liberty|division|quarter|ward|lordship)\b\s*", " ", nm, flags=re.I).strip())
    s = re.sub(r"^(?:Great|Little|Much|Magna|Parva)\s+", "", nm)
    if s != nm: out.append(s)
    return [o for o in dict.fromkeys(out) if o and o != nm and len(o) >= 3]


def find(names, counties):
    """Steps 1 to 3. Returns (index or None, method, n_candidates)."""
    for step, cands in (("exact", names), ("part", [v for n in names for v in variants(n)])):
        amb = 0
        for nm in cands:
            k = key(nm)
            ids = [i for c in counties for i in BYC.get((c, k), [])] if counties else BY.get(k, [])
            i, n = collapse(ids)
            if i is not None:
                return i, step, 1
            amb = max(amb, n)
        if amb:
            return None, "ambiguous", amb
    for nm in names:   # "Goring" -> Goring-on-Thames, "Bidford" -> Bidford-on-Avon: a unique longer name with an "on/next/by" tail
        k = key(nm)
        pool = [(c, kk) for c in counties for kk in KEYS_C.get(c, [])] if counties else [(None, kk) for kk in BY]
        hit = sorted({(c, kk) for c, kk in pool if re.match(re.escape(k) + r" (?:on|next|by|in|under|le|en|cum|st) ", kk)})
        if len(hit) == 1:
            i, n = collapse(BYC[hit[0]] if counties else BY[hit[0][1]])
            if i is not None:
                return i, "part", 1
    if counties:
        best = []
        for nm in names:
            k = key(nm)
            for c in counties:
                for kk in KEYS_C.get(c, []):
                    if kk[:1] != k[:1]: continue
                    r = difflib.SequenceMatcher(None, k, kk).ratio()
                    if r >= .80: best.append((r, c, kk))
        best.sort(reverse=True)
        if best and best[0][0] >= .88 and (len(best) == 1 or best[0][0] - best[1][0] >= .04 or best[1][2] == best[0][2]):
            i, n = collapse(BYC[(best[0][1], best[0][2])])
            if i is not None:
                return i, "close", 1
    return None, "none", 0


rows = []
for a in A.itertuples():
    if a.kind not in ("enclosure", "agreement", "amendment") or a.nation in ("Ireland", "Scotland"):
        continue
    cs = [c for c in a.counties if c in COUNTIES]
    for j, (nm, alts) in enumerate(a.places):
        i, how, n = find([nm] + list(alts), cs)
        rows.append({"act": a.id, "j": j, "place": nm, "alts": "; ".join(alts), "county_given": "; ".join(cs), "gi": i, "how": how, "ncand": n})
P = pd.DataFrame(rows)

# step 4: settle ambiguous names by a matched neighbour in the same act
for idx, r in P[P.how == "ambiguous"].iterrows():
    sib = P[(P.act == r.act) & P.gi.notna()]
    if not len(sib): continue
    a = A.loc[A.id == r.act].iloc[0]; cs = [c for c in a.counties if c in COUNTIES]
    names = [r.place] + ([x for x in r.alts.split("; ") if x] if r.alts else [])
    cand = sorted({i for nm in names + [v for n in names for v in variants(n)] for i in ([j for c in cs for j in BYC.get((c, key(nm)), [])] if cs else BY.get(key(nm), []))})
    sx = XY[sib.gi.astype(int).values]
    dist = [(float(np.min(np.hypot(*(sx - XY[i]).T))), i) for i in cand]
    dist.sort()
    if dist and dist[0][0] <= 20000 and (len(dist) == 1 or dist[1][0] > 2 * dist[0][0]):
        P.loc[idx, "gi"] = dist[0][1]; P.loc[idx, "how"] = "neighbour"
# step 5: right name, wrong county in the table; the place must lie within 15 km of the stated county (a border slip),
# because a unique name elsewhere in England is more often a different place that the gazetteer lacks a namesake for
from shapely.geometry import shape as _shape, Point as _Pt
from shapely.ops import transform as _tr
from pyproj import Transformer as _T
_bng = _T.from_crs(4326, 27700, always_xy=True)
CPOLY = {f["properties"]["county"]: _tr(lambda x, y: _bng.transform(x, y), _shape(f["geometry"])) for f in jload(f"{DATA}/historic_counties.geojson")["features"]}
HOMONYM = {("Eccleshill", "Yorkshire"), ("Llandrillo", "Denbighshire; Caernarfonshire")}   # checked by hand: a different place of the same name
for idx, r in P[P.gi.isna() & (P.county_given != "")].iterrows():
    names = [r.place] + ([x for x in r.alts.split("; ") if x] if r.alts else [])
    if (r.place, r.county_given) in HOMONYM: continue
    for nm in names:
        ids = BY.get(key(nm), [])
        i, n = collapse(ids)
        near = i is not None and min(CPOLY[c].distance(_Pt(XY[i][0], XY[i][1])) for c in r.county_given.split("; ")) <= 15000
        if i is not None and len(key(nm)) >= 6 and near:
            P.loc[idx, "gi"] = i; P.loc[idx, "how"] = "other county"; break
P["gi"] = P.gi.astype("Int64")
for c in ("label", "item", "hc", "lon", "lat", "x", "y"):
    P["g_" + c] = P.gi.map(lambda i: E[c][i] if pd.notna(i) else None)
P["g_type"] = P.gi.map(lambda i: (E.types[i][0] if E.types[i] else "") if pd.notna(i) else None)
P.to_pickle(f"{WORK}/places.pkl")
E.to_pickle(f"{WORK}/gaz_keyed.pkl")
ok = P.gi.notna()
print("places", len(P), "matched", int(ok.sum()), f"{100 * ok.mean():.1f}%"); print(P.how.value_counts().to_dict())
