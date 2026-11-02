"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *
WAR = WAR

R = jload(f"{DATA}/results.json")
s, pk, g, er, b, W, C = R["source"], R["peaks"], R["geo"], R["eras"], R["belt"], R["waves"], R["counties"]
N = lambda v: f"{round(v):,}"
readme = f"""# Fencing the commons: every enclosure Act in England and Wales, mapped

A map and analysis of parliamentary enclosure in England and Wales: every Act that enclosed a parish's open fields, commons or wastes, as listed in the Chronological Tables of Private and of Local Acts on legislation.gov.uk, placed on the map and in time. {N(s['n_private'])} private Acts and {N(s['n_local'])} local Acts, from {s['first_year']} to {s['last_year']}, naming {N(g['places'])} places, of which {N(g['matched'])} ({g['rate']:.0f}%) are located.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Two waves: {N(pk['y1760_79'])} private Acts in 1760 to 1779 (peak {pk['first_wave_n']} in {pk['first_wave_year']}); {N(pk['y1793_1815_all'])} Acts in the French war years {WAR[0]} to {WAR[1]} ({N(pk['y1793_1815_private'])} private, {N(pk['y1793_1815_local'])} local), {er['all']['war_pct']:.0f}% of all Acts in {er['war_years']} years. Busiest year {pk['all_year']} ({pk['all_n']} Acts); private Acts peaked at {pk['private_n']} in {pk['private_year']}. {pk['y1814']} Acts in 1814, {pk['y1816']} in 1816.
- Shares: private Acts {er['private']['before_pct']:.0f}% before {WAR[0]}, {er['private']['war_pct']:.0f}% in the war years, {er['private']['after_pct']:.0f}% after; all Acts {er['all']['before_pct']:.0f}%, {er['all']['war_pct']:.0f}% and {er['all']['after_pct']:.0f}%.
- Two tables: from {pk['local_first']} a growing share of enclosure Acts sits in the local table ({pk['local_share_1811_14']:.0f}% in 1811 to 1814), so private Acts alone understate the second wave.
- Where: Northamptonshire has the most private Acts per 100 km2 ({C['Northamptonshire']['per100_private']:.2f}), then Leicestershire, Rutland, Huntingdonshire and Nottinghamshire. Twelve Midland belt counties cover {b['area_pct']:.0f}% of England and hold {b['acts_pct']:.0f}% of its private Acts ({b['per100']:.2f} per 100 km2 against {b['eng_per100']:.2f}). Kent has {C['Kent']['private']}, Devon {C['Devon']['private']}, Cornwall {C['Cornwall']['private']} (last of {R['n_counties']}). Wales {R['wales']['private']} private Acts, {R['wales']['war_pct']:.0f}% in the war years.
- The second wave spread: Midland belt share {W['w1']['belt_pct']:.0f}% (1750 to 1779) to {W['war']['belt_pct']:.0f}% ({WAR[0]} to {WAR[1]}); Norfolk and Suffolk {W['w1']['eastanglia_pct']:.0f}% to {W['war']['eastanglia_pct']:.0f}%; south-west and Welsh border {W['w1']['southwest_pct']:.0f}% to {W['war']['southwest_pct']:.0f}%; Wales {W['w1']['wales_pct']:.1f}% to {W['war']['wales_pct']:.1f}%; the north {W['w1']['north_pct']:.0f}% to {W['war']['north_pct']:.0f}%.
- Centre of gravity: near Nottingham in the 1760s, west of Leicester in the 1810s (about {R['centroid_move']['km']} km), near Rugby in the 1830s and 1840s.
- Cases: first title Plumstead Marsh (Kent) {R['first']['year']}; last private Act Terrington (Norfolk) {R['last']['year']}, last local Act Gedney (Lincolnshire) {R['last']['local_year']}; biggest Act {R['biggest']['n_places']} places around Shenstone, Staffordshire, {R['biggest']['year']}; {R['twice']['n']} places named in Acts of two or more years.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`; page data embedded, `data/places.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/enclosure_acts.csv` | All {N(s['n_all'])} enclosure Acts: source table, year, session, chapter, title, class, counties in the title, county used, places, whether located, mean position, era. |
| `data/enclosed_places.csv` | Every named place: the Act, the name as written, alternative spellings, the county given, how it was matched, and the Wikidata item, name, county, type and coordinates. |
| `data/unmatched_places.csv` | The {N(g['places'] - g['matched'])} named places not located, with the reason. |
| `data/acts_by_year.csv` | Private, local and all enclosure Acts per year, 1700 to 1849. |
| `data/acts_by_county.csv` | Per historic county: Acts, area of the rebuilt county, density, first, middle and last year, war share. |
| `data/other_inclosure_titles.csv` | Titles mentioning inclosure that are not counted (amendments, commissioners' orders, passing mentions, Irish Acts). |
| `data/historic_counties.geojson` | Historic counties of England and Wales rebuilt from Wikidata places (approximate). |
| `data/england_wales.geojson` | Coastline of England and Wales. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/places.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Tables: titles rejoined across rows; annotation rows (repeals, amendments, savings) dropped; year = first calendar year of the session. Every title with a word starting "inclos" or "enclos" kept ({N(s['n_private_mentions'])} private, {N(s['n_local_mentions'])} local); enclosure Acts and confirmations of agreed enclosures counted; {s['amend_private']} amendments, {s['orders_local']} confirmations of the Inclosure Commissioners' orders, passing mentions and {s['ireland']} Irish Acts set aside.
- Places: each title split into the places it names, matched to the Wikidata gazetteer within the stated county (exact, parish of a named piece of land, close spelling, settled by a neighbour, just over a county boundary). {g['rate']:.0f}% located ({g['private']['rate']:.0f}% for private, {g['local']['rate']:.0f}% for local Acts). Nothing else guessed.
- Counties: an Act counts for the first county in its title. Historic county shapes rebuilt from gazetteer places (Voronoi cells merged by county, clipped to the coast); Yorkshire as one county.
- Caveats: this counts Acts as the tables list them, not every enclosure. The commonly quoted total of more than 5,000 English enclosure Acts also takes in public local Acts and post-1845 Inclosure Commissioners' awards confirmed by general Acts, not itemised here; enclosure by agreement is absent. Two pages of the local table (1802 to 1803, 1841) are missing. An Act counts once whatever its acreage.

## How to rerun

Needs Python 3 with numpy, pandas, scipy, shapely, pyproj, matplotlib, Pillow and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs are in `raw/` (the two chronological tables as JSON and the Wikidata gazetteer) and the coastline files in `/home/claude/newdata/raw/geo/` (paths in `code/common.py`). Intermediate files go to `/dev/shm/enclosure/work` (set `ENTMP` to change).

```
python3 code/01_parse.py        # read the tables, keep and classify inclosure titles, split places
python3 code/02_geo.py          # gazetteer, rebuilt historic counties, coastline
python3 code/03_geocode.py      # match places to the gazetteer
python3 code/04_results.py      # results.json, data tables, page data
python3 code/05_build_site.py   # index.html
python3 code/06_figures.py      # header, blog and paper figures
python3 code/07_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/08_readme.py       # README, LICENSE, Reddit post
python3 code/09_release.py      # blog post, Zenodo files
```

## Sources and licences

- Chronological Table of Private and Personal Acts and Chronological Table of Local Acts, legislation.gov.uk ({LEG_URL}, {LOC_URL}). Crown copyright, Open Government Licence v3.0. Contains public sector information licensed under the Open Government Licence v3.0.
- Wikidata places with coordinates and historic county. CC0.
- Coastline from modern county outlines; Natural Earth (public domain) for neighbouring land.
- Hillshade tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Fencing the commons: mapping parliamentary enclosure in England and Wales from the Chronological Tables of Acts. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/meteorite-falls/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. The enclosure Acts are derived
from the Chronological Tables of Private and Personal Acts and of Local Acts
published by legislation.gov.uk: Crown copyright, used under the Open
Government Licence v3.0 (contains public sector information licensed under
the Open Government Licence v3.0). Place names and coordinates come from
Wikidata (CC0). Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Every Act of Parliament that fenced off the open fields and commons of England and Wales, mapped: {N(s['n_all'])} enclosure Acts in two waves, {er['all']['war_pct']:.0f}% of them passed during the wars with France ({WAR[0]} to {WAR[1]})

## Body

I took every enclosure Act in Parliament's own chronological tables ({N(s['n_private'])} private and {N(s['n_local'])} local Acts, 1562 to {s['last_year']}) and put the {N(g['matched'])} parishes and townships they name on a map, coloured by decade. Two waves stand out: the 1760s and 1770s, centred on the Midlands, and the French war years {WAR[0]} to {WAR[1]}, when wheat was dear and {N(pk['y1793_1815_all'])} Acts were passed, peaking at {pk['all_n']} in {pk['all_year']}. Northamptonshire had {C['Northamptonshire']['private']} private Acts; Cornwall had {C['Cornwall']['private']}. The second wave spread out: Norfolk and Suffolk went from {W['w1']['eastanglia_pct']:.0f}% of Acts to {W['war']['eastanglia_pct']:.0f}%, and Wales started enclosing its hills. Caveats: this counts Acts as the tables list them, not every enclosure (lots happened by agreement, and post-1845 awards are not itemised); {g['rate']:.0f}% of named places were found in the gazetteer. Interactive map with a play button, county view and every Act's title: {PAGE}

## Source comment

Source: legislation.gov.uk Chronological Table of Private and Personal Acts and Chronological Table of Local Acts (Open Government Licence v3.0). Places geocoded with Wikidata (CC0); historic county shapes rebuilt from Wikidata places. Enclosure Act = a title enacting or confirming an inclosure; amendments, Inclosure Commissioners' order confirmations and Irish Acts left out.

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for t in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
