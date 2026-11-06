# Audit critique du rendu — 6 novembre 2026

## Verdict

**Le dépôt fournit maintenant un pipeline exécutable et un pilote réel interprété : 688 patchs, deux entraînements et une inspection WSI/XML. Il ne constitue pas encore le rendu scientifique final.**

Le sujet exige des expériences sur des données réelles, leur interprétation, un rapport de 15 pages maximum et une soutenance de 10 minutes. Des tests logiciels et une démonstration synthétique ne remplacent aucun de ces résultats.

## Correspondance entre consignes et preuves

| Exigence | Avant correction | Maintenant | Ce qui reste nécessaire |
| --- | --- | --- | --- |
| Compréhension du problème | Cadrage écrit | Cadrage et limites patch/lame/patiente précisés | Validation collective du périmètre et de l'attente pN |
| Exploration et préparation | Tâches à réaliser | Pilote réel audité, cohortes documentées, figures et inspection d'une lame | Vérification élargie de la source et des conventions spatiales ; relecture du groupe |
| CNN et méthode justifiée | Aucun code sur GitHub | Deux entraînements réels : AP validation 0,796 et 0,895 | Cohorte élargie, stabilité et décisions finales justifiées |
| Évaluation et robustesse | Protocole uniquement | Validation réelle, figures et métriques par lame ; test sans prédictions | Test après gel du protocole et analyse des incertitudes |
| Interprétabilité | Méthode prévue | Trois Grad-CAM réels inspectés et commentés ; carte nulle signalée | Confrontation à des masques correspondants et relecture humaine |
| Niveau ganglion/patiente | Ambiguïté identifiée | Règles pN sur catégories connues, limites explicites | Données complètes et évaluation adaptée, ou périmètre alternatif confirmé |
| Reproductibilité | Documentation seule | Dépendances, configurations, empreintes, tests et démonstration | Reproduction par un autre membre sur ses données et sa machine |
| Rapport, 15 pages maximum | Plan | Document de travail et bilan détaillé du pilote avec chiffres, figures et limites | Expériences finales, relecture et mise en forme dans les 15 pages |
| Oral, 10 minutes | Trame | Trame, messages et questions de préparation | Supports finaux et répétition collective |
| Suivi et contribution | 11 issues ouvertes | Suivi relié au code et aux livrables | Comptes des membres, contributions et relectures effectives |

## Corrections effectuées

1. Import du code précédemment absent de GitHub et réconciliation de la documentation.
2. Démonstration complète sur données synthétiques, explicitement distinguée du mode avec poids ImageNet.
3. Sélection reproductible d'un pilote par groupes, sans consulter les labels pour sélectionner les images.
4. Exploration des effectifs et exemples de train, figures d'évaluation et commentaires descriptifs.
5. Grad-CAM en ligne de commande, avec exemples corrects/erronés, traçabilité et détection des cartes nulles.
6. Contrôles supplémentaires : paramètres invalides, alias de chemins, groupes patient incohérents, manifeste et prédictions modifiés.
7. Provenance des expériences : état Git, dépendances, paramètres, durée, empreintes et données utilisées.
8. Actualisation des guides devenus faux : dépôt existant, code importé, démonstration disponible et limites restantes.

## Ce qui ne doit pas être déclaré terminé

Les deux entraînements du pilote sont réels, mais la robustesse sur la cohorte finale, l'analyse clinique et la validation pN ne sont pas établies. Le modèle retenu manque 15 des 38 positifs de validation. Les scores du bruit artificiel ne remplacent aucun résultat manquant. La présence d'un script de règles pN ne démontre pas la détection et la mesure des lésions.

Les groupes patient du challenge sont artificiels : le contrôle des identifiants fournis ne démontre pas l'indépendance biologique de toutes les lames. Une seule source hospitalière dans le test ne permet pas d'en déduire une robustesse à tous les hôpitaux.

## Prochain jalon vérifiable

Le jalon d'accès aux données et de pilote est réalisé : [accès reproductible](acces_donnees.md), [bilan du pilote](../reports/pilot_real/README.md), [inspection WSI](../reports/wsi_example/README.md). La prochaine étape est une reproduction par le groupe, puis une cohorte finale justifiée et un protocole figé avant le test. Le miroir est communautaire et son équivalence au bundle officiel reste non démontrée.

La date limite, les ressources de calcul et la clarification pN doivent être confirmées en parallèle. Les scripts ne peuvent pas deviner ces informations.

## Source

Sujet fourni *Projet 1 spécialisation — MBA 2*, pages 1 à 7 : contexte, alternatives de données, quatre étapes, livrables et grille d'évaluation. Voir aussi les références officielles dans `sources.md`. Les exigences du sujet et les choix du groupe sont distingués dans le cadrage.
