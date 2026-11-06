# Lire et interpréter les résultats

Ce guide explique des calculs. Il ne contient aucun résultat CAMELYON17 réel.

## Comprendre les erreurs

- TP : patch tumoral correctement détecté.
- FN : patch tumoral classé négatif ; c'est un échec de détection au niveau patch.
- FP : patch non tumoral classé positif ; il peut augmenter le nombre de vérifications inutiles.
- TN : patch non tumoral correctement classé négatif.

Sensibilité = TP / (TP + FN). Elle mesure la proportion de patchs tumoraux retrouvés. Spécificité = TN / (TN + FP). Précision = TP / (TP + FP) : parmi les alertes du modèle, combien correspondent au label positif ? Précision et sensibilité répondent à deux questions différentes.

Si le dénominateur est nul, la mesure est non définie. Ne pas la remplacer automatiquement par zéro et conclure à une mauvaise performance.

## Exemple arithmétique fictif

Supposons 20 patchs positifs dont 16 détectés et 80 négatifs dont 8 fausses alertes. Alors TP=16, FN=4, FP=8, TN=72. Sensibilité=80 %, spécificité=90 %, précision=66,7 % et accuracy=88 %.

Ce scénario démontre qu'une accuracy de 88 % peut coexister avec 20 % de patchs tumoraux manqués. **Ces nombres sont inventés pour expliquer les formules ; ils ne sont pas issus du projet.**

## Scores et seuil

Le modèle produit un score de classe tumorale, puis un seuil le convertit en décision. Abaisser le seuil peut augmenter la sensibilité et les fausses alertes. Le seuil se choisit sur validation, selon une règle justifiée ; regarder le test pour le choisir crée un biais d'évaluation.

ROC-AUC et Average Precision évaluent un classement sur plusieurs seuils. Une AP élevée ne signifie pas que la sensibilité au seuil 0,5 est élevée. La prévalence influence la précision et la courbe précision-rappel ; comparer des ensembles différents exige de la connaître.

## Comparer les expériences et les centres

Comparer les modèles sur le même manifeste et la même validation. Rapporter l'effectif en patchs mais aussi en lames/groupes patient. Documenter les graines et le budget. Une seule exécution ne démontre pas la stabilité d'une amélioration.

Le test OOD officiel WILDS provient d'un seul centre. Notre protocole exclut `id_val`, partagé avec train, et ne compare donc pas validation ID et OOD. Les écarts entre les ensembles conservés combinent changement de centre, de cas et d'effectifs ; ne pas leur donner une interprétation causale automatique. Le [bilan du pilote réel](../reports/pilot_real/README.md) applique ces précautions à des résultats mesurés.

Les patchs d'une lame sont corrélés. Pour ajouter des intervalles de confiance, rééchantillonner les groupes pertinents et justifier leur indépendance. Le starter n'affiche aucun intervalle calculé en faisant semblant que tous les patchs sont indépendants.

## Commenter Grad-CAM

Décrire d'abord ce qui est visible, puis le lien avec l'annotation si elle existe, puis une hypothèse et sa limite. Exemple de structure : « La carte met en évidence [zone observée]. Cette zone [recouvre/ne recouvre pas] [annotation disponible]. Cela suggère [hypothèse], sans prouver [conclusion trop forte]. »

Ne pas nommer un type de cellule ou une structure que l'on ne sait pas identifier. Demander une expertise si nécessaire. Comparer erreurs et succès ; ne pas garder seulement les belles cartes. La carte est relative et grossière, pas une segmentation.

## Forme attendue dans le rapport

Pour chaque expérience : question → protocole → observation chiffrée → interprétation → limite. Toujours préciser l'unité du résultat. Un FN patch n'est pas automatiquement une patiente entière manquée ; l'agrégation doit être définie et évaluée séparément.
