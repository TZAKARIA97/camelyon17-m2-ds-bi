# CAMELYON17 — pipeline de classification

Le projet couvre l'indexation des lames, l'extraction de patches à plusieurs niveaux,
l'extraction de caractéristiques ResNet18, l'entraînement, le réglage du seuil et la
comparaison objective des niveaux et des modèles.

## Installation

```bash
python -m pip install -r requirements.txt
```

## 1. Préparer l'index et les annotations

```bash
CAMELYON_DIR=data/CAMELYON17 python camelyon_data.py remote-index
```

Les lames restent sur S3. Seuls `stages.csv`, les annotations XML et l'index sont
téléchargés localement.

## 2. Extraire les mêmes lames à plusieurs niveaux

Test pilote :

```bash
CAMELYON_DIR=data/CAMELYON17 python extract_patches.py \
  --out patches --slides annotated --max-slides 10 \
  --patch-level 0 1 2 --max-tumor 100 --max-normal 100 \
  --slide-workers 2 --workers 4
```

Extraction finale : supprimer `--max-slides` après validation du pilote. Les lames
déjà terminées sont ignorées grâce à `journal_lames.csv`; les erreurs restent
identifiables et peuvent être relancées.

## 3. Comparer les niveaux et les modèles

```bash
CAMELYON_DIR=data/CAMELYON17 python analyze.py \
  --out patches --patch-level 0 1 2 --modele tous \
  --resultats resultats --rappel 0.95 --graine 42
```

Le choix est fait avec l'AUC de validation, jamais avec le test. Les sorties principales
sont `comparaison_niveaux_modeles.csv` et `configuration_recommandee.txt`.

## 4. Utiliser le modèle final

```bash
python predict.py --input dossier_de_png \
  --modele resultats_finaux/modele_final.joblib \
  --sortie predictions_nouvelles.csv
```

Le modèle final contient son seuil. La sortie fournit la probabilité tumorale et
l'étiquette prédite pour chaque patch.

## 5. Tests

```bash
python -m unittest discover -s tests -v
```

La séparation est réalisée par patiente afin d'éviter qu'une même patiente apparaisse
dans plusieurs ensembles.
