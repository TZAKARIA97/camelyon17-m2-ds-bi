# Validation technique — 6 novembre 2026

## Résultats vérifiés

| Contrôle | Résultat | Portée |
| --- | --- | --- |
| Suite automatisée | **35 tests réussis, aucun ignoré** | Logique, HTTP Range borné, reprise sans écrasement, RGB/RGBA opaque, exclusion ID explicite, XML, calculs, configuration, provenance et pipeline tensoriel |
| Démonstration complète | **Terminée** sur 24 images de bruit | Audit → exploration → entraînement → évaluation → rapport → Grad-CAM |
| Poids ImageNet | **Téléchargés et chargés** ; passe avant avec tête binaire réussie | Vérification des poids officiels, aucune performance médicale |
| Fine-tuning et perte pondérée | **Exécutés** pendant une époque synthétique | Vérification du second mode, pas comparaison scientifique |
| Figures | Matrice de confusion et Grad-CAM inspectées visuellement | Lisibilité, alignement, statut synthétique visible |
| Notebooks | Schéma valide ; **9 cellules de code exécutées séquentiellement en Python** | 4 cellules d’exploration et 5 de lecture des résultats |
| Compilation et liens | Modules compilés, liens Markdown locaux contrôlés | Absence d’erreur de syntaxe et de liens internes manquants |
| Publication | Code, métadonnées, résultats et figures sélectionnées | Archives, cohorte d'images brutes et checkpoints hors Git |
| Pilote réel WILDS | **688 PNG RGBA opaques vérifiés**, aucun doublon exact fichier/pixels | CRC ZIP, SHA-256, dimensions, séparations et provenance du miroir conservés |
| Paire WSI/XML | **Deux MD5 conformes** à la distribution officielle | Une lame, trois régions avec masques et superpositions |
| Comparaison réelle | **Deux modèles, trois époques chacun** | 416 patchs train ; 128 de validation ; AP 0,796 et 0,895 |
| Interprétation réelle | Matrice, ROC/PR et **3 Grad-CAM inspectés** | Un TP, un TN à carte nulle et un FN ; aucun FP disponible pour le modèle retenu |

La suite inclut les fuites de patientes/lames, les centres OOD, les doublons et alias de chemins, les métadonnées manquantes, les masques XML, les métriques non définies, les règles pN sur catégories connues, la sélection de groupes, les paramètres invalides et la détection de manifeste/prédictions modifiés.

Le test d’intégration crée des images artificielles, apprend une époque avec des poids aléatoires, sauvegarde puis recharge le checkpoint et évalue un ensemble distinct. Le statut synthétique et la provenance des poids sont enregistrés. La démonstration vérifie aussi les exports graphiques et l’explication de prédictions correctes/erronées disponibles ; les catégories absentes ne sont pas fabriquées.

## Commandes de reproduction

Après installation du socle, de la visualisation et de PyTorch CPU selon le README :

```bash
python -m unittest discover -s tests -v
python -m src.demo --out outputs/demo_synthetic
python -m compileall -q src tests
```

Donner un nouveau dossier de sortie si la démonstration a déjà été exécutée. Les tests tensoriels sont ignorés si PyTorch/torchvision sont absents : ne pas annoncer une validation complète dans ce cas.

## Limite spécifique des notebooks

L’environnement de vérification refuse l’ouverture de sockets par le noyau Jupyter, en TCP comme en IPC. Le démarrage du noyau n’a donc pas pu être validé ici. En remplacement, chaque cellule de code a été exécutée dans l’ordre dans un contexte Python commun par notebook, avec les données de démonstration ; le schéma des deux fichiers a aussi été validé.

Ce contrôle valide le code des cellules. Il ne remplace pas un essai de l’interface Jupyter/VS Code et du noyau choisi sur le poste du groupe. Les scripts en ligne de commande ne dépendent pas du noyau Jupyter et ont fonctionné de bout en bout.

## Environnement vérifié

Python 3.12 ; NumPy 2.3.5 ; pandas 2.2.3 ; Pillow 13.0.0 ; scikit-learn 1.8.0 ; torch 2.15.0+cpu ; torchvision 0.29.2+cpu ; matplotlib 3.10.8. Outils de notebooks installés : nbformat 5.11.1, nbclient 0.11.0, ipykernel 7.4.0.

OpenSlide Python 1.4.7 et openslide-bin 4.0.1.2 ont ouvert la vraie lame `patient_089_node_3.tif`, dont le MD5 correspond à la distribution officielle. Trois régions, masques et superpositions ont été exportés ; une miniature annotée et une superposition ont été inspectées visuellement. Le XML réel utilise `Tumor`, alias maintenant pris en charge et testé. Windows, CUDA et le poste ASAP du groupe ne sont pas validés par ces contrôles Linux/CPU.

## Validation scientifique restant à effectuer

- Confirmation de la provenance du miroir et des conventions spatiales entre WILDS et WSI ; la lecture de la paire originale ne valide pas tous les patchs du miroir.
- Cohorte finale plus large, justifiée, auditée et relue par le groupe.
- Stabilité sur plusieurs graines et éventuel choix de seuil selon un objectif défini sur validation.
- Évaluation finale sur le test, qui n'a encore fourni aucune prédiction.
- Niveau ganglion/patiente selon les données et le périmètre confirmé.
- Reproduction indépendante par un autre membre.

Aucun des tests techniques ne constitue une performance médicale ou un résultat scientifique du projet.

Les expériences réelles du pilote, distinctes des tests techniques, sont décrites dans [le bilan](../reports/pilot_real/README.md). Les configurations enregistrent le commit d'exécution et son état propre. Les CSV de prédictions publiés ont uniquement leurs chemins rendus relatifs ; les empreintes des fichiers d'origine et publiés sont conservées séparément. Les figures ont été vérifiées visuellement ; l'espacement des titres de la planche d'exploration a été corrigé après inspection.
