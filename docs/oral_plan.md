# Trame de soutenance finale — 12 diapositives, 15 minutes maximum

La soutenance principale contient 12 diapositives. Les trois annexes restent après la conclusion et ne sont utilisées que pour répondre aux questions.

## Chronométrage cible

| Temps | Diapositive | Sujet | Message attendu |
|---|---:|---|---|
| 0:00–0:30 | 1 | Introduction | Sujet, équipe et portée du projet |
| 0:30–2:30 | 2 | Problématique | Du WSI au patient et question de généralisation |
| 2:30–3:50 | 3 | Volumes | 85 lames sélectionnées, 45 utilisées pour le développement, 13 367 patchs |
| 3:50–5:00 | 4 | Extraction | 112 µm, niveau 2, tissu et zone centrale |
| 5:00–6:10 | 5 | Modèle | ResNet18 gelé, 512 caractéristiques, logistique et 40 tests |
| 6:10–7:10 | 6 | Protocoles | Séparer le pipeline final de l’étude multicentre exploratoire |
| 7:10–8:00 | 7 | Niveau | Interpréter le gain du niveau 2 |
| 8:00–9:00 | 8 | Normalisation | Expliquer la règle qui conserve les images originales |
| 9:00–10:45 | 9 | Centre 2 | Lire la matrice, le seuil 0,3139 et les 92 faux négatifs |
| 10:45–11:45 | 10 | Hypothèses | Domain shift, petites lésions et seuil hors domaine |
| 11:45–12:45 | 11 | Lame et pN | Séparer ce qui est codé de ce qui est validé |
| 12:45–14:00 | 12 | Conclusion | Bilan concret, limite scientifique et perspectives |
| 14:00–15:00 | — | Marge | Transitions, retard éventuel et respiration |

## Répartition entre cinq personnes

| Personne | Diapositives | Durée cible | Responsabilité |
|---|---:|---:|---|
| 1 | 1–2 | 2 min 30 | Cadrage et problématique |
| 2 | 3–4 | 2 min 30 | Volumes, séparation et extraction |
| 3 | 5–7 | 3 min | Architecture, protocoles et choix du niveau 2 |
| 4 | 8–9 | 2 min 45 | Normalisation et test du centre non vu |
| 5 | 10–12 | 3 min 15 | Analyse critique, portée lame/pN et conclusion |

Chaque membre présente un bloc cohérent et doit pouvoir expliquer le pipeline complet.

## Annexes de secours

- **A1 — Volumes exacts :** distingue les 85 lames du pipeline final des 14 lames de l’étude multicentre.
- **A2 — Paramètres et contrôles :** 112 µm, 224 × 224, zone centrale, quotas, 512 caractéristiques et 40 tests.
- **A3 — Suite expérimentale :** analyse des faux négatifs, recalibrage, adaptation de domaine et validation lame/pN.

Les annexes ne font pas partie du chronométrage. Ne pas les afficher spontanément.

## Messages à ne pas rater

- Le pipeline final utilise réellement 35 lames d’entraînement et 10 de validation au niveau 2, soit 13 367 patchs.
- Les 40 lames du test lame/pN sont sélectionnées mais les sorties finales ne sont pas exécutées.
- L’étude multicentre est un protocole exploratoire distinct : 14 lames, 14 patientes et 3 189 patchs au niveau 1.
- Les scores des deux protocoles ne doivent jamais être fusionnés.
- Le niveau 2 atteint 0,9738 de ROC-AUC en validation.
- Les images originales obtiennent 0,8967 de spécificité moyenne dans l’étude multicentre.
- Sur le centre 2, le seuil est 0,3139 et le rappel chute à 65,2 %.
- Les hypothèses sur les faux négatifs ne constituent pas des causalités démontrées.
- Les règles lame/pN sont codées, mais aucune métrique lame ni aucun kappa pN n’est revendiqué.

## Questions probables

- **Pourquoi une séparation par patiente ?** Pour empêcher qu’une même lame ou une même patiente influence à la fois l’apprentissage et l’évaluation.
- **Pourquoi 112 µm ?** Pour conserver le même champ anatomique malgré les différences de scanner et de résolution.
- **Pourquoi geler ResNet18 ?** Pour limiter le coût et le surapprentissage. La représentation reste toutefois issue d’ImageNet.
- **Pourquoi le niveau 2 ?** Il obtient 0,9738 contre 0,9682 au niveau 1, avec un coût de lecture inférieur.
- **Pourquoi les images originales ?** Elles donnent la meilleure spécificité moyenne sous la règle de rappel définie.
- **Que montre le test final ?** 589 VN, 11 FP, 92 FN et 172 VP sur 864 patchs. La spécificité reste forte, mais le rappel devient insuffisant.
- **Avez-vous validé le stade pN ?** Non. La chaîne existe dans le code, mais l’évaluation finale n’est pas exécutée.
- **Que prouve Grad-CAM ?** Une localisation qualitative des régions contributives, pas une causalité ni une validation clinique.

## Discipline orale

1. Ne pas lire les slides.
2. Donner les volumes avant les pourcentages.
3. Lire la matrice de confusion avant les métriques.
4. Distinguer « sélectionné », « exécuté », « codé » et « validé ».
5. Terminer par la conclusion scientifique, puis s’arrêter.
