"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23873003 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Fencing_the_Commons"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
C, W = R["counties"], R["waves"]

# statements made in words in the paper only
assert R["peaks"]["years_over_100"] == [1801, 1809, 1810, 1811, 1812, 1813, 1814]                 # "every year from 1809 to 1814"
assert W["war"]["waste_pct"] <= W["w1"]["waste_pct"] and W["war"]["multi_pct"] > W["w1"]["multi_pct"]
assert R["source"]["ireland"] == 10                                                                 # "Ten Acts for Irish counties"
assert max(C[c]["median_year"] for c in ("Leicestershire", "Northamptonshire")) < min(C[c]["median_year"] for c in ("Norfolk", "Devon"))
assert R["twice"]["three"] > 10


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


rows = "".join(f"{tex(SHORT.get(r['county'], r['county']))} & {r['private']:,} & {r['local']:,} & {r['area_km2']:,.0f} & {r['per100_private']:.2f} & {r['first'] or ''} & {r['median_year'] or ''} & {r['last'] or ''} & {'' if r['war_pct'] is None else round(r['war_pct'])}\\\\\n"
               for r in sorted(C.values(), key=lambda r: -r["per100_private"]))
TC = ("{\\footnotesize\\setlength{\\tabcolsep}{4pt}\\begin{longtable}{lrrrrrrrr}\\caption{Enclosure Acts by historic county, ordered by private Acts per 100 km$^2$. Area from the rebuilt boundaries; first, middle and last year of all Acts; share of all Acts in the war years.}\\label{tab:counties}\\\\"
      "\\toprule County & Private & Local & km$^2$ & Per 100 km$^2$ & First & Middle & Last & War \\%\\\\\\midrule\\endfirsthead\\toprule County & Private & Local & km$^2$ & Per 100 km$^2$ & First & Middle & Last & War \\%\\\\\\midrule\\endhead\n" + rows +
      "\\bottomrule\\end{longtable}}")
g = R["geo"]; H = g["how"]
lab = [("exact", "Exact name in the county"), ("part", "Parish or main name of a compound"), ("close", "Close spelling in the county"), ("neighbour", "Ambiguous, settled by a neighbour"), ("other county", "Unique name just over a county boundary"), ("ambiguous", "Ambiguous, left unmatched"), ("none", "Not found")]
rows = "".join(f"{t} & {H.get(k, 0):,} & {100 * H.get(k, 0) / g['places']:.1f}\\%\\\\\n" for k, t in lab)
TG = ("\\begin{table}[tbp]\\centering\\small\\caption{How the named places of enclosure Acts were matched to the gazetteer.}\\label{tab:geo}"
      "\\begin{tabular}{lrr}\\toprule Match & Places & Share\\\\\\midrule\n" + rows + f"\\midrule All named places & {g['places']:,} & 100\\%\\\\\n\\bottomrule\\end{{tabular}}\\end{{table}}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|meta\.doi)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("COUNTIES", TC), ("GEO", TG)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
