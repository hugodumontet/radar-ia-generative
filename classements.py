"""Classements par usage du Radar des modèles IA.

Lit le jeu de données officiel d'Arena (LMArena) sur Hugging Face
(lmarena-ai/leaderboard-dataset, licence CC BY 4.0) via l'API JSON de
Hugging Face, sans dépendance externe, et écrit classements.json.

Usage : python3 -I classements.py classements.json

Règles :
- seule la publication Arena la plus récente de chaque usage est gardée ;
- un modèle doit avoir au moins MIN_VOTES votes (sinon le classement est du bruit) ;
- les réglages d'un même modèle (High, Max, xHigh…) sont regroupés : on garde le meilleur ;
- 5 modèles par usage.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

DATASET = "lmarena-ai/leaderboard-dataset"
API = "https://datasets-server.huggingface.co/filter"
MIN_VOTES = 1000
TOP = 5

USAGES = [
    {"id": "images", "label": "Images", "config": "text_to_image", "categorie": "overall",
     "description": "Créer une image à partir d'un texte (visuels, illustrations, publicités)."},
    {"id": "video", "label": "Vidéo", "config": "text_to_video", "categorie": "overall",
     "description": "Créer une courte vidéo à partir d'un texte."},
    {"id": "sites", "label": "Sites web", "config": "webdev", "categorie": "overall",
     "description": "Créer une page ou un site web complet à partir d'une demande."},
    {"id": "code", "label": "Code", "config": "text", "categorie": "coding",
     "description": "Écrire, corriger et expliquer du code (scripts, automatisations)."},
    {"id": "recherche", "label": "Recherche web", "config": "search", "categorie": "overall",
     "description": "Répondre en cherchant sur internet, avec des sources."},
    {"id": "documents", "label": "Documents", "config": "document", "categorie": "overall",
     "description": "Lire et analyser des PDF et des fichiers (rapports, études)."},
]

REGLAGES = r"\s*\((?:high|max|xhigh|medium|low|minimal|search|thinking)\)\s*$"


# Noms qu'Arena écrit autrement que le labo (à compléter au besoin).
NOMS = {"gemini-omni-flash": "Gemini Omni Flash"}


def nom_de_base(nom):
    base = re.sub(REGLAGES, "", nom, flags=re.I).strip()
    return NOMS.get(base, base)


def lire(config, where, offset):
    q = urllib.parse.urlencode({
        "dataset": DATASET, "config": config, "split": "latest",
        "where": where, "orderby": '"rating" DESC', "offset": offset, "length": 100,
    })
    for essai in range(3):
        try:
            with urllib.request.urlopen(f"{API}?{q}", timeout=60) as r:
                return json.load(r)
        except Exception:
            if essai == 2:
                raise
            time.sleep(5)


def classement(u):
    # Date de la publication Arena la plus récente pour cet usage (1 ligne suffit).
    where = f"\"category\"='{u['categorie']}'"
    q = urllib.parse.urlencode({"dataset": DATASET, "config": u["config"], "split": "latest", "where": where,
                                "orderby": '"leaderboard_publish_date" DESC', "offset": 0, "length": 1})
    with urllib.request.urlopen(f"{API}?{q}", timeout=60) as r:
        date = json.load(r)["rows"][0]["row"]["leaderboard_publish_date"]
    where += f" AND \"leaderboard_publish_date\"='{date}' AND \"vote_count\">={MIN_VOTES}"
    # Les lignes arrivent triées par score : on s'arrête dès que le top est complet.
    lignes, offset = [], 0
    while True:
        page = lire(u["config"], where, offset)
        lignes += [x["row"] for x in page["rows"]]
        offset += 100
        if len({nom_de_base(x["model_name"]).lower() for x in lignes}) >= TOP or offset >= page.get("num_rows_total", 0) or offset >= 1000:
            break
    vus, top = set(), []
    for x in sorted(lignes, key=lambda x: -x["rating"]):
        if x["leaderboard_publish_date"] != date or (x["vote_count"] or 0) < MIN_VOTES:
            continue
        base = nom_de_base(x["model_name"])
        if base.lower() in vus:
            continue
        vus.add(base.lower())
        top.append({
            "rang": len(top) + 1,
            "nom": base,
            "reglage": x["model_name"] if x["model_name"] != base else "",
            "labo": x["organization"],
            "score": round(x["rating"]),
            "marge": round((x["rating_upper"] - x["rating_lower"]) / 2),
            "votes": int(x["vote_count"]),
            "licence": x["license"],
        })
        if len(top) == TOP:
            break
    return date, top


def main(sortie):
    res = {
        "maj": time.strftime("%Y-%m-%d"),
        "source": {"nom": "Arena (LMArena)", "licence": "CC BY 4.0",
                   "lien": f"https://huggingface.co/datasets/{DATASET}",
                   "min_votes": MIN_VOTES},
        "usages": [],
    }
    for u in USAGES:
        date, top = classement(u)
        res["usages"].append({k: u[k] for k in ("id", "label", "description")} | {"date_arena": date, "modeles": top})
        print(u["label"], date, "·", ", ".join(m["nom"] for m in top))
    if any(len(u["modeles"]) < 3 for u in res["usages"]):
        raise SystemExit("Moins de 3 modèles pour un usage : fichier non écrit.")
    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
