# Guide exécutable et expliqué

Toutes les commandes se lancent depuis la racine du dépôt, dans l'environnement activé. Les chemins d'exemple doivent être adaptés aux vrais fichiers. Une étape échouée doit être comprise avant de poursuivre.

## 1. Vérifier l'environnement

Suivre le README pour Python 3.12, `requirements-viz.txt` et `requirements-cpu-tested.txt`. Pour CUDA, installer le couple torch/torchvision approprié depuis https://pytorch.org/get-started/locally/ ; ne pas appliquer l'index CPU à une installation GPU. Le poste Windows et le GPU du groupe n'ont pas été testés ici.

```bash
python -m unittest discover -s tests -v
python -m src.demo --out outputs/demo_synthetic
```

Cette démonstration teste le logiciel avec du bruit et des poids aléatoires. Les configurations, sorties et figures portent le statut synthétique. Elle n'entraîne pas un modèle médical.

Les notebooks sont facultatifs pour exécuter les scripts. Pour les ouvrir : installer `requirements-notebooks.txt`, choisir le même environnement Python dans son éditeur et lire les cellules Markdown avant les cellules de code. Le second notebook lit par défaut les sorties de la démonstration, puis peut être dirigé vers une expérience réelle.

## 2. Obtenir les données sans téléchargement aveugle

Choisir la source et noter version, licence, provenance, volume et lieu de stockage. La source officielle WILDS est citée dans `docs/sources.md`. Son téléchargement standard récupère le bundle ; sélectionner un pilote ensuite ne réduit pas rétroactivement ce téléchargement.

Si les données existent déjà sur un serveur, un disque partagé ou une plateforme de calcul, lancer le pipeline à proximité des données. Le convertisseur puis le sélecteur ci-dessous peuvent travailler sur les seules métadonnées : la colonne `path` du manifeste réduit indique les images à rendre accessibles. Il faut ensuite vérifier leur présence avant l'entraînement.

Ne pas comparer une version Kaggle et WILDS sans contrôler labels, patientes, centres et séparation. Aucun téléchargement ni compte externe n'est déclenché automatiquement.

## 3. Créer puis réduire le manifeste WILDS

Le dossier local attendu contient `metadata.csv` et `patches/` :

```bash
python -m src.data.wilds_manifest --root data/wilds/camelyon17_v1.0 --out data/manifests/wilds_patches.csv
python -m src.data.subset --manifest data/manifests/wilds_patches.csv --patients-per-group 2 --patches-per-patient 128 --seed 42 --out data/manifests/wilds_pilot.csv
python -m src.data.audit data/manifests/wilds_pilot.csv --check-files
```

Le premier script reprend le schéma officiel. Le second tire au plus deux groupes patient par couple ensemble/centre puis au plus 128 patchs par groupe. Il ne sélectionne pas sur le label et ne déplace aucune patiente entre ensembles. Le fichier `.selection.json` conserve paramètres, identifiants sélectionnés et empreintes.

Ce pilote réduit le calcul et peut manquer une classe : le modèle refuse alors l'entraînement. Il faut justifier une sélection plus large, pas supprimer le contrôle. Ses scores ne représentent pas le benchmark complet.

Les chemins restent relatifs à la racine du dépôt, ou absolus si la source est absolue. Ne pas déplacer les données après la création du manifeste sans régénérer et revérifier celui-ci. Si l'audit détecte une fuite dans les métadonnées choisies, documenter le problème avant toute correction ; ne pas prétendre suivre encore exactement le benchmark officiel si le split change.

## 4. Explorer avant de modéliser

```bash
python -m src.data.explore --manifest data/manifests/wilds_pilot.csv --out outputs/exploration_pilot
```

Lire `counts.csv`, `summary.json`, `distribution.png`, `training_examples.png` et `example_selection.csv`. Expliquer les effectifs par classe/centre et la qualité des exemples. Les images affichées viennent de train ; le test final n'est pas utilisé pour choisir les prétraitements.

Une patiente peut contribuer aux deux classes : sommer les nombres de patientes par classe double-compterait certaines personnes. Les différences de coloration doivent être décrites à partir d'images réellement observées.

## 5. Entraîner la référence et une amélioration

```bash
python -m src.models.train --manifest data/manifests/wilds_pilot.csv --config configs/baseline.json --out outputs/baseline_01
python -m src.models.train --manifest data/manifests/wilds_pilot.csv --config configs/fine_tune.json --out outputs/finetune_01
```

