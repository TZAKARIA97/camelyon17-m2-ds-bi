# MODIFS JOELLE :
# - Pour les variantes à tester : import de parametres_decoupage.py et option --variante. main lit les réglages du fichier
#   et appelle lancer une fois par variante. Sans --variante = les valeurs par défaut.
# - Sélection des lames : options --selection et --sets. On découpe les lames du fichier de sélection
#   (entraînement et validation), et chaque patch garde son set (colonne "set" de patches.csv).
# - Surface fixe : option --patch-um et fonction geometrie. Un patch couvre toujours 112 µm quel que soit le niveau et le scanner.
# - Détection du tissu : seuil de saturation de detect_purple réglable (option --violet-s-min).
# - Étiquetage "centre" en plus de "pourcentage" (options --labelling et --centre-um, colonne tumor_frac_centre)
# - Mesure fine de la tumeur (fonctions polygones_xml et mesure_fine) pour les patchs proches de la tumeur, la part
#   de tumeur est mesurée sur les contours XML redessinés à 0,5 µm par pixel et non sur le masque
#   de la miniature (8 µm par pixel) trop imprécis pour l'étiquetage "centre".
# - Zones vides des lames en blanc et non en noir (cd.rgb_fond_blanc, dans read_level_parallel et cd.read_patch).
# - patches.csv : colonnes ajoutées (set, tumor_frac_centre, patch_um, taille_lue, labelling, violet_s_min).
#
# # extract_patches.py : découpage des lames en patchs
#   Pour chaque lame choisie : repérer le tissu sur une miniature, poser une grille de patchs de 112 µm,
#     calculer la part de tumeur de chaque patch (lames annotées), lui donner une étiquette (tumor / normal), tirer au plus
#     250 patchs de chaque étiquette, puis lire chacun dans la lame, revérifier son tissu et l'enregistrer en PNG
#     (+ une ligne dans patches.csv + une image d'aperçu de la lame).
#   Ordre d'exécution :
#     main -> lancer (une fois par variante) -> extraire_niveau (boucle sur les lames, plusieurs à la fois)
#          -> process_slide (une lame) -> candidate_patches (grille, tissu, tumeur, étiquettes) puis tirage,
#             save_preview (aperçu) et read_and_save (lecture et enregistrement de chaque patch, plusieurs à la fois).
#   Utilisation (depuis le dossier version_finale) : python extract_patches.py --variante retenue

import argparse # Gestion des arguments passés depuis le terminal
import os # Interaction avec le système d'exploitation (variables d'environnement)
import threading # Variables locales à chaque thread
import time # Mesure du temps de traitement de chaque lame
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed # Exécution de plusieurs tâches en parallèle (processus pour les lames, threads pour les lectures)
from pathlib import Path # Manipulation des chemins d'accès aux fichiers et dossiers

import cv2
import numpy as np
import pandas as pd

import camelyon_data as cd # Importation des fonctions de lecture et de traitement des données CAMELYON17
import xml.etree.ElementTree as ET # Lecture des contours XML (mesure fine de la tumeur)
import parametres_decoupage as pdc # Le fichier de paramétrage (variantes à tester)

cv2.setNumThreads(1) # OpenCV n'utilise qu'un seul cœur par appel : le parallélisme est géré par nos processus et threads (évite la surcharge du processeur)


# 1 DETECTION DES REGIONS TISSULAIRES

def detect_purple(rgb, s_min=30): # Conversion de l'image RGB vers l'espace colorimétrique HSV
    # Repère le tissu sur une image RGB (seuil de saturation réglable) :
    # - un pixel est du tissu si sa teinte est rose-violet, sa saturation >= s_min et sa luminosité entre 50 et 245
    # - puis une ouverture et une fermeture 5 x 5 enlèvent les petits points et bouchent les petits trous.
    # Renvoie un masque True / False de la taille de l'image.
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2] # Séparation des canaux teinte, saturation et luminosité
    purple_pink = (h >= 120) | (h <= 10)  # Sélection des teintes violettes et roses
    mask = purple_pink & (s >= s_min) & (v >= 50) & (v <= 245) # Filtrage selon la saturation et la luminosité
    mask = mask.astype(np.uint8) # Conversion du masque en entiers non signés
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)) # Création d'un élément structurant elliptique
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k) # Suppression des petits éléments isolés
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k) # Remplissage des petites zones vides
    return mask.astype(bool) # Retour du masque sous forme booléenne


