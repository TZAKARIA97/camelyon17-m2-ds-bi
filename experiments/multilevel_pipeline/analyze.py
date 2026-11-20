import argparse
import os
import shutil
import warnings
from itertools import product # Génération de combinaisons cartésiennes d'éléments
from pathlib import Path

import joblib # Sauvegarde et chargement des modèles entraînés
import numpy as np
import pandas as pd
import torch # Bibliothèque utilisée pour le calcul tensoriel et l'apprentissage profond
from PIL import Image # Lecture et manipulation des images
from sklearn.ensemble import RandomForestClassifier # Modèle de classification par forêt aléatoire
from sklearn.linear_model import LogisticRegression # Modèle de classification par régression logistique
from sklearn.metrics import (accuracy_score, confusion_matrix, precision_score,
                             recall_score, roc_auc_score, roc_curve)# Métriques permettant d'évaluer les performances des modèles
from sklearn.model_selection import train_test_split # Séparation des données en ensembles d'entraînement, de validation et de test
from sklearn.pipeline import make_pipeline # Création d'une chaîne de traitements successifs (prétraitement puis classification)
from sklearn.preprocessing import StandardScaler # Standardisation des variables pour les ramener à une échelle comparable
from torch.utils.data import DataLoader, Dataset # Gestion des jeux de données et chargement des données par lots pour PyTorch
from torchvision import models, transforms # Modèles préentraînés et transformations d'images pour la vision par ordinateur

import camelyon_data as cd

PATCH_DIR = os.environ.get("PATCH_DIR", "patches")  # Même dossier par défaut que extract_patches.py
RESULTS_DIR = Path(os.environ.get("RESULTS_DIR", cd.DATA_DIR.parent / "resultats")) # Dossier de sauvegarde des résultats


# 1. PATCHS ET SEPARATION PAR PATIENTE

def charger_patchs(chemin_csv): 
    if not os.path.exists(chemin_csv): # Vérification de l'existence du fichier CSV contenant les informations sur les patches
        raise FileNotFoundError(f"{chemin_csv} introuvable : lancez d'abord python extract_patches.py")
    patchs = pd.read_csv(chemin_csv) # Lecture du fichier CSV contenant les informations sur les patches extraits
    colonnes = {"path", "slide", "patient", "center", "label"}
    manquantes = colonnes - set(patchs.columns)
    if manquantes:
        raise ValueError(f"Colonnes absentes de {chemin_csv} : {sorted(manquantes)}")
    patchs = patchs[patchs["label"].isin(["tumor", "normal"])].reset_index(drop=True)# Conservation uniquement des patches tumoraux et normaux
    patchs["y"] = (patchs["label"] == "tumor").astype(int)# Attribution de 1 aux patches tumoraux et de 0 aux patches normaux
    patientes, lames = cd.charger_tables()  # Chargement des tableaux contenant les informations sur les patientes et les lames
    patchs = patchs.merge(lames[["lame", "patiente", "ganglion", "classe"]], # Sélection des colonnes utiles du tableau des lames
                          left_on="slide", right_on="lame", how="left").drop(columns="lame")# Ajout des informations des lames aux patches grâce à leur identifiant, puis suppression de la colonne en double
    return patchs.merge(patientes[["patiente", "stade_pN"]], on="patiente", how="left")# Ajout du stade pN de chaque patiente


def _tirer_patientes(pat, part, graine):  # Stratification par centre et présence de tumeur, puis par tumeur seule si nécessaire
    for strate in [pat["tumeur"].astype(str) + "_" + pat["centre"].astype(str), pat["tumeur"]]:
        try:
            return train_test_split(pat, test_size=part, stratify=strate, random_state=graine) # Séparation des patientes en conservant les proportions des classes
        except ValueError:
            continue
    return train_test_split(pat, test_size=part, random_state=graine) # Séparation aléatoire sans stratification si cela échoue


def creer_affectation_patientes(pat, part_test=0.2, part_validation=0.2, graine=42):
    """Crée une affectation patiente->set réutilisable à l'identique entre niveaux."""
    if len(pat) < 3:
        raise ValueError(
            f"Au moins 3 patientes sont nécessaires pour créer entraînement/validation/test ; {len(pat)} disponible(s)."
        )
    reste, test = _tirer_patientes(pat, part_test, graine)
    entr, val = _tirer_patientes(reste, part_validation / (1 - part_test), graine)
    return {**{p: "entrainement" for p in entr["patient"]},
            **{p: "validation" for p in val["patient"]},
            **{p: "test" for p in test["patient"]}}


