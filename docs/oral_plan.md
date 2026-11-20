# Trame de soutenance finale — 15 minutes

Cette trame accompagne les **12 diapositives** du support final. La priorité est le raisonnement scientifique : problème, choix méthodologiques, expériences, résultats, limites et conclusion.

| Temps | Diapositive | Sujet | Message attendu |
|---|---:|---|---|
| 0:00–0:30 | 1 | Introduction | Sujet, équipe et trois axes de travail |
| 0:30–2:00 | 2 | Problématique | Du WSI au patient ; formuler la question inter-centres |
| 2:00–3:10 | 3 | Données | Cinq centres, WSI/XML et séparation par patient |
| 3:10–4:30 | 4 | Extraction | 112 µm, niveau 2, tissu et zone centrale |
| 4:30–5:50 | 5 | Modèle | ResNet18 gelé, 512 caractéristiques et logistique |
| 5:50–7:00 | 6 | Protocole | Trois expériences et gel du seuil avant le test |
| 7:00–8:00 | 7 | Niveau | Interpréter le gain du niveau 2 sans le surévaluer |
| 8:00–9:00 | 8 | Multicentres | Expliquer la règle qui conserve les images originales |
| 9:00–11:00 | 9 | Test centre 2 | Lire la matrice et insister sur les 92 faux négatifs |
| 11:00–12:00 | 10 | Erreurs | Domain shift, micrométastases et limite de Grad-CAM |
| 12:00–13:00 | 11 | Lame et pN | Séparer ce qui est codé de ce qui est validé |
| 13:00–14:15 | 12 | Conclusion | Bilan concret, réponse scientifique et perspectives |
| 14:15–15:00 | — | Marge | Transitions, retard et respiration avant les questions |

## Répartition entre cinq personnes

| Personne | Diapositives | Durée cible | Responsabilité |
|---|---:|---:|---|
| 1 | 1–2 | 2 min | Cadrage et problématique |
| 2 | 3–4 | 2 min 30 | Données et extraction |
| 3 | 5–6 | 2 min 30 | Modèle et protocole |
| 4 | 7–9 | 4 min | Résultats expérimentaux |
| 5 | 10–12 | 3 min 15 | Analyse critique et conclusion |

Chaque membre doit néanmoins pouvoir expliquer le pipeline complet et répondre sur les limites.

## Messages à ne pas rater

- Le découpage est réalisé par **patient**, pas aléatoirement par patch.
- Le champ de **112 µm** fixe la même surface anatomique malgré les différences de scanner.
- ResNet18 est utilisé comme **extracteur gelé** ; la régression logistique fournit une frontière contrôlable.
- Le niveau 2 est retenu avec une ROC-AUC de validation de **0,9738**.
- Les images originales sont conservées dans l’expérience multicentre historique.
- Sur le centre 2, la spécificité est élevée (**98,2 %**) mais le rappel chute à **65,2 %**.
- Les règles lame/pN sont codées, mais aucune métrique lame ni aucun kappa pN n’est revendiqué.

## Questions probables de l’enseignante

- **Pourquoi une séparation par patient ?** Des patchs d’une même lame partagent texture, coloration et artefacts ; les séparer entre apprentissage et validation créerait une fuite.
- **Pourquoi geler ResNet18 ?** Pour limiter le coût et le surapprentissage. La contrepartie est une représentation ImageNet non spécialisée à l’histologie.
- **Pourquoi retenir le niveau 2 ?** Il obtient 0,9738 contre 0,9682 au niveau 1, avec un coût de lecture inférieur à champ physique constant.
- **Pourquoi les images originales ?** La règle fixée privilégie la spécificité sous contrainte de rappel ; elles obtiennent 0,8967 de spécificité moyenne.
- **Que montre réellement le test final ?** 589 VN, 11 FP, 92 FN et 172 VP sur 864 patchs : faible taux de fausses alertes, mais sensibilité insuffisante hors centre.
- **Avez-vous validé le stade pN ?** Non. La chaîne est implémentée, mais les sorties finales ne sont pas exécutées dans l’archive collective.
- **Que prouve Grad-CAM ?** Une localisation qualitative des régions contributives, pas une causalité ni une validation clinique.
- **Pourquoi ne pas fusionner tous les scores ?** L’expérience multicentre historique est au niveau 1, tandis que la sélection finale du niveau de lecture concerne le pipeline niveau 2.

## Discipline orale

1. Lire la matrice de confusion avant de commenter les scores.
2. Distinguer systématiquement « codé », « exécuté » et « validé ».
3. Ne pas présenter la ROC-AUC de validation comme une preuve de généralisation.
4. Ne pas masquer l’absence de métriques lame et pN.
5. Terminer par la conclusion scientifique, pas par une liste de livrables.
