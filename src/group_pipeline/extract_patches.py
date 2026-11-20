import argparse # Gestion des arguments passés depuis le terminal
import hashlib # Construction d'une graine stable propre à chaque lame
import os # Interaction avec le système d'exploitation (variables d'environnement)
import threading # Variables locales à chaque thread
import time # Mesure du temps de traitement de chaque lame
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed # Exécution de plusieurs tâches en parallèle (processus pour les lames, threads pour les lectures)
from pathlib import Path # Manipulation des chemins d'accès aux fichiers et dossiers

import cv2
import numpy as np
import pandas as pd

from . import camelyon_data as cd #Importation des fonctions de lecture et de traitement des données CAMELYON17

cv2.setNumThreads(1) # OpenCV n'utilise qu'un seul cœur par appel : le parallélisme est géré par nos processus et threads (évite la surcharge du processeur)


# 1 DETECTION DES REGIONS TISSULAIRES
def detect_purple(rgb): # Conversion de l'image RGB vers l'espace colorimétrique HSV

    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2] # Séparation des canaux teinte, saturation et luminosité
    purple_pink = (h >= 120) | (h <= 10)  # Sélection des teintes violettes et roses
    mask = purple_pink & (s >= 30) & (v >= 50) & (v <= 245)# Filtrage selon la saturation et la luminosité
    mask = mask.astype(np.uint8)# Conversion du masque en entiers non signés
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))# Création d'un élément structurant elliptique
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)       # Suppression des petits éléments isolés
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)      # Remplissage des petites zones vides
    return mask.astype(bool)# Retour du masque sous forme booléenne


# 2 LECTURE PARALLELE DES LAMES
class SlidePool: # Une lame ouverte par thread : un même objet slide ne doit pas être partagé entre plusieurs threads

    def __init__(self, path):
        self.path = path # Chemin de la lame (local ou s3://...)
        self.local = threading.local() # Espace de stockage propre à chaque thread

    def get(self): # Renvoie la lame ouverte par le thread courant, en l'ouvrant à la première utilisation
        if not hasattr(self.local, "slide"):
            self.local.slide = cd.open_slide(self.path)
        return self.local.slide


