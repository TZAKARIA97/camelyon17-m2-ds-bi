# Glossaire pour le groupe

| Terme | Explication simple |
|---|---|
| WSI / lame entière | Numérisation très grande d'une coupe de tissu ; on lit des régions pour économiser la mémoire. |
| Patch | Petite région carrée d'une lame. Plusieurs patches d'une même lame sont corrélés. |
| Annotation XML | Coordonnées des contours dessinés par les experts, pas une image directement. |
| Masque | Image de même repère indiquant quels pixels appartiennent à une région annotée. |
| Label | Réponse de référence utilisée pour apprendre/évaluer ; sa définition doit être précise. |
| Patient / lame / centre | Unités de regroupement permettant de séparer les données sans fuite. |
| Classification | Donner une classe à une image. La tâche patch est supervisée. |
| Segmentation | Attribuer une classe aux pixels ; différente d'une classification patch. |
| Clustering | Former des groupes sans utiliser les labels comme cibles ; ce n'est pas la tâche principale ici. |
| Entraînement | Données qui servent à ajuster les poids du modèle. |
| Validation | Données servant au choix du modèle, des réglages et du seuil. |
| Test | Données réservées à l'évaluation finale. |
| ID / OOD | Données de centres déjà vus / de centres non vus pendant l'apprentissage. |
| Faux négatif | Exemple tumoral prédit non tumoral. |
| Sensibilité | Part des exemples positifs détectés : TP / (TP + FN). |
| Précision | Part des prédictions positives qui sont justes : TP / (TP + FP). |
| Transfer learning | Réutiliser un modèle préentraîné comme point de départ. |
| Fine-tuning | Réajuster certains poids préentraînés sur les nouvelles données. |
| Grad-CAM | Carte des régions contribuant au score du CNN ; elle ne remplace pas l'annotation. |
| pN | Catégorie d'atteinte ganglionnaire ; elle exige plus que des labels de patches isolés. |

Pour chaque résultat, pouvoir dire : ce que l'on mesure, sur quelles données, comment on le calcule, ce qu'on en déduit et ce qu'on ne peut pas conclure.
