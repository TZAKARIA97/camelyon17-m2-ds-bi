# Audit des prédictions fournies par le groupe

## Provenance et périmètre

Le fichier `predictions_validation.csv` provient de l'archive `envoi.zip` transmise par le groupe. Il contient 1 002 prédictions au niveau patch, toutes marquées `validation`, issues du niveau 1 et d'une seule lame : `patient_092_node_1`. Les deux classes sont artificiellement équilibrées : 501 patchs sains et 501 tumoraux.

Empreinte SHA-256 du CSV audité : `358c23e2e6959ad2fab79188fdd33cb12b58dcadf51eccfcacd6356d9cf5752e`.

Les images PNG et le classifieur Joblib contenus dans l'archive ne sont pas versionnés. Le premier choix évite de placer 1 002 artefacts générés dans Git ; le second évite de distribuer et de charger sans nécessité un objet Pickle exécutable. Les métriques sont recalculées directement depuis les labels et probabilités du CSV.

## Résultats reproductibles

| Règle de décision | ROC-AUC | VN | FP | FN | VP | Exactitude | Rappel tumoral | Précision tumorale |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Seuil fixe 0,5 | 0,9683 | 494 | 7 | 264 | 237 | 72,95 % | 47,31 % | 97,13 % |
| Seuil choisi pour rappel ≥ 95 % | 0,9683 | 457 | 44 | 23 | 478 | 93,31 % | 95,41 % | 91,57 % |

Le seuil atteignant le rappel cible sur ce fichier est `0,18060946`. Il ne s'agit pas d'un seuil validé pour une utilisation finale : il est choisi et mesuré sur le même ensemble de validation.

## Interprétation critique

La ROC-AUC de 0,9683 indique que les scores classent généralement les patchs tumoraux au-dessus des patchs sains sur cet échantillon. Elle ne garantit pas une bonne décision avec le seuil 0,5. À ce seuil, 264 patchs tumoraux sur 501 sont manqués ; l'exactitude globale masque donc un rappel insuffisant.

Abaisser le seuil à 0,1806 réduit fortement les faux négatifs, au prix de 44 faux positifs. Ce compromis est cohérent avec une priorité donnée au dépistage, mais le seuil doit être fixé sur une validation distincte puis évalué sur un test indépendant.

## Ce que ces chiffres ne démontrent pas

- Une seule lame ne permet pas d'estimer la généralisation à d'autres patients, lames ou centres.
- Les 1 002 patchs ne sont pas 1 002 observations indépendantes : des régions voisines d'une même lame sont corrélées.
- L'équilibre 50/50 des classes ne représente pas nécessairement la distribution réelle et rend l'exactitude peu transférable.
- Aucune performance au niveau lame, patiente ou stade pN n'est démontrée.
- Le CSV seul ne permet pas de vérifier une éventuelle fuite entre entraînement et validation ni la qualité visuelle des labels.

Le fichier `metrics.json` est régénérable avec la commande documentée dans `docs/pipeline_groupe.md`.
