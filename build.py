"""Construit data.json pour le Radar des modèles IA à partir des CSV Epoch AI.

Usage : python3 build.py notable_ai_models.csv frontier_ai_models.csv data.json AAAA-MM-JJ
"""
import csv, json, math, re, sys

csv.field_size_limit(10**9)
notable, frontier, out, updated = sys.argv[1:5]

def load(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

recs = load(notable)
names = {r["Model"] for r in recs}
recs += [r for r in load(frontier) if r["Model"] not in names]

GEN = re.compile(r"generation|chat|text-to-|image-to-|video-to-|speech synthesis|tts|language modeling|autocompletion|summarization|translation|image editing|image completion|code|question answering|coding|instruction", re.I)
SKIP = {"Biology", "Medicine", "Earth science", "Materials science", "Robotics", "Games"}
C = {"United States of America":"US","China":"CN","France":"FR","United Kingdom":"GB","South Korea":"KR","Canada":"CA","Germany":"DE","Australia":"AU","Hong Kong":"HK","Israel":"IL","Singapore":"SG","Japan":"JP","Switzerland":"CH","Finland":"FI","United Arab Emirates":"AE","India":"IN","Austria":"AT","Belgium":"BE","Netherlands":"NL","Saudi Arabia":"SA","Taiwan":"TW","Norway":"NO","Russia":"RU","Spain":"ES","Sweden":"SE","Italy":"IT","Brazil":"BR","Denmark":"DK","Poland":"PL","Ireland":"IE","Vietnam":"VN","Turkey":"TR","Indonesia":"ID","Czech Republic":"CZ","Portugal":"PT"}
A = {"API access":"api","Hosted access (no API)":"hosted","Limited access":"limited","Open weights (unrestricted)":"open","Open weights (restricted use)":"open-r","Open weights (non-commercial)":"open-nc","Unreleased":"unrel"}

def mod(r):
    d, t, s = r.get("Domain") or "", r.get("Task") or "", ""
    if "Language" in d or re.search(r"language|chat|question answering|translation|summar", t, re.I): s += "T"
    if re.search(r"code|coding", t, re.I): s += "C"
    if "Image generation" in d or re.search(r"image generation|text-to-image|image-to-image|image editing|image completion", t, re.I): s += "I"
    if re.search(r"video generation|text-to-video|image-to-video|video-to-video", t, re.I): s += "V"
    if re.search(r"Audio|Speech", d) and re.search(r"generation|synthesis|tts|text-to-speech", t, re.I): s += "A"
    if re.search(r"Vision|Multimodal", d): s += "M"
    return s or "T"

def num(v):
    try:
        x = float(v)
        return 0 if not math.isfinite(x) or x == 0 else float(f"{x:.2g}")
    except (TypeError, ValueError):
        return 0

rows = []
for r in recs:
    date = (r.get("Publication date") or "")[:10]
    if date < "2018" or not GEN.search(r.get("Task") or "") or (r.get("Domain") or "").strip() in SKIP:
        continue
    cty = []
    for c in (r.get("Country (of organization)") or "").split(","):
        c = C.get(c.strip(), c.strip())
        if c and c not in cty:
            cty.append(c)
    p = num(r.get("Parameters"))
    m = re.search(r'https?://[^\s,;"<>]+', r.get("Link") or "")
    link = re.sub(r'[).,;]+$', '', m.group(0)) if m else ""
    rows.append([r["Model"], r.get("Organization") or "", date, ",".join(cty), mod(r),
                 A.get(r.get("Model accessibility") or "", "?"), 1 if r.get("Frontier model") == "True" else 0,
                 int(p) if p else 0, num(r.get("Training compute (FLOP)")), link])

rows.sort(key=lambda x: x[2], reverse=True)
json.dump({"updated": updated, "source": "Epoch AI — Notable & Frontier AI Models (CC BY 4.0)", "rows": rows},
          open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"{len(rows)} modèles écrits dans {out}")