def polygones_xml(xml_path):
    # Contours du XML en pixels du niveau 0, séparés en tumeurs et zones exclues (même lecture que cd.xml_to_mask)
    tumeurs, exclus = [], []
    for ann in ET.parse(xml_path).getroot().iter("Annotation"):
        pts = np.array([[float(c.get("X").replace(",", ".")), float(c.get("Y").replace(",", "."))]
                        for c in ann.iter("Coordinate")])
        if len(pts) < 3:
            continue
        (exclus if ann.get("PartOfGroup") in cd.EXCLUDE_GROUPS else tumeurs).append(pts)
    return tumeurs, exclus


def mesure_fine(tumeurs, exclus, x0, y0, pas, frac_centre, n=224):
    # Part de tumeur dans le patch (x0, y0, côté pas en pixels du niveau 0) et dans sa zone centrale,
    # mesurée sur une image n x n où l'on redessine les contours (décalés au coin du patch et mis à l'échelle)
    def dans_le_patch(pts): # on ne redessine que les contours qui touchent le patch
        return pts[:, 0].max() >= x0 and pts[:, 0].min() < x0 + pas and pts[:, 1].max() >= y0 and pts[:, 1].min() < y0 + pas
    def local(pts):
        return np.round((pts - [x0, y0]) * n / pas).astype(np.int32)
    img = np.zeros((n, n), np.uint8)
    t = [local(p) for p in tumeurs if dans_le_patch(p)]
    if t:
        cv2.fillPoly(img, t, 1)
    e = [local(p) for p in exclus if dans_le_patch(p)]
    if e:
        cv2.fillPoly(img, e, 0)
    c = max(1, int(round(n * frac_centre)))   # côté de la zone centrale en pixels de cette image
    d = (n - c) // 2
    return img.mean(), img[d:d + c, d:d + c].mean()


def geometrie(slide, args):
    # Taille d'un patch au niveau 0 (= le pas, sans chevauchement) et taille à lire au niveau du patch.
    # - patch_um = None : "patch" pixels lus au niveau du patch (la surface dépend du niveau et du scanner)
    # - patch_um = 112 : surface fixe de 112 µm, quel que soit le niveau et le scanner. 
    #   On lit le nombre de pixels qui couvre 112 µm à ce niveau puis on le redimensionne en "patch" pixels (224) pour ResNet18.
    ds = slide.level_downsamples[args.patch_level]
    if args.patch_um is None:
        pas = int(round(args.patch * ds))
    else:
        pas = int(round(args.patch_um / cd.taille_pixel_um(slide)))
    taille_lue = max(1, int(round(pas / ds)))
    return pas, taille_lue


# 2 LECTURE PARALLELE DES LAMES

class SlidePool: # Une lame ouverte par thread : un même objet slide ne doit pas être partagé entre plusieurs threads
    # Donne à chaque thread sa propre lame ouverte (pool.get()), ouverte seulement à la première demande.

    def __init__(self, path):
        self.path = path # Chemin de la lame (local ou s3://...)
        self.local = threading.local() # Espace de stockage propre à chaque thread

    def get(self): # Renvoie la lame ouverte par le thread courant, en l'ouvrant à la première utilisation
        if not hasattr(self.local, "slide"):
            self.local.slide = cd.open_slide(self.path)
        return self.local.slide


