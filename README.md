# CAMELYON17 — Projet M2 Data Science & BI

Projet pédagogique de détection de métastases dans des images histopathologiques. Équipe de cinq étudiants.

**État : documentation et organisation initialisées. Le code préparé reste à importer. Aucun entraînement ni résultat sur les données réelles n'est publié dans ce dépôt.**

## Commencer ici

1. Lire le [périmètre, la roadmap et les livrables](docs/00_roadmap_et_livrables.md).
2. Consulter les [tâches GitHub](https://github.com/TZAKARIA97/camelyon17-m2-ds-bi/issues).
3. Importer le code depuis l'archive déjà préparée en suivant le [guide d'import](docs/00_importer_le_code_prepare.md).
4. Organiser la répartition du travail avec le [guide d'équipe](docs/00_organisation_equipe.md).
5. Suivre les [règles de contribution](CONTRIBUTING.md).

## Question scientifique

Détecter les régions tumorales au niveau des patchs, mesurer la généralisation entre centres hospitaliers et expliquer les erreurs. L'analyse au niveau ganglion/patiente dépend des annotations et de la couverture des données réellement disponibles.

**WILDS est une option de données autorisée par le sujet, pas une méthode de regroupement de tumeurs.** ASAP sert à visualiser les lames et annotations. L'organisation Agile sert à suivre le travail. Ces trois éléments remplissent des fonctions différentes.

Le sujet annonce le stade pN comme objectif et conditionne l'évaluation ganglion/patiente aux données disponibles. Cette tension doit être explicitement clarifiée avec l'enseignante avant de figer le périmètre. Une classification de patchs ne constitue pas, à elle seule, une prédiction validée de stade pN.

## Livrables demandés

| Livrable | Contenu |
| --- | --- |
| Code et pipeline reproductible | Préparation, entraînement, évaluation, visualisation et instructions d'exécution |
| Rapport, 15 pages maximum | Contexte, données, méthode, expériences, résultats, interprétabilité et limites |
| Soutenance, 10 minutes | Raisonnement, choix, résultats et limites ; chaque membre maîtrise l'ensemble |
| Suivi du projet | Contributions, décisions, retours et progression documentés |

Un dashboard n'est pas présenté ici comme un livrable obligatoire : les trois livrables explicites du sujet sont le code, le rapport et la présentation.

## Données et reproductibilité

- Aucun téléchargement massif avant un essai de lecture et un budget de stockage/calcul.
- Aucun mélange de patchs d'une même patiente entre entraînement, validation et test.
- Le test final ne sert pas au choix du modèle, des hyperparamètres ou du seuil.
- Les données, modèles entraînés, secrets et environnements locaux restent hors de Git.
- Les tests sur données synthétiques vérifient le logiciel ; ils ne mesurent pas sa validité médicale.

L'[état détaillé du dépôt](docs/00_etat_du_depot.md) distingue les éléments publiés des éléments restant à vérifier.

## Accès

Le dépôt était **public** lors de son initialisation le 6 novembre 2026. Ne pas y déposer d'informations confidentielles, de codes d'accès, de données médicales ni de documents de cours non autorisés à la diffusion.

Les invitations des quatre autres membres restent à effectuer après identification de leurs comptes GitHub. Les rôles proposés ne constituent pas des invitations.
