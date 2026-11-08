"""Met à jour le statut des sorties de la semaine en les comparant aux données Epoch.

Usage : python3 -I fraicheur.py sorties.json alias.json data.json AAAA-MM-JJ

Statuts :
  confirme   : Epoch contient le modèle (sa fiche Epoch prime dans le catalogue)
  attente    : annoncé officiellement il y a 14 jours ou moins, pas encore chez Epoch
  pas_encore : plus de 14 jours sans être chez Epoch (Epoch peut encore l'ajouter plus tard)
"""
import datetime as dt
import json
import re
import sys

sorties_p, alias_p, data_p, jour = sys.argv[1:5]
DELAI = 14
J = dt.date.fromisoformat(jour)

def norm(s):
    return re.sub(r"[\s\-_.·:/()]+", "", (s or "").lower())

sorties = json.load(open(sorties_p, encoding="utf-8"))
alias = json.load(open(alias_p, encoding="utf-8"))["alias"]
rows = json.load(open(data_p, encoding="utf-8"))["rows"]

# Index Epoch : nom normalisé -> nom exact. On ajoute aussi la version sans le
# fournisseur en tête (« Tencent Hy3 » se trouve aussi comme « Hy3 »).
index = {}
for r in rows:
    nom, org = r[0], r[1]
    index.setdefault(norm(nom), nom)
    premier = (org or "").split()[0] if org else ""
    if premier and norm(nom).startswith(norm(premier)) and len(norm(nom)) > len(norm(premier)):
        index.setdefault(norm(nom)[len(norm(premier)):], nom)

compte = {"confirme": 0, "attente": 0, "pas_encore": 0}
for s in sorties["sorties"]:
    essais = [s["nom"], f"{s['fournisseur'].split()[0]} {s['nom']}"] + alias.get(s["nom"], [])
    trouve = next((index[norm(e)] for e in essais if norm(e) in index), None)
    if trouve:
        s["statut"], s["nom_epoch"] = "confirme", trouve
    else:
        s.pop("nom_epoch", None)
        age = (J - dt.date.fromisoformat(s["date"])).days
        s["statut"] = "attente" if age <= DELAI else "pas_encore"
    compte[s["statut"]] += 1

sorties["maj"] = jour
json.dump(sorties, open(sorties_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(sorties['sorties'])} sorties : {compte['confirme']} confirmées par Epoch, "
      f"{compte['attente']} en attente, {compte['pas_encore']} pas encore chez Epoch")
