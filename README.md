# Radar des modèles IA

Tableau de bord des modèles d'IA générative sortis depuis 2018, avec les nouveaux dès leur sortie (texte, code, image, vidéo, audio), filtrables par pays, fournisseur, modalité, accès et période.

Consulter : https://hugodumontet.github.io/radar-ia-generative/

- Données (v23) : une base à nous, construite par `build.py` sans doublon, dans cet ordre de priorité :
  1. [Epoch AI, Data on AI Models](https://epoch.ai/data/ai-models), fichier complet `all_ai_models.csv` (licence CC BY 4.0) : base et historique, avec environ une semaine de décalage ;
  2. annonces officielles retenues chaque vendredi (`sorties.json`) ;
  3. [models.dev](https://models.dev) (licence MIT, mis à jour plusieurs fois par jour) : sorties à partir du 01/10/2026, labos suivis seulement.
  [OpenRouter](https://openrouter.ai/models) sert seulement à savoir si un modèle est utilisable par le public et à repérer des sorties : sa date est celle de l'ajout chez OpenRouter, pas la sortie.
- Critère d'entrée : un modèle génératif sorti depuis 2018 qui vient d'un labo suivi (`labos.json`), OU qui est utilisable par le public (models.dev, OpenRouter), OU qu'Epoch juge notable. Les versions retravaillées par un autre labo (champ « Base model » d'Epoch) sont écartées, sauf si notables. Pays et fournisseur : le premier listé (fournisseur principal) ; filtres et chiffres ne regardent que lui.
- Mise à jour automatique chaque vendredi : une nouvelle publication est ajoutée dans `data/` et listée dans `snapshots.json`.
- Bloc « Sorties de la semaine » : `collect.py` lit chaque vendredi les annonces officielles des labos (flux d'OpenAI, Google DeepMind, Google, Mistral AI, ElevenLabs, page actualités d'Anthropic, comptes officiels Hugging Face) et repère les sorties dans le catalogue OpenRouter et la presse tech (TechCrunch, Ars Technica, The Decoder). Liste des sources : `sources.json`. Seuls le titre, le lien et la date sont lus, jamais le texte des articles.
- Le tri suit `tri/CRITERES.md` (une annonce officielle est obligatoire) ; chaque semaine, les choix et les éléments écartés sont gardés dans `tri/AAAA-MM-JJ.json`. Les sorties retenues sont dans `sorties.json`.
- `fraicheur.py` (statuts « Confirmé par Epoch » / « Pas encore chez Epoch ») n'est plus appelé depuis la v23 : ces statuts ne sont plus affichés.
- Bloc « Quel modèle pour quel usage ? » (v17) : `classements.py` lit chaque semaine le jeu de données officiel d'Arena sur Hugging Face ([lmarena-ai/leaderboard-dataset](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset), licence CC BY 4.0) et écrit `classements.json` : 6 usages, top 5, au moins 1 000 votes, réglages d'un même modèle regroupés.
- Prix : `prix.json`, relevés à la main sur les pages tarifs officielles (montants des API en dollars hors taxes, convertis en euros au taux de la BCE ; abonnements en euros tels qu'affichés en France). `prix.py taux` met à jour le taux BCE ; `prix.py controle` compare à [LiteLLM](https://github.com/BerriAI/litellm) (licence MIT) pour repérer un changement. LiteLLM ne sert qu'à repérer : un prix ne change qu'après relecture de la page officielle.
- Bande « Version bêta » et pastille à côté du titre (v19) : réglées dans `bandeau.json`. `actif` affiche ou masque la bande, `pastille` affiche ou masque la pastille, `message` change le texte. Changer `version` (par exemple la date du jour) fait réapparaître la bande chez les visiteurs qui l'avaient fermée.

Radar créé par [Hugo Dumontet](https://www.linkedin.com/in/hugodumontet/) avec Claude.
