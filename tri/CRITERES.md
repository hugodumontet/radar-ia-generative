# Critères du bloc « Sorties de la semaine »

Lus par Claude chaque vendredi, au moment de trier `candidats.json` produit par `collect.py`. Ils se modifient ici, sans toucher à la tâche planifiée.

## Un modèle est retenu si

1. C'est un **nouveau modèle d'IA générative** (texte, code, image, vidéo, audio) ou une **nouvelle version** présentée par le labo comme un modèle à part entière (ex. « Introducing GPT-6 Cyber », « Images 2.6 »).
2. Sa **première annonce officielle publique** tombe dans la semaine (du vendredi précédent au jeudi inclus). Vérifier la date : les dépôts Hugging Face sont souvent créés en privé bien avant, et certains articles parlent d'un modèle sorti plus tôt.
3. Il a une **preuve officielle** : page d'annonce du labo, ou dépôt sur le compte Hugging Face officiel du labo. Un article de presse seul ne prouve rien : il sert à repérer, puis on cherche la page officielle (souvent citée dans l'article).
4. **Labo absent d'Epoch** (aucune ligne avec ce fournisseur dans `data.json`) : il faut en plus qu'au moins **2 médias différents** de `sources.json` en parlent.

## Un élément est écarté s'il s'agit de

- un modèle déjà sorti (déjà chez Epoch, ou annoncé une semaine précédente) : article produit, témoignage client, mise à jour, nouveau nom commercial ;
- la seule publication des poids d'un modèle déjà annoncé ;
- une variante technique (version compressée, quantifiée, distillée de recherche), un outil de sécurité ou de filtrage, un modèle d'embedding, de classement ou de prévision ;
- un modèle hors IA générative (biologie, robotique, prévision météo, OCR pur…) ;
- tout ce qui n'est pas une sortie : levée de fonds, étude, partenariat, nomination, incident.

En cas de doute, écarter et noter la raison : mieux vaut un bloc court et sûr qu'un bloc long et discutable.

## Champs à remplir dans `sorties.json`

- `nom` : nom officiel tel que le labo l'écrit, précédé du nom du labo seulement si c'est ainsi qu'Epoch nomme ses modèles (ex. « Tencent Hy4 »).
- `fournisseur` : nom du labo tel qu'Epoch l'écrit quand il existe déjà dans `data.json`.
- `date` : date de la première annonce officielle (AAAA-MM-JJ).
- `modalites` : codes du radar (T texte, C code, I image, V vidéo, A audio, M comprend les images), seulement ce que l'annonce affirme.
- `lien` : page officielle (jamais un article de presse).
- `reperes` : articles de presse qui en parlent (source + lien), facultatif.
- `publication` : date de la publication du vendredi.

Ne rien inventer : un champ non confirmé par la page officielle est laissé de côté.

## Alias

Si le nom chez Epoch risque d'être différent (ex. « ChatGPT Images 2.6 » au lieu de « Images 2.6 »), ajouter les variantes dans `alias.json`. Ne jamais rapprocher deux modèles différents (« Hy4 » n'est pas « Hy4 preview »).
