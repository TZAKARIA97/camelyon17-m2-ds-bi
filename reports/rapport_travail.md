# Détection de métastases — document de travail du rapport

**Statut : rédaction préparatoire, non remise finale. Aucune expérience CAMELYON17 réelle n’a encore été réalisée dans cet environnement. Les sections de résultats doivent être complétées, pas remplacées par les scores de démonstration.**

## Résumé

Le projet étudie la détection de tissu tumoral dans des patchs histopathologiques et la généralisation à un centre hospitalier non utilisé pour apprendre. Le pipeline prépare un manifeste traçable, vérifie la séparation des groupes, entraîne une référence ResNet18 et produit une évaluation accompagnée de visualisations Grad-CAM. À ce stade, son fonctionnement logiciel a été testé sur des images artificielles. La qualité sur CAMELYON17 et l’applicabilité au niveau patiente restent à établir.

À la fin du projet, remplacer ce résumé par : données réellement utilisées, méthode retenue, principaux résultats chiffrés et limite principale.

## 1. Problème et périmètre

Le sujet vise la détection de métastases dans des lames de ganglions lymphatiques et évoque une agrégation vers le stade pN. Le traitement patch permet de travailler sur de petites régions, mais une décision locale ne suffit pas à établir un stade patiente. L’étendue des lésions, la couverture des ganglions et les annotations nécessaires doivent être disponibles.

La question de travail est : dans quelle mesure une référence CNN préentraînée détecte-t-elle les patchs positifs et conserve-t-elle ses performances sur un centre non vu ? Les faux négatifs et les différences entre domaines sont étudiés avec leurs dénominateurs et leurs limites. Le système reste pédagogique, sans validation clinique.

WILDS est une alternative autorisée par le sujet. L’attente exacte concernant le pN doit être confirmée puisque le sujet mentionne à la fois cet objectif et une évaluation patiente conditionnée aux données. Le compte rendu de cette clarification est à ajouter ici.

## 2. Données réellement utilisées — à compléter

| Élément | État actuel / information à renseigner |
| --- | --- |
| Source, version et accès | WILDS envisagé ; aucun lot réel accessible ici |
| Licence et provenance | À vérifier sur la source retenue |
| Effectifs train/validation/test | Non mesurés sur données réelles |
| Groupes patient, lames et centres | À extraire du manifeste audité |
| Définition du label | À confirmer sur l’export retenu ; WILDS utilise la région centrale |
| Sélection du pilote | Script reproductible disponible ; cohorte réelle non sélectionnée |
| Matériel, temps et stockage | Environnement d’exécution du groupe à renseigner |

Pour la version officielle WILDS, les entrées sont des patchs 96 × 96 et le label positif dépend de la présence tumorale dans le carré central de 32 × 32. Les conventions de centre et de séparation sont prises dans le code officiel, pas déduites du nom d’un dossier d’un autre export.

Les groupes patient CAMELYON17 sont artificiels : on ne peut pas les interpréter comme une cohorte longitudinale réelle. Leurs identifiants servent aux contrôles de séparation, mais ne prouvent pas l’indépendance de tous les patients biologiques d’origine.

Insérer ici le tableau `counts.csv`, des exemples de train et les observations de qualité/annotation. Expliquer la représentativité et les limites de la sous-cohorte.

## 3. Méthode implémentée

### 3.1 Préparation

Le manifeste lie chaque image à son label, son groupe patient, sa lame, son centre et son ensemble. L’audit refuse les labels inconnus, les chemins dupliqués, les groupes partagés entre ensembles et les centres OOD incohérents. Il ne remplace pas le contrôle visuel de l’annotation ni une recherche de copies renommées.

Le pilote sélectionne des groupes par ensemble/centre, puis un nombre borné de patchs par groupe. La sélection n’utilise pas le label. Elle réduit le calcul et peut permettre de copier seulement les fichiers utiles depuis un stockage déjà disponible ; elle n’annule pas un téléchargement complet déjà réalisé.

### 3.2 Modèle et comparaison

La référence utilise ResNet18 avec des poids ImageNet et une sortie binaire. Le backbone est gelé ; seule la dernière couche apprend. L’amélioration préparée dégèle le dernier bloc tout en gardant les autres paramètres identiques. Les images sont redimensionnées sans crop et normalisées numériquement avec les constantes ImageNet.