def separer_par_patiente(patchs, part_test=0.2, part_validation=0.2, graine=42,
                         affectation_patientes=None):
    patchs = patchs.copy() # Création d'une copie du tableau pour conserver les données initiales
    pat = patchs.groupby("patient").agg(tumeur=("y", "max"), centre=("center", "first")).reset_index() # Regroupement des patches par patiente et récupération de son statut tumoral et de son centre
    affectation_patientes = affectation_patientes or creer_affectation_patientes(
        pat, part_test, part_validation, graine
    )
    patchs = patchs[patchs["patient"].isin(affectation_patientes)].copy()
    patchs["set"] = patchs["patient"].map(affectation_patientes)
    if patchs["set"].isna().any():
        raise ValueError("Certaines patientes n'ont pas d'affectation entraînement/validation/test.")
    for nom in ["entrainement", "validation", "test"]: # Vérification des trois ensembles
        sous = patchs[patchs["set"] == nom] # Sélection des patches de l'ensemble étudié
        if sous["y"].nunique() < 2: # Vérification de la présence des deux classes dans l'ensemble
            raise ValueError(
                f"Le set {nom} ne contient qu'une seule classe. Changez la graine ou ajoutez des lames/patientes."
            )
    patients_par_set = patchs.groupby("set")["patient"].apply(set)
    if any(patients_par_set[a] & patients_par_set[b]
           for a, b in [("entrainement", "validation"), ("entrainement", "test"), ("validation", "test")]):
        raise AssertionError("Fuite de données : une patiente apparaît dans plusieurs ensembles.")
    return patchs


# 2. CARACTERISTIQUES RESNET18

PREPARATION = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class PatchsDataset(Dataset): #Lecture des PNG listés dans le tableau et renvoie l'image préparée et son label

    def __init__(self, tableau, transformation=PREPARATION):
        self.tableau = tableau.reset_index(drop=True) # Réinitialisation des indices du tableau
        self.transformation = transformation # Enregistrement des transformations à appliquer aux images

    def __len__(self): 
        return len(self.tableau) # Retour du nombre total de patches

    def __getitem__(self, i):
        ligne = self.tableau.iloc[i] # Récupération des informations du patch correspondant à l'indice
        image = Image.open(ligne["path"]).convert("RGB") # Ouverture de l'image et conversion au format RGB
        return self.transformation(image), int(ligne["y"]) # Application des transformations et retour de l'image avec son label


def choisir_appareil():
    if hasattr(torch, "xpu") and torch.xpu.is_available(): # Vérification de la disponibilité d'un processeur Intel compatible XPU
        return "xpu"
    if torch.cuda.is_available(): # Vérification de la disponibilité d'un GPU compatible CUDA
        return "cuda"
    return "cpu" # Utilisation du processeur classique si aucun accélérateur n'est disponible


def creer_extracteur(appareil):
    modele = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)# Chargement du modèle ResNet18 pré-entraîné sur ImageNet
    modele.fc = torch.nn.Identity() # Suppression de la dernière couche de classification pour récupérer les 512 caractéristiques de chaque patch
    return modele.to(appareil).eval() # Envoi du modèle sur l'appareil choisi et passage en mode évaluation


def extraire_caracteristiques(modele, tableau, appareil, taille_lot=64, nb_workers=0):
    if tableau.empty:
        raise ValueError("Impossible d'extraire des caractéristiques depuis un ensemble vide.")
    chargeur = DataLoader(PatchsDataset(tableau), batch_size=taille_lot, shuffle=False, num_workers=nb_workers) # Création du chargeur de données pour lire les patches par lots sans modifier leur ordre
    X, y = [], [] # Initialisation des listes contenant les caractéristiques et les labels
    with torch.no_grad(): # Désactivation du calcul des gradients pour réduire le temps de calcul et la consommation mémoire
        for images, etiquettes in chargeur: # Parcours des patches par lots
            X.append(modele(images.to(appareil)).cpu().numpy()) # Extraction des caractéristiques, puis transfert des résultats vers le CPU et conversion en tableau
            y.append(etiquettes.numpy()) # Ajout des labels correspondants aux patches
    return np.concatenate(X), np.concatenate(y) # Regroupement des caractéristiques et des labels de tous les lots en deux tableaux


