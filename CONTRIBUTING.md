# Contribuer au projet

## Une tâche, une branche, une relecture

1. Choisir une issue et préciser le responsable ainsi qu'un relecteur.
2. Mettre à jour la branche principale et créer une branche courte.
3. Réaliser un changement limité, compréhensible et accompagné de sa justification.
4. Vérifier le changement avec un contrôle adapté.
5. Ouvrir une pull request, indiquer l'issue concernée et demander une relecture.
6. Fusionner lorsque le changement est compris et vérifié.

Exemple depuis un terminal :

```bash
git clone https://github.com/TZAKARIA97/camelyon17-m2-ds-bi.git
cd camelyon17-m2-ds-bi
git switch main
git pull --ff-only
git switch -c feat/audit-donnees
```

Le clonage copie le projet. La nouvelle branche isole une modification jusqu'à sa relecture. Pour un débutant, l'éditeur de fichiers GitHub permet aussi de proposer une modification sur une nouvelle branche.

Ajouter les fichiers explicitement, après vérification :

```bash
git status
git diff
git add chemin/du/fichier.py
git commit -m "Vérifie la séparation des patientes entre ensembles"
git push -u origin feat/audit-donnees
```

Le chemin ci-dessus est un exemple à remplacer. Ne pas pousser de fichiers de données ou de secrets.

## Définition d'une tâche terminée

- Le livrable annoncé existe et le relecteur sait le retrouver.
- Le code concerné s'exécute avec des instructions écrites.
- Les contrôles pertinents passent, ou la limitation est explicitement documentée.
- Les hypothèses, données utilisées et résultats sont traçables.
- L'auteur et le relecteur savent expliquer la méthode et les limites.
- L'issue contient un lien vers la pull request ou l'artefact final.

## Code et explications

Écrire des fonctions courtes, des noms explicites et des docstrings. Commenter les raisons d'une décision, les hypothèses et les transformations importantes. Dans les notebooks, introduire chaque étape et interpréter chaque résultat. Commenter chaque ligne sans valeur explicative rend le code moins lisible.

Chaque expérimentation doit conserver sa configuration, la version du code, la définition des données, la graine aléatoire, les versions de dépendances et les métriques. Distinguer exécution de démonstration, test logiciel et expérience sur données réelles.

## Revue scientifique

Vérifier particulièrement les fuites entre patientes, le rôle du jeu de test, la définition des labels, les unités de résolution et les conclusions trop fortes. Une carte Grad-CAM ne prouve pas la justesse clinique d'une prédiction.

## Sources et IA

Citer les données, le code repris, les modèles préentraînés et les outils. Consigner l'aide de l'IA, les corrections humaines et les vérifications réalisées. Aucun membre ne doit présenter un résultat ou du code qu'il ne sait pas expliquer.