def read_level_parallel(pool, level, workers): # Lecture de la miniature découpée en bandes horizontales lues en parallèle (au lieu d'un seul bloc lu tuile par tuile)
    # Lit la miniature (niveau level) en bandes horizontales lues en même temps par plusieurs threads.
    # Renvoie la lame ouverte, la miniature (tableau RGB, zones vides en blanc) et le niveau réellement utilisé.
    slide = pool.get()
    level = min(level, slide.level_count - 1) # Adaptation du niveau demandé au nombre de niveaux disponibles
    w, h = slide.level_dimensions[level] # Dimensions de la miniature
    ds = slide.level_downsamples[level] # Facteur de réduction entre le niveau 0 et la miniature
    n = max(1, min(workers, h // 256)) # Nombre de bandes (au plus une par thread, chaque bande d'au moins 256 pixels)
    bounds = np.linspace(0, h, n + 1).astype(int) # Limites verticales des bandes

    def strip(i): # Lecture d'une bande ; read_region attend des coordonnées au niveau 0, d'où la multiplication par ds
        y0, y1 = int(bounds[i]), int(bounds[i + 1])
        img = pool.get().read_region((0, int(round(y0 * ds))), level, (w, y1 - y0))
        return np.asarray(cd.rgb_fond_blanc(img))

    with ThreadPoolExecutor(n) as ex: # Lecture simultanée des bandes puis assemblage vertical
        thumb = np.vstack(list(ex.map(strip, range(n))))
    return slide, thumb, level


# 3 IDENTIFICATION DES PATCHES CANDIDATS
def candidate_patches(row, pool, args):
    # Les patchs possibles d'une lame, avec leur étiquette :
    # - lit la miniature, fabrique le masque de tumeur (XML) et repère le tissu (detect_purple)
    # - pose une grille de patchs de 112 µm sans chevauchement et calcule la part de tissu et de tumeur de chaque case
    # - garde les cases avec assez de tissu (min_tissue) ; pour celles proches de la tumeur, mesure fine (mesure_fine)
    # - étiquette : lames annotées -> tumor / normal selon la règle choisie ("border" écartés), lames négatives -> normal
    # Renvoie la lame, la miniature, le masque du tissu, le masque de tumeur et le tableau des candidats (cand).

    slide, thumb, level = read_level_parallel(pool, args.level, args.workers) # Chargement de la lame et de sa miniature (lecture parallèle)
    xml = row["xml_path"] if not pd.isna(row["xml_path"]) else None # Remplacement des valeurs manquantes (NaN) par None
    mask = cd.xml_to_mask(xml, slide, level) if xml else np.zeros(thumb.shape[:2], np.uint8) # Masque tumoral à partir du XML, ou masque vide si la lame n'est pas annotée
    W0, H0 = slide.dimensions# Récupération des dimensions de la lame au niveau initial
    pas, _ = geometrie(slide, args) # Taille d'un patch en pixels du niveau 0
    gw, gh = W0 // pas, H0 // pas # Calcul du nombre de patches sur chaque axe

    ds_t = slide.level_downsamples[level] # réduction de la miniature (sert plus bas pour couvert)
    tissue = detect_purple(thumb, args.violet_s_min).astype(np.float32)# Détection des régions tissulaires sur la miniature

    def couvert(image, ds): # la partie de l'image couverte par la grille
        return image[:int(round(gh * pas / ds)), :int(round(gw * pas / ds))]
    tissue_frac = cv2.resize(couvert(tissue, ds_t), (gw, gh), interpolation=cv2.INTER_AREA)# Redimensionnement du masque tissulaire à la grille des patches
    tumor_frac = cv2.resize(couvert(mask, ds_t).astype(np.float32), (gw, gh), interpolation=cv2.INTER_AREA)# Redimensionnement du masque tumoral à la même résolution

    k = 8
    n_c = max(1, int(round(k * args.centre_um / (args.patch_um or pas * cd.taille_pixel_um(slide)))))
    d = (k - n_c) // 2 # nombre de petites cases avant la zone centrale
    fin = cv2.resize(couvert(mask, ds_t).astype(np.float32), (k * gw, k * gh), interpolation=cv2.INTER_AREA)
    tumor_centre = fin.reshape(gh, k, gw, k)[:, d:d + n_c, :, d:d + n_c].mean(axis=(1, 3))

    rows, cols = np.nonzero(tissue_frac >= args.min_tissue)# Récupération des positions dont la proportion de tissu dépasse le seuil minimal.
    tf, tu = tissue_frac[rows, cols], tumor_frac[rows, cols]# Extraction des proportions tissulaires et tumorales
    cand = pd.DataFrame({"x": cols * pas, "y": rows * pas, "tissue_frac": tf, "tumor_frac": tu})# Création du DataFrame contenant les coordonnées et les proportions associées à chaque patch
    tc = tumor_centre[rows, cols] # ===== AJOUT (version finale) : part de tumeur dans la zone centrale =====
    if xml:
        proches = cv2.dilate((tumor_frac > 0).astype(np.uint8), np.ones((3, 3), np.uint8))[rows, cols] > 0
        tumeurs, exclus = polygones_xml(xml)
        frac_centre = args.centre_um / (args.patch_um or pas * cd.taille_pixel_um(slide))
        tu, tc = tu.astype(np.float64), tc.astype(np.float64)
        for i in np.nonzero(proches)[0]:
            tu[i], tc[i] = mesure_fine(tumeurs, exclus, int(cols[i] * pas), int(rows[i] * pas), pas, frac_centre)
        cand["tumor_frac"] = tu
    cand["tumor_frac_centre"] = tc

    if row["annotated"]: # Attribution des labels pour les lames annotées
        if args.labelling == "centre":
            cand["label"] = np.where(tc > 0, "tumor", np.where(tu == 0, "normal", "border"))
        else:
            cand["label"] = np.where(tu >= args.tumor_thr, "tumor", np.where(tu == 0, "normal", "border"))
        cand = cand[cand.label != "border"]    # Suppression des patches situés sur les frontières tumorales
    elif row.get("slide_label") == "negative":# Attribution du label normal aux lames négatives
        cand["label"] = "normal"
    else:
        cand["label"] = "unlabeled"  # Attribution du label non renseigné aux autres lames
    return slide, thumb, tissue, mask, cand

# 4 CREATION DES IMAGES DE PREVISUALISATION

def save_preview(path, thumb, tissue, mask, chosen, patch, ds):
    # Image d'aperçu d'une lame : miniature, tissu en vert, tumeur en rouge, cadre autour de chaque patch choisi
    # (rouge = tumor, bleu = normal). patch = côté du patch et ds = réduction de la miniature, en pixels du niveau 0.
    img = thumb.copy()# Copie de la miniature originale
    img[tissue > 0] = (0.6 * img[tissue > 0] + 0.4 * np.array([0, 200, 0])).astype(np.uint8) # Superposition d'une couleur verte sur les régions identifiées comme tissulaires afin de les visualiser
    img[mask > 0] = (0.5 * img[mask > 0] + 0.5 * np.array([255, 0, 0])).astype(np.uint8)# Superposition de la couleur rouge sur les régions tumorales
    colors = {"tumor": (255, 0, 0), "normal": (0, 0, 255), "unlabeled": (128, 128, 128)}# Définition des couleurs associées à chaque classe de patches : rouge pour les tumoraux, bleu pour les normaux et gris pour les non étiquetés
    s = max(1, int(round(patch / ds)))# Calcul de la taille des rectangles à dessiner sur la miniature en tenant compte du facteur de réduction, avec une taille minimale d'un pixel
    for r in chosen.itertuples():# Parcours des patches sélectionnés afin de les représenter sur l'image de prévisualisation
        x, y = int(r.x / ds), int(r.y / ds)# Conversion des coordonnées du patch depuis la résolution originale vers les coordonnées correspondantes sur la miniature
        cv2.rectangle(img, (x, y), (x + s, y + s), colors[r.label], 1)# Dessin d'un rectangle autour de chaque patch sélectionné en utilisant la couleur correspondant à sa classe
    cv2.imwrite(str(path), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))# Conversion de l'image du format RGB vers BGR puis sauvegarde de l'image de prévisualisation au chemin spécifié


# 5 TRAITEMENT D'UNE LAME (exécuté dans un processus séparé)

def process_slide(row, args): # Extraction des patches à partir de la lame et des paramètres définis
    # Tout le travail pour une lame (exécuté dans un processus à part) :
    # - candidats et étiquettes (candidate_patches)
    # - tirage au hasard d'au plus max_tumor patchs tumoraux et max_normal sains (graine fixe)
    # - aperçu (save_preview)
    # - lecture, revérification du tissu et enregistrement de chaque patch choisi, plusieurs à la fois (read_and_save)
    # Renvoie le nom de la lame, le tableau des patchs enregistrés et le temps pris.
    t0 = time.time() # Début du chronométrage de la lame
    out = Path(args.out) # Dossier de sortie
    pool = SlidePool(row["tif_path"]) # Gestionnaire des lames ouvertes (une par thread)
    slide, thumb, tissue, mask, cand = candidate_patches(row, pool, args)
    rng = np.random.default_rng(args.seed)# Initialisation du générateur de nombres aléatoires avec une graine fixe pour garantir la reproductibilité
    chosen = [] # Initialisation de la liste qui contiendra les patches sélectionnés
    for label, group in cand.groupby("label"): # Regroupement des patches selon leur classe
        n = args.max_tumor if label == "tumor" else args.max_normal # Définition du nombre maximal de patches à sélectionner selon leur classe
        idx = rng.permutation(len(group))[:n] # Sélection aléatoire des indices des patches dans chaque groupe
        chosen.append(group.iloc[idx])# Ajout des patches sélectionnés à la liste
    chosen = pd.concat(chosen) if chosen else cand.iloc[:0]# Concaténation des groupes sélectionnés dans un seul DataFrame, ou création d'un DataFrame vide si aucun patch n'a été sélectionné
    chosen = chosen.sort_values(["y", "x"]) # Tri par position : des patches voisins se trouvent dans les mêmes blocs du fichier, téléchargés une seule fois

    ds = slide.dimensions[0] / thumb.shape[1] # Calcul du facteur de réduction entre la largeur de la lame originale et celle de sa miniature
    pas, taille_lue = geometrie(slide, args)
    (out / "previews").mkdir(parents=True, exist_ok=True) # Création du dossier destiné à stocker les images de prévisualisation
    save_preview(out / "previews" / f"{row['slide']}.png", thumb, tissue, mask, chosen,
                 pas, ds) # Création et sauvegarde de l'image de prévisualisation avec les patches sélectionnés
    for label in chosen.label.unique(): # Création des dossiers de destination une seule fois, avant les threads
        (out / label).mkdir(parents=True, exist_ok=True)

    def read_and_save(r):
        # Un patch : le lit dans la lame, le remet à 224 pixels, revérifie sa part de tissu (sinon écarté : None)
        # l'enregistre en PNG dans <dossier>/<étiquette>/ et renvoie sa ligne pour patches.csv
        # On lit taille_lue pixels (la surface de patch_um µm) puis on redimensionne en args.patch (224).
        img = cd.read_patch(pool.get(), int(r.x), int(r.y), size=taille_lue, level=args.patch_level)# Lecture du patch avec la lame ouverte par le thread courant
        if taille_lue != args.patch: # ramené à args.patch pixels (INTER_AREA pour réduire, INTER_LINEAR pour agrandir)
            img = cv2.resize(img, (args.patch, args.patch),
                             interpolation=cv2.INTER_AREA if taille_lue > args.patch else cv2.INTER_LINEAR)
        if detect_purple(img, args.violet_s_min).mean() < args.min_tissue:   # Vérification de la proportion de tissu directement sur le patch en pleine résolution
            return None # Exclusion du patch si sa proportion de tissu est inférieure au seuil minimal
        p = out / r.label / f"{row['slide']}_x{int(r.x)}_y{int(r.y)}.png" # Construction du chemin de sauvegarde du patch à partir de l'identifiant de la lame et de ses coordonnées
        cv2.imwrite(str(p), cv2.cvtColor(img, cv2.COLOR_RGB2BGR)) # Conversion de l'image du format RGB vers BGR puis sauvegarde au format PNG
        # Colonnes ajoutées : set (sélection), part de tumeur dans la zone centrale, surface et taille lue, réglages utilisés
        return {"path": str(p), "slide": row["slide"], "patient": row["patient"],
                "center": row["center"], "set": row.get("set", ""), "niveau": args.patch_level, "label": r.label,
                "x": int(r.x), "y": int(r.y), "tissue_frac": round(float(r.tissue_frac), 3),
                "tumor_frac": round(float(r.tumor_frac), 3), "tumor_frac_centre": round(float(r.tumor_frac_centre), 3),
                "patch_um": args.patch_um, "taille_lue": taille_lue, "labelling": args.labelling,
                "violet_s_min": args.violet_s_min}# Création d'un dictionnaire contenant les informations associées au patch sauvegardé

    with ThreadPoolExecutor(args.workers) as ex:# Création d'un pool de threads pour paralléliser la lecture et la sauvegarde des patches
        recs = [r for r in ex.map(read_and_save, chosen.itertuples()) if r]# Application de la fonction read_and_save à chaque patch sélectionné et récupération des résultats non nuls
    return row["slide"], pd.DataFrame(recs), time.time() - t0 # Retour du nom de la lame, des patches sauvegardés et du temps de traitement

# 6 INTERFACE LIGNE DE COMMANDE

"""
Exemples :

    python extract_patches.py                         (niveaux 0 et 1 -> patches/niveau_0 et patches/niveau_1)
    python extract_patches.py --max-slides 2
    python extract_patches.py --patch-level 0         (niveau 0 seulement)
    python extract_patches.py --patch-level 1         (niveau 1 seulement)
    python extract_patches.py --slides all
    python extract_patches.py --slide-workers 4 --workers 24   (bonne connexion)
    python extract_patches.py --slide-workers 2 --workers 8    (PC lent ou wifi faible)

"""

def main():
    # Lit les options de la commande. Sans --variante : une seule extraction (comme à l'origine).
    # Avec --variante : pour chaque variante, les réglages de parametres_decoupage.py deviennent les valeurs par défaut
    # (une option écrite dans la commande l'emporte), puis lancer découpe dans patches/<variante>/.
    ap = argparse.ArgumentParser() # Création du parseur permettant de récupérer les arguments fournis lors de l'exécution du script
    ap.add_argument("--out", default=os.environ.get("PATCH_DIR", "patches")) # Définition du dossier de sortie, avec utilisation de la variable d'environnement PATCH_DIR si elle existe
    ap.add_argument("--slides", choices=["annotated", "labelled", "all"], default="annotated",
                    help="annotated: 50 annotated slides | labelled: + negative slides | all: every slide")# Choix des catégories de lames à traiter, avec les lames annotées par défaut
    ap.add_argument("--max-slides", type=int, default=None)# Définition du nombre maximal de lames à traiter, sans limite par défaut
    ap.add_argument("--patch-level", type=int, nargs="+", default=[0, 1],
                    help="niveau(x) de découpe des patches : 0 = 0,25 µm/pixel, 1 = 0,5 µm/pixel (par défaut les deux)")
    ap.add_argument("--patch", type=int, default=224)# Définition de la taille des patches en pixels
    ap.add_argument("--level", type=int, default=5, help="niveau de la miniature pour la détection du violet (pas celui des patches)")# Définition du niveau de résolution utilisé pour détecter les régions tissulaires sur la miniature
    ap.add_argument("--min-tissue", type=float, default=0.5, help="min purple fraction in a patch")# Définition de la proportion minimale de tissu violet nécessaire pour conserver un patch
    ap.add_argument("--tumor-thr", type=float, default=0.5, help="min tumor fraction for 'tumor'")# Définition de la proportion minimale de tissu tumoral nécessaire pour attribuer le label tumor
    ap.add_argument("--max-tumor", type=int, default=250, help="max tumor patches per slide")# Définition du nombre maximal de patches tumoraux sélectionnés par lame
    ap.add_argument("--max-normal", type=int, default=250, help="max normal patches per slide")# Définition du nombre maximal de patches normaux sélectionnés par lame
    ap.add_argument("--slide-workers", type=int, default=3, help="slides processed at the same time")# Nombre de lames traitées en même temps (un processus par lame)
    ap.add_argument("--workers", type=int, default=16, help="parallel reads inside one slide")# Nombre de threads de lecture à l'intérieur d'une lame
    ap.add_argument("--seed", type=int, default=0) # Définition de la graine aléatoire pour garantir la reproductibilité de la sélection des patches
    ap.add_argument("--variante", nargs="+", default=None,
                    help="variante(s) de parametres_decoupage.py, ou 'toutes' : un dossier patches/<variante>/ par variante")
    ap.add_argument("--patch-um", type=float, default=None, help="côté du patch en µm (surface fixe) ; None = 'patch' pixels au niveau")
    ap.add_argument("--labelling", choices=["pourcentage", "centre"], default="pourcentage",
                    help="pourcentage : tumeur >= tumor-thr sur tout le patch | centre : tumeur dans la zone centrale")
    ap.add_argument("--centre-um", type=float, default=56, help="côté de la zone centrale en µm (étiquetage 'centre')")
    ap.add_argument("--violet-s-min", type=int, default=30, help="saturation minimale (sur 255) de la méthode violet")
    ap.add_argument("--selection", default=None, help="CSV de la sélection des lames (colonnes slide et set) ; remplace --slides")
    ap.add_argument("--sets", nargs="+", default=["entrainement", "validation"], help="sets de la sélection à découper")
    args = ap.parse_args()

    if args.variante is None:
        lancer(args)
        return
    noms = list(pdc.VARIANTES) if args.variante == ["toutes"] else args.variante
    for nom in noms:
        # Les valeurs de parametres_decoupage.py (PARAMETRES puis la variante) deviennent les valeurs par défautsauf si option dans la commande
        ap.set_defaults(**{**pdc.PARAMETRES, **pdc.VARIANTES[nom]})
        args = ap.parse_args()
        args.out = str(Path(args.out) / nom)
        print(f"\n########## Variante {nom} -> {args.out} ##########")
        lancer(args)


def lancer(args): # Une extraction complète avec les options données 
    # Pour une variante (appelée une fois par variante par main):
    # - Construit l'index des lames
    # - Choisit les lames à découper (fichier de sélection, sinon --slides)
    # - Prépare le dossier patches/<variante>/niveau_<n> 
    # - Appelle extraire_niveau qui fait le vrai travail

    df = cd.build_remote_index()# Construction de l'index des lames à partir des fichiers locaux ou des données distantes sur AWS selon le mode choisi
    if args.selection:
        selection = pd.read_csv(args.selection)
        selection = selection[selection["set"].isin(args.sets)]
        df = df.merge(selection[["slide", "set"]], on="slide") # on ne garde que les lames de la sélection, avec leur set
        print(f"Sélection {args.selection} : {len(df)} lames des sets {args.sets}")
    elif args.slides == "annotated": # Sélection uniquement des lames disposant d'annotations tumorales
        df = df[df.annotated]
    elif args.slides == "labelled": # Sélection des lames annotées et des lames identifiées comme négatives
        if df.slide_label.isna().all():# Vérification de la présence des labels associés aux lames
            print("! slide_label vide (stage_labels.csv manquant) : seules les lames annotées sont prises.")
        df = df[df.annotated | (df.slide_label == "negative")]# Conservation des lames annotées ou dont le label est négatif
    if args.max_slides:# Vérification de l'existence d'une limite sur le nombre de lames à traiter
        df = df.head(args.max_slides) # Conservation uniquement des premières lames selon la limite définie

    for niveau in args.patch_level: # Un passage par niveau, chacun dans son dossier : patches/niveau_0, patches/niveau_1
        print(f"\n===== Niveau {niveau} =====")
        extraire_niveau(argparse.Namespace(**{**vars(args), "patch_level": niveau,
                                               "out": str(Path(args.out) / f"niveau_{niveau}")}), df)


def extraire_niveau(args, df): # Extraction des patches d'un niveau pour toutes les lames sélectionnées
    # Boucle sur les lames pour un niveau :
    # - Saute les lames déjà présentes dans patches.csv et traite les autres plusieurs à la fois
    # - Ajoute les patchs de chaque lame terminée à patches.csv

    out = Path(args.out) # Conversion du chemin de sortie en objet Path pour faciliter la manipulation des fichiers et dossiers
    out.mkdir(parents=True, exist_ok=True) # Création du dossier de sortie s'il n'existe pas déjà
    csv_path = out / "patches.csv" # Définition du chemin du fichier CSV qui contiendra les informations sur les patches extraits
    done = set(pd.read_csv(csv_path).slide) if csv_path.exists() else set() # Récupération des identifiants des lames déjà traitées à partir du CSV, ou initialisation d'un ensemble vide si le fichier n'existe pas
    todo = [r for _, r in df[~df.slide.isin(done)].iterrows()] # Sélection des lames qui n'ont pas encore été traitées afin d'éviter de répéter le travail
    print(f"{len(df)} lames sélectionnées, {len(done)} déjà faites, {len(todo)} à traiter "
          f"({args.slide_workers} lames x {args.workers} lectures en parallèle) -> {out.resolve()}") # Affichage du nombre de lames sélectionnées, déjà traitées et restantes, du parallélisme et du chemin de sortie

    t_start = time.time() # Début du chronométrage global
    with ProcessPoolExecutor(args.slide_workers) as ex: # Création d'un pool de processus : plusieurs lames traitées en même temps
        futures = {ex.submit(process_slide, r, args): r["slide"] for r in todo} # Envoi de chaque lame à un processus
        for i, fut in enumerate(as_completed(futures), 1): # Récupération des résultats au fur et à mesure que les lames se terminent
            name = futures[fut]
            try:
                name, recs, secs = fut.result()# Résultat de la lame : nom, patches sauvegardés, temps de traitement
            except Exception as e: # Interception des erreurs afin qu'une lame problématique n'interrompe pas le traitement de toutes les autres
                print(f"[{i}/{len(todo)}] {name} : ERREUR {e}")# Affichage du numéro de la lame, de son identifiant et du message d'erreur rencontré
                continue # Passage à la lame suivante en cas d'erreur
            if len(recs): # Seul le processus principal écrit dans le CSV (évite que deux processus écrivent en même temps)
                recs.to_csv(csv_path, mode="a", header=not csv_path.exists(), index=False) # Ajout des informations des patches au fichier CSV sans écraser les données précédentes et ajout de l'en-tête uniquement si le fichier n'existe pas
            counts = recs.label.value_counts().to_dict() if len(recs) else {} # Calcul du nombre de patches sauvegardés pour chaque classe, ou création d'un dictionnaire vide si aucun patch n'a été extrait
            eta = (time.time() - t_start) / i * (len(todo) - i) # Estimation du temps restant à partir du temps moyen par lame
            print(f"[{i}/{len(todo)}] {name} : {counts} en {secs / 60:.1f} min | reste ~{eta / 60:.0f} min") # Affichage de l'avancement, des patches obtenus, du temps de la lame et du temps restant estimé

    if csv_path.exists():# Vérification de l'existence du fichier CSV contenant les résultats
        allp = pd.read_csv(csv_path) # Chargement de l'ensemble des informations enregistrées dans le fichier CSV
        print("\nTotal :", allp.label.value_counts().to_dict(), f"({allp.slide.nunique()} lames)") # Affichage du nombre total de patches par classe et du nombre de lames traitées


if __name__ == "__main__": 
    main()
