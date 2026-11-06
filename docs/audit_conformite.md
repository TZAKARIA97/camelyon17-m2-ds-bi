# Audit critique du rendu — 6 novembre 2026

## Verdict

**Le dépôt initial ne répondait pas à l'ensemble du besoin : il contenait neuf fichiers de documentation et aucune chaîne de code publiée. La version corrigée fournit un socle technique exécutable et documenté, mais pas encore le rendu scientifique final.**

Le sujet exige des expériences sur des données réelles, leur interprétation, un rapport de 15 pages maximum et une soutenance de 10 minutes. Des tests logiciels et une démonstration synthétique ne remplacent aucun de ces résultats.

## Correspondance entre consignes et preuves

| Exigence | Avant correction | Maintenant | Ce qui reste nécessaire |
| --- | --- | --- | --- |
| Compréhension du problème | Cadrage écrit | Cadrage et limites patch/lame/patiente précisés | Validation collective du périmètre et de l'attente pN |
| Exploration et préparation | Tâches à réaliser | Scripts, audit, sous-échantillonnage et notebook | Inventaire réel, contrôle des annotations et interprétation des images |
| CNN et méthode justifiée | Aucun code sur GitHub | ResNet18 gelé, configuration de fine-tuning, provenance | Entraînements réels et comparaison sur validation |
| Évaluation et robustesse | Protocole uniquement | Scores, métriques, figures et regroupements par centre/lame | Test réel après sélection, analyse des écarts et incertitudes |
| Interprétabilité | Méthode prévue | Grad-CAM exportable avec sélection explicite des exemples | Confrontation aux annotations et commentaire humain |
| Niveau ganglion/patiente | Ambiguïté identifiée | Règles pN sur catégories connues, limites explicites | Données complètes et évaluation adaptée, ou périmètre alternatif confirmé |
| Reproductibilité | Documentation seule | Dépendances, configurations, empreintes, tests et démonstration | Reproduction par un autre membre sur ses données et sa machine |
| Rapport, 15 pages maximum | Plan | Plan et document de travail rédigé sur les parties établies | Résultats réels, figures, discussion et mise en forme finale |
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

L'entraînement CAMELYON17, l'analyse clinique des images, la robustesse sur une cohorte réelle et la validation pN ne sont pas faits. Les scores du bruit artificiel ne doivent pas servir à remplir un tableau de résultats manquant. La présence d'un script de règles pN ne démontre pas la détection et la mesure des lésions.

Les groupes patient du challenge sont artificiels : le contrôle des identifiants fournis ne démontre pas l'indépendance biologique de toutes les lames. Une seule source hospitalière dans le test ne permet pas d'en déduire une robustesse à tous les hôpitaux.

## Prochain jalon vérifiable

Rendre accessible un dossier WILDS vérifié contenant `metadata.csv` et les images correspondantes, ou un accès au stockage déjà utilisé par le groupe. Créer un pilote, l'auditer, afficher ses images et consigner ses effectifs. Aucun entraînement lourd n'est nécessaire avant cette validation.

La date limite, les ressources de calcul et la clarification pN doivent être confirmées en parallèle. Les scripts ne peuvent pas deviner ces informations.

## Source

Sujet fourni *Projet 1 spécialisation — MBA 2*, pages 1 à 7 : contexte, alternatives de données, quatre étapes, livrables et grille d'évaluation. Voir aussi les références officielles dans `sources.md`. Les exigences du sujet et les choix du groupe sont distingués dans le cadrage.
