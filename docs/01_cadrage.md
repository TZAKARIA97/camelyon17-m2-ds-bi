# Cadrage — version de démarrage, 6 novembre 2026

## Objectif et contraintes

Reconnaître le tissu tumoral sur des patches de ganglions, analyser les erreurs et la généralisation inter-hôpitaux. Comprendre la chaîne patch → lame/ganglion → patient. Groupe de cinq, temps limité, capacité GPU et deadline non communiquées.

Question : dans quelle mesure un CNN en transfer learning généralise-t-il à un centre non utilisé pour apprendre ? La mortalité, la survie et le clustering non supervisé ne sont pas les objectifs des consignes.

## Exigences confirmées dans le PDF

- Pipeline reproductible ; rapport 15 pages maximum ; oral 10 minutes.
- Compréhension clinique, exploration, justification des prétraitements et de la modélisation, séparation sans fuite.
- Analyse des faux négatifs, robustesse entre centres, une méthode d'interprétabilité et discussion responsable.
- Suivi 20 %, données 25 %, modèles/méthodologie 25 %, interprétation/éthique 10 %, oral 20 %.
- Chaque membre contribue et comprend l'ensemble. L'usage d'IA et le code externe doivent être transparents et cités.
- Aucun dashboard n'est explicitement exigé. La date limite n'est pas indiquée dans les deux PDF fournis.

## Point à faire confirmer à l'enseignante

Le pN figure dans l'objectif et la grille, mais l'étape 4 prévoit une évaluation ganglion/patient « si les données le permettent ». WILDS est explicitement autorisé. Confirmer si, en choisissant WILDS, une étude patch approfondie avec explication des limites pN suffit, ou si une démonstration patient est attendue. Ne pas interpréter cette ambiguïté comme une dispense acquise.

## Décision de travail retenue

CAMELYON17-WILDS 1.0 sert de pipeline principal patch. Une paire WSI/XML originale apporte la compréhension de la donnée brute. Le [guide d'accès](acces_donnees.md) permet de récupérer un pilote sans télécharger les six archives complètes. Un second pipeline complet WSI n'est pas imposé par nous : son coût sera arbitré après faisabilité et réponse pédagogique. Limiter d'abord les expériences à une baseline et une amélioration isolée.

ASAP reste une piste de visualisation, QuPath une alternative. OpenSlide est indépendant du module Python ASAP. Un éventuel NumPy 1 dédié ne doit pas modifier l'environnement IA partagé. Un outil installé n'est pas une preuve de faisabilité tant qu'une image et son annotation ne sont pas correctement lues.

## Limites dès le départ

WILDS seul n'offre pas une reconstruction exhaustive de toutes les lésions des cinq ganglions. Le pN exige la taille physique/type des lésions et les ganglions complets. Une moyenne de probabilités ou un nombre de patches positifs ne suffit pas. Les patients CAMELYON17 sont des regroupements artificiels de lames ; ne pas les décrire comme des cohortes longitudinales réelles.

## Validation du premier jalon

- Dépôt et documentation prêts ; tests logiciels passants.
- Accès de chaque collègue confirmé séparément.
- Une paire TIFF/XML ou un lot WILDS de provenance vérifiée.
- Inventaire réel et audit des identifiants réussis.
- Première visualisation relue par deux membres.
- Choix du périmètre, des ressources et du protocole écrit.

La paire WSI/XML a été téléchargée, vérifiée et ouverte avec OpenSlide. Le lot WILDS et ses contrôles sont décrits dans le guide d'accès et le bilan du pilote. La relecture par deux membres et les accès des collègues ne sont pas déclarés acquis.
