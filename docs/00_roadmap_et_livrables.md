# Roadmap et livrables

## Besoin et points à clarifier

Le sujet porte sur la détection de métastases du cancer du sein dans des lames de ganglions lymphatiques. Il ne s'agit pas d'une étude de mortalité ni d'un simple regroupement non supervisé d'images.

L'objectif annoncé comprend la détection et l'étendue des métastases ainsi que le stade pN. L'étape d'évaluation prévoit toutefois l'analyse ganglion/patiente « si les données le permettent ». Le groupe doit faire confirmer ce qui est attendu si la version simplifiée WILDS est retenue.

WILDS figure parmi les alternatives autorisées dans le sujet. Cela autorise son examen comme source de données principale ; cela ne démontre pas que ses données permettront tous les objectifs d'agrégation. Le mot WILDS ne désigne pas l'algorithme à entraîner.

## Ordre de travail

| Phase | Travail | Preuve attendue avant de poursuivre |
| --- | --- | --- |
| 0. Cadrage | Lire le sujet, confirmer la date limite, les niveaux de prédiction et les ressources | Une page de périmètre, décisions et critères de succès |
| 1. Données et pilote | Choisir une source, examiner métadonnées/annotations, ouvrir un petit échantillon | Inventaire, estimation du stockage et exemple vérifié de lecture |
| 2. Préparation | Contrôler les labels et la qualité, définir les ensembles, gérer le déséquilibre | Manifest traçable et audit de séparation des patientes/lames |
| 3. Référence de modélisation | Entraîner un premier CNN ou modèle de transfert simple | Configuration sauvegardée, historique et modèle reproductible |
| 4. Expériences limitées | Tester une amélioration motivée à la fois sur validation | Tableau comparatif et choix expliqué, sans consultation du test |
| 5. Évaluation et explication | Évaluer le modèle choisi, analyser les centres et les erreurs, produire une méthode d'interprétabilité | Métriques, effectifs, exemples d'erreurs et limites |
| 6. Agrégation conditionnelle | Vérifier si couverture, identifiants et annotations permettent ganglion/patiente | Méthode évaluée ou impossibilité documentée et périmètre validé |
| 7. Rendu | Finaliser code, rapport et présentation | Reproduction par un autre membre et répétition de 10 minutes |

Le rapport se construit pendant les phases 0 à 6. Les dépendances imposent cet ordre ; les tâches de visualisation, documentation et préparation peuvent avancer en parallèle après accord sur les interfaces.

## Stratégie pour un volume important

Commencer par les métadonnées et un pilote. Pour une piste WSI, tester une lame et son annotation correspondante, puis estimer le coût avant d'élargir. Pour WILDS, vérifier l'emplacement, le format et les conditions d'accès de la version choisie avant de lancer un téléchargement.

Utiliser un stockage partagé ou un environnement de calcul adapté si disponible ; conserver dans Git les scripts et la méthode d'accès. Une petite cohorte doit être sélectionnée et justifiée, avec des patientes distinctes entre ensembles. Éviter une sélection composée seulement des cas les plus faciles.

## Protocole minimum

- Définir explicitement l'unité : patch, lame, ganglion ou patiente.
- Vérifier la correspondance image/annotation ; une annotation manquante n'est pas une preuve d'absence de tumeur.
- Auditer les identifiants avant entraînement. Ne pas refaire un découpage aléatoire de patchs sans contrôler la patiente.
- Réserver un ensemble de validation au réglage ; conserver le test pour l'évaluation finale.
- Fixer le seuil sur la validation, puis l'appliquer au test.
- Rapporter les effectifs, la matrice de confusion, la sensibilité/rappel, la précision, la spécificité et des métriques de classement pertinentes, avec leurs définitions.
- Distinguer une métrique non définie d'une valeur nulle, notamment lorsqu'un ensemble ne contient qu'une classe.
- Comparer les centres avec leurs effectifs et leurs limites ; ne pas conclure à une performance équivalente à partir de petits groupes.
- Examiner des vrais/faux positifs et négatifs. Une explication visuelle aide l'analyse, sans démontrer une causalité ni une validité clinique.
- Ne pas déduire un stade pN d'un simple nombre de patchs positifs.

## Livrables explicitement demandés

| Livrable | Exigence du sujet | Proposition d'organisation |
| --- | --- | --- |
| Code | Pipeline reproductible de préparation, entraînement, évaluation et visualisation | Scripts, configuration, dépendances, notebook pédagogique et guide |
| Rapport | 15 pages maximum | Contexte 1 p., données 3 p., méthode 3 p., expériences/résultats 3 p., interprétation 2 p., limites/conclusion 2 p., références 1 p. |
| Oral | 10 minutes | Problème 1 min, données 2 min, méthode 2 min, résultats 2 min, interprétation/limites 2 min, conclusion 1 min |
| Suivi | Sérieux, régularité, retours intégrés, travail en groupe | Issues, décisions, comptes rendus courts et relectures |

La répartition des pages et du temps est une proposition, pas une consigne supplémentaire. La date limite exacte et les modalités de dépôt restent à reprendre depuis l'annonce de cours.

La grille attribue 20 % au suivi, 25 % aux données, 25 % aux modèles et à la méthode, 10 % à l'interprétation/équité/éthique et 20 % à l'oral. La compréhension et la justification priment sur la recherche d'un score élevé.

## Source du cadrage

Document fourni dans la conversation : *Projet 1 spécialisation — MBA 2*, daté du 20 octobre 2026, pages 1 à 7. Ce document n'est pas republié dans le dépôt. Le présent guide reformule le sujet et identifie les décisions propres au groupe.
