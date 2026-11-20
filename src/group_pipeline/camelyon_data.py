import argparse # Gestion des arguments et commandes passés depuis le terminal
import io # Lecture d'une archive ZIP directement en mémoire
import os # Interaction avec le système d'exploitation et récupération des variables d'environnement
import zipfile # Lecture de l'archive ZIP des annotations (petite, quelques centaines de Ko)
import xml.etree.ElementTree as ET # Lecture et analyse des fichiers XML contenant les annotations
from pathlib import Path # Manipulation des chemins d'accès aux fichiers et dossiers

import cv2 # Traitement d'images, notamment le remplissage des polygones
import numpy as np # Manipulation de tableaux numériques et de matrices d'images
import pandas as pd # Manipulation des tableaux de données et des fichiers CSV

# CHEMINS D'ACCÈS

DATA_DIR = Path(os.environ.get("CAMELYON_DIR", "data/CAMELYON17")) # Récupération du dossier principal depuis une variable d'environnement, ou utilisation du chemin par défaut
ANNOT_DIR = DATA_DIR / "annotations" # Dossier contenant les annotations XML
LABELS_CSV = DATA_DIR / "stages.csv" # Fichier des labels, même nom que sur AWS (CAMELYON17/stages.csv)
PATIENTES_CSV = DATA_DIR / "stages_patientes.csv" # Tableau patientes (une ligne par patiente)
LAMES_CSV = DATA_DIR / "stages_lames.csv" # Tableau lames (une ligne par lame)

TUMOR_GROUPS = {"metastases", "_0", "_1", "tumor"} # Groupes considérés comme tumoraux
EXCLUDE_GROUPS = {"normal", "_2", "exclusion"}   # Groupes correspondant aux régions à exclure du masque


# 1. EXPLORATION DU BUCKET AWS (les lames .tif restent sur AWS, rien n'est téléchargé)

def _s3_client():# Importation des bibliothèques nécessaires à la connexion AWS
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client("s3", config=Config(signature_version=UNSIGNED)) # Création d'un client S3 avec accès anonyme


def list_bucket(bucket="camelyon-dataset", prefix="", s3=None):# Création du client S3 si aucun client n'est fourni

    s3 = s3 or _s3_client()
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/") # Récupération du contenu du bucket au niveau du préfixe indiqué
    print(f"s3://{bucket}/{prefix}")
    for p in resp.get("CommonPrefixes", []):
        print("  [dossier]", p["Prefix"]) # Affichage des sous-dossiers
    for o in resp.get("Contents", []):
        print(f"  {o['Key']}  ({o['Size'] / 1e6:.2f} MB)") # Affichage des fichiers et de leur taille


# 2. CONSTRUCTION DE L'INDEX

REMOTE_ROOT = os.environ.get("CAMELYON_S3", "s3://camelyon-dataset/CAMELYON17/") # Chemin du dossier distant AWS, modifiable par variable d'environnement

