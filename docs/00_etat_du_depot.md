# État du dépôt — 6 novembre 2026

## Disponible

- Code Python : inventaire WSI, conversion WILDS, sélection d'un pilote, audit et exploration.
- Entraînement ResNet18 et évaluation traçable par patch, centre et lame.
- Figures de résultats et export Grad-CAM sur succès et erreurs.
- Démonstration complète sans téléchargement avec 24 images artificielles.
- Tests de logique, calcul, entraînement/rechargement et provenance.
- Documentation pédagogique, notebooks, document de travail du rapport et trame d'oral.
- Issues GitHub et règles de contribution pour l'équipe.
- Acquisition partielle de 688 PNG réels, métadonnées et empreintes ; reprise contrôlée disponible.
- Une paire WSI/XML officielle vérifiée par MD5, ouverte avec OpenSlide et illustrée par des superpositions.
- Deux entraînements ImageNet réels et comparaison sur validation, figures et trois Grad-CAM commentés dans le [bilan du pilote](../reports/pilot_real/README.md).

L'ancien blocage d'accès aux fichiers est résolu ; l'import manuel du ZIP n'est plus nécessaire. Consulter `validation.md` pour les contrôles effectivement exécutés.

## Pas encore démontré

Le pilote contient 416 patchs de train, 128 de validation et 144 de test. La provenance communautaire de WILDS est explicitée ; son équivalence binaire au bundle officiel n'est pas démontrée. Les métadonnées et résultats agrégés sont publiés ; les données et checkpoints sont générés localement par les commandes.

Il reste à confirmer la cohorte finale et sa provenance, valider le périmètre pN, reproduire et élargir les expériences, analyser leur stabilité et les erreurs, évaluer une fois le protocole figé sur le test, finaliser le rapport de 15 pages et la soutenance de 10 minutes. Aucun diagnostic patient ni résultat pN n'est établi.

Les identifiants des quatre collègues, la date de remise et les ressources du groupe restent à confirmer. Le dépôt est public ; les invitations, protections de branches et un tableau GitHub Projects ne sont pas déclarés configurés.
