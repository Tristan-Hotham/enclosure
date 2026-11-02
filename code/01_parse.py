"""Parse the Chronological Tables (private and local) into acts, and keep every act whose title mentions inclosure.

Reading the tables. Each page is a list of rows tagged H2 (headings) or H3 (act lines). Headings are either part
headings ("Part 20 (1783-1794)"), session headings ("1783 (23 Geo. 3).", sometimes with a session number), or the
wrapped tail of a long title. An act line starts with its chapter ("c. 94", "c.94", or for local acts "c.vii"); a title
too long for one row runs on into the next row(s), which carry no chapter. Rows that annotate earlier acts ("see: ...",
"r.- ...", "am.- ...", "saved in pt.- ...", "s. 5 r.- ...") are notes, not acts, and are dropped together with their
own run-on rows. The year of an act is the first calendar year of its session heading.

Which acts. Every act whose title contains a word starting "inclos" or "enclos" (inclosure, inclosures, inclosing,
inclose, enclosure...). Each is then classed:
  * enclosure: a title of the usual form "Place (County) inclosure", including "commons inclosure", "drainage and
    inclosure", "inclosure and tithe exchange" and the like;
  * agreement: an act confirming an inclosure already agreed locally ("confirming an agreement concerning X inclosure");
  * amendment: an act explaining, amending or extending an earlier inclosure act;
  * other: titles that mention inclosing in passing (estate acts, sales, drainage acts with a clause).
The main counts use enclosure + agreement acts ("enclosing acts"); amendments and others are kept and reported.

Places. The text before the first county in brackets is split into places on commas, "and", "with" and "cum" where
these join separate townships, keeping compound names (Great and Little X becomes Great X and Little X; "East and West
Somerton" becomes East Somerton and West Somerton). Alternative spellings ("Hickham or Hykeham") are kept as one place
with alternatives. Local act titles usually give no county."""
import collections
import pandas as pd
from common import *

ROM = re.compile(r"^[ivxlcdm]+$", re.I)
NOTE = re.compile(r"^(see:|see\s|\(c\.|\[\d+\]|(?:r|am|ext|cont|excl|expld|appl|mod|incorp|saved|sch|s|ss|pt|rep|transf|power|savings?|restr|superseded|spent)\b[^A-Z]{0,40}?\.\s?-|s\.\s?\d|ss\.\s?\d|[a-z]+\.(?:in|and)\b)")
CH = re.compile(r"^c\.\s?([0-9]+|[ivxlcdm]+)\b\.?\s*(.*)$", re.I)
SESS = re.compile(r"^(\d{4})(?:\s*[-–/]\s*(\d{2,4}))?(?=\s*(?:\(|$|\.|\s\d|\s*$))")
WORD = re.compile(r"\b(?:in|en)clos\w*", re.I)


def pages(path):
    d = jload(path)
    key = lambda u: int(re.search(r"/(\d+)$", u).group(1))
    return [(key(u), d[u]["rows"]) for u in sorted(d, key=key)], d


def assemble(path, source):
    """Return a list of act dicts with chapter, full title, session heading and year."""
    P, d = pages(path)
    acts, part, sess, year, last = [], "", "", None, None
    n_rows = n_notes = 0
    for pg, rows in P:
        for r in rows:
            n_rows += 1
            tag, x = (r.split("\t", 1) + [""])[:2]
            x = re.sub(r"\s+", " ", x).strip()
            if not x:
                continue
            if tag == "H2":
                m = SESS.match(x)
                if m and 1500 < int(m.group(1)) < 2000:
                    year, sess, last = int(m.group(1)), x, None
                    continue
                if re.search(r"Part\s?\d+\s*\(", x) or x.startswith("Acts of the Parliaments"):
                    pm = re.search(r"Part\s?(\d+)\s*\(([^)]*)\)", x)
                    if pm: part = f"Part {pm.group(1)} ({pm.group(2).strip()})"
                    last = None
                    continue
                if re.match(r"^\d\.\s", x):        # editorial footnote ("1. The date of the Royal Assent ...")
                    last = None
                    continue
                if last is not None:
                    last["title"] += " " + x       # run-on text that the page tagged as a heading
                continue
            m = CH.match(x)
            if m and (source == "private" or ROM.match(m.group(1))):
                last = {"source": source, "page": pg, "part": part, "session": sess, "year": year, "chapter": m.group(1).lower() if ROM.match(m.group(1)) and source == "local" else m.group(1),
                        "title": m.group(2), "row": n_rows}
                acts.append(last)
                continue
            if NOTE.match(x):
                n_notes += 1
                last = {"note": True, "title": x}  # notes swallow their own run-on rows
                continue
            if last is not None and not last.get("note") and not last["title"].rstrip().endswith((".", ".*")):
                last["title"] += " " + x
            elif last is not None and last.get("note"):
                last["title"] += " " + x
            elif source == "private" and x[:1].isupper():
                last = {"source": source, "page": pg, "part": part, "session": sess, "year": year, "chapter": "", "title": x, "row": n_rows}
                acts.append(last)                  # an act listed without a chapter number (early tables)
    for a in acts:
        a["title"] = re.sub(r"\s+", " ", a["title"]).replace(" ,", ",").replace("( ", "(").replace(" )", ")").strip()
    return acts, {"pages": len(P), "rows": n_rows, "notes": n_notes}


