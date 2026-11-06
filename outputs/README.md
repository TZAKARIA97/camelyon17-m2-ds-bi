# Sorties locales

Les scripts écrivent ici dans un nouveau dossier par exécution. Images médicales, prédictions, environnements et checkpoints restent hors Git.

- `demo_synthetic/` : démonstration entièrement artificielle ; aucune performance clinique.
- Une expérience réelle : configuration, versions, historique, durée et `best.pt`.
- Une évaluation : `metrics.json`, `predictions.csv`, `provenance.json`.
- Un rapport : PNG de confusion et ROC/PR, tables par centre/lame, texte descriptif.
- Grad-CAM : images, sélection CSV, provenance et index commentable.

Les fichiers choisis pour le rapport final peuvent être copiés dans `reports/` après vérification de leur provenance, de leur diffusion et de l'absence de données sensibles. Ne pas publier les sorties de démonstration comme résultats réels.