def caracteristiques_par_set(patchs, dossier_resultats, appareil=None, nb_workers=0):
    os.makedirs(dossier_resultats, exist_ok=True) # Création du dossier de sauvegarde des caractéristiques s'il n'existe pas déjà
    appareil = appareil or choisir_appareil() # Sélection de l'appareil de calcul, automatiquement si aucun n'est précisé
    modele = None # Initialisation du modèle, qui sera chargé uniquement si nécessaire
    sortie = {} # Initialisation du dictionnaire contenant les caractéristiques de chaque ensemble
    for nom in ["entrainement", "validation", "test"]: # Parcours des trois ensembles de données
        fx = os.path.join(dossier_resultats, f"X_{nom}.npy") # Chemin du fichier contenant les caractéristiques des patches
        fy = os.path.join(dossier_resultats, f"y_{nom}.npy") # Chemin du fichier contenant les labels des patches
        fc = os.path.join(dossier_resultats, f"chemins_{nom}.csv") # Chemin du fichier contenant les chemins des patches utilisés
        tableau = patchs[patchs["set"] == nom] # Sélection des patches appartenant à l'ensemble étudié
        # Vérification que les caractéristiques déjà enregistrées correspondent aux mêmes patches, dans le même ordre pour éviter de réutiliser des résultats provenant d'une ancienne séparation des données
        if (all(os.path.exists(f) for f in (fx, fy, fc))
                and pd.read_csv(fc)["path"].tolist() == tableau["path"].tolist()):
            sortie[nom] = (np.load(fx), np.load(fy))  # Chargement des caractéristiques et des labels déjà calculés
            continue
        modele = modele or creer_extracteur(appareil) # Création du modèle ResNet18 uniquement s'il n'a pas encore été chargé
        X, y = extraire_caracteristiques(modele, tableau, appareil, nb_workers=nb_workers) # Extraction des caractéristiques et des labels pour l'ensemble étudié
        np.save(fx, X) # Sauvegarde des caractéristiques dans un fichier
        np.save(fy, y) # Sauvegarde des labels dans un fichier
        tableau[["path"]].to_csv(fc, index=False) # Sauvegarde des chemins des patches utilisés pour vérifier le cache lors d'une prochaine exécution
        sortie[nom] = (X, y) # Ajout des caractéristiques et des labels au dictionnaire des résultats
    return sortie


# 3. REGRESSION LOGISTIQUE

def nouvelle_regression(C, l1_ratio, poids_classes="balanced"): # La pondération balanced compense le déséquilibre entre les patches tumoraux et normaux
    return make_pipeline(StandardScaler(), # Standardisation des caractéristiques avant la classification
                         LogisticRegression(C=C, l1_ratio=float(l1_ratio), solver="liblinear",
                                            max_iter=5000, class_weight=poids_classes,
                                            random_state=42)) # Solveur stable pour une classification binaire L1/L2


def regler_regression_logistique(X_entr, y_entr, X_val, y_val, valeurs_C=(0.001, 0.01, 0.1, 1, 10), poids_classes="balanced"):  # Retour du meilleur modèle et du tableau des résultats obtenus
    resultats = [] # Initialisation de la liste contenant les résultats des différents réglages
    for regularisation, l1_ratio in [("L2", 0), ("L1", 1)]:  # Test des deux types de régularisation
        for C in valeurs_C: # Test des différentes valeurs du paramètre C
            clf = nouvelle_regression(C, l1_ratio, poids_classes).fit(X_entr, y_entr) # Création et entraînement du modèle sur les données d'entraînement
            auc = roc_auc_score(y_val, clf.predict_proba(X_val)[:, 1]) # Calcul de l'AUC sur les données de validation à partir des probabilités de prédiction
            resultats.append({"régularisation": regularisation, "l1_ratio": l1_ratio, "C": C, "AUC validation": round(auc, 4)}) # Enregistrement des paramètres testés et de leur AUC
    tableau = pd.DataFrame(resultats).sort_values("AUC validation", ascending=False).reset_index(drop=True)  # Classement des modèles selon leur AUC de validation, du meilleur au moins performant
    meilleur = tableau.iloc[0] # Récupération du meilleur réglage
    clf = nouvelle_regression(meilleur["C"], int(meilleur["l1_ratio"]), poids_classes).fit(X_entr, y_entr) # Réentraînement du modèle avec les meilleurs paramètres sur les données d'entraînement
    return clf, tableau