priv, cp = assemble(f"{RAW}/chron_private_rows.json", "private")
loc, cl = assemble(f"{RAW}/chron_local_rows.json", "local")
chk = {"private": cp, "local": cl, "private_acts_all": len(priv), "local_acts_listed": len(loc)}
raw_private_mentions = sum(1 for u, v in jload(f"{RAW}/chron_private_rows.json").items() for r in v["rows"] if re.search(r"(?:in|en)clos", r, re.I))
chk["private_rows_mentioning"] = raw_private_mentions
assert all(a["year"] for a in priv + loc)

# ---------- classify ----------
AMEND_START = re.compile(r"^(amend\w*|explanation|explaining|enlarging|rendering (?:more )?(?:effectual|valid)|removing doubts|validating|partial repeal|repeal\w*|reviving|continuing)\b", re.I)
AMEND_IN = re.compile(r"\b(?:in|en)closures?(?: act)?\s*(?::|,)?\s*(?:amending|explaining|enlarging|rendering|repeal\w*|removing doubts|amendment|continuance|explanation)\b|\b(?:in|en)closures?(?: act)?\s+(?:amendment|continuance)\b|:\s*(?:amending|repeal of) the (?:in|en)closure|^[^:]*:\s*amending\b", re.I)
ORDER = re.compile(r"prov\w*ional orders?|^annual inclosure|^second annual inclosure", re.I)


def classify(t, src):
    if not WORD.search(t):
        return None
    if ORDER.search(t):
        return "order"            # confirmations of Inclosure Commissioners' orders under the general Acts (local table only)
    if AMEND_START.search(t) or AMEND_IN.search(t):
        return "amendment"
    if re.search(r"\bagreement\b|\bagreed\b|\barticles\b", t, re.I) and re.search(r"(confirm|establish|effectual)", t, re.I):
        return "agreement"
    if re.search(r"company|preservation|squares", t, re.I) or re.match(r"^(Settlement of lands|Making the site)", t):
        return "other"
    if re.search(r"\b(?:in|en)closures?\b", t, re.I) and not re.search(r"(?:'s|s') (?:settled )?estates?\b|\bestate\b.*?:", t):
        return "enclosure"
    if re.search(r"\b(divide|dividing|division|divisions)\b.*\b(inclos|enclos)", t, re.I) or re.search(r"\b(inclos\w*|enclos\w*) and (divid|allot)", t, re.I):
        return "enclosure"
    return "other"


for a in priv + loc:
    a["kind"] = classify(a["title"], a["source"])
A = [a for a in priv + loc if a["kind"]]
chk["kinds_private"] = dict(collections.Counter(a["kind"] for a in A if a["source"] == "private"))
chk["kinds_local"] = dict(collections.Counter(a["kind"] for a in A if a["source"] == "local"))
chk["allotment_only_private"] = sum(1 for a in priv if not a["kind"] and re.search(r"\ballot", a["title"], re.I) and re.search(r"\((?:[^()]*)\)", a["title"]))

# ---------- county and places ----------
import difflib
IRELAND = {"dublin", "county dublin", "kildare", "kerry", "kilkenny", "tipperary", "limerick", "cork", "meath", "wicklow", "louth",
           "wexford", "carlow", "galway", "mayo", "antrim", "down", "armagh", "tyrone", "londonderry", "fermanagh", "donegal",
           "westmeath", "longford", "roscommon", "sligo", "leitrim", "cavan", "monaghan", "clare", "waterford", "queen s county",
           "king s county", "ireland"}
SCOTLAND = {"scotland", "fife", "perth", "aberdeen", "argyll", "ayr", "lanark", "edinburgh", "midlothian", "berwick", "roxburgh",
            "dumfries", "inverness", "forfar", "stirling", "renfrew", "banff", "kincardine", "moray", "elgin"}
TOWN_CTY = {"kingston upon hull": "Yorkshire", "hull": "Yorkshire", "york": "Yorkshire"}


