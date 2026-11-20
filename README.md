# CAMELYON17 — Projet M2 Data Science & BI

Détection de tissu tumoral sur des patchs histopathologiques, analyse des erreurs et généralisation entre centres hospitaliers. Travail pédagogique en équipe de cinq.

**État : le travail du groupe est maintenant intégré sous la forme d'un pipeline WSI distant → patchs 224 × 224 → caractéristiques ResNet18 → classifieur classique. Un CSV de 1 002 prédictions a été audité. Le pilote WILDS initial reste disponible comme référence comparative. Aucun test final multi-patient ni résultat pN n'est encore démontré.** Lire le [pipeline du groupe](docs/pipeline_groupe.md), le [bilan chiffré fourni](reports/group_validation/README.md) et l'[audit de conformité](docs/audit_conformite.md).

## Démarrer en cinq minutes, hors installation

Python 3.12 est la version vérifiée. Depuis un terminal :

```bash
git clone https://github.com/TZAKARIA97/camelyon17-m2-ds-bi.git
cd camelyon17-m2-ds-bi
python -m venv .venv
```

Activer l'environnement : `source .venv/bin/activate` sous Linux/macOS, ou `.venv\Scripts\Activate.ps1` sous Windows PowerShell. Puis installer séparément le socle et le couple PyTorch CPU :

```bash
python -m pip install -r requirements-viz.txt
python -m pip install -r requirements-cpu-tested.txt
python -m unittest discover -s tests -v
python -m src.demo --out outputs/demo_synthetic
```

La démonstration fabrique **24 images de bruit**, utilise des poids aléatoires et ne télécharge pas d'images médicales ni de poids ImageNet. Elle vérifie toute la chaîne sur CPU. Ses scores ne doivent pas apparaître comme résultats CAMELYON17 dans le rapport.

Ouvrir ensuite `outputs/demo_synthetic/report/rapport_evaluation.md` et `outputs/demo_synthetic/gradcam/index.md`. Pour recommencer, donner un nouveau dossier : les sorties existantes ne sont pas écrasées.

Les tests tensoriels sont ignorés si torch/torchvision ne sont pas installés : un résultat avec des tests ignorés ne valide pas toute la chaîne. Le [compte rendu de validation](docs/validation.md) donne les contrôles réellement exécutés.

## Exécuter la direction actuelle du groupe

Le pipeline courant travaille directement depuis les lames originales sans télécharger toute la collection. Utiliser un environnement séparé :

```bash
python -m venv .venv-group
source .venv-group/bin/activate
python -m pip install -r requirements-group-pipeline.txt
python -m pip install -r requirements-cpu-tested.txt
python -m src.group_pipeline.camelyon_data remote-index
python -m src.group_pipeline.extract_patches --index data/CAMELYON17/index.csv --max-slides 2 --patch-level 1
python -m src.group_pipeline.analyze --patch-level 1 --modele logistique --rappel 0.95
```

Commencer impérativement par le pilote borné et contrôler les prévisualisations. Le [guide du pipeline WSI](docs/pipeline_groupe.md) explique les commandes, les hypothèses et les limites. ASAP reste un outil de contrôle visuel facultatif, isolé du pipeline Python.

## Conserver le pilote WILDS comme référence

Suivre le [guide exécutable pas à pas](docs/02_demarrage.md). Il couvre :

1. Accès aux données et contrôle de la source.
2. Conversion du manifeste WILDS et sélection reproductible d'un pilote.
3. Audit des groupes, exploration et justification des prétraitements.
4. Entraînement d'une référence puis comparaison d'une amélioration sur validation.
5. Évaluation du modèle choisi, export des figures et des exemples Grad-CAM.
6. Interprétation, limites et rédaction.

L'[accès aux données est préparé](docs/acces_donnees.md) : `python -m src.data.acquire_wilds --out data/wilds/pilot_download` récupère uniquement le pilote depuis un miroir communautaire figé. `python -m src.data.acquire_wsi_example` récupère une paire TIFF/XML originale d'environ 519 Mo, contrôlée par MD5. Le détail des sources et leurs limites est documenté.

Sur les 128 patchs de validation, l'AP passe de 0,796 à 0,895 avec le dégel du dernier bloc. Le modèle retenu manque néanmoins 15 des 38 positifs au seuil 0,5. Ces résultats de pilote ne constituent pas une performance clinique ni un résultat sur le test.

Le dépôt conserve également la chaîne WILDS déjà exécutée. Elle utilise des patchs 96 × 96 et une définition de label différente ; ses scores ne sont donc pas directement comparables à ceux du pipeline WSI 224 × 224.

## Fichiers utiles

| Besoin | Fichier ou dossier |
| --- | --- |
| Vérifier ce qui répond au sujet | [Audit de conformité](docs/audit_conformite.md) |
| Comprendre le besoin et les décisions | [Cadrage](docs/01_cadrage.md), [roadmap](docs/00_roadmap_et_livrables.md) |
| Exécuter et expliquer chaque étape | [Guide](docs/02_demarrage.md), `notebooks/` |
| Exécuter le travail actuel du groupe | [Pipeline WSI du groupe](docs/pipeline_groupe.md), `src/group_pipeline/` |
| Lire les résultats fournis | [Audit des 1 002 prédictions](reports/group_validation/README.md) |
| Contrôler les données | `src/data/`, [dictionnaire](data/README.md) |
| Entraîner et comparer | `src/models/`, `configs/baseline.json`, `configs/fine_tune.json` |
| Évaluer et visualiser | `src/evaluation/`, `src/visualization/` |
| Rédiger le rapport | [Document de travail](reports/rapport_travail.md), [plan de 15 pages](docs/rapport_plan.md) |
| Préparer les 10 minutes d'oral | [Trame et questions](docs/oral_plan.md) |
| Suivre les tâches | [Issues GitHub](https://github.com/TZAKARIA97/camelyon17-m2-ds-bi/issues), [contribution](CONTRIBUTING.md) |

## Périmètre et limites

WILDS est une option de données autorisée par les consignes, pas un algorithme de regroupement de tumeurs. ASAP sert à visualiser les lames ; Agile organise le travail. Les scripts WILDS et WSI ne donnent pas automatiquement des labels interchangeables. Le seuil de 50 % de surface tumorale du nouvel extracteur est une hypothèse à valider, pas une vérité clinique.

Le sujet annonce le stade pN comme objectif et conditionne l'évaluation ganglion/patiente aux données disponibles. Cette attente reste à clarifier avec l'enseignante. `staging.py` applique des règles à cinq catégories de ganglions déjà connues ; il ne détecte ni ne mesure les lésions et ne valide pas un diagnostic patient.

Les identifiants patient CAMELYON17 représentent des regroupements artificiels de lames. Les séparer est un garde-fou utile, sans prouver l'indépendance de tous les patients biologiques d'origine.

Le dépôt est public. Les images, checkpoints, environnements et secrets restent hors Git. Les quatre autres membres ne sont pas encore invités, leurs comptes restant à identifier.

[Sources](docs/sources.md) · [Protocole](docs/protocole.md) · [Transparence IA](docs/usage_ia.md)
