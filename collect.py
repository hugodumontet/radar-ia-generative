"""Collecte les annonces de la semaine pour le bloc « Sorties de la semaine ».

Usage : python3 -I collect.py sources.json DEBUT FIN candidats.json
  DEBUT et FIN au format AAAA-MM-JJ, inclus.

Garde seulement le titre, le lien, la date et la source de chaque élément
(jamais le texte des articles). Une source en panne est signalée dans le
fichier de sortie sans bloquer les autres.
"""
import datetime as dt
import email.utils
import gzip
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

src_path, debut, fin, out = sys.argv[1:5]
D0, D1 = dt.date.fromisoformat(debut), dt.date.fromisoformat(fin)
UA = {"User-Agent": "radar-ia-generative/1.0 (+https://github.com/hugodumontet/radar-ia-generative)"}
ATOM = "{http://www.w3.org/2005/Atom}"

# Repérage dans les médias : on ne garde que les titres qui parlent d'un modèle.
MOTS = re.compile(r"\b(model|models|LLM|GPT|Gemini|Claude|Llama|Grok|Qwen|DeepSeek|Mistral|Kimi|GLM|MiniMax|Gemma|Phi|Sora|Veo|Imagen|Midjourney|Flux|open[- ]weights?|open[- ]source|releases?|launch(es)?|unveils?|introduces?|debuts?)\b", re.I)
# Comptes Hugging Face : on écarte les variantes techniques et les petits outils.
BRUIT_HF = re.compile(r"(gguf|awq|gptq|fp8|nvfp4|bf16|int4|int8|mlx|onnx|-quant|guard|embedding|reranker|tokenizer|-lora|sae|-draft|eagle)", re.I)

def get(url, essais=2):
    for i in range(essais):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
            if raw[:2] == b"\x1f\x8b":  # certains sites compressent même sans qu'on le demande
                raw = gzip.decompress(raw)
            if url.endswith(".xml") or "/rss" in url or "/feed" in url:
                ET.fromstring(raw)  # une réponse illisible (page d'erreur) déclenche le second essai
            return raw
        except Exception:
            if i == essais - 1:
                raise

def date_de(txt):
    txt = (txt or "").strip()
    if not txt:
        return None
    try:
        return email.utils.parsedate_to_datetime(txt).date()
    except Exception:
        pass
    try:
        return dt.date.fromisoformat(txt[:10])
    except Exception:
        return None

def lire_rss(raw):
    root = ET.fromstring(raw)
    items = []
    for it in root.findall(".//item"):
        items.append((it.findtext("title"), it.findtext("link"),
                      date_de(it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date"))))
    for it in root.findall(f".//{ATOM}entry"):
        lien = it.find(f"{ATOM}link[@rel='alternate']")
        if lien is None:  # un élément XML sans enfant vaut False : pas de « or » ici
            lien = it.find(f"{ATOM}link")
        items.append((it.findtext(f"{ATOM}title"), lien.get("href") if lien is not None else "",
                      date_de(it.findtext(f"{ATOM}published") or it.findtext(f"{ATOM}updated"))))
    return items

def rss(s):
    items, page = [], 1
    while True:
        url = s["url"] if page == 1 else f"{s['url']}{'&' if '?' in s['url'] else '?'}paged={page}"
        try:
            lot = lire_rss(get(url))
        except Exception:
            if page == 1:
                raise
            break
        items += lot
        dates = [d for _, _, d in lot if d]
        # Flux courts : on remonte les pages tant que la semaine n'est pas couverte.
        if not lot or not dates or min(dates) <= D0 or page >= 10:
            break
        page += 1
    return items

def anthropic(s):
    html = get(s["url"]).decode("utf-8", "replace")
    slugs = []
    for slug in re.findall(r'href="/news/([a-z0-9-]+)"', html):
        if slug not in slugs and slug not in {"announcements", "news"}:
            slugs.append(slug)
    items = []
    for slug in slugs[:30]:
        url = f"https://www.anthropic.com/news/{slug}"
        try:
            page = get(url).decode("utf-8", "replace")
        except Exception:
            continue
        m = re.search(r'article:published_time" content="([^"]+)"', page)
        t = re.search(r'<meta property="og:title" content="([^"]+)"', page)
        items.append(((t.group(1) if t else slug).replace("&amp;", "&"), url, date_de(m.group(1)) if m else None))
    return items

def hf(s):
    items = []
    for compte in s["comptes"]:
        # Les labos créent souvent le dépôt en privé puis le rendent public plus tard :
        # la date de création ne suffit pas. On prend les dépôts modifiés pendant la
        # semaine et créés il y a moins de 30 jours (sinon : simple mise à jour d'un ancien modèle).
        raw = get(f"https://huggingface.co/api/models?author={compte}&sort=lastModified&direction=-1"
                  f"&limit=40&expand[]=createdAt&expand[]=lastModified")
        for m in json.loads(raw):
            cree, modif = date_de(m.get("createdAt")), date_de(m.get("lastModified"))
            if BRUIT_HF.search(m["id"]) or not cree or not modif:
                continue
            if D0 <= cree <= D1:
                d = cree
            elif D0 <= modif <= D1 and cree >= D0 - dt.timedelta(days=30):
                d = modif
            else:
                continue
            items.append((m["id"], f"https://huggingface.co/{m['id']}", d))
    return items

LECTEURS = {"rss": rss, "anthropic": anthropic, "hf": hf}
sources = json.load(open(src_path, encoding="utf-8"))["sources"]
candidats, etat = [], []
for s in sources:
    try:
        items = LECTEURS[s["type"]](s)
    except Exception as e:
        etat.append({"source": s["nom"], "ok": False, "erreur": f"{type(e).__name__}: {str(e)[:120]}"})
        continue
    dates = [d for _, _, d in items if d]
    garde = 0
    vus = set()
    for titre, lien, d in items:
        if not d or not (D0 <= d <= D1) or lien in vus:
            continue
        if s["role"] == "reperage" and not MOTS.search(titre or ""):
            continue
        vus.add(lien)
        garde += 1
        candidats.append({"date": d.isoformat(), "source": s["nom"], "role": s["role"],
                          "titre": re.sub(r"\s+", " ", titre or "").strip(), "lien": lien})
    complet = bool(dates) and (min(dates) <= D0 or s["type"] == "hf")
    etat.append({"source": s["nom"], "ok": True, "elements": len(items), "gardes": garde,
                 "plus_ancien": min(dates).isoformat() if dates else None,
                 "semaine_couverte": complet})

candidats.sort(key=lambda c: (c["role"] != "officiel", c["date"]))
json.dump({"debut": debut, "fin": fin, "etat_des_sources": etat, "candidats": candidats},
          open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
ko = [e["source"] for e in etat if not e["ok"]]
partiel = [e["source"] for e in etat if e["ok"] and not e["semaine_couverte"]]
print(f"{len(candidats)} candidats du {debut} au {fin} -> {out}")
if ko:
    print("Sources en panne :", ", ".join(ko))
if partiel:
    print("Semaine pas entièrement couverte :", ", ".join(partiel))