def one_county(p):
    p = re.sub(r"[^a-z ]", " ", p.lower()); p = re.sub(r"\s+", " ", p).strip()
    p = re.sub(r"^(the )?county of ", "", p)
    if not p: return None
    if p in CTY_ALIAS: return CTY_ALIAS[p]
    if p.endswith("shire") and p[:-5].strip() in CTY_ALIAS: return CTY_ALIAS[p[:-5].strip()]
    if p in IRELAND or p.replace("county ", "") in IRELAND: return "Ireland"
    if p in SCOTLAND: return "Scotland"
    if len(p) >= 6:
        m = difflib.get_close_matches(p, [k for k in CTY_ALIAS if k.endswith("shire")], n=1, cutoff=.88) if p.endswith("shire") else []   # typos: Northamptoshire, Notttinghamshire
        if m: return CTY_ALIAS[m[0]]
    return None


def county_of(s):
    """'Yorkshire, West Riding' -> (['Yorkshire'], 'West Riding', []); 'Salop., Staffordshire' -> (['Shropshire', 'Staffordshire'], '', []);
    'Kildwick, Yorkshire' -> (['Yorkshire'], '', ['Kildwick']). Returns (None, '', []) if no part is a county."""
    out, riding, local = [], "", []
    s = re.sub(r"\b(east|west|north)\s+and\s+(east|west|north)\s+ridings?", r"\1 riding", s, flags=re.I)
    for part in re.split(r",|\band\b|;|&|\bor\b", s):
        q = part.strip(" .")
        if not q: continue
        m = re.search(r"\b(east|west|north) riding\b", q, re.I)
        if m:
            riding = m.group(1).title() + " Riding"
            q = re.sub(r"\b(east|west|north) riding( of)?", "", q, flags=re.I).strip(" .")
            if not q or q.lower().startswith("york"):
                if "Yorkshire" not in out: out.append("Yorkshire")
                continue
        c = one_county(q)
        if c:
            if c not in out: out.append(c)
        elif q.lower() in TOWN_CTY:
            out.append(TOWN_CTY[q.lower()]); local.append(q)
        else:
            local.append(q)
    return (out or None), riding, local


SPLIT_WORDS = r"\s*,\s*(?:and\s+)?|\s+and\s+|\s*&\s*"
PRE = r"(Great|Little|East|West|North|South|Upper|Lower|Over|Nether|High|Low|Old|New|Much|Long|Kings?|King's|Bishops?|Abbots?|Church|Chipping|Steeple|Market|Monks?)"


def split_places(s):
    """Split the place text of a title into places. Returns a list of (name, [alternatives])."""
    s = re.sub(r"\s*\((?:[^()]*)\)\s*", " ", s).strip()     # drop inner brackets ("Hook (Snaith)") for splitting
    s = re.sub(r"\s*\[[^\]]*\]\s*", " ", s).strip()
    s = re.sub(r",?\s*&c\.?", "", s)
    toks = [t for t in re.split(SPLIT_WORDS, s) if t and t.strip(" .")]
    out, i = [], 0
    while i < len(toks):
        t = re.sub(r"^(?:or|and)\s+", "", toks[i].strip(" .;:"))
        nxt = toks[i + 1].strip() if i + 1 < len(toks) else ""
        if re.fullmatch(PRE, t, re.I) and nxt:      # "Great and Little Cressingham", "East and West Somerton"
            m2 = re.match(PRE + r"\s+(.+)$", nxt, re.I)
            if m2:
                out.append((f"{t} {m2.group(2)}".strip(" ."), [])); out.append((nxt.strip(" .;:"), [])); i += 2; continue
        if t:
            alts = [a.strip(" .") for a in re.split(r"\s+(?:or|otherwise|alias)\s+", t) if a.strip(" .")]
            if alts: out.append((alts[0], alts[1:]))
        i += 1
    clean = []
    for nm, alts in out:
        nm = re.sub(r"\s+", " ", nm).strip(" .,;:'")
        nm = re.sub(r"^(?:the\s+)?(?:parish(?:es)?|township|manor|hamlet|lordship|liberty)\s+of\s+", "", nm, flags=re.I)
        nm = re.sub(r"\s+(?:in|en)closures?$", "", nm, flags=re.I)
        nm = re.sub(r"\s+(?:in the parish of|in the county of|within the parish of)\b.*$", "", nm, flags=re.I)
        if len(nm) >= 3 and nm[:1].isupper() and not re.search(r"\b(drainage|allotments?|embank\w*|poor rates?|poor relief|tithes?)\b", nm, re.I) \
                and not re.fullmatch(r"(?:others?|other places|elsewhere|several parishes|the same|lands?)", nm, re.I):
            clean.append((nm, alts))
    return clean


VERB = re.compile(r"^(?:[A-Z][a-z]+ing\s+(?!(?:and|with|cum|upon|on|in|under|next|by|juxta|le|de|super|or)\b)(?=[a-z])|Appointment|Declaration|Confirm\w*|Confirmation|Establish\w*|Enabling|Empowering|Amend\w*|Rendering|Removing|Validating|Making|Exchange|Ascertaining|Explain\w*|Explanation|"
                  r"Enlarging|Appointing|Assigning|Regulating|Dividing|Inclosing|Enclosing|For|Partial|Repeal\w*|Settlement|Settling|Vesting|Allotting|Inclosure of|Enclosure of|Allotment)\b")
