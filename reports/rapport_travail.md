# Détection de métastases — document de travail du rapport

**Statut : document de travail, non remise finale. Un pilote réel de 688 patchs et deux entraînements ont été exécutés. Le test final, la stabilité et le périmètre pN restent à traiter. Les résultats ci-dessous viennent du pilote réel, pas de la démonstration synthétique.**

## Résumé

Le projet étudie la détection de tissu tumoral dans des patchs histopathologiques et la généralisation à un centre hospitalier non utilisé pour apprendre. Sur un pilote réel CAMELYON17-WILDS, 416 patchs servent à apprendre et 128 à valider. Le dégel du dernier bloc de ResNet18 augmente l'AP de validation de 0,796 à 0,895, mais le modèle retenu manque encore 15 des 38 patchs positifs au seuil 0,5. Les 144 patchs de test n'ont fourni aucune prédiction. La petite cohorte, la sélection sur validation, la source communautaire et l'absence de répétitions limitent les conclusions ; aucune application au niveau patiente n'est validée.

À la fin du projet, remplacer ce résumé par : données réellement utilisées, méthode retenue, principaux résultats chiffrés et limite principale.

## 1. Problème et périmètre

Le sujet vise la détection de métastases dans des lames de ganglions lymphatiques et évoque une agrégation vers le stade pN. Le traitement patch permet de travailler sur de petites régions, mais une décision locale ne suffit pas à établir un stade patiente. L’étendue des lésions, la couverture des ganglions et les annotations nécessaires doivent être disponibles.

La question de travail est : dans quelle mesure une référence CNN préentraînée détecte-t-elle les patchs positifs et conserve-t-elle ses performances sur un centre non vu ? Les faux négatifs et les différences entre domaines sont étudiés avec leurs dénominateurs et leurs limites. Le système reste pédagogique, sans validation clinique.

WILDS est une alternative autorisée par le sujet. L’attente exacte concernant le pN doit être confirmée puisque le sujet mentionne à la fois cet objectif et une évaluation patiente conditionnée aux données. Le compte rendu de cette clarification est à ajouter ici.

## 2. Données du pilote réel

| Élément | État actuel / information à renseigner |
| --- | --- |
| Source, version et accès | CAMELYON17-WILDS 1.0, miroir communautaire figé ; équivalence binaire à l'original non démontrée |
| Licence et provenance | CC0 annoncée pour WILDS ; source, révision, CRC et SHA-256 conservés dans le bilan |
| Effectifs train/validation/test | 416 / 128 / 144 patchs ; 106 / 38 / 46 positifs |
| Groupes patient, lames et centres | 43 groupes artificiels, 49 lames ; train centres 0/3/4, validation 1, test 2 |
| Définition du label | Présence tumorale dans le carré central 32 × 32 d'un patch 96 × 96 |
| Sélection du pilote | Graine 42, tous les groupes disponibles, 16 patchs par groupe sans sélection par label |
| Matériel, temps et stockage | CPU, deux threads ; trois époques en 8,8 s et 11,4 s, hors acquisition et initialisation |

Pour la version officielle WILDS, les entrées sont des patchs 96 × 96 et le label positif dépend de la présence tumorale dans le carré central de 32 × 32. Les conventions de centre et de séparation sont prises dans le code officiel, pas déduites du nom d’un dossier d’un autre export.

Les groupes patient CAMELYON17 sont artificiels : on ne peut pas les interpréter comme une cohorte longitudinale réelle. Leurs identifiants servent aux contrôles de séparation, mais ne prouvent pas l’indépendance de tous les patients biologiques d’origine.

Les 33 560 patchs de validation interne `id_val` sont exclus, car ils partagent 26 groupes et 30 lames avec train ; les autres splits officiels restent inchangés. La validation du pilote contient 29,7 % de positifs alors que la validation complète est équilibrée : le sous-échantillonnage par groupe modifie la composition. Les tableaux, exemples de train, contrôles et limites de la source sont détaillés dans [le bilan du pilote](pilot_real/README.md). Une [paire WSI/XML originale](wsi_example/README.md) a aussi été vérifiée par MD5 et inspectée.

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

## 4. Expériences et résultats du pilote

