"""Construit data.json, la base du Radar des modèles IA, à partir de plusieurs sources.

Usage :
  python3 -I build.py all_ai_models.csv notable_ai_models.csv models.json openrouter.json \
      sorties.json alias.json labos.json data.json AAAA-MM-JJ

Sources (une seule ligne par modèle, dans cet ordre de priorité) :
  1. Epoch AI, fichier complet « all_ai_models » (CC BY 4.0) : base et historique.
  2. sorties.json : annonces officielles retenues par la tâche du vendredi.
  3. models.dev (MIT) : modèles disponibles dès leur sortie, labos suivis seulement.
  OpenRouter ne crée aucune ligne : il sert seulement à savoir si un modèle est utilisable par le public.

Critère d'entrée d'un modèle Epoch (au moins un des trois) :
  - il vient d'un labo suivi (labos.json) ;
  - il est utilisable par le public (présent sur models.dev ou OpenRouter) ;
  - Epoch le classe « notable ».
Sont exclues les versions retravaillées par un autre labo à partir d'un modèle existant
(champ « Base model » d'Epoch), sauf si Epoch les classe notables.

Pays et fournisseur : la première valeur est le fournisseur principal ; le radar ne filtre que sur elle.
Format d'une ligne : [nom, fournisseurs, date, pays, modalités, accès, frontier, paramètres,
calcul, lien, source] avec source = "e" (Epoch), "o" (annonce officielle), "m" (models.dev).
"""
import csv, json, math, re, sys

csv.field_size_limit(10**9)
if len(sys.argv) != 10:
    # Ancien appel (avant la v23 : build.py notable.csv frontier.csv data.json D) : on ne touche à rien.
    sys.exit("build.py attend 9 arguments depuis la v23 : data.json n'a pas été modifié. "
             "Les consignes de la tâche du vendredi sont à mettre à jour (doc claude/consignes-tache-vendredi.md du projet).")
(all_p, notable_p, md_p, or_p, sorties_p, alias_p, labos_p, out, updated) = sys.argv[1:10]

GEN = re.compile(r"generation|chat|text-to-|image-to-|video-to-|speech synthesis|tts|language modeling|autocompletion|summarization|translation|image editing|image completion|code|question answering|coding|instruction", re.I)
SKIP = {"Biology", "Medicine", "Earth science", "Materials science", "Robotics", "Games"}
C = {"United States of America":"US","China":"CN","France":"FR","United Kingdom":"GB","South Korea":"KR","Canada":"CA","Germany":"DE","Australia":"AU","Hong Kong":"HK","Israel":"IL","Singapore":"SG","Japan":"JP","Switzerland":"CH","Finland":"FI","United Arab Emirates":"AE","India":"IN","Austria":"AT","Belgium":"BE","Netherlands":"NL","Saudi Arabia":"SA","Taiwan":"TW","Norway":"NO","Russia":"RU","Spain":"ES","Sweden":"SE","Italy":"IT","Brazil":"BR","Denmark":"DK","Poland":"PL","Ireland":"IE","Vietnam":"VN","Turkey":"TR","Indonesia":"ID","Czech Republic":"CZ","Portugal":"PT"}
A = {"API access":"api","Hosted access (no API)":"hosted","Limited access":"limited","Open weights (unrestricted)":"open","Open weights (restricted use)":"open-r","Open weights (non-commercial)":"open-nc","Unreleased":"unrel"}
# Variantes de models.dev qui doublonnent un modèle déjà listé (alias « latest », instantanés datés).
VARIANTE = re.compile(r"\(latest\)|-latest$|\b(19|20)\d{2}(\d{2})?\b$|\b\d{2}\.\d{2}\b|\b\d{4}$|\b\d{2}-\d{2}$|\(\d{4}-\d{2}-\d{2}\)"
                      r"|highspeed|ultraspeed|\(fast\)|custom tools", re.I)
