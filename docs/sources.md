# Sources

- Consignes : Ines Krissaane, Projet 1 spécialisation - MBA 2, 20/10/2026, fourni au groupe ; exigences relues le 06/11/2026.
- Rappel - Projet 1 : transfer learning, Grad-CAM, fuite de données, coloration.
- CAMELYON17 données : https://camelyon17.grand-challenge.org/Data/
- CAMELYON17 évaluation et pN : https://camelyon17.grand-challenge.org/Evaluation/
- WILDS : https://github.com/p-lambda/wilds
- Guide WILDS et volumes : https://wilds.stanford.edu/get_started/
- Problèmes signalés sur les téléchargements CodaLab : https://github.com/p-lambda/wilds/issues/171 (notre propre requête a répondu 404 le 06/11/2026).
- Miroir communautaire utilisé, non officiel : https://huggingface.co/datasets/fumiyau/wilds-archive/tree/f7b0ea1de482b7dcccfd9a15af2825a4e70b335d ; équivalence au bundle original non vérifiée.
- Distribution CAMELYON sur AWS : https://registry.opendata.aws/camelyon/
- Sommes MD5 officielles utilisées pour la paire WSI/XML : https://camelyon-dataset.s3.us-west-2.amazonaws.com/CAMELYON17/checksums.md5
- Code de référence du split et du label (consulté le 06/11/2026) : https://github.com/p-lambda/wilds/blob/main/wilds/datasets/camelyon17_dataset.py
- OpenSlide Python : https://openslide.org/api/python/
- ASAP : https://github.com/computationalpathologygroup/ASAP
- QuPath : https://qupath.readthedocs.io/
- Installation PyTorch : https://pytorch.org/get-started/locally/
- ResNet18 : https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet18.html
- Grad-CAM : Selvaraju et al., ICCV 2017, https://openaccess.thecvf.com/content_iccv_2017/html/Selvaraju_Grad-CAM_Visual_Explanations_ICCV_2017_paper.html

Le code du starter est rédigé pour ce projet ; l'adaptation des conventions WILDS est explicitée dans wilds_manifest.py. Conserver les licences des dépendances et des données. Ne pas appliquer automatiquement une licence au travail collectif sans accord du groupe.