La première commande télécharge les poids ImageNet si absents du cache. Elle gèle le backbone et apprend la couche de sortie binaire. La seconde dégèle en plus le dernier bloc ; les autres paramètres restent identiques pour isoler ce changement. Trois époques servent au pilote, sans garantie de convergence.

Le meilleur checkpoint de chaque expérience est sélectionné sur l'Average Precision de validation. Comparer `history.csv`, `training_summary.json` et les évaluations de validation. Conserver configuration, dépendances, graine, empreinte du manifeste et état Git. Les poids restent dans `outputs/`, hors Git.

Les images sont redimensionnées sans crop et normalisées avec les constantes ImageNet ; cela ne normalise pas la coloration histologique. Les labels WILDS portent sur le centre du patch : ne pas introduire un crop aléatoire qui pourrait en changer le sens.

## 6. Évaluer sans choisir sur le test

```bash
python -m src.evaluation.evaluate --manifest data/manifests/wilds_pilot.csv --checkpoint outputs/baseline_01/best.pt --split val --out outputs/baseline_val
python -m src.evaluation.evaluate --manifest data/manifests/wilds_pilot.csv --checkpoint outputs/finetune_01/best.pt --split val --out outputs/finetune_val
```

Choisir entre les modèles avec la validation et une règle écrite. Le seuil 0,5 fourni est fixe : il n'a pas été optimisé pour une exigence clinique. Toute modification du seuil doit être décidée sur validation et consignée avant le test, via une configuration cohérente avec le checkpoint.

Après gel du protocole, remplacer le checkpoint ci-dessous par celui réellement choisi :

```bash
python -m src.evaluation.evaluate --manifest data/manifests/wilds_pilot.csv --checkpoint outputs/baseline_01/best.pt --split test --out outputs/final_test
python -m src.visualization.report --evaluation outputs/final_test --out outputs/final_report
```

Le script produit scores par patch, métriques globales, par centre et par lame, et empreintes de provenance. Le rapport ajoute matrice de confusion, courbes ROC/PR, tables et une description des erreurs. Les métriques par lame restent des métriques de patchs regroupés : ce n'est pas une classification de lame.

Pour WILDS officiel, le test OOD correspond à un centre. Comparer validation ID, validation OOD et test OOD avec leurs rôles et effectifs ; ne pas inventer plusieurs centres dans ce test ni attribuer toute différence au centre seul.

## 7. Exporter et interpréter les Grad-CAM

```bash
python -m src.visualization.explain --manifest data/manifests/wilds_pilot.csv --checkpoint outputs/baseline_01/best.pt --evaluation outputs/final_test --out outputs/final_gradcam --per-category 2
```

Utiliser le même checkpoint que pour l'évaluation. La commande sélectionne jusqu'à deux exemples de chaque type TP/TN/FP/FN selon une règle fixe, vérifie les empreintes et recalcule les scores. Lire `index.md` et compléter les observations avec les annotations réellement accessibles.

Toutes les cartes expliquent la classe tumorale, y compris lorsque le modèle prédit négatif. Une carte nulle est signalée. Une zone colorée n'est ni une segmentation, ni une probabilité locale, ni une preuve de diagnostic juste.

## 8. Piste WSI facultative selon le périmètre retenu

```bash
python -m pip install -r requirements-wsi-tested.txt
python -m src.data.inventory --root data/raw --out data/manifests/slides.csv
python -m src.data.inspect_wsi --wsi data/raw/centre_0/patient_XXX_node_Y.tif --xml data/raw/annotations/patient_XXX_node_Y.xml --coords data/manifests/coords.csv --out outputs/inspection_01
```

Les noms et le centre ci-dessus sont des exemples. `coords.csv` contient des coordonnées vérifiées en pixels niveau 0. L'inspection exporte au plus six régions par défaut, une miniature et les métadonnées de résolution. Aucune coordonnée inventée n'est livrée. Ne pas traiter l'absence de XML comme un label négatif.

## 9. Préparer le rendu

Compléter `reports/rapport_travail.md` avec les observations et expériences réelles ; respecter la limite de 15 pages lors de la mise en forme finale. Construire les 10 minutes d'oral avec `docs/oral_plan.md`. Le [guide d'interprétation](interpretation.md) aide à expliquer les résultats sans conclusions excessives.

Le dépôt existe déjà : le cloner, ne pas recréer un dépôt avec un historique indépendant. Les contributions passent par branches et pull requests ; les quatre invitations restent à effectuer une fois les comptes connus.
