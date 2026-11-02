"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, the England and Wales outline and the rebuilt historic counties) is
embedded; data/places.json is loaded by the page. Facts stated in words are checked here. The full-screen map snippet
(code/fullscreen_snippet.html) is pasted before </body>. 10.5281/zenodo.23873003 and https://blog.tristanhotham.com/2026/10/31/enclosure/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
PL = jload(f"{DATA}/places.json")
pk, C, W, CR = R["peaks"], R["counties"], R["waves"], R["county_rank"]

# facts stated in words (page, blog, paper, collage)
assert R["first"]["year"] == 1562 and "Plumstead Marsh" in R["first"]["title"] and R["plumstead"]["n"] >= 3
std = [a for a in PL["acts"] if a[0] > 1600 and re.search(r"\([A-Za-z ,.]+\)\s*inclosure", a[3])]
assert std[0][0] == 1709 and std[0][3].startswith("Ropley Commons (Hampshire)"), std[0]
assert R["last"]["year"] == 1847 and R["last"]["title"].startswith("Terrington (Norfolk)") and R["last"]["local_year"] == 1873 and R["last"]["local_title"].startswith("Gedney")
assert [r["county"] for r in CR[:10]] == ["Northamptonshire", "Leicestershire", "Rutland", "Huntingdonshire", "Nottinghamshire", "Warwickshire", "Bedfordshire", "Oxfordshire", "Worcestershire", "Buckinghamshire"]
assert R["light"]["Kent"]["rank"] == 44 and R["light"]["Devon"]["rank"] == 43 and R["light"]["Cornwall"]["rank"] == R["n_counties"] == 52
assert C["Essex"]["per100_private"] < 1 and C["Sussex"]["per100_private"] < 1 and R["belt"]["eng_per100"] > 2
assert [r["county"] for r in R["most_acts"][:3]] == ["Yorkshire", "Lincolnshire", "Norfolk"]
assert sorted(C, key=lambda c: -C[c]["all"])[:3] == ["Yorkshire", "Lincolnshire", "Norfolk"] and C["Norfolk"]["war_pct"] > 60
assert W["w1"]["belt_pct"] > 50 and W["war"]["west_pct"] / W["w1"]["west_pct"] >= 1.9 and W["w1"]["wales_pct"] < 1 and W["war"]["north_pct"] < W["w1"]["north_pct"]
assert pk["y1814"] > pk["y1815"] > pk["y1816"] and pk["all_year"] == 1811 and pk["private_year"] == 1801 and pk["first_wave_year"] == 1777
assert 1780 <= pk["trough_year"] <= 1789
cen = R["centroid"]
assert cen[2]["label"] == "1760s" and cen[2]["near"] == "Carlton" and cen[7]["label"] == "1810s" and cen[9]["near"] == "Rugby" and cen[2]["lat"] > cen[7]["lat"]
assert all(abs(c["lon"] + 1.15) < .4 and 52.2 < c["lat"] < 53.1 for c in cen)            # "never left the East Midlands"
T = {t["place"]: t for t in R["twice_top"]}
assert T["Elsdon"]["years"] == [1728, 1769, 1805, 1807] and all(T[p]["n"] == 4 for p in ("Simonburn", "Chatteris", "Rothbury")) and R["twice"]["max"] == 4
assert R["twice_gap"][0]["place"] == "Eccleshall" and R["twice_gap"][0]["years"] == [1719, 1841]
assert R["biggest"]["title"].startswith("Over Stonnall") and R["biggest"]["n_places"] == 10 and R["biggest"]["year"] == 1811
assert R["eras"]["all"]["war_pct"] > R["eras"]["all"]["before_pct"] and 0.4 < pk["local_share_1811_14"] / 100 < 0.6     # "about half"
assert R["source"]["local_missing"] == "1802 to 1803 and 1841"


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23873003", "https://blog.tristanhotham.com/2026/10/31/enclosure/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*EW*/", open(f"{DATA}/england_wales.geojson", encoding="utf-8").read())
    html = html.replace("/*COUNTIES*/", open(f"{DATA}/historic_counties.geojson", encoding="utf-8").read())
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