Les configurations initiales utilisent trois époques pour le pilote, une taille 96, un batch 32, un taux d’apprentissage 0,001 et un seuil fixe 0,5. Ce sont des paramètres de départ, pas des hyperparamètres démontrés optimaux. Les paramètres réellement retenus et leurs justifications doivent remplacer cette description si les expériences les modifient.

Le checkpoint est choisi sur l’Average Precision de validation. Le test final n’intervient pas dans la sélection. En cas de modification du seuil, sa règle est décidée sur validation avant l’évaluation finale.

### 3.3 Évaluation et interprétabilité

Les métriques incluent matrice de confusion, sensibilité, spécificité, précision, F1, accuracy, ROC-AUC et AP. Les sorties conservent les effectifs et les cas non définis. Les résultats sont déclinés par centre et par lame, au niveau patch.

Grad-CAM est calculé sur le dernier bloc convolutionnel pour la classe tumorale. Les exemples proviennent de catégories correctes et erronées selon une règle de sélection écrite. Leur interprétation nécessite une confrontation aux annotations ; une carte plausible ne prouve pas une causalité ni une validité histologique.

## 4. Expériences et résultats — non réalisés sur données réelles

| Expérience prévue | Hypothèse | Données/validation | Résultat réel |
| --- | --- | --- | --- |
| Référence gelée | Une représentation préentraînée fournit un premier niveau de discrimination | À préciser après audit | Non réalisé |
| Dernier bloc dégelé | Une adaptation partielle peut améliorer la validation, avec risque de surapprentissage | Même manifeste et même validation | Non réalisé |
| Évaluation finale | Le modèle choisi conserve une utilité sur un centre non vu | Test réservé | Non réalisé |

Ajouter les courbes d’apprentissage, le tableau comparatif, les effectifs, la matrice finale, les métriques et les erreurs. Ne pas insérer les sorties de `demo_synthetic` dans cette section.

Pour chaque résultat : donner l’observation exacte, son interprétation, puis sa limite. Une variation d’AP n’explique pas à elle seule la sensibilité au seuil choisi. Ne pas déduire une robustesse universelle d’un seul centre de test.

## 5. Analyse des erreurs et explications — à compléter

Présenter des faux négatifs, faux positifs et prédictions correctes, avec leurs références et la règle de sélection. Décrire ce qui est observé sans inventer une cause histologique. Relier les cartes Grad-CAM aux zones annotées si disponibles ; signaler les cas ambigus et les cartes nulles.

Les différences entre centres peuvent refléter la coloration, l’acquisition ou la composition des cas, mais les expériences doivent soutenir l’interprétation retenue. Sans comparaison contrôlée, conserver ces causes comme hypothèses.

## 6. Niveau patiente, limites et usage responsable

Le module de règles pN prend cinq catégories de ganglions connues. Il ne fournit ni mesure des lésions ni classification de ces catégories à partir des images. Aucune performance pN n’est démontrée par sa présence ou ses tests. Documenter ici le périmètre confirmé avec l’enseignante et l’évaluation effectivement possible.

Les limites à discuter après expérience incluent la taille et la sélection de la cohorte, le nombre de centres, les dépendances entre patchs, les annotations, le budget d’apprentissage, la stabilité entre graines et l’absence de validation clinique. Le modèle ne doit pas être présenté comme un outil opérationnel de diagnostic.

## 7. Reproductibilité, sources et contributions

Chaque expérience conserve le manifeste et son empreinte, les paramètres, les versions des dépendances, l’état Git, la durée, le checkpoint et les prédictions. Une reproduction par un autre membre du groupe reste à réaliser.

Les tests et la démonstration vérifient le logiciel sur des données artificielles. Ils n’évaluent aucune qualité médicale. Détailler les contributions réelles des cinq membres, l’usage de l’IA et les relectures, conformément aux consignes.

Références à mettre en forme : `docs/sources.md`. Plan et enveloppe de pages : `docs/rapport_plan.md`. À l’export final, vérifier les **15 pages maximum**, figures, couverture et références comprises sauf consigne contraire explicitement confirmée.

## Conclusion provisoire

Le pipeline est implémenté et sa chaîne logicielle fonctionne sur une démonstration synthétique. La question scientifique reste ouverte tant que les expériences réelles, leur analyse et l’évaluation des limites ne sont pas réalisées.