def _rows(tif_by_stem, xml_by_stem): # Lecture du CSV des labels, ou création d'un DataFrame vide
    labels = pd.read_csv(LABELS_CSV) if LABELS_CSV.exists() else pd.DataFrame(columns=["patient", "stage"])
    labels.columns = [c.lower() for c in labels.columns] # Normalisation des noms de colonnes
    # Création des dictionnaires associant les fichiers à leurs labelss
    slide_lab = dict(zip(labels.patient.str.replace(".tif", "", regex=False), labels.stage))
    patient_lab = dict(zip(labels.patient.str.replace(".zip", "", regex=False), labels.stage))
    centre = dict(zip(labels.patient.str.replace(".zip", "", regex=False), labels["center"])) if "center" in labels else {} # Centre médical lu dans stages.csv
    rows = []
    for stem, tif in sorted(tif_by_stem.items()): # Parcours des images TIFF disponibles
        if "_node_" not in stem or stem.endswith("_mask"): # Exclusion des fichiers ne correspondant pas à une lame
            continue
        patient = stem.split("_node_")[0] # Extraction de l'identifiant du patient
        num = int(patient.split("_")[1]) # Conversion du numéro de patient en entier
        rows.append({ # Ajout des informations de la lame dans la liste
            "slide": stem,
            "tif_path": str(tif),
            "xml_path": str(xml_by_stem[stem]) if stem in xml_by_stem else None,
            "patient": patient,
            "node": int(stem.split("_node_")[1]),
            "center": centre.get(patient, num // 20 if num < 100 else None), # Centre de stages.csv, sinon déduit du numéro (20 patientes par centre)
            "slide_label": slide_lab.get(stem),
            "pN_stage": patient_lab.get(patient),
        })
    df = pd.DataFrame(rows) # Conversion de la liste en DataFrame
    if not df.empty: # Création d'une colonne indiquant la présence d'une annotation
        df["annotated"] = df.xml_path.notna()
    return df


def download_annotations(root=REMOTE_ROOT, fs=None):
    """Télécharge UNIQUEMENT les annotations XML et stage_labels.csv (quelques Mo).
    Aucune lame .tif n'est téléchargée. Renvoie la liste des fichiers du dossier distant."""
    if fs is None: # Création du système de fichiers S3 (accès anonyme) si nécessaire
        import s3fs
        fs = s3fs.S3FileSystem(anon=True)
    root = root.replace("s3://", "").rstrip("/") # Normalisation du chemin distant
    files = fs.find(root) # Liste récursive des fichiers distants (aucun téléchargement)
    ANNOT_DIR.mkdir(parents=True, exist_ok=True) # Création du dossier local des annotations

    xmls = [f for f in files if f.lower().endswith(".xml")] # Annotations XML présentes en fichiers séparés
    for f in xmls:
        dest = ANNOT_DIR / Path(f).name
        if not dest.exists(): # Téléchargement uniquement si le fichier n'est pas déjà présent
            fs.get(f, str(dest))
    if not xmls: # Sinon : annotations regroupées dans une archive ZIP (ex : lesion_annotations.zip)
        zips = [f for f in files if "annotation" in Path(f).name.lower() and f.lower().endswith(".zip")]
        for z in zips:
            with zipfile.ZipFile(io.BytesIO(fs.cat_file(z))) as zf: # Lecture de l'archive en mémoire
                for m in zf.namelist():
                    if m.lower().endswith(".xml"): # Extraction des seuls fichiers XML
                        (ANNOT_DIR / Path(m).name).write_bytes(zf.read(m))

    if not LABELS_CSV.exists(): # Recherche du fichier des labels
        is_labels = lambda f: Path(f).name.lower() in ("stages.csv", "stage_labels.csv")
        csvs = [f for f in files if is_labels(f)]
        if not csvs: # Pas dans le dossier : recherche dans tout le bucket, CAMELYON17 en priorité
            bucket = root.split("/")[0]
            csvs = sorted((f for f in fs.find(bucket) if is_labels(f)),
                          key=lambda f: "camelyon17" not in f.lower())
        if csvs:
            LABELS_CSV.parent.mkdir(parents=True, exist_ok=True)
            fs.get(csvs[0], str(LABELS_CSV)) # Téléchargement du CSV des labels
            print(f"  stage_labels.csv récupéré depuis s3://{csvs[0]}")
        else:
            print("  ! stage_labels.csv introuvable dans le bucket : slide_label et pN_stage resteront vides")

    if LABELS_CSV.exists(): # Fabrication des tableaux patientes et lames dès que stages.csv est disponible
        charger_tables()
    n_xml = len(list(ANNOT_DIR.glob("*.xml")))
    print(f"  {n_xml} annotations XML dans {ANNOT_DIR} | labels : {'OK' if LABELS_CSV.exists() else 'absents'}")
    return files


def build_remote_index(root=REMOTE_ROOT, fs=None): # Création du système de fichiers S3 si nécessaire
    if fs is None:
        import s3fs
        fs = s3fs.S3FileSystem(anon=True)
    files = download_annotations(root, fs) # Téléchargement des seuls XML + CSV, les .tif restent sur AWS
    tifs = {Path(f).stem: "s3://" + f for f in files if f.lower().endswith(".tif")}# Construction du dictionnaire des images TIFF (chemins distants)
    if not tifs:# Vérification de la présence de fichiers TIFF
        zips = [f for f in files if f.lower().endswith(".zip")]
        raise RuntimeError(
            f"Aucun .tif sous {root} ({len(files)} fichiers, dont {len(zips)} .zip). "
            "Les lames zippées ne peuvent pas être lues à distance : vérifiez le dossier avec "
            "'python camelyon_data.py ls', ou utilisez Colab/Kaggle.")
    xmls = {p.stem: p for p in ANNOT_DIR.glob("*.xml")} # Construction du dictionnaire des annotations locales
    return _rows(tifs, xmls)# Construction du DataFrame avec les chemins TIFF distants


# 2 BIS. FICHIER stages.csv ET TABLEAUX PATIENTES / LAMES

def telecharger_stages(chemin=LABELS_CSV):
    # On télécharge stages.csv (le stade pN de chaque patiente et la classe de chaque lame), s'il n'est pas déjà présent
    if not Path(chemin).exists():
        Path(chemin).parent.mkdir(parents=True, exist_ok=True)
        _s3_client().download_file("camelyon-dataset", "CAMELYON17/stages.csv", str(chemin))
    # pd.read_csv lit le fichier CSV et le transforme en DataFrame
    return pd.read_csv(chemin)


def construire_tables(stages):
    # On fabrique un tableau "patientes" (une ligne par patiente) à partir de stages.csv

    # On garde les lignes dont le nom finit par .zip (= les lignes patientes)
    # .str applique une méthode de texte # à chaque élément de la colonne et .copy() fait une vraie copie (pour pouvoir la modifier sans avertissement)
    patientes = stages[stages["patient"].str.endswith(".zip")].copy()
    # On récupère le numéro de la patiente avec une regex : la partie entre () est extraite puis convertie en entier
    # .str.extract(...) cherche le modèle (la regex) dans le texte et récupère ce qui est entre parenthèses.
    patientes["patiente"] = patientes["patient"].str.extract(r"patient_(\d+)")[0].astype(int) #\d+ = un ou plusieurs chiffres à la suite
    # On renomme les colonnes en français
    patientes = patientes.rename(columns={"stage": "stade_pN", "center": "centre_medical"})
    # On garde seulement les colonnes utiles et on renumérote les lignes à partir de 0 (drop=True = sans garder l'ancien index)
    patientes = patientes[["patiente", "centre_medical", "stade_pN"]].reset_index(drop=True)

    # On fabrique un tableau "lames" (une ligne par lame) à partir de stages.csv

    # On garde les lignes dont le nom finit par .tif (= les lignes lames)
    lames = stages[stages["patient"].str.endswith(".tif")].copy()
    # On extrait deux nombres d'un coup (numéro de patiente et numéro de ganglion) dans deux nouvelles colonnes
    lames[["patiente", "ganglion"]] = lames["patient"].str.extract(r"patient_(\d+)_node_(\d+)").astype(int)
    # On renomme les colonnes en français
    lames = lames.rename(columns={"patient": "lame", "stage": "classe", "center": "centre_medical"})
    # On retire ".tif" à la fin du nom (regex=False : .tif est compris comme un texte et non une regex)
    lames["lame"] = lames["lame"].str.replace(".tif", "", regex=False)
    # On garde les colonnes utiles dans cet ordre et on renumérote les lignes
    lames = lames[["lame", "patiente", "ganglion", "centre_medical", "classe"]].reset_index(drop=True)
    return patientes, lames


def charger_tables():
    # Relit stages_patientes.csv et stages_lames.csv, ou les fabrique à partir de stages.csv (téléchargé si besoin)
    if not (PATIENTES_CSV.exists() and LAMES_CSV.exists()):
        patientes, lames = construire_tables(telecharger_stages())
        patientes.to_csv(PATIENTES_CSV, index=False)
        lames.to_csv(LAMES_CSV, index=False)
    return pd.read_csv(PATIENTES_CSV), pd.read_csv(LAMES_CSV)


# 3. LECTURE DES ANNOTATIONS ET CREATION DES MASQUES
def annotation_groups(xml_path):
    root = ET.parse(xml_path).getroot()
    return sorted({a.get("PartOfGroup") for a in root.iter("Annotation")})# Extraction des groupes d'annotations sans doublons.


def xml_to_mask(xml_path, slide, level): # Récupération des dimensions de la lame au niveau choisi
    w, h = slide.level_dimensions[level]
    ds = slide.level_downsamples[level] # Récupération du facteur de réduction de résolution
    mask = np.zeros((h, w), np.uint8)# Initialisation d'un masque binaire rempli de zéros
    excluded = []# Liste des polygones à exclure
    for ann in ET.parse(xml_path).getroot().iter("Annotation"):# Parcours des annotations XML
        # Extraction des coordonnées des sommets du polygone
        # Conversion des coordonnées en nombres décimaux
        pts = np.array([[float(c.get("X").replace(",", ".")),
                         float(c.get("Y").replace(",", "."))]
                        for c in ann.iter("Coordinate")])
        # Ignorer les annotations contenant moins de trois points
        if len(pts) < 3:
            continue
        # Adaptation des coordonnées au niveau de résolution choisi
        # Conversion en entiers pour leur utilisation avec OpenCV
        pts = np.round(pts / ds).astype(np.int32)
        group = (ann.get("PartOfGroup") or "").lower()# Récupération du groupe associé à l'annotation
        if group in EXCLUDE_GROUPS:# Stockage des polygones appartenant aux groupes exclus
            excluded.append(pts)
        elif group in TUMOR_GROUPS: # Remplissage du polygone tumoral dans le masque avec la valeur 1
            cv2.fillPoly(mask, [pts], 1)
        else:
            raise ValueError(
                f"Groupe XML non pris en charge : {group!r}. "
                "Ne pas l'interpréter automatiquement comme tumoral."
            )
    if excluded:# Application des exclusions avec la valeur 0
        cv2.fillPoly(mask, excluded, 0)
    return mask

#4. OUVERTURE ET CHARGEMENT DES LAMES

S3_OPTIONS = {"anon": True, "default_block_size": 512 * 1024, "default_cache_type": "readahead"}

def open_slide(path):# Utilisation de TiffSlide pour les fichiers stockés sur AWS

    if str(path).startswith("s3://"):
        import tiffslide
        return tiffslide.TiffSlide(str(path), storage_options=S3_OPTIONS)
    import openslide
    return openslide.OpenSlide(str(path))# Utilisation d'OpenSlide pour les fichiers locaux


def load_slide(row, level=5):# Adaptation du niveau demandé au nombre de niveaux disponibles

    slide = open_slide(row["tif_path"])
    level = min(level, slide.level_count - 1)
    size = slide.level_dimensions[level] # Récupération des dimensions au niveau sélectionné
    thumb = np.asarray(slide.read_region((0, 0), level, size).convert("RGB"))# Lecture de l'image et conversion en tableau NumPy RGB
    mask = xml_to_mask(row["xml_path"], slide, level) if row["xml_path"] else np.zeros(thumb.shape[:2], np.uint8)# Création du masque si une annotation XML est disponible sinon initialisation d'un masque vide
    return slide, thumb, mask, level


#5. EXTRACTION DES PATCHES

def read_patch(slide, x0, y0, size=224, level=0): #Lecture d'une région de la lame à partir des coordonnées # fournies, puis conversion en tableau NumPy RGB

    return np.asarray(slide.read_region((x0, y0), level, (size, size)).convert("RGB"))

# 6. SEPARATION DES DONNEES PAR PATIENTE

def split_by_patient(df, test_size=0.2, seed=0):# Importation de la méthode de séparation par groupes
    from sklearn.model_selection import GroupShuffleSplit
    tr, te = next(GroupShuffleSplit(1, test_size=test_size, random_state=seed)# Séparation des indices en respectant les groupes patientes
                  .split(df, groups=df.patient))
    return df.iloc[tr], df.iloc[te] # Retour des DataFrames d'entraînement et de test


# 7. INTERFACE LIGNE DE COMMANDE

"""
Exemples :
    python -m src.group_pipeline.camelyon_data ls
    python -m src.group_pipeline.camelyon_data stages
    python -m src.group_pipeline.camelyon_data annotations
    python -m src.group_pipeline.camelyon_data remote-index
"""

if __name__ == "__main__": #Exécution du programme principal uniquement si le fichier est lancé directement et non importé comme module
    ap = argparse.ArgumentParser() # Création du parseur d'arguments
    ap.add_argument("cmd", choices=["ls", "stages", "annotations", "remote-index"]) # Définition des commandes autorisées
    ap.add_argument("--bucket", default="camelyon-dataset") # Définition du bucket AWS
    ap.add_argument("--prefix", default=None, help="dossier dans le bucket")# Définition du préfixe AWS
    a = ap.parse_args() # Récupération des arguments fournis dans le terminal

    if a.cmd == "ls":# Commande d'exploration du bucket
        list_bucket(a.bucket, a.prefix or "")
        raise SystemExit
    if a.cmd == "stages":# Téléchargement de stages.csv et fabrication des tableaux patientes et lames
        patientes, lames = charger_tables()
        print(f"stages.csv : {len(patientes)} patientes et {len(lames)} lames -> {PATIENTES_CSV} et {LAMES_CSV}")
        print(patientes.head(), "\n", lames.head())
        raise SystemExit
    if a.cmd == "annotations":# Téléchargement des seuls fichiers XML et CSV
        download_annotations(f"s3://{a.bucket}/{a.prefix}" if a.prefix else REMOTE_ROOT)
        raise SystemExit
    if a.cmd == "remote-index":# Construction de l'index distant
        root = f"s3://{a.bucket}/{a.prefix}" if a.prefix else REMOTE_ROOT
        df = build_remote_index(root)# Construction de l'index local
    if not df.empty:# Enregistrement de l'index au format CSV
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(DATA_DIR / "index.csv", index=False)
        print(f"\n{len(df)} lames, {df.annotated.sum()} annotées -> {DATA_DIR / 'index.csv'}")# Affichage du nombre de lames et d'annotations