CONNECT = re.compile(r"\b(?:concerning|under the|lands? (?:in|of|within|at|called)|grounds? (?:in|of|called)|inclosures? (?:made )?(?:in|of)|inclos\w* (?:certain )?(?:lands |grounds |the [a-z ]+ )?(?:in|of|within)|"
                     r"completion of|effectual|establishing|fields? (?:in|of)|commons? (?:in|of)|wastes? (?:in|of)|manors? of|parish(?:es)? of|township of|for inclosing|inclosing|award for inclosing|for|in|of)\s+(?=[A-Z])")


def tidy_head(h):
    h = h.strip(" ,.;:")
    h = re.sub(r"^(?:(?:of|for|the|in|and|within)\s+)+(?=[A-Z])", "", h)
    if VERB.match(h) or (h[:1].islower()):
        ms = list(CONNECT.finditer(h))
        if ms: h = h[ms[-1].end():]
        elif h[:1].islower(): return ""
        else: return ""
    return h.strip(" ,.;:")


def places_of(a):
    t = a["title"].replace("[", "(").replace("]", ")")
    t = re.sub(r"\)(?=[A-Za-z])", ") ", re.sub(r"(?<=[a-z])\)(?=[A-Z][a-z]+shire)", ") (", t))
    t = re.sub(r"(?<=[a-z]) ([A-Z][a-z]+shire)\)", r" (\1)", t) if not re.search(r"\([^)]*shire\)", t) else t
    county, riding, head, tail, local = None, "", None, "", []
    for m in re.finditer(r"\(([^()]+)\)", t):
        c, rd, lc = county_of(m.group(1))
        if c:
            county, riding, head, tail, local = c, rd, t[:m.start()], t[m.end():], lc
            break
    if head is None:
        m = re.search(r"\s+(?:commons?\s+|wastes?\s+|open fields\s+|fields\s+|moors?\s+|marsh\s+|heath\s+|drainage\s+and\s+|lands\s+)?(?:(?:in|en)closures?|drainage|allotment|embankment)\b", t, re.I)
        head = t[:m.start()] if m else ""
    pieces = [tidy_head(x) for x in re.split(r"\b(?:in|en)closures?\b,?(?:\s+and\s+(?:allotment|division)s? of lands in)?", head, flags=re.I)]
    ps = []
    for x in pieces:
        if x: ps += split_places(x)
    # a place written after the county ("Framwelgate (Durham) and Witton-Gilbert inclosure") shares it
    m = re.match(r"^\s*(?:,\s*|and\s+)+([A-Z][^()]*?)\s+(?:(?:in|en)closures?|commons|drainage)\b", tail)
    if m and county:
        ps += split_places(m.group(1))
    # a county named as the place itself ("Staffordshire Inclosure", "Salop. Inclosures") is a county-wide act
    if not county:
        keep = []
        for nm, alts in ps:
            c = one_county(nm) if (nm.endswith("shire") or nm in COUNTIES or nm in ("Salop", "Salop.")) else None
            if c and c not in ("Ireland", "Scotland") and len(ps) <= 2: county = [c]
            else: keep.append((nm, alts))
        ps = keep
    seen, uniq = set(), []
    for nm, alts in ps:
        if nm.lower() not in seen: seen.add(nm.lower()); uniq.append((nm, alts))
    return county, riding, uniq, local


rows = []
for k, a in enumerate(A):
    a["id"] = k
    c, rd, ps, lc = places_of(a)
    a["within"] = lc
    a["county"] = c[0] if c else None
    a["counties"] = c or []
    a["riding"] = rd
    a["places"] = ps
    a["n_places"] = len(ps)
df = pd.DataFrame(A)
df["nation"] = df.county.map(lambda c: NATION.get(c, c) if c else None)
chk["ireland_private"] = int((df.nation == "Ireland").sum()); chk["scotland_private"] = int((df.nation == "Scotland").sum())
chk["enclosing_private"] = int(((df.source == "private") & df.kind.isin(["enclosure", "agreement"])).sum())
chk["enclosing_local"] = int(((df.source == "local") & df.kind.isin(["enclosure", "agreement"])).sum())
chk["no_county_private_enclosing"] = int(((df.source == "private") & df.kind.isin(["enclosure", "agreement"]) & df.county.isna()).sum())
chk["no_places"] = int((df.n_places == 0).sum())
df.to_pickle(f"{WORK}/acts.pkl")
jsave(chk, f"{WORK}/checks_parse.json", indent=1)
print(json.dumps(chk, indent=1))
print(df.groupby(["source", "kind"]).size())
