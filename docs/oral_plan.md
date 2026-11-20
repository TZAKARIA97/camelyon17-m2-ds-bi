# Trame de soutenance finale — 15 minutes

Cette trame accompagne les 15 diapositives du support final. Elle couvre la chaîne du projet, les choix de code, les expériences disponibles et les limites réellement observées.

| Temps | Diapositive | Sujet | Message attendu |
|---|---:|---|---|
| 0:00–0:45 | 1 | Introduction | Besoin médical, objectif et portée pédagogique |
| 0:45–1:40 | 2 | Problématique | Distinguer patch, lame et patiente |
| 1:40–2:40 | 3 | Trajectoire et livrables | Relier le projet aux consignes et annoncer l’état réel |
| 2:40–3:35 | 4 | Données | CAMELYON17, centres, XML et hiérarchie |
| 3:35–4:30 | 5 | Architecture | Responsabilité de chaque module du dépôt |
| 4:30–5:30 | 6 | Séparation | Prévenir les fuites par patiente et geler le test |
| 5:30–6:35 | 7 | Extraction | Surface 112 µm, niveau, MPP, tissu et étiquetage |
| 6:35–7:35 | 8 | Modèle | ResNet18 gelé, 512 caractéristiques et logistique |
| 7:35–8:35 | 9 | Protocole | Questions expérimentales, métriques et règle de choix |
| 8:35–9:30 | 10 | Niveau | Interpréter le gain du niveau 2 sans le surévaluer |
| 9:30–10:35 | 11 | Multicentres | Distinguer l’expérience historique niveau 1 du pipeline final niveau 2 |
| 10:35–11:45 | 12 | Test centre 2 | Lire la matrice avant les scores et expliquer les faux négatifs |
| 11:45–12:45 | 13 | Erreurs et Grad-CAM | Formuler des hypothèses sans prétendre démontrer une causalité |
| 12:45–13:50 | 14 | Carte, lame et pN | Distinguer code implémenté et évaluation exécutée |
| 13:50–15:00 | 15 | Conclusion | Répondre à la problématique et donner les prochaines étapes |

## Répartition orale proposée

La répartition doit suivre des blocs cohérents. Chaque membre doit néanmoins pouvoir expliquer l’ensemble du pipeline.

| Bloc | Diapositives | Contenu |
|---|---:|---|
| Cadrage et données | 1 à 4 | Besoin, unités, trajectoire, données |
| Préparation et code | 5 à 7 | Architecture, séparation, extraction |
| Modélisation | 8 à 9 | ResNet18, logistique, protocole |
| Résultats | 10 à 12 | Niveau, robustesse multicentre, test |
| Recul critique | 13 à 15 | Erreurs, portée pN, conclusion |

## Questions probables de l’enseignante

- **Pourquoi ne pas découper aléatoirement les patchs ?** Des patchs proches d’une même lame partagent texture, coloration et artefacts. Les séparer entre entraînement et validation surestimerait la généralisation.
- **Pourquoi une surface de 112 µm ?** Elle fixe le champ anatomique malgré les différences de MPP et de niveau de lecture. Les patchs sont ensuite redimensionnés en 224 × 224 pour ResNet18.
- **Pourquoi geler ResNet18 ?** Le calcul et le risque de surapprentissage diminuent. La limite est une représentation non spécialisée à l’histologie.
- **Pourquoi retenir le niveau 2 ?** L’AUC de validation passe de 0,9682 à 0,9738, avec un coût de lecture inférieur. Le gain reste faible et local à cette expérience.
- **Pourquoi retenir les images originales alors que Reinhard a une AUC légèrement supérieure ?** La règle fixée avant le test privilégie la spécificité moyenne sous une contrainte de rappel de 95 % par centre. Les images originales obtiennent 0,8967 contre 0,8750 pour Reinhard.
- **Que montre le test final ?** Sur 864 patchs du centre 2, le modèle obtient 172 VP, 589 VN, 11 FP et 92 FN. La spécificité atteint 98,2 %, mais le rappel chute à 65,2 %.
- **Avez-vous validé le stade pN ?** Non. Les cartes de chaleur, la classe de lame et les règles pN sont codées, mais les cellules finales ne contiennent pas de sorties exécutées dans l’archive collective.
- **Que prouve Grad-CAM ?** Il aide à localiser les régions qui contribuent au score. Il ne prouve ni causalité ni correspondance avec l’annotation d’un pathologiste.
- **Les résultats multicentres et le niveau 2 appartiennent-ils à la même expérience ?** Non. L’étude multicentre publiée utilise les patchs du prototype au niveau 1. Elle complète l’analyse, mais ses scores ne doivent pas être fusionnés avec ceux du pipeline final niveau 2.
- **Quelle est la conclusion scientifique ?** La discrimination patch est forte en validation, mais la baisse de rappel hors centre empêche une revendication clinique ou pN.

## Règles de présentation

1. Annoncer le dénominateur avant un pourcentage.
2. Lire la matrice de confusion avant de commenter l’accuracy.
3. Distinguer systématiquement « codé », « exécuté » et « validé ».
4. Ne pas présenter les scores de démonstration synthétique comme des résultats CAMELYON17.
5. Ne pas masquer l’absence de métriques lame et pN.
