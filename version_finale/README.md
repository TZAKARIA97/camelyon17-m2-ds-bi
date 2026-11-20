# Version finale collective

Cette arborescence reprend la dernière version livrée par le groupe. Le protocole retenu utilise des patchs couvrant 112 µm, lus au niveau 2 puis redimensionnés à 224 × 224 pixels. ResNet18 sert d'extracteur fixe et une régression logistique produit la probabilité tumorale.

## Ordre d'exécution

1. Exécuter les parties 1 à 4 de `notebooks/01_preparation_donnees.ipynb`.
2. Comparer les variantes avec `python extract_patches.py --variante base centre niveaux`.
3. Extraire la variante finale avec `python extract_patches.py --variante retenue`.
4. Exécuter les parties 1 à 4 de `notebooks/02_modelisation_evaluation.ipynb`.
5. Produire les cartes avec `python cartes_chaleur.py --niveau 2`.
6. Régler la chaîne sur la validation et figer `resultats/reglages_figes.json`.
7. Ouvrir le test une seule fois, puis analyser les erreurs.

Les données lourdes, patchs, cartes et modèles restent hors Git. `resultats_publics/selection_niveau.json` conserve les chiffres de sélection visibles dans le notebook transmis.

## Contrôles légers

```bash
python -m compileall -q .
python analyses/multicentres/scripts/verifier_resultats_publics.py
```

La vérification multicentre relit uniquement les résultats agrégés publiés. Les inventaires et prédictions détaillés restent hors du dépôt public. Une reproduction complète nécessite les lames, les poids et les fichiers détaillés détenus par le groupe.