# 4. RANDOM FOREST

def nouvelle_foret(n_arbres, profondeur_max, min_feuille, graine):
    return RandomForestClassifier(n_estimators=n_arbres, max_depth=profondeur_max, min_samples_leaf=min_feuille, max_features="sqrt", class_weight="balanced_subsample", n_jobs=-1, random_state=graine) # Création du modèle Random Forest


def regler_random_forest(X_entr, y_entr, X_val, y_val, graine=42, n_arbres=(300,), profondeurs=(None, 10, 20), min_feuilles=(1, 5, 20)):# Retour du meilleur modèle et du tableau des résultats obtenus
    resultats, meilleure, meilleure_auc = [], None, -1 # Initialisation des résultats, du meilleur modèle et de sa meilleure AUC
    for n, prof, feuille in product(n_arbres, profondeurs, min_feuilles): # Test de toutes les combinaisons possibles de paramètres
        foret = nouvelle_foret(n, prof, feuille, graine).fit(X_entr, y_entr) # Création et entraînement de la forêt aléatoire sur les données d'entraînement
        auc = roc_auc_score(y_val, foret.predict_proba(X_val)[:, 1])# Calcul de l'AUC sur les données de validation
        resultats.append({"n_arbres": n, "profondeur_max": prof if prof is not None else "illimitée", "min_feuille": feuille, "AUC validation": round(auc, 4)})# Enregistrement des paramètres testés et de leur AUC
        if auc > meilleure_auc: # Vérification si le modèle actuel obtient une meilleure AUC
            meilleure, meilleure_auc = foret, auc # Mise à jour du meilleur modèle et de sa performance
    tableau = pd.DataFrame(resultats).sort_values("AUC validation", ascending=False).reset_index(drop=True)  # Classement des combinaisons de paramètres selon leur AUC de validation
    return meilleure, tableau

# Association des noms des modèles à leurs fonctions d'entraînement et de réglage

MODELES = {
    "logistique": lambda X_entr, y_entr, X_val, y_val, graine: regler_regression_logistique(X_entr, y_entr, X_val, y_val),
    "random_forest": regler_random_forest,
}


# 5. EVALUATION

def seuil_pour_rappel(y_vrai, proba, rappel_min=0.95):
    if not 0 < rappel_min <= 1:
        raise ValueError("Le rappel minimal doit être dans ]0, 1].")
    _, taux_vp, seuils = roc_curve(y_vrai, proba) # Calcul des taux de vrais positifs et des seuils associés à la courbe ROC
    admissibles = seuils[taux_vp >= rappel_min]
    if not len(admissibles):
        raise ValueError(f"Aucun seuil ne permet d'atteindre un rappel de {rappel_min:.3f}.")
    return float(np.max(admissibles)) # Seuil le plus élevé atteignant le rappel demandé


def metriques(y_vrai, proba, seuil):
    y_predit = (proba >= seuil).astype(int) # Attribution du label 1 si la probabilité dépasse le seuil, sinon attribution du label 0
    vn, fp, fn, vp = confusion_matrix(y_vrai, y_predit, labels=[0, 1]).ravel() # Calcul de la matrice de confusion
    return {"seuil": round(seuil, 3), "AUC": round(roc_auc_score(y_vrai, proba), 4), # Calcul du seuil utilisé et de l'AUC
            "VP": int(vp), "FN": int(fn), "FP": int(fp), "VN": int(vn), # Enregistrement du nombre de prédictions correctes et incorrectes
            "exactitude": round(accuracy_score(y_vrai, y_predit), 3), # Calcul de la propor tion totale de prédictions correctes
            "rappel": round(recall_score(y_vrai, y_predit, zero_division=0), 3), # Calcul de la proportion de patches tumoraux correctement détectés
            "precision": round(precision_score(y_vrai, y_predit, zero_division=0), 3)} # Calcul de la proportion de prédictions tumorales réellement tumorales


# 6. CHAINE COMPLETE

