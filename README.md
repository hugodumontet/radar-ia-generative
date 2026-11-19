# Radar des modèles IA

Tableau de bord des modèles d'IA générative frontier et notables sortis depuis 2018 (texte, code, image, vidéo, audio), filtrables par pays, fournisseur, modalité, accès et période.

Consulter : https://hugodumontet.github.io/radar-ia-generative/

- Données : [Epoch AI, Data on AI Models](https://epoch.ai/data/ai-models), fichiers « notable » et « frontier », licence CC BY 4.0.
- Mise à jour automatique chaque vendredi : une nouvelle publication est ajoutée dans `data/` et listée dans `snapshots.json`.
- `build.py` transforme les CSV d'Epoch en `data.json`.
- Bloc « Sorties de la semaine » : pour ne pas attendre Epoch, `collect.py` lit chaque vendredi les annonces officielles des labos (flux d'OpenAI, Google DeepMind, Google, Mistral AI, page actualités d'Anthropic, comptes officiels Hugging Face) et repère les sorties dans la presse tech (TechCrunch, Ars Technica, The Decoder). Liste des sources : `sources.json`. Seuls le titre, le lien et la date sont lus, jamais le texte des articles.
- Le tri suit `tri/CRITERES.md` (une annonce officielle est obligatoire) ; chaque semaine, les choix et les éléments écartés sont gardés dans `tri/AAAA-MM-JJ.json`. Les sorties retenues sont dans `sorties.json`.
- `fraicheur.py` compare ces sorties à Epoch : « Confirmé par Epoch » dès qu'Epoch ajoute le modèle, « Annoncé, en attente » sinon, « Pas encore chez Epoch » après 14 jours. Les chiffres, le graphique et le catalogue restent calculés sur Epoch seul.
- Bloc « Quel modèle pour quel usage ? » (v17) : `classements.py` lit chaque semaine le jeu de données officiel d'Arena sur Hugging Face ([lmarena-ai/leaderboard-dataset](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset), licence CC BY 4.0) et écrit `classements.json` : 6 usages, top 5, au moins 1 000 votes, réglages d'un même modèle regroupés.
- Prix : `prix.json`, relevés à la main sur les pages tarifs officielles (montants des API en dollars hors taxes, convertis en euros au taux de la BCE ; abonnements en euros tels qu'affichés en France). `prix.py taux` met à jour le taux BCE ; `prix.py controle` compare à [LiteLLM](https://github.com/BerriAI/litellm) (licence MIT) pour repérer un changement. LiteLLM ne sert qu'à repérer : un prix ne change qu'après relecture de la page officielle.
- Bande « Version bêta » et pastille à côté du titre (v19) : réglées dans `bandeau.json`. `actif` affiche ou masque la bande, `pastille` affiche ou masque la pastille, `message` change le texte. Changer `version` (par exemple la date du jour) fait réapparaître la bande chez les visiteurs qui l'avaient fermée.

Radar créé par [Hugo Dumontet](https://www.linkedin.com/in/hugodumontet/) avec Claude.
