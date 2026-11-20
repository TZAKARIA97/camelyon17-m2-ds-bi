# Alignement de la version collective

## Décision

La version collective reçue le 20 novembre 2026 est la référence fonctionnelle du projet. Elle est intégrée sans remplacer le pilote WILDS historique ni l'ancien audit d'une lame. Les résultats de protocoles différents restent séparés afin d'éviter toute comparaison trompeuse.

## Protocole retenu

| Élément | Décision alignée |
| --- | --- |
| Surface observée | 112 µm × 112 µm, indépendante du scanner |
| Entrée du réseau | 224 × 224 pixels après redimensionnement |
| Niveau de lecture | Niveau 2 |
| Étiquetage positif | Tumeur dans la zone centrale de 56 µm |
| Représentation | ResNet18 ImageNet gelé, 512 caractéristiques |
| Classifieur | Régression logistique |
| Séparation | Par patiente, avec ensembles enregistrés dans `selection_lames.csv` |
| Sélection du niveau | Validation uniquement |
| Chaîne aval | Carte de chaleur, classe de la lame, stade pN |

Le niveau 2 ne signifie pas un champ fixe de 224 pixels du niveau 2. La surface physique reste 112 µm : le nombre de pixels effectivement lus dépend du MPP et du facteur de sous-échantillonnage, puis l'image est redimensionnée à 224 × 224 pixels. Cette règle corrige la divergence avec l'expérience annexe précédemment poussée.

## Résultats disponibles

La comparaison exécutée dans le notebook collectif donne une ROC-AUC de validation de 0,9682 au niveau 1 et de 0,9738 au niveau 2. La règle annoncée autorisait le niveau 2 si son écart restait inférieur à 0,01 ; il est ici légèrement meilleur et demande quatre fois moins de lecture. Le niveau 2 est donc retenu.

L'expérience multicentre indépendante compare les images originales, Reinhard et Macenko. La méthode originale est retenue sur validation avec un seuil de 0,31390092, une spécificité moyenne de 0,8967 et une ROC-AUC moyenne de 0,9752. Sur le centre 2 réservé au test, elle obtient une ROC-AUC de 0,8715, un rappel de 0,6515, une précision de 0,9399 et une spécificité de 0,9817. Cette baisse de rappel montre que la généralisation inter-centres reste la principale limite.

## Portée réelle

Les cellules d'extraction, de comparaison des niveaux et de sélection du protocole ont produit des sorties. Dans l'archive collective, les cellules de cartes de chaleur, de classification complète des lames, d'évaluation pN et de kappa ne sont pas exécutées. Le code correspondant est conservé, mais aucun chiffre final n'est inventé pour ces étapes.

## Vérifications reproductibles

```bash
python -m unittest discover -s tests -v
python version_finale/analyses/multicentres/scripts/verifier_resultats_publics.py
python -m compileall -q version_finale src tests
```

Le vérificateur public contrôle la cohérence des métriques agrégées, le choix réalisé sur validation et l'ouverture du test avec le seuil figé. Il ne recharge pas les images ni les poids et ne constitue donc pas une nouvelle inférence. Les prédictions et inventaires détaillés contenant des identifiants pseudonymisés ne sont pas publiés dans ce dépôt public.