# Modèles qui ne génèrent pas de contenu (recherche, modération, transcription) : hors radar.
NON_GEN = re.compile(r"embed|rerank|guard|safety|moderation|transcri|whisper|\bstt\b", re.I)
# models.dev ne sert qu'à la fraîcheur : il n'ajoute que les sorties à partir de cette date.
# L'historique reste celui d'Epoch (sinon doublons d'écriture : « Claude Sonnet 3.7 » / « Claude 3.7 Sonnet »).
MD_DEPUIS = "2026-10-01"

def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def load_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_json(p, defaut):
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        print(f"Attention : {p} illisible, source ignorée")
        return defaut

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

def premier(s):
    return (s or "").split(",")[0].strip()

# ---------- Données d'appui ----------
labos = load_json(labos_p, {"labos": []})["labos"]
LAB_EPOCH = {n: l for l in labos for n in l["epoch"]}
LAB_NOM = {norm(l["nom"]): l for l in labos} | {norm(n): l for l in labos for n in l["epoch"]}
def labo_prefixe(id_, cle):
    p = id_.split("/")[0].lstrip("~")
    return next((l for l in labos if p in l[cle]), None)

alias = load_json(alias_p, {"alias": {}}).get("alias", {})

md_raw = load_json(md_p, {})
md = [v for v in (md_raw.values() if isinstance(md_raw, dict) else md_raw) if isinstance(v, dict) and v.get("name")]
orr = load_json(or_p, {"data": []}).get("data", [])

def cles(nom, four=""):
    """Toutes les écritures possibles d'un nom, pour retrouver un modèle d'une source à l'autre."""
    n = norm(nom)
    out = {n, norm(re.sub(r"\([^)]*\)", "", nom))}
    # « Preview » n'est pas retiré : chez Epoch, la préversion et la version finale sont deux sorties.
    out |= {re.sub(r"(instruct|it|chat)+$", "", x) for x in list(out)}
    f = norm((four or "").split()[0]) if four else ""
    if f:
        out |= {x[len(f):] for x in list(out) if x.startswith(f) and len(x) > len(f)}
    for a in alias.get(nom, []):
        out.add(norm(a))
    out.discard("")
    return out

PUBLIC = set()
for m in md:
    PUBLIC |= cles(m["name"])
for m in orr:
    nom = m.get("name", "").split(": ", 1)[-1]
    PUBLIC |= cles(nom)

# ---------- 1. Epoch ----------
recs = load_csv(all_p)
notables = {r["Model"] for r in load_csv(notable_p)}
org_de = {r["Model"]: premier(r.get("Organization")) for r in recs}
EPOCH_CLES = set()  # tout ce qu'Epoch connaît, même hors radar : une autre source ne le rajoute pas
for r in recs:
    EPOCH_CLES |= cles(r["Model"], premier(r.get("Organization")))

rows, vus = [], set()
compte = {"labo": 0, "public": 0, "notable": 0, "derive": 0}
for r in recs:
    date = (r.get("Publication date") or "")[:10]
    org1 = premier(r.get("Organization"))
    # Une fiche toute fraîche d'un labo suivi n'a souvent pas encore sa tâche : on la garde.
    frais = not (r.get("Task") or "").strip() and org1 in LAB_EPOCH and date >= "2025"
    if date < "2018" or (r.get("Domain") or "").strip() in SKIP or not (frais or GEN.search(r.get("Task") or "")):
        continue
    if NON_GEN.search(r["Model"]):
        continue
    notable = r["Model"] in notables or bool((r.get("Notability criteria") or "").strip())
    labo = org1 in LAB_EPOCH
    public = bool(cles(r["Model"], org1) & PUBLIC)
    if not (labo or public or notable):
        continue
    base = (r.get("Base model") or "").strip()
    if base and not notable and org_de.get(base) and org_de[base] != org1:
        compte["derive"] += 1
        continue
    compte["notable" if notable else "labo" if labo else "public"] += 1
    cty = []
    for c in (r.get("Country (of organization)") or "").split(","):
        c = C.get(c.strip(), c.strip())
        if c and c not in cty:
            cty.append(c)
    if not cty and labo:
        cty = [LAB_EPOCH[org1]["pays"]]
    p = num(r.get("Parameters"))
    m = re.search(r'https?://[^\s,;"<>]+', r.get("Link") or "")
    link = re.sub(r'[).,;]+$', '', m.group(0)) if m else ""
    rows.append([r["Model"], r.get("Organization") or "", date, ",".join(cty), mod(r),
                 A.get(r.get("Model accessibility") or "", "?"), 1 if r.get("Frontier model") == "True" else 0,
                 int(p) if p else 0, num(r.get("Training compute (FLOP)")), link, "e"])
    vus |= cles(r["Model"], org1)
