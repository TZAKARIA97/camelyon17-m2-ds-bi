# Pipeline WSI retenu par le groupe

Ce document décrit la chaîne ajoutée à partir du travail collectif. Elle part des lames CAMELYON17 originales, conserve les TIFF sur un stockage S3 distant et ne télécharge localement que les métadonnées, les annotations XML et les patchs sélectionnés.

## 1. Ce que fait réellement la chaîne

1. `camelyon_data.py` inventorie les lames distantes, récupère les XML et `stages.csv`, puis construit un index.
2. `extract_patches.py` lit les lames à distance, détecte grossièrement le tissu par sa couleur, projette les annotations XML et extrait des PNG de 224 × 224 pixels aux niveaux 0 ou 1.
3. `analyze.py` sépare les données par identifiant patient, transforme chaque PNG en 512 caractéristiques avec ResNet18 préentraîné, puis compare une régression logistique et une forêt aléatoire.
4. Le seuil de décision est choisi sur la validation pour atteindre un rappel cible, puis appliqué sans changement au test.

Cette approche est une extraction de caractéristiques suivie d'un modèle classique. Ce n'est pas un fine-tuning de ResNet18 : les poids du réseau ne sont pas adaptés aux images histologiques.

## 2. Installation

Python 3.12 reste la version de référence du dépôt. L'environnement WSI est séparé du socle afin d'isoler les dépendances sensibles, notamment OpenSlide/TiffSlide et NumPy.

```bash
python -m venv .venv-group
source .venv-group/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-group-pipeline.txt
python -m pip install -r requirements-cpu-tested.txt
```

La dernière commande installe le couple PyTorch CPU vérifié. Pour un GPU, utiliser à sa place le couple torch/torchvision recommandé par PyTorch pour la version de CUDA du poste. Sous Windows, activer avec `.venv-group\Scripts\Activate.ps1`. La bibliothèque système OpenSlide peut être nécessaire pour les TIFF locaux. La lecture S3 utilise TiffSlide.

ASAP n'est pas requis pour exécuter la chaîne : il reste utile pour contrôler visuellement les lames et les annotations. Un conflit NumPy propre à ASAP ne doit donc pas bloquer le pipeline Python ; il est préférable de garder ASAP dans un environnement séparé.

## 3. Préparer l'index sans télécharger toutes les lames

```bash
python -m src.group_pipeline.camelyon_data remote-index
```

La commande produit `data/CAMELYON17/index.csv`. Les chemins `s3://` pointent vers les TIFF distants ; seules les petites annotations et tables sont conservées localement. Vérifier avant l'extraction : nombre de lames, nombre de XML, groupes XML rencontrés et présence des labels.

La source distante peut être remplacée sans changer le code :

```bash
export CAMELYON_S3=s3://mon-bucket/mon-prefixe/
```

## 4. Lancer un pilote borné

Commencer par deux lames et un seul niveau. Cela vérifie les accès, la géométrie et le volume avant une exécution coûteuse.

```bash
python -m src.group_pipeline.extract_patches \
  --index data/CAMELYON17/index.csv \
  --slides labelled \
  --max-slides 2 \
  --patch-level 1 \
  --slide-workers 1 \
  --workers 4
```

Inspecter `patches/niveau_1/previews/` et `patches/niveau_1/patches.csv`. Il faut vérifier visuellement que les rectangles tumoraux recouvrent les annotations et que les patchs normaux contiennent bien du tissu.

Le seuil tumoral par défaut exige qu'au moins 50 % du patch soit couvert par le masque. C'est un choix sévère : il peut éliminer les petites métastases et cellules tumorales isolées. Il doit être comparé à d'autres règles sur validation, puis figé avant le test. Les patchs de frontière sont actuellement exclus ; ils ne doivent pas être implicitement qualifiés de normaux.

## 5. Extraire la cohorte retenue

Une fois le pilote contrôlé :

```bash
python -m src.group_pipeline.extract_patches \
  --index data/CAMELYON17/index.csv \
  --slides labelled \
  --patch-level 0 1 \
  --slide-workers 3 \
  --workers 8
```

Le bon niveau de parallélisme dépend de la mémoire, du débit réseau et du serveur. Augmenter les workers n'accélère pas nécessairement la lecture distante. Les sorties déjà inscrites dans `patches.csv` sont reprises par lame.

## 6. Entraîner et comparer

```bash
python -m src.group_pipeline.analyze --patch-level 1 --modele logistique --rappel 0.95
python -m src.group_pipeline.analyze --patch-level 1 --modele random_forest --rappel 0.95
```

La séparation est faite par identifiant patient afin d'éviter qu'un même patient apparaisse dans plusieurs ensembles. Cette précaution est nécessaire, mais elle ne suffit pas : il faut aussi publier les effectifs par patient, lame, centre et classe, et vérifier les deux classes dans chaque ensemble.

La sélection du modèle et du seuil utilise exclusivement la validation. Le test ne doit être consulté qu'après le gel de la méthode. Pour comparer les modèles, conserver au minimum ROC-AUC, rappel, précision, matrice de confusion, effectifs et temps de calcul. Une répétition sur plusieurs graines est nécessaire pour quantifier la stabilité.

## 7. Reproduire l'audit du CSV fourni

```bash
python -m src.group_pipeline.summarize_results \
  --predictions reports/group_validation/predictions_validation.csv \
  --out reports/group_validation/metrics.json \
  --seuil-fixe 0.5 \
  --rappel-cible 0.95
```

Le CSV et le résumé sont versionnés. Les 1 002 PNG et le fichier `classifieur.joblib` du ZIP ne le sont pas : ce sont des artefacts générés volumineux. De plus, un fichier Joblib/Pickle ne doit être chargé que si sa provenance est totalement fiable, car son chargement peut exécuter du code.

## 8. Décisions encore nécessaires

- Fixer une définition du label patch compatible avec l'objectif : couverture de 50 %, région centrale ou autre règle justifiée.
- Définir une cohorte finale et publier les dénominateurs ; un échantillon équilibré artificiellement ne mesure pas la prévalence réelle.
- Comparer niveau 0 et niveau 1 à protocole identique.
- Évaluer plusieurs patients et centres, puis effectuer un test indépendant une seule fois.
- Définir l'agrégation patch → lame. L'agrégation lame → patiente et le stade pN restent hors démonstration tant que les catégories de lésions et les règles cliniques ne sont pas validées.
