# Données et contrats de fichiers

Les dossiers `raw/`, `processed/`, `wilds/` ne sont pas suivis par Git. Pas de téléchargement automatique à l'import.

## Acquisition minimale

Consulter https://camelyon17.grand-challenge.org/Data/ pour accéder au jeu officiel.
Commencer par les labels/métadonnées, puis une paire `patient_XXX_node_Y.tif` / `.xml` de même identifiant. Vérifier les sommes de contrôle si fournies. Noter la source, le poids, la date et la licence dans le journal. Ne pas supposer qu'une version Kaggle est équivalente à WILDS.

Pour WILDS, la version étiquetée représente environ 10 Go à télécharger et 15 Go sur disque selon son dépôt ; prévoir aussi l'archive et les sorties. `get_dataset(..., download=True)` télécharge le bundle, même si l'on sous-échantillonne ensuite. Faire un premier test sur un sous-ensemble réduit diminue le calcul, pas nécessairement le téléchargement. Les patches supplémentaires non étiquetés ne sont pas nécessaires à la baseline.

## Manifest d'entraînement `patches.csv`

| Champ obligatoire | Sens |
|---|---|
| path | chemin relatif à la racine du dépôt, ou absolu local |
| patient_id | identifiant stable, texte préservant les zéros initiaux |
| slide_id | identifiant unique de lame |
| center_id | identifiant du centre, avec convention de la source |
| label | 0 ou 1 selon la règle documentée |
| split | train, val (OOD), id_val, test (OOD), id_test |

Conserver aussi `source`, `x`, `y`, `level`, `size`, `mpp_x`, `mpp_y`, `label_rule` lorsque disponibles. Ne pas inventer une résolution absente.

`slides.csv` est un inventaire sans label déduit de la présence/absence de XML. `inspection.csv` est une sortie exploratoire sur quelques coordonnées ; ce n'est pas un dataset d'entraînement prêt.

Le script `audit` contrôle les identifiants, pas les clones d'images renommés ni les relations entre patients réels sous-jacents. Vérifier aussi la provenance et, au besoin, les empreintes de fichiers.