def analyser_patchs(dossier_patchs=PATCH_DIR, niveau=0, dossier_resultats=RESULTS_DIR, rappel_min=0.95, graine=42, nb_workers=0, modele="logistique", affectation_patientes=None):
    dossier_niveau = Path(dossier_resultats) / f"niveau_{niveau}" # Création des dossiers de résultats : un dossier par niveau et un sous-dossier par modèle
    dossier_resultats = str(dossier_niveau / modele) # Définition du dossier de sauvegarde associé au modèle choisi
    os.makedirs(dossier_resultats, exist_ok=True) # Création du dossier de résultats s'il n'existe pas déjà
    patchs = charger_patchs(os.path.join(dossier_patchs, f"niveau_{niveau}", "patches.csv")) # Chargement des patches et des informations associées aux patientes
    patchs = separer_par_patiente(patchs, graine=graine, affectation_patientes=affectation_patientes) # Répartition commune entre niveaux
    print(patchs.groupby(["set", "label"]).size().unstack(fill_value=0)) # Affichage du nombre de patches tumoraux et normaux dans chaque ensemble

    sets = caracteristiques_par_set(patchs, str(dossier_niveau), nb_workers=nb_workers)# Extraction ou chargement des caractéristiques ResNet18 pour chaque ensemble
    (X_entr, y_entr), (X_val, y_val), (X_test, y_test) = sets["entrainement"], sets["validation"], sets["test"] # Récupération des caractéristiques et des labels des trois ensembles

    clf, reglages = MODELES[modele](X_entr, y_entr, X_val, y_val, graine) # Entraînement du modèle choisi et recherche des meilleurs paramètres à partir de la validation
    print(reglages)

    proba_val = clf.predict_proba(X_val)[:, 1] # Calcul des probabilités de présence d'une tumeur pour les patches de validation
    seuil = seuil_pour_rappel(y_val, proba_val, rappel_min) # Détermination du seuil permettant d'atteindre le rappel minimal souhaité
    proba_test = clf.predict_proba(X_test)[:, 1] # Calcul des probabilités de présence d'une tumeur pour les patches de test
    res = pd.DataFrame([{"set": "validation", **metriques(y_val, proba_val, seuil)}, # Calcul des métriques sur l'ensemble de validation
                        {"set": "test", **metriques(y_test, proba_test, seuil)}]) # Calcul des métriques sur l'ensemble de test
    print(res.to_string(index=False))

    joblib.dump({"classifieur": clf, "seuil": seuil}, os.path.join(dossier_resultats, "classifieur.joblib")) # Sauvegarde du modèle entraîné et du seuil de classification
    reglages.to_csv(os.path.join(dossier_resultats, "reglages_testes.csv"), index=False) # Sauvegarde des paramètres testés et de leurs performances
    res.to_csv(os.path.join(dossier_resultats, "metriques.csv"), index=False) # Sauvegarde des métriques obtenues sur la validation et le test
    predictions = pd.concat([patchs[patchs["set"] == "validation"].assign(proba_tumoral=proba_val), # Ajout des probabilités tumorales aux patches de validation
                             patchs[patchs["set"] == "test"].assign(proba_tumoral=proba_test)]) # Ajout des probabilités tumorales aux patches de test et regroupement des deux ensembles
    predictions.to_csv(os.path.join(dossier_resultats, "predictions.csv"), index=False) # Sauvegarde des prédictions et des informations associées à chaque patch
    return clf, seuil, res # Retour du modèle entraîné, du seuil choisi et du tableau des métriques


