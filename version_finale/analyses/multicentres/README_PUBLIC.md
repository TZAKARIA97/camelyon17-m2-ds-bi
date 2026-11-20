# Résultats multicentres publiables

Cette partie publie uniquement la configuration et les métriques agrégées de l'expérience multicentre. Les inventaires, prédictions par patch, identifiants pseudonymisés, exemples d'erreurs et notebooks complets restent dans l'archive de travail du groupe et ne sont pas diffusés dans le dépôt public.

Le protocole compare les images originales, Reinhard et Macenko sur les mêmes ensembles. Le choix est réalisé sur les centres de validation 0 et 4, avec un rappel minimal visé de 0,95. La méthode originale est retenue avec une spécificité moyenne de 0,8967 et une ROC-AUC moyenne de 0,9752. Le seuil 0,31390092 est ensuite appliqué sans modification au centre 2 réservé au test.

Sur 864 patchs de test, la méthode obtient une ROC-AUC de 0,8715, un rappel de 0,6515, une précision de 0,9399 et une spécificité de 0,9817. Le recul du rappel interdit de conclure à une généralisation inter-centres suffisante.

Vérification :

```bash
python scripts/verifier_resultats_publics.py
```