def read_level_parallel(pool, level, workers): # Lecture de la miniature découpée en bandes horizontales lues en parallèle (au lieu d'un seul bloc lu tuile par tuile)
    slide = pool.get()
    level = min(level, slide.level_count - 1) # Adaptation du niveau demandé au nombre de niveaux disponibles
    w, h = slide.level_dimensions[level] # Dimensions de la miniature
    ds = slide.level_downsamples[level] # Facteur de réduction entre le niveau 0 et la miniature
    n = max(1, min(workers, h // 256)) # Nombre de bandes (au plus une par thread, chaque bande d'au moins 256 pixels)
    bounds = np.linspace(0, h, n + 1).astype(int) # Limites verticales des bandes

    def strip(i): # Lecture d'une bande ; read_region attend des coordonnées au niveau 0, d'où la multiplication par ds
        y0, y1 = int(bounds[i]), int(bounds[i + 1])
        img = pool.get().read_region((0, int(round(y0 * ds))), level, (w, y1 - y0))
        return np.asarray(img.convert("RGB"))

    with ThreadPoolExecutor(n) as ex: # Lecture simultanée des bandes puis assemblage vertical
        thumb = np.vstack(list(ex.map(strip, range(n))))
    return slide, thumb, level


# 3 IDENTIFICATION DES PATCHES CANDIDATS
def candidate_patches(row, pool, args):

    slide, thumb, level = read_level_parallel(pool, args.level, args.workers) # Chargement de la lame et de sa miniature (lecture parallèle)
    if args.patch_level >= slide.level_count:
        raise ValueError(
            f"Niveau de patch {args.patch_level} absent de {row['slide']} "
            f"(niveaux disponibles : 0 à {slide.level_count - 1})."
        )
    xml = row["xml_path"] if not pd.isna(row["xml_path"]) else None # Remplacement des valeurs manquantes (NaN) par None
    mask = cd.xml_to_mask(xml, slide, level) if xml else np.zeros(thumb.shape[:2], np.uint8) # Masque tumoral à partir du XML, ou masque vide si la lame n'est pas annotée
    W0, H0 = slide.dimensions# Récupération des dimensions de la lame au niveau initial
    pas = int(round(args.patch * slide.level_downsamples[args.patch_level])) # Taille d'un patch en pixels du niveau 0 (224 au niveau 0, ~448 au niveau 1)
    gw, gh = W0 // pas, H0 // pas # Calcul du nombre de patches sur chaque axe
    if gw < 1 or gh < 1:
        raise ValueError(f"Patch trop grand pour la lame : pas niveau 0 = {pas}, dimensions = {(W0, H0)}")

    tissue = detect_purple(thumb).astype(np.float32)# Détection des régions tissulaires sur la miniature
    tissue_frac = cv2.resize(tissue, (gw, gh), interpolation=cv2.INTER_AREA)# Redimensionnement du masque tissulaire à la grille des patches
    tumor_frac = cv2.resize(mask.astype(np.float32), (gw, gh), interpolation=cv2.INTER_AREA)# Redimensionnement du masque tumoral à la même résolution

    rows, cols = np.nonzero(tissue_frac >= args.min_tissue)# Récupération des positions dont la proportion de tissu dépasse le seuil minimal.
    tf, tu = tissue_frac[rows, cols], tumor_frac[rows, cols]# Extraction des proportions tissulaires et tumorales
    cand = pd.DataFrame({"x": cols * pas, "y": rows * pas, "tissue_frac": tf, "tumor_frac": tu})# Création du DataFrame contenant les coordonnées et les proportions associées à chaque patch

    if row["annotated"]:# Attribution des labels pour les lames annotées
        cand["label"] = np.where(tu >= args.tumor_thr, "tumor", np.where(tu == 0, "normal", "border"))
        cand = cand[cand.label != "border"]    # Suppression des patches situés sur les frontières tumorales
    elif row.get("slide_label") == "negative":# Attribution du label normal aux lames négatives
        cand["label"] = "normal"
    else:
        cand["label"] = "unlabeled"  # Attribution du label non renseigné aux autres lames
    return slide, thumb, tissue, mask, cand

# 4 CREATION DES IMAGES DE PREVISUALISATION

def save_preview(path, thumb, tissue, mask, chosen, patch, ds):
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
    t0 = time.time() # Début du chronométrage de la lame
    out = Path(args.out) # Dossier de sortie
    pool = SlidePool(row["tif_path"]) # Gestionnaire des lames ouvertes (une par thread)
    slide, thumb, tissue, mask, cand = candidate_patches(row, pool, args)
    # Une graine déterministe propre à la lame évite d'appliquer exactement la
    # même permutation relative à chaque groupe, tout en restant reproductible.
    slide_seed = int.from_bytes(
        hashlib.sha256(f"{args.seed}:{row['slide']}".encode()).digest()[:8], "big"
    )
    rng = np.random.default_rng(slide_seed)
    chosen = [] # Initialisation de la liste qui contiendra les patches sélectionnés
    for label, group in cand.groupby("label"): # Regroupement des patches selon leur classe
        n = args.max_tumor if label == "tumor" else args.max_normal # Définition du nombre maximal de patches à sélectionner selon leur classe
        idx = rng.permutation(len(group))[:n] # Sélection aléatoire des indices des patches dans chaque groupe
        chosen.append(group.iloc[idx])# Ajout des patches sélectionnés à la liste
    chosen = pd.concat(chosen) if chosen else cand.iloc[:0]# Concaténation des groupes sélectionnés dans un seul DataFrame, ou création d'un DataFrame vide si aucun patch n'a été sélectionné
    chosen = chosen.sort_values(["y", "x"]) # Tri par position : des patches voisins se trouvent dans les mêmes blocs du fichier, téléchargés une seule fois

    ds = slide.dimensions[0] / thumb.shape[1]# Calcul du facteur de réduction entre la largeur de la lame originale et celle de sa miniature
    (out / "previews").mkdir(parents=True, exist_ok=True)# Création du dossier destiné à stocker les images de prévisualisation
    save_preview(out / "previews" / f"{row['slide']}.png", thumb, tissue, mask, chosen,
                 args.patch * slide.level_downsamples[args.patch_level], ds)# Création et sauvegarde de l'image de prévisualisation avec les patches sélectionnés
    for label in chosen.label.unique(): # Création des dossiers de destination une seule fois, avant les threads
        (out / label).mkdir(parents=True, exist_ok=True)

    def read_and_save(r):
        img = cd.read_patch(pool.get(), int(r.x), int(r.y), size=args.patch, level=args.patch_level)# Lecture du patch avec la lame ouverte par le thread courant
        if detect_purple(img).mean() < args.min_tissue:   # Vérification de la proportion de tissu violet directement sur le patch en pleine résolution
            return None # Exclusion du patch si sa proportion de tissu est inférieure au seuil minimal
        p = out / r.label / f"{row['slide']}_x{int(r.x)}_y{int(r.y)}.png" # Construction du chemin de sauvegarde du patch à partir de l'identifiant de la lame et de ses coordonnées
        cv2.imwrite(str(p), cv2.cvtColor(img, cv2.COLOR_RGB2BGR)) # Conversion de l'image du format RGB vers BGR puis sauvegarde au format PNG
        # Chemin relatif au manifeste patches.csv : le dossier peut ainsi être
        # déplacé avec ses images sans réécrire toutes les lignes.
        return {"path": p.relative_to(out).as_posix(), "slide": row["slide"], "patient": row["patient"],
                "center": row["center"], "niveau": args.patch_level, "label": r.label, "x": int(r.x), "y": int(r.y),
                "tissue_frac": round(float(r.tissue_frac), 3), "tumor_frac": round(float(r.tumor_frac), 3)}# Création d'un dictionnaire contenant les informations associées au patch sauvegardé

    with ThreadPoolExecutor(args.workers) as ex:# Création d'un pool de threads pour paralléliser la lecture et la sauvegarde des patches
        recs = [r for r in ex.map(read_and_save, chosen.itertuples()) if r]# Application de la fonction read_and_save à chaque patch sélectionné et récupération des résultats non nuls
    return row["slide"], pd.DataFrame(recs), time.time() - t0 # Retour du nom de la lame, des patches sauvegardés et du temps de traitement

# 6 INTERFACE LIGNE DE COMMANDE

"""
Exemples :

    python -m src.group_pipeline.extract_patches --max-slides 2
    python -m src.group_pipeline.extract_patches --index data/CAMELYON17/index.csv
    python -m src.group_pipeline.extract_patches --patch-level 0
    python -m src.group_pipeline.extract_patches --patch-level 1

"""

def main():
    ap = argparse.ArgumentParser() # Création du parseur permettant de récupérer les arguments fournis lors de l'exécution du script
    ap.add_argument("--out", default=os.environ.get("PATCH_DIR", "patches"))# Définition du dossier de sortie, avec utilisation de la variable d'environnement PATCH_DIR si elle existe
    ap.add_argument("--index", type=Path, default=None,
                    help="index CSV déjà préparé ; évite un nouvel inventaire S3")
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
    args = ap.parse_args()
    if args.patch <= 0 or args.min_tissue < 0 or args.min_tissue > 1 or args.tumor_thr < 0 or args.tumor_thr > 1:
        ap.error("patch doit être positif et min-tissue/tumor-thr doivent être compris entre 0 et 1")
    if args.slide_workers < 1 or args.workers < 1:
        ap.error("slide-workers et workers doivent être supérieurs ou égaux à 1")
    if args.level < 0 or any(niveau < 0 for niveau in args.patch_level):
        ap.error("level et patch-level doivent être positifs ou nuls")
    if args.max_slides is not None and args.max_slides < 1:
        ap.error("max-slides doit être supérieur ou égal à 1")

    if args.index and not args.index.is_file():
        ap.error(f"index introuvable : {args.index}")
    df = pd.read_csv(args.index) if args.index else cd.build_remote_index()
    colonnes_index = {"slide", "tif_path", "xml_path", "patient", "center", "slide_label", "annotated"}
    manquantes = colonnes_index - set(df.columns)
    if manquantes:
        ap.error(f"colonnes manquantes dans l'index : {sorted(manquantes)}")
    if df.empty:
        ap.error("l'index ne contient aucune lame")
    if df["annotated"].dtype == object:
        valeurs = df["annotated"].astype(str).str.lower()
        inconnues = sorted(set(valeurs) - {"true", "false"})
        if inconnues:
            ap.error(f"valeurs annotated inconnues : {inconnues}")
        df["annotated"] = valeurs.eq("true")
    if args.slides == "annotated":# Sélection uniquement des lames disposant d'annotations tumorales
        df = df[df.annotated]
    elif args.slides == "labelled":# Sélection des lames annotées et des lames identifiées comme négatives
        if df.slide_label.isna().all():# Vérification de la présence des labels associés aux lames
            print("! slide_label vide (stage_labels.csv manquant) : seules les lames annotées sont prises.")
        df = df[df.annotated | (df.slide_label == "negative")]# Conservation des lames annotées ou dont le label est négatif
    if args.max_slides:# Vérification de l'existence d'une limite sur le nombre de lames à traiter
        df = df.head(args.max_slides)# Conservation uniquement des premières lames selon la limite définie

    for niveau in args.patch_level: # Un passage par niveau, chacun dans son dossier : patches/niveau_0, patches/niveau_1
        print(f"\n===== Niveau {niveau} =====")
        extraire_niveau(argparse.Namespace(**{**vars(args), "patch_level": niveau,
                                               "out": str(Path(args.out) / f"niveau_{niveau}")}), df)


def extraire_niveau(args, df): # Extraction des patches d'un niveau pour toutes les lames sélectionnées
    out = Path(args.out)#Conversion du chemin de sortie en objet Path pour faciliter la manipulation des fichiers et dossiers
    out.mkdir(parents=True, exist_ok=True)# Création du dossier de sortie s'il n'existe pas déjà
    csv_path = out / "patches.csv" #Définition du chemin du fichier CSV qui contiendra les informations sur les patches extraits
    done = set(pd.read_csv(csv_path).slide) if csv_path.exists() and csv_path.stat().st_size else set()# Récupération des identifiants des lames déjà traitées à partir du CSV, ou initialisation d'un ensemble vide si le fichier n'existe pas
    todo = [r for _, r in df[~df.slide.isin(done)].iterrows()]# Sélection des lames qui n'ont pas encore été traitées afin d'éviter de répéter le travail
    print(f"{len(df)} lames sélectionnées, {len(done)} déjà faites, {len(todo)} à traiter "
          f"({args.slide_workers} lames x {args.workers} lectures en parallèle) -> {out.resolve()}")# Affichage du nombre de lames sélectionnées, déjà traitées et restantes, du parallélisme et du chemin de sortie

    t_start = time.time() # Début du chronométrage global
    with ProcessPoolExecutor(args.slide_workers) as ex: # Création d'un pool de processus : plusieurs lames traitées en même temps
        futures = {ex.submit(process_slide, r, args): r["slide"] for r in todo} # Envoi de chaque lame à un processus
        for i, fut in enumerate(as_completed(futures), 1):# Récupération des résultats au fur et à mesure que les lames se terminent
            name = futures[fut]
            try:
                name, recs, secs = fut.result()# Résultat de la lame : nom, patches sauvegardés, temps de traitement
            except Exception as e: # Interception des erreurs afin qu'une lame problématique n'interrompe pas le traitement de toutes les autres
                print(f"[{i}/{len(todo)}] {name} : ERREUR {e}")# Affichage du numéro de la lame, de son identifiant et du message d'erreur rencontré
                continue # Passage à la lame suivante en cas d'erreur
            if len(recs): # Seul le processus principal écrit dans le CSV (évite que deux processus écrivent en même temps)
                recs.to_csv(csv_path, mode="a", header=not csv_path.exists(), index=False)# Ajout des informations des patches au fichier CSV sans écraser les données précédentes et ajout de l'en-tête uniquement si le fichier n'existe pas
            counts = recs.label.value_counts().to_dict() if len(recs) else {}# Calcul du nombre de patches sauvegardés pour chaque classe, ou création d'un dictionnaire vide si aucun patch n'a été extrait
            eta = (time.time() - t_start) / i * (len(todo) - i) # Estimation du temps restant à partir du temps moyen par lame
            print(f"[{i}/{len(todo)}] {name} : {counts} en {secs / 60:.1f} min | reste ~{eta / 60:.0f} min")# Affichage de l'avancement, des patches obtenus, du temps de la lame et du temps restant estimé

    if csv_path.exists():# Vérification de l'existence du fichier CSV contenant les résultats
        allp = pd.read_csv(csv_path)# Chargement de l'ensemble des informations enregistrées dans le fichier CSV
        print("\nTotal :", allp.label.value_counts().to_dict(), f"({allp.slide.nunique()} lames)")# Affichage du nombre total de patches par classe et du nombre de lames traitées


if __name__ == "__main__":
    main()