| Expérience prévue | Hypothèse | Données/validation | Résultat réel |
| --- | --- | --- | --- |
| Référence gelée | Une représentation préentraînée fournit un premier niveau de discrimination | 416 train / 128 validation | AP 0,796 ; sensibilité 55,3 % ; 17 FN |
| Dernier bloc dégelé | Une adaptation partielle peut améliorer la validation, avec risque de surapprentissage | Même manifeste et même validation | AP 0,895 ; sensibilité 60,5 % ; 15 FN |
| Évaluation finale | Le modèle choisi conserve une utilité sur un centre non vu | 144 test réservés | Non réalisée pendant le pilote |

Le fine-tuning est retenu à l'époque 2 selon l'AP prévue, et non à l'époque 3 malgré une accuracy supérieure à cette dernière. Sa matrice de validation est TN=90, FP=0, FN=15, TP=23. L'accuracy de 88,3 % ne doit pas masquer 39,5 % de positifs manqués. L'absence de FP sur 90 négatifs ne garantit pas une spécificité parfaite ailleurs. La validation a servi à choisir le modèle ; le gain n'est pas une estimation indépendante sur le test. Les figures et fichiers exacts sont dans [le bilan détaillé](pilot_real/README.md).

Pour chaque résultat : donner l’observation exacte, son interprétation, puis sa limite. Une variation d’AP n’explique pas à elle seule la sensibilité au seuil choisi. Ne pas déduire une robustesse universelle d’un seul centre de test.

## 5. Analyse des erreurs et explications — premiers résultats

Trois Grad-CAM ont été exportés et inspectés selon une règle fixe : premier chemin trié par catégorie disponible. Le TP sélectionné présente une contribution surtout centrale ; le FN une contribution surtout sur le bord droit ; le TN possède une carte nulle. Le modèle retenu n'a aucun FP dans cette validation. Les trois exemples proviennent du groupe 020 et ne représentent pas toute la cohorte. Aucune correspondance aux masques pixel de ces exemples n'est démontrée ; la lecture d'une autre lame WSI ne remplace pas ce contrôle.

Sur la lame `patient_038_node_2`, les six patchs positifs sont manqués malgré l'amélioration globale du modèle. Sur `patient_039_node_1`, l'unique positif est le mieux classé, mais son score reste sous le seuil : AP=1 et sensibilité=0 peuvent donc coexister. Il faut distinguer classement des scores et décision au seuil retenu.

Les différences entre centres peuvent refléter la coloration, l’acquisition ou la composition des cas, mais les expériences doivent soutenir l’interprétation retenue. Sans comparaison contrôlée, conserver ces causes comme hypothèses.

## 6. Niveau patiente, limites et usage responsable

Le module de règles pN prend cinq catégories de ganglions connues. Il ne fournit ni mesure des lésions ni classification de ces catégories à partir des images. Aucune performance pN n’est démontrée par sa présence ou ses tests. Documenter ici le périmètre confirmé avec l’enseignante et l’évaluation effectivement possible.

Les limites à discuter après expérience incluent la taille et la sélection de la cohorte, le nombre de centres, les dépendances entre patchs, les annotations, le budget d’apprentissage, la stabilité entre graines et l’absence de validation clinique. Le modèle ne doit pas être présenté comme un outil opérationnel de diagnostic.

## 7. Reproductibilité, sources et contributions

Chaque expérience conserve le manifeste et son empreinte, les paramètres, les versions des dépendances, l’état Git, la durée, le checkpoint et les prédictions. Une reproduction par un autre membre du groupe reste à réaliser.

Les tests et la démonstration vérifient le logiciel sur des données artificielles. Ils n’évaluent aucune qualité médicale. Détailler les contributions réelles des cinq membres, l’usage de l’IA et les relectures, conformément aux consignes.

Références à mettre en forme : `docs/sources.md`. Plan et enveloppe de pages : `docs/rapport_plan.md`. À l’export final, vérifier les **15 pages maximum**, figures, couverture et références comprises sauf consigne contraire explicitement confirmée.

## Conclusion provisoire

Le pipeline fonctionne sur un premier pilote réel et une comparaison contrôlée a été réalisée. Le fine-tuning améliore le classement sur la validation, mais les faux négatifs restent nombreux. Une cohorte finale justifiée, plusieurs graines, une éventuelle règle de seuil décidée sur validation et un test après gel du protocole sont nécessaires avant une conclusion de généralisation. La reproduction et la relecture par le groupe restent à effectuer.
