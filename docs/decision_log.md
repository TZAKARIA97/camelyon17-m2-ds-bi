# Journal de décisions

| Date | Décision | Justification | État / preuve |
|---|---|---|---|
| 06/11/2026 | Démarrer par un dépôt de code et audit des données | Fiabilité avant calcul long | Code intégré, preuves techniques dans validation.md |
| 06/11/2026 | Accepter WILDS comme piste principale patch | Autorisé par les consignes | Périmètre patient à confirmer |
| 06/11/2026 | Test WSI borné à une paire et 6 patches | Éviter un téléchargement massif prématuré | Données réelles non fournies |
| 06/11/2026 | Prévoir ResNet18 gelé | Base simple à expliquer et comparer | Entraînement réel non réalisé ; démonstration synthétique testée |
| 06/11/2026 | Séparer l'environnement ASAP si nécessaire | Conflit NumPy rapporté, pas diagnostiqué ici | Erreur complète et versions à collecter |

Pour chaque nouvelle décision : options, preuve, conséquence, date et auteur.

## Complément après audit du dépôt

- Le blocage d'accès au code a été résolu. Le dépôt existant est conservé, la documentation réconciliée et le code récupéré y est intégré.
- Ajout d’une démonstration CPU entièrement synthétique, sans téléchargement, pour expliquer et vérifier la chaîne. Ses chiffres ne sont pas des résultats du projet.
- Ajout d’un pilote sélectionné par groupes sans utiliser les labels, d’une exploration, de figures et d’un export Grad-CAM. Les scripts ne déclenchent pas de téléchargement massif.
- La règle de sélection de checkpoint reste l’AP de validation ; le seuil initial reste fixe à 0,5. Le test ne choisit ni le modèle ni les réglages.
- La version actuelle du dépôt remplace le ZIP initial pour démarrer ; les anciennes instructions d’import manuel sont retirées.
- Le rapport est un document de travail explicitement incomplet. Aucune conclusion médicale ou performance pN n’est inventée.
