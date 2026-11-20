# Fichier pour le modèle de patch (avec le notebook 02_modelisation_evaluation et le script cartes_chaleur.py)
# (les mêmes réglages partout : même ResNet18, même préparation des images, même façon d'extraire les caractéristiques)

"""
ResNet18 pré-entraîné sur ImageNet, sans sa dernière couche : il transforme un patch de 224 x 224 pixels
en 512 caractéristiques. La régression logistique (entraînée dans le notebook 02_modelisation_evaluation) transforme ensuite
ces 512 caractéristiques en probabilité "tumoral".
"""
import os

import numpy as np
import torch
from torchvision import models, transforms

# Préparation de chaque patch, identique au prototype (tenseur + normalisation avec les moyennes et écarts-types d'ImageNet)
preparation = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def choisir_appareil():
    # "xpu" = la carte graphique Intel si PyTorch la trouve (plus rapide), sinon le processeur
    return "xpu" if hasattr(torch, "xpu") and torch.xpu.is_available() else "cpu"


def charger_resnet(appareil):
    # ResNet18 avec les poids appris sur ImageNet, dernière couche (fc) remplacée par Identity : sortie = 512 caractéristiques.
    # SANS_POIDS_IMAGENET=1 : poids au hasard, seulement pour tester le code sans internet (jamais pour de vrais résultats)
    if os.environ.get("SANS_POIDS_IMAGENET") == "1":
        torch.manual_seed(0)   # mêmes poids au hasard à chaque chargement (sinon le notebook et le script ne seraient pas d'accord)
        modele = models.resnet18(weights=None)
    else:
        modele = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    modele.fc = torch.nn.Identity()
    return modele.to(appareil).eval()   # mode évaluation (BatchNorm avec les moyennes apprises)


def caracteristiques(modele, images, appareil, taille_lot=64):
    # images = liste d'images RGB (tableaux numpy 224 x 224 x 3 ou images PIL). Renvoie un tableau (nombre d'images, 512).
    sorties = []
    with torch.no_grad():   # pas de gradients : on n'entraîne pas le réseau
        for debut in range(0, len(images), taille_lot):
            lot = torch.stack([preparation(im) for im in images[debut:debut + taille_lot]]).to(appareil)
            sorties.append(modele(lot).cpu().numpy())
    return np.concatenate(sorties) if sorties else np.zeros((0, 512), np.float32)


def extracteur_cartes(modele):
    # Pour Grad-CAM : ResNet18 sans sa moyenne finale ni sa dernière couche -> 512 cartes de 7 x 7 par patch
    return torch.nn.Sequential(*list(modele.children())[:-2]).eval()
