# Fencing the commons: every enclosure Act in England and Wales, mapped

A map and analysis of parliamentary enclosure in England and Wales: every Act that enclosed a parish's open fields, commons or wastes, as listed in the Chronological Tables of Private and of Local Acts on legislation.gov.uk, placed on the map and in time. 3,655 private Acts and 449 local Acts, from 1562 to 1873, naming 5,375 places, of which 4,259 (79%) are located.

Interactive page: https://maps.tristanhotham.com/enclosure/
Paper: https://doi.org/10.5281/zenodo.23873003
Blog post: https://blog.tristanhotham.com/2026/10/31/enclosure/

## Headline results

- Two waves: 985 private Acts in 1760 to 1779 (peak 87 in 1777); 1,967 Acts in the French war years 1793 to 1815 (1,541 private, 426 local), 48% of all Acts in 23 years. Busiest year 1811 (125 Acts); private Acts peaked at 100 in 1801. 114 Acts in 1814, 43 in 1816.
- Shares: private Acts 43% before 1793, 42% in the war years, 15% after; all Acts 38%, 48% and 14%.
- Two tables: from 1799 a growing share of enclosure Acts sits in the local table (51% in 1811 to 1814), so private Acts alone understate the second wave.
- Where: Northamptonshire has the most private Acts per 100 km2 (7.50), then Leicestershire, Rutland, Huntingdonshire and Nottinghamshire. Twelve Midland belt counties cover 21% of England and hold 39% of its private Acts (5.18 per 100 km2 against 2.73). Kent has 15, Devon 26, Cornwall 1 (last of 52). Wales 70 private Acts, 60% in the war years.
- The second wave spread: Midland belt share 53% (1750 to 1779) to 31% (1793 to 1815); Norfolk and Suffolk 2% to 13%; south-west and Welsh border 12% to 22%; Wales 0.4% to 3.5%; the north 26% to 19%.
- Centre of gravity: near Nottingham in the 1760s, west of Leicester in the 1810s (about 46 km), near Rugby in the 1830s and 1840s.
- Cases: first title Plumstead Marsh (Kent) 1562; last private Act Terrington (Norfolk) 1847, last local Act Gedney (Lincolnshire) 1873; biggest Act 10 places around Shenstone, Staffordshire, 1811; 258 places named in Acts of two or more years.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`; page data embedded, `data/places.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/enclosure_acts.csv` | All 4,104 enclosure Acts: source table, year, session, chapter, title, class, counties in the title, county used, places, whether located, mean position, era. |
| `data/enclosed_places.csv` | Every named place: the Act, the name as written, alternative spellings, the county given, how it was matched, and the Wikidata item, name, county, type and coordinates. |
| `data/unmatched_places.csv` | The 1,116 named places not located, with the reason. |
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

- Tables: titles rejoined across rows; annotation rows (repeals, amendments, savings) dropped; year = first calendar year of the session. Every title with a word starting "inclos" or "enclos" kept (3,722 private, 483 local); enclosure Acts and confirmations of agreed enclosures counted; 43 amendments, 29 confirmations of the Inclosure Commissioners' orders, passing mentions and 10 Irish Acts set aside.
- Places: each title split into the places it names, matched to the Wikidata gazetteer within the stated county (exact, parish of a named piece of land, close spelling, settled by a neighbour, just over a county boundary). 79% located (81% for private, 65% for local Acts). Nothing else guessed.
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

- Chronological Table of Private and Personal Acts and Chronological Table of Local Acts, legislation.gov.uk (https://www.legislation.gov.uk/changes/chron-tables/private, https://www.legislation.gov.uk/changes/chron-tables/local). Crown copyright, Open Government Licence v3.0. Contains public sector information licensed under the Open Government Licence v3.0.
- Wikidata places with coordinates and historic county. CC0.
- Coastline from modern county outlines; Natural Earth (public domain) for neighbouring land.
- Hillshade tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Fencing the commons: mapping parliamentary enclosure in England and Wales from the Chronological Tables of Acts. Zenodo. https://doi.org/10.5281/zenodo.23873003

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
