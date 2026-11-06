# Journal de décisions

| Date | Décision | Justification | État / preuve |
|---|---|---|---|
| 06/11/2026 | Démarrer par un dépôt de code et audit des données | Fiabilité avant calcul long | Code intégré, preuves techniques dans validation.md |
| 06/11/2026 | Retenir WILDS comme piste principale patch | Autorisé par les consignes ; accord de l'utilisateur | Pilote réel réalisé ; périmètre patient à confirmer |
| 06/11/2026 | Test WSI borné à une paire | Éviter un téléchargement massif prématuré | Paire MD5 vérifiée, 3 régions avec masques inspectées |
| 06/11/2026 | Comparer ResNet18 gelé et dernier bloc dégelé | Base simple à expliquer et comparaison contrôlée | Deux entraînements réels, AP validation 0,796 et 0,895 |
| 06/11/2026 | Séparer l'environnement ASAP si nécessaire | Conflit NumPy rapporté, pas diagnostiqué ici | Erreur complète et versions à collecter |

Pour chaque nouvelle décision : options, preuve, conséquence, date et auteur.

## Complément après audit du dépôt

- Le blocage d'accès au code a été résolu. Le dépôt existant est conservé, la documentation réconciliée et le code récupéré y est intégré.
- Ajout d’une démonstration CPU entièrement synthétique, sans téléchargement, pour expliquer et vérifier la chaîne. Ses chiffres ne sont pas des résultats du projet.
- Ajout d’un pilote sélectionné par groupes sans utiliser les labels, d’une exploration, de figures et d’un export Grad-CAM. Les scripts ne déclenchent pas de téléchargement massif.
- La règle de sélection de checkpoint reste l’AP de validation ; le seuil initial reste fixe à 0,5. Le test ne choisit ni le modèle ni les réglages.
- La version actuelle du dépôt remplace le ZIP initial pour démarrer ; les anciennes instructions d’import manuel sont retirées.
- Le rapport est un document de travail explicitement incomplet. Aucune conclusion médicale ou performance pN n’est inventée.

## Décisions sur le pilote réel

- Utiliser un miroir communautaire figé car le lien CodaLab essayé répond 404 ; consigner que l'équivalence binaire avec l'original n'est pas démontrée.
- Exclure les 33 560 patchs `id_val` qui partagent groupes/lames avec train. Conserver les train/val/test OOD originaux et les audits stricts.
- Après un premier échantillon sans positif dans test, inclure tous les groupes disponibles et tirer 16 patchs par groupe : 688 au total. Cette adaptation après lecture des effectifs est explicite.
- Accepter les PNG RGBA uniquement avec alpha opaque ; convertir en RGB au chargement, comme le prétraitement prévu. Préserver les fichiers source.
- Retenir le fine-tuning à l'époque 2 pour le pilote, selon l'AP de validation prévue, malgré une accuracy plus élevée à l'époque 3. Ne pas calculer les prédictions du test pendant cette phase.
- Le modèle choisi manque 15 positifs sur 38 en validation. Une AP supérieure ne justifie donc pas de déclarer la détection fiable.
- Revoir la cohorte, la stabilité et le seuil avant le test final. Les détails et preuves sont dans le [bilan du pilote](../reports/pilot_real/README.md).
