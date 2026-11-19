"""Contrôle des prix du Radar des modèles IA (passage du jeudi).

Usage :
  python3 -I prix.py taux prix.json        -> met à jour le taux euro/dollar de la BCE dans prix.json
  python3 -I prix.py controle prix.json classements.json rapport.json
      -> compare prix.json à LiteLLM (licence MIT) et liste ce qu'il faut vérifier
         sur les pages officielles. Ne modifie JAMAIS un prix : c'est Hugo qui valide.

LiteLLM sert seulement à REPÉRER un changement : il s'est déjà trompé
(Mistral Large 4 affiché au prix promo après la fin de la promo, novembre 2026).
"""
import datetime
import json
import re
import sys
import urllib.request

LITELLM = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
BCE = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def taux(chemin):
    xml = get(BCE).decode()
    date = re.search(r"time='(\d{4}-\d\d-\d\d)'", xml).group(1)
    usd = float(re.search(r"currency='USD' rate='([\d.]+)'", xml).group(1))
    if not 0.7 < usd < 1.6:
        raise SystemExit(f"Taux BCE improbable ({usd}) : prix.json inchangé.")
    p = json.load(open(chemin, encoding="utf-8"))
    p["taux"].update({"eur_usd": usd, "date": date})
    json.dump(p, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Taux BCE du {date} : 1 € = {usd} $")


def controle(chemin, classements, sortie):
    p = json.load(open(chemin, encoding="utf-8"))
    c = json.load(open(classements, encoding="utf-8"))
    ll = json.loads(get(LITELLM))
    auj = datetime.date.today().isoformat()
    ecarts, fins, sans_prix = [], [], []
    for nom, v in p["api"].items():
        cle = v.get("litellm")
        if v.get("jusqu_au") and v["jusqu_au"] < auj:
            fins.append({"modele": nom, "jusqu_au": v["jusqu_au"], "lien": v["lien"]})
        if not cle or cle not in ll:
            continue
        e, s = ll[cle].get("input_cost_per_token"), ll[cle].get("output_cost_per_token")
        if e is None or s is None:
            continue
        e, s = round(e * 1e6, 4), round(s * 1e6, 4)
        if (e, s) != (v["entree"], v["sortie"]):
            ecarts.append({"modele": nom, "radar": [v["entree"], v["sortie"]], "litellm": [e, s], "lien": v["lien"]})
    connus = set(p["api"]) | set(p.get("a_confirmer", {}))
    for u in c["usages"]:
        for m in u["modeles"]:
            if m["nom"] not in connus:
                sans_prix.append({"modele": m["nom"], "labo": m["labo"], "usage": u["label"]})
    rapport = {"date": auj, "ecarts_litellm": ecarts, "promos_terminees": fins, "nouveaux_sans_prix": sans_prix}
    json.dump(rapport, open(sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rapport, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "taux":
        taux(sys.argv[2])
    else:
        controle(*sys.argv[2:5])
