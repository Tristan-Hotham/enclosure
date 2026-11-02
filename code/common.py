"""Shared paths, county names and helpers for the enclosure project.

Raw inputs (read in place, never modified):
  raw/chron_private_rows.json   Chronological Table of Private and Personal Acts, legislation.gov.uk, parts 1 to 33
                                (1539 to 1987), as {url: {title, rows: ["H2\\t<heading>", "H3\\t<act line>", ...]}}.
                                Crown copyright, Open Government Licence v3.0.
  raw/chron_local_rows.json     Chronological Table of Local Acts, legislation.gov.uk, same format, 185 of its 187 pages
                                (pages 3 and 27, the parts for 1802 to 1803 and for 1841, timed out when collected).
                                Only the headings and the rows mentioning inclosure were kept. OGL v3.0.
  raw/uk_places_wikidata.tsv    About 49,500 UK places from Wikidata (CC0): item, English label, coordinate, type,
                                historic county (P7959) and the place it is located in.
  /home/claude/newdata/raw/geo/counties_uk.geojson, uk_topo.json   modern county and country outlines (used for the coast,
                                the England and Wales outline, and to place Cornish villages that lack a historic county)
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("EN_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("EN_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("EN_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("ENTMP", "/dev/shm/enclosure"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "enclosure"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23873003"                # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/enclosure/"          # filled in by the publisher
LEG_URL = "https://www.legislation.gov.uk/changes/chron-tables/private"
LOC_URL = "https://www.legislation.gov.uk/changes/chron-tables/local"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

WAR = (1793, 1815)             # Britain at war with Revolutionary and Napoleonic France, February 1793 to 1815
FIRST_WAVE = (1760, 1779)      # the first wave as usually described (the 1760s and 1770s)

# Historic counties of England and Wales, as Wikidata's P7959 labels them, with the nation used for counting.
# Monmouthshire is counted with Wales here (it is in Wales today); the paper says so.
ENGLAND = ["Bedfordshire", "Berkshire", "Buckinghamshire", "Cambridgeshire", "Cheshire", "Cornwall", "Cumberland",
           "Derbyshire", "Devon", "Dorset", "County Durham", "Essex", "Gloucestershire", "Hampshire", "Herefordshire",
           "Hertfordshire", "Huntingdonshire", "Kent", "Lancashire", "Leicestershire", "Lincolnshire", "Middlesex",
           "Norfolk", "Northamptonshire", "Northumberland", "Nottinghamshire", "Oxfordshire", "Rutland", "Shropshire",
           "Somerset", "Staffordshire", "Suffolk", "Surrey", "Sussex", "Warwickshire", "Westmorland", "Wiltshire",
           "Worcestershire", "Yorkshire"]
WALES = ["Anglesey", "Brecknockshire", "Caernarfonshire", "Cardiganshire", "Carmarthenshire", "Denbighshire",
         "Flintshire", "Glamorgan", "Merionethshire", "Monmouthshire", "Montgomeryshire", "Pembrokeshire", "Radnorshire"]
COUNTIES = ENGLAND + WALES
NATION = {c: ("England" if c in ENGLAND else "Wales") for c in COUNTIES}
SHORT = {"County Durham": "Durham"}   # display name

# How the chronological tables write each county (lower case, punctuation dropped) -> historic county.
CTY_ALIAS = {
    "bedford": "Bedfordshire", "beds": "Bedfordshire", "berks": "Berkshire", "berkshire": "Berkshire", "bucks": "Buckinghamshire",
    "buckingham": "Buckinghamshire", "cambridge": "Cambridgeshire", "cambs": "Cambridgeshire", "isle of ely": "Cambridgeshire",
    "ely": "Cambridgeshire", "chester": "Cheshire", "cheshire": "Cheshire", "cornwall": "Cornwall", "cumberland": "Cumberland",
    "derby": "Derbyshire", "derbys": "Derbyshire", "devon": "Devon", "devonshire": "Devon", "dorset": "Dorset", "dorsetshire": "Dorset",
    "durham": "County Durham", "county of durham": "County Durham", "essex": "Essex", "gloucester": "Gloucestershire",
    "glos": "Gloucestershire", "gloucs": "Gloucestershire", "southampton": "Hampshire", "county of southampton": "Hampshire",
    "hants": "Hampshire", "hampshire": "Hampshire", "isle of wight": "Hampshire", "hereford": "Herefordshire", "herefordshire": "Herefordshire",
    "hertford": "Hertfordshire", "herts": "Hertfordshire", "huntingdon": "Huntingdonshire", "hunts": "Huntingdonshire",
    "kent": "Kent", "lancaster": "Lancashire", "lancs": "Lancashire", "lancashire": "Lancashire", "leicester": "Leicestershire",
    "leics": "Leicestershire", "lincoln": "Lincolnshire", "lincs": "Lincolnshire", "middlesex": "Middlesex", "middx": "Middlesex",
    "norfolk": "Norfolk", "northampton": "Northamptonshire", "northants": "Northamptonshire", "northumberland": "Northumberland",
    "nottingham": "Nottinghamshire", "notts": "Nottinghamshire", "oxford": "Oxfordshire", "oxon": "Oxfordshire", "rutland": "Rutland",
    "rutlandshire": "Rutland", "salop": "Shropshire", "shropshire": "Shropshire", "somerset": "Somerset", "somersetshire": "Somerset",
    "stafford": "Staffordshire", "staffs": "Staffordshire", "suffolk": "Suffolk", "surrey": "Surrey", "sussex": "Sussex",
    "warwick": "Warwickshire", "warwicks": "Warwickshire", "westmorland": "Westmorland", "westmoreland": "Westmorland",
    "wilts": "Wiltshire", "wiltshire": "Wiltshire", "worcester": "Worcestershire", "worcs": "Worcestershire", "york": "Yorkshire",
    "yorks": "Yorkshire", "yorkshire": "Yorkshire",
    "anglesey": "Anglesey", "anglesea": "Anglesey", "brecknock": "Brecknockshire", "brecon": "Brecknockshire", "breconshire": "Brecknockshire",
    "caernarvon": "Caernarfonshire", "carnarvon": "Caernarfonshire", "caernarvonshire": "Caernarfonshire", "carnarvonshire": "Caernarfonshire",
    "caernarfonshire": "Caernarfonshire", "cardigan": "Cardiganshire", "carmarthen": "Carmarthenshire", "caermarthen": "Carmarthenshire",
    "denbigh": "Denbighshire", "flint": "Flintshire", "glamorgan": "Glamorgan", "glamorganshire": "Glamorgan", "merioneth": "Merionethshire",
    "merionethshire": "Merionethshire", "monmouth": "Monmouthshire", "montgomery": "Montgomeryshire", "pembroke": "Pembrokeshire",
    "radnor": "Radnorshire",
}
for _c in COUNTIES:
    CTY_ALIAS.setdefault(re.sub(r"[^a-z ]", "", _c.lower()), _c)

# Decade colours for the dots (a warm to cool ramp through the two waves); index = decade bin
DECADES = [(1600, "before 1720"), (1720, "1720s"), (1730, "1730s"), (1740, "1740s"), (1750, "1750s"), (1760, "1760s"), (1770, "1770s"),
           (1780, "1780s"), (1790, "1790s"), (1800, "1800s"), (1810, "1810s"), (1820, "1820s"), (1830, "1830s"), (1840, "after 1840")]
DEC_COL = ["#5B3A29", "#7A4B2A", "#9A5B26", "#B86E22", "#D2861E", "#E3A21A", "#D9BC2B",
           "#9DB548", "#5FA463", "#2E9A8C", "#2C7FA6", "#3A5FA8", "#5A4B9E", "#7B4B8F"]


def dec_bin(y):
    if y < 1720: return 0
    if y >= 1840: return len(DECADES) - 1
    return 1 + (y - 1720) // 10


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    raise ValueError(f)


# Towns labelled on the page map: cities and county towns that already mattered in the eighteenth century (rank 2 shown
# first, then rank 1, then rank 0 as you zoom in). Coordinates come from the gazetteer.
TOWNS = {2: [("London", "Middlesex"), ("Bristol", "Gloucestershire"), ("Norwich", "Norfolk"), ("York", "Yorkshire"), ("Newcastle upon Tyne", "Northumberland"),
             ("Exeter", "Devon"), ("Leicester", "Leicestershire"), ("Nottingham", "Nottinghamshire"), ("Lincoln", "Lincolnshire"), ("Oxford", "Oxfordshire"),
             ("Cambridge", "Cambridgeshire"), ("Birmingham", "Warwickshire"), ("Manchester", "Lancashire"), ("Liverpool", "Lancashire"), ("Leeds", "Yorkshire"),
             ("Shrewsbury", "Shropshire"), ("Gloucester", "Gloucestershire"), ("Carmarthen", "Carmarthenshire"), ("Caernarfon", "Caernarfonshire"),
             ("Carlisle", "Cumberland"), ("Northampton", "Northamptonshire"), ("Ipswich", "Suffolk"), ("Plymouth", "Devon"), ("Southampton", "Hampshire"),
             ("Canterbury", "Kent"), ("Kingston upon Hull", "Yorkshire")],
         1: [("Bedford", "Bedfordshire"), ("Reading", "Berkshire"), ("Aylesbury", "Buckinghamshire"), ("Chester", "Cheshire"), ("Truro", "Cornwall"),
             ("Derby", "Derbyshire"), ("Dorchester", "Dorset"), ("Durham", "County Durham"), ("Chelmsford", "Essex"), ("Winchester", "Hampshire"),
             ("Hereford", "Herefordshire"), ("Hertford", "Hertfordshire"), ("Huntingdon", "Huntingdonshire"), ("Maidstone", "Kent"), ("Lancaster", "Lancashire"),
             ("Oakham", "Rutland"), ("Taunton", "Somerset"), ("Stafford", "Staffordshire"), ("Guildford", "Surrey"), ("Lewes", "Sussex"), ("Chichester", "Sussex"),
             ("Warwick", "Warwickshire"), ("Coventry", "Warwickshire"), ("Kendal", "Westmorland"), ("Salisbury", "Wiltshire"), ("Worcester", "Worcestershire"),
             ("Sheffield", "Yorkshire"), ("Brecon", "Brecknockshire"), ("Cardigan", "Cardiganshire"), ("Haverfordwest", "Pembrokeshire"), ("Dolgellau", "Merionethshire"),
             ("Denbigh", "Denbighshire"), ("Mold", "Flintshire"), ("Montgomery", "Montgomeryshire"), ("Presteigne", "Radnorshire"), ("Monmouth", "Monmouthshire"),
             ("Cardiff", "Glamorgan"), ("Beaumaris", "Anglesey"), ("Bath", "Somerset"), ("Colchester", "Essex"), ("Portsmouth", "Hampshire"), ("Boston", "Lincolnshire")],
         0: [("Stamford", "Lincolnshire"), ("King's Lynn", "Norfolk"), ("Great Yarmouth", "Norfolk"), ("Bury St Edmunds", "Suffolk"), ("Banbury", "Oxfordshire"),
             ("Lichfield", "Staffordshire"), ("Ludlow", "Shropshire"), ("Wells", "Somerset"), ("Swansea", "Glamorgan"), ("Aberystwyth", "Cardiganshire"),
             ("Wakefield", "Yorkshire"), ("Halifax", "Yorkshire"), ("Doncaster", "Yorkshire"), ("Beverley", "Yorkshire"), ("Scarborough", "Yorkshire"),
             ("Richmond", "Yorkshire"), ("Ripon", "Yorkshire"), ("Hexham", "Northumberland"), ("Berwick-upon-Tweed", "Northumberland"), ("Penrith", "Cumberland"),
             ("Preston", "Lancashire"), ("Leominster", "Herefordshire"), ("Cirencester", "Gloucestershire"), ("Devizes", "Wiltshire"), ("Newbury", "Berkshire"),
             ("Abingdon", "Berkshire"), ("Buckingham", "Buckinghamshire"), ("St Albans", "Hertfordshire"), ("Kettering", "Northamptonshire"), ("Peterborough", "Northamptonshire"),
             ("Ely", "Cambridgeshire"), ("Wisbech", "Cambridgeshire"), ("Grantham", "Lincolnshire"), ("Louth", "Lincolnshire"), ("Newark-on-Trent", "Nottinghamshire"),
             ("Melton Mowbray", "Leicestershire"), ("Market Harborough", "Leicestershire"), ("Rugby", "Warwickshire"), ("Stratford-upon-Avon", "Warwickshire"),
             ("Evesham", "Worcestershire"), ("Bridgwater", "Somerset"), ("Barnstaple", "Devon"), ("Bodmin", "Cornwall"), ("Sherborne", "Dorset"), ("Thetford", "Norfolk"),
             ("Wrexham", "Denbighshire"), ("Welshpool", "Montgomeryshire"), ("Bangor", "Caernarfonshire"), ("Llandovery", "Carmarthenshire"), ("Abergavenny", "Monmouthshire")]}

TOWN_LL = {"Carmarthen": (51.857, -4.312), "Caernarfon": (53.139, -4.273), "Brecon": (51.946, -3.391), "Haverfordwest": (51.801, -4.969),
           "Dolgellau": (52.742, -3.885), "Aberystwyth": (52.414, -4.082), "Abingdon": (51.671, -1.282), "Newark-on-Trent": (53.076, -0.809),
           "Abergavenny": (51.824, -3.017)}


def place_key(s):
    """Name key for gazetteer matching (see 03_geocode.py)."""
    s = norm(s.replace("'", "").replace("\u2019", ""))
    s = re.sub(r"\b(saint|st|s)\b", "st", s)
    s = re.sub(r"\b(upon|super|on)\b", "on", s)
    s = re.sub(r"\b(juxta|near|nigh)\b", "next", s)
    s = re.sub(r"\bthe\b", " ", s)
    s = re.sub(r"\bst (\w+?)s\b", r"st \1", s)                                 # St Mary's -> st mary
    s = re.sub(r"\bkings\b", "king", s)
    return re.sub(r"\s+", " ", s).strip()