def comparer_configurations(dossier_patchs, niveaux, modeles, dossier_resultats=RESULTS_DIR,
                            rappel_min=0.95, graine=42, nb_workers=0):
    """Teste plusieurs niveaux/modèles et choisit uniquement avec l'AUC de validation."""
    tables = {
        niveau: charger_patchs(os.path.join(dossier_patchs, f"niveau_{niveau}", "patches.csv"))
        for niveau in niveaux
    }
    patients_communs = set.intersection(*(set(table["patient"]) for table in tables.values()))
    if len(patients_communs) < 3:
        raise ValueError("Moins de 3 patientes sont communes à tous les niveaux demandés.")
    reference = pd.concat(
        [table[table["patient"].isin(patients_communs)] for table in tables.values()],
        ignore_index=True,
    )
    pat = reference.groupby("patient").agg(
        tumeur=("y", "max"), centre=("center", "first")
    ).reset_index()
    affectation = creer_affectation_patientes(pat, graine=graine)
    lignes = []
    erreurs = []
    for niveau in niveaux:
        for modele in modeles:
            print(f"\n===== Niveau {niveau} | modèle {modele} =====")
            try:
                _, seuil, met = analyser_patchs(
                    dossier_patchs, niveau, dossier_resultats, rappel_min, graine, nb_workers,
                    modele, affectation
                )
                val = met.loc[met["set"] == "validation"].iloc[0]
                test = met.loc[met["set"] == "test"].iloc[0]
                lignes.append({
                    "niveau": niveau, "modele": modele, "seuil": seuil,
                    "AUC_validation": val["AUC"], "rappel_validation": val["rappel"],
                    "precision_validation": val["precision"], "AUC_test": test["AUC"],
                    "rappel_test": test["rappel"], "precision_test": test["precision"],
                })
            except Exception as exc:
                erreurs.append({"niveau": niveau, "modele": modele, "erreur": str(exc)})
                warnings.warn(f"Niveau {niveau}, modèle {modele} ignoré : {exc}")
    if not lignes:
        detail = "; ".join(f"niveau {e['niveau']}/{e['modele']}: {e['erreur']}" for e in erreurs)
        raise RuntimeError(f"Aucune configuration valide. {detail}")
    comparaison = pd.DataFrame(lignes).sort_values(
        ["AUC_validation", "rappel_validation", "precision_validation"], ascending=False
    ).reset_index(drop=True)
    dossier_resultats = Path(dossier_resultats)
    dossier_resultats.mkdir(parents=True, exist_ok=True)
    comparaison.to_csv(dossier_resultats / "comparaison_niveaux_modeles.csv", index=False)
    if erreurs:
        pd.DataFrame(erreurs).to_csv(dossier_resultats / "configurations_ignorees.csv", index=False)
    meilleure = comparaison.iloc[0]
    (dossier_resultats / "configuration_recommandee.txt").write_text(
        f"niveau={int(meilleure['niveau'])}\nmodele={meilleure['modele']}\n"
        f"AUC_validation={meilleure['AUC_validation']:.4f}\nseuil={meilleure['seuil']:.6f}\n",
        encoding="utf-8",
    )
    source = dossier_resultats / f"niveau_{int(meilleure['niveau'])}" / str(meilleure["modele"])
    for nom_source, nom_final in [
        ("classifieur.joblib", "modele_final.joblib"),
        ("metriques.csv", "metriques_finales.csv"),
        ("reglages_testes.csv", "reglages_finaux.csv"),
        ("predictions.csv", "predictions_finales.csv"),
    ]:
        shutil.copy2(source / nom_source, dossier_resultats / nom_final)
    print("\nComparaison finale :")
    print(comparaison.to_string(index=False))
    print(f"\nConfiguration recommandée : niveau {int(meilleure['niveau'])}, {meilleure['modele']}")
    return comparaison


# 7. INTERFACE LIGNE DE COMMANDE

"""
Exemples :
    python analyze.py
    python analyze.py --patch-level 1
    python analyze.py --modele random_forest
    python analyze.py --modele logistique --rappel 0.95
    python analyze.py --patch-level 0 --modele random_forest --graine 42
    python analyze.py --out patches --resultats resultats --lecteurs-png 4
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=PATCH_DIR, help="dossier des patches") # Définition du dossier contenant les patches
    ap.add_argument("--patch-level", type=int, nargs="+", default=[0, 1], help="niveau(x) des patches à comparer")
    ap.add_argument("--modele", choices=[*MODELES, "tous"], default="tous") # Choix du modèle de classification
    ap.add_argument("--resultats", default=str(RESULTS_DIR)) # Définition du dossier dans lequel seront enregistrés les résultats
    ap.add_argument("--rappel", type=float, default=0.95, help="rappel minimal pour choisir le seuil") # Définition du rappel minimal souhaité pour déterminer le seuil de classification
    ap.add_argument("--graine", type=int, default=42) # Définition de la graine aléatoire pour garantir la reproductibilité des résultats
    ap.add_argument("--lecteurs-png", type=int, default=0, help="processus de lecture des PNG pour ResNet18") # Définition du nombre de processus utilisés pour charger les images
    a = ap.parse_args()
    modeles = list(MODELES) if a.modele == "tous" else [a.modele]
    comparer_configurations(a.out, a.patch_level, modeles, a.resultats,
                            a.rappel, a.graine, a.lecteurs_png)
