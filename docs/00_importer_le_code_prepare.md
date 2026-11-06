# Importer le code déjà préparé

## Pourquoi cette étape reste ouverte

L'archive **CAMELYON17_Demarrage_M2.zip** a été préparée dans la conversation de travail. L'environnement contenant ces fichiers n'était pas accessible lors de l'initialisation du dépôt. La documentation présente ne remplace pas les scripts, le notebook et leurs tests.

## Import par l'interface GitHub

1. Télécharger l'archive depuis la conversation de travail et la décompresser sur son ordinateur.
2. Ouvrir le dossier intérieur `camelyon17-m2-ds-bi`. Les dossiers `src`, `tests`, `configs`, `docs` et les fichiers de dépendances doivent se trouver à ce niveau.
3. Dans GitHub, créer une branche `setup/import-code` à partir de `main`.
4. Ajouter les fichiers et dossiers de l'archive à la racine du dépôt sur cette branche. Ne pas ajouter le ZIP ni un second dossier englobant `camelyon17-m2-ds-bi`.
5. Inclure les fichiers de configuration et modèles GitHub utiles, qui peuvent être masqués par le système.
6. Examiner les différences des fichiers communs : README, règles d'exclusion et modèles GitHub. Réconcilier leur contenu au lieu d'écraser sans lecture.
7. Suivre les instructions de dépendances de l'archive et exécuter les tests disponibles.
8. Ouvrir une pull request ; renseigner les commandes exécutées, résultats et limites.
9. Mettre à jour `docs/00_etat_du_depot.md` et le README pour décrire l'état réellement atteint, puis fusionner après relecture.

## Critères de réussite

- Les fichiers attendus existent sur la branche, notamment le code, les tests, la configuration et le notebook.
- Aucun fichier d'environnement, secret, jeu de données ou modèle volumineux n'est ajouté.
- Les commandes de démarrage fonctionnent dans un environnement propre documenté.
- Les tests exécutés ont une sortie conservée dans le compte rendu.
- Le README distingue encore les validations sur données synthétiques et les résultats sur données réelles.

Un succès de tests logiciels ne prouve pas la qualité des prédictions médicales. L'entraînement et l'évaluation sur les données retenues sont des tâches distinctes.
