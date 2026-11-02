"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23873003, https://doi.org/10.5281/zenodo.23873003 and https://blog.tristanhotham.com/2026/10/31/enclosure/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Fencing_the_Commons"

# the page build checks the shared facts; these are numbers written in words or alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "05_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
pk, C, W, g = R["peaks"], R["counties"], R["waves"], R["geo"]
assert 4200 <= g["matched"] <= 4400                                                                  # "about 4,300 small dots"
assert (pk["first_wave_n"], pk["first_wave_year"], pk["all_n"], pk["all_year"]) == (87, 1777, 125, 1811)
assert [round(W[k][r + "_pct"]) for k in ("w1", "war") for r in ("belt", "eastanglia", "southwest")] == [53, 2, 12, 31, 13, 22]
assert W["war"]["belt_pct"] < 100 / 3 and 18 <= R["belt"]["area_pct"] <= 23                          # "under a third", "about a fifth of England"
assert round(C["Northamptonshire"]["per100_private"], 1) == 7.5
assert 12 <= [r["county"] for r in R["county_rank"]].index("Yorkshire") + 1 <= 30                   # "in the middle of the table"
assert R["centroid"][3]["near"] == "Loughborough" and R["centroid"][3]["label"] == "1770s"
gp = {t["place"]: t for t in R["twice_gap"]}
assert sorted(gp[p]["gap"] for p in ("Eccleshall", "Compton Bassett", "Barston")) == [83, 106, 122]
assert {t["place"]: t for t in R["twice_top"]}["Lanchester"]["years"] == [1762, 1772, 1773, 1779]
assert pk["private_year"] < pk["all_year"]

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23873003"}
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s = R["source"]
meta = {"title": "Fencing the commons: every enclosure Act in England and Wales, mapped",
        "slug": "enclosure",
        "excerpt": f"I mapped every enclosure Act in Parliament's chronological tables, {s['n_all']:,} of them, place by place. They came in two waves, and {R['eras']['all']['war_pct']:.0f}% were passed in the years of war with France, when wheat was dear.",
        "seo_description": f"A map of {s['n_all']:,} enclosure Acts in England and Wales: two waves, the Midland belt, and the war-years boom that peaked at {pk['all_n']} Acts in {pk['all_year']}.",
        "tags": ["enclosure", "history", "maps", "data visualisation", "agricultural history", "commons", "England", "Wales", "Georgian Britain"],
        "header_alt": f"Title card reading 'Fencing the commons' in green and black on pale paper, beside a map of England and Wales covered in small dots coloured by decade, gold in the Midlands and blue in Norfolk and the south, and below it a bar chart of enclosure Acts per year with two peaks, in the 1770s and around 1811. Text: every enclosure Act in the Chronological Tables, {s['n_private']:,} private Acts and {s['n_local']:,} local Acts."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/enclosure_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data", "raw"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"enclosure/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"enclosure/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "enclosure/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("km$^2$", "km²")
zmeta = {"title": "Fencing the Commons: Mapping Parliamentary Enclosure in England and Wales from the Chronological Tables of Private and Local Acts",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Contains public sector information from legislation.gov.uk licensed under the Open Government Licence v3.0. Place data: Wikidata (CC0).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["enclosure", "inclosure Acts", "parliamentary enclosure", "open fields", "common rights", "agrarian history", "England", "Wales", "historical GIS", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": LEG_URL, "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": LOC_URL, "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
