# Protocole expérimental à figer avant entraînement final

1. Version/source des données et licences ; effectifs par centre, patient, lame et classe. Prévalence observée : ne pas supposer que WILDS reproduit le déséquilibre clinique.
2. Règle de label : WILDS = présence tumorale dans les 32×32 pixels centraux d'un patch 96×96. Pour les WSI, définir la règle, le niveau et les microns/pixel. Un seuil de 10 % arbitraire pourrait supprimer les petites lésions : il ne doit pas être adopté sans analyse.
3. Séparation par patient ET contrôle de lame ; centres non vus pour val/test OOD. Audit avant tout apprentissage, y compris calcul de moyennes ou référence de normalisation de coloration.
4. Baseline gelée, puis une modification à la fois. La normalisation numérique ImageNet est distincte d'une normalisation de coloration. Pas de GAN pour le démarrage.
5. Modèle/hyperparamètres/seuil choisis uniquement sur validation. Si un objectif de sensibilité est utilisé, le fixer et justifier avant d'examiner le test. Le seuil fixe 0,5 du starter ne prétend pas répondre à un objectif clinique.
6. Test final conservé pour une évaluation finale. Rapporter TP, FP, TN, FN, sensibilité, spécificité, précision, F1, ROC-AUC, Average Precision (AP : ne pas confondre avec une aire PR trapézoïdale).
7. Résultats par centre et contrôle de la variabilité entre graines si le temps le permet. Les patches d'une lame ne sont pas indépendants : des intervalles éventuels doivent rééchantillonner patients/lames, pas des patches isolés.
8. Grad-CAM sur succès et erreurs, exemples sélectionnés avec une règle écrite. Une carte plausible n'est pas une preuve de causalité ou de validité histologique ; hypothèses à confronter aux annotations et, si possible, à un expert.
9. pN : différencier une règle sur labels de ganglions fournis et une vraie évaluation de prédictions du modèle. Exiger les cinq ganglions, l'échelle physique, la détection des lésions, les types ITC/micro/macro et un test patient indépendant avant d'affirmer un pipeline pN validé. Le simple script de règles ne remplit pas ces conditions.
10. Archive de chaque expérience : manifeste, empreinte, versions, paramètres, temps de calcul, checkpoint, scores et interprétation. Écrire les limites avant de généraliser.

## Précisions sur les unités et la reproductibilité

Le contrôle de groupe porte sur les identifiants artificiels fournis par CAMELYON17 ; l’indépendance des patients biologiques d’origine ne peut pas être déduite de ces seuls identifiants. Les métriques par lame restent des métriques calculées sur ses patchs, sans agrégation clinique implicite.

Les empreintes du manifeste, du checkpoint et des prédictions détectent les remplacements de ces fichiers. Elles ne constituent pas une empreinte exhaustive de toutes les images. La source, les checksums de distribution lorsqu’ils existent et le contrôle des images doivent donc être conservés séparément. L’export Grad-CAM recalcule les scores des seuls exemples sélectionnés.

La présence d’un seul centre dans le test OOD WILDS limite les conclusions de généralisation. Notre politique `exclude-id-val` retire la validation interne qui partage des groupes avec train et conserve les autres ensembles officiels. Elle ne permet pas une comparaison ID/OOD. Éviter d’attribuer tout écart entre ensembles au centre de façon causale.

## Pilote réel du 6 novembre 2026

- Source : miroir communautaire figé CAMELYON17-WILDS 1.0 ; identité binaire avec le bundle original non vérifiée.
- Sélection : graine 42, au plus 10 groupes par ensemble/centre, 16 patchs par groupe, tirage sans utiliser le label ; 688 patchs au total.
- Un premier essai à 2 groupes par centre donnait un test sans patch positif. Le plafond a été élargi à tous les groupes disponibles pour ce pilote technique. Cette adaptation après lecture des effectifs est consignée ; elle n'est pas une validation indépendante du protocole final.
- Comparaison : mêmes configurations, même manifeste, trois époques, AP de validation pour le checkpoint et la méthode ; égalité départagée en faveur du modèle gelé.
- Le test est téléchargé et contrôlé, mais aucune prédiction ni métrique de modèle n'y est calculée à ce stade. Les effectifs de ses labels ont été examinés pour l'audit.
- L'inspection WSI concerne une lame du centre d'entraînement 4. Elle ne remplace pas un audit de toutes les annotations du pilote.
- Les données, checkpoints et images brutes restent hors Git ; les paramètres, résultats agrégés et preuves sélectionnées sont publiés.