n_epoch = len(rows)

# Accès connu par models.dev (utile pour les lignes qui ne viennent pas d'Epoch).
ACCES_MD = {}
for m in md:
    for k in cles(m["name"]):
        ACCES_MD.setdefault(k, "open" if m.get("open_weights") else "api")

def mods_md(m):
    mo = m.get("modalities") or {}
    out_, in_ = mo.get("output") or [], mo.get("input") or []
    s = ""
    if "text" in out_: s += "T"
    if re.search(r"code|coder|codestral|devstral", m["name"] + " " + (m.get("family") or ""), re.I): s += "C"
    if "image" in out_: s += "I"
    if "video" in out_: s += "V"
    if "audio" in out_: s += "A"
    if "image" in in_ and "T" in s: s += "M"
    return s or "T"

# ---------- 2. Annonces officielles retenues le vendredi ----------
n_off = 0
for s in load_json(sorties_p, {"sorties": []}).get("sorties", []):
    k = cles(s["nom"], s.get("fournisseur", ""))
    if k & (vus | EPOCH_CLES) or (s.get("date") or "") < "2018":
        continue
    lab = LAB_NOM.get(norm(s.get("fournisseur"))) or LAB_NOM.get(norm(premier(s.get("fournisseur"))))
    acc = next((ACCES_MD[x] for x in k if x in ACCES_MD), "?")
    rows.append([s["nom"], s.get("fournisseur", ""), s["date"], lab["pays"] if lab else "",
                 s.get("modalites") or "T", acc, 0, 0, 0, s.get("lien", ""), "o"])
    vus |= k
    n_off += 1

# ---------- 3. models.dev (labos suivis seulement) ----------
n_md = 0
for m in sorted(md, key=lambda x: x.get("release_date") or ""):
    lab = labo_prefixe(m.get("id", ""), "md")
    date = (m.get("release_date") or "")
    if (not lab or len(date) < 10 or date < MD_DEPUIS or NON_GEN.search(m["name"])
            or VARIANTE.search(m["name"]) or VARIANTE.search(m.get("id", ""))):
        continue
    k = cles(m["name"], lab["nom"])
    if k & (vus | EPOCH_CLES):
        continue
    rows.append([m["name"], lab["nom"], date[:10], lab["pays"], mods_md(m),
                 "open" if m.get("open_weights") else "api", 0, 0, 0, "", "m"])
    vus |= k
    n_md += 1

rows.sort(key=lambda x: x[2], reverse=True)
json.dump({"updated": updated,
           "source": "Epoch AI — AI Models (CC BY 4.0) ; annonces officielles des labos ; models.dev (MIT)",
           "rows": rows},
          open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"{len(rows)} modèles écrits dans {out} : {n_epoch} Epoch "
      f"(notables {compte['notable']}, labos suivis {compte['labo']}, utilisables par le public {compte['public']}, "
      f"{compte['derive']} dérivés écartés), {n_off} annonces officielles, {n_md} models.dev")
