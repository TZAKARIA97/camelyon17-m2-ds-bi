# Fichier avec les caractéristiques ResNet18 de TOUS les patchs de tissu des lames entières

"""
Pour chaque lame de validation et de test (fichier de sélection), on parcourt tout le tissu avec un pas égal
à la zone centrale (56 µm) : chaque endroit du tissu est ainsi au centre d'un patch (comme dans le prototype).
Pour chaque patch on enregistre ses 512 caractéristiques ResNet18 (pas la probabilité) : la régression
logistique est appliquée ensuite dans le notebook 02_modelisation_evaluation, et peut donc être changée sans tout recalculer.

Mêmes réglages que le découpage (parametres_decoupage.py) : surface du patch (112 µm), détection du tissu
(detect_purple, seuil de saturation), tissu minimum (50 % sur la miniature puis sur le patch lui-même),
lecture à surface fixe puis redimensionnement en 224 pixels.

Pour aller vite (lames lues sur AWS) :
- on lit la lame par grands blocs (bloc x bloc cases) au lieu de patch par patch : les patchs se chevauchent
  (112 µm de côté, pas de 56 µm), chaque pixel n'est donc lu qu'une fois au lieu de quatre ;
- plusieurs blocs sont lus en même temps (threads) pendant que ResNet18 calcule (carte graphique si disponible).

Résultat : un fichier par lame, cartes/niveau_<n>/<lame>.npz (positions, caractéristiques, aperçu de la lame).
Une lame déjà faite est sautée : si le calcul est coupé, on relance la même commande.

Utilisation (depuis le dossier version_finale) :
    python cartes_chaleur.py --niveau 2                      (validation puis test)
    python cartes_chaleur.py --niveau 2 --sets validation    (seulement la validation)
    python cartes_chaleur.py --niveau 2 --max-slides 1       (essai sur une lame, pour mesurer le temps)
"""

import argparse
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

import camelyon_data as cd
import extract_patches as ep
import modele_patch as mp
import parametres_decoupage as pdc

P = pdc.PARAMETRES


def positions_tissu(thumb, ds_t, W0, H0, pas0, patch0, args):
    # Grille de pas pas0 (pixels du niveau 0) : le patch (r, c) a son coin en (c * pas0, r * pas0).
    # On garde les patchs avec au moins min_tissue de tissu sur la miniature (comme pour le découpage).
    tissu = ep.detect_purple(thumb, args.violet_s_min).astype(np.float64)
    integ = cv2.integral(tissu)                      # somme cumulée : surface de tissu d'un rectangle en 4 lectures
    nr, nc = (H0 - patch0) // pas0 + 1, (W0 - patch0) // pas0 + 1
    r, c = np.meshgrid(np.arange(nr), np.arange(nc), indexing="ij")
    y0 = np.clip(np.round(r * pas0 / ds_t).astype(int), 0, tissu.shape[0])
    x0 = np.clip(np.round(c * pas0 / ds_t).astype(int), 0, tissu.shape[1])
    y1 = np.clip(np.round((r * pas0 + patch0) / ds_t).astype(int), 0, tissu.shape[0])
    x1 = np.clip(np.round((c * pas0 + patch0) / ds_t).astype(int), 0, tissu.shape[1])
    surface = integ[y1, x1] - integ[y0, x1] - integ[y1, x0] + integ[y0, x0]
    frac = surface / np.maximum((y1 - y0) * (x1 - x0), 1)
    garde = frac >= args.min_tissue
    return r[garde], c[garde], frac[garde]


def traiter_lame(ligne, modele, appareil, args, sortie):
    t0 = time.time()
    pool = ep.SlidePool(ligne["tif_path"])               # une lame ouverte par thread (code de la camarade)
    slide, thumb, niveau_t = ep.read_level_parallel(pool, args.level, args.workers)
    ds_t = slide.level_downsamples[niveau_t]
    W0, H0 = slide.dimensions
    mpp = cd.taille_pixel_um(slide)
    L = min(args.niveau, slide.level_count - 1)
    dsL = slide.level_downsamples[L]
    pas0 = int(round(args.centre_um / mpp))              # pas = zone centrale (56 µm), en pixels du niveau 0
    patch0 = int(round(args.patch_um / mpp))             # côté du patch (112 µm), en pixels du niveau 0
    taille_lue = max(1, int(round(patch0 / dsL)))        # pixels lus au niveau L (comme geometrie dans extract_patches)

    r, c, frac = positions_tissu(thumb, ds_t, W0, H0, pas0, patch0, args)

    # Blocs de args.bloc x args.bloc cases : on lit chaque bloc d'un coup puis on y découpe ses patchs
    blocs = pd.DataFrame({"r": r, "c": c, "frac": frac})
    blocs["br"], blocs["bc"] = blocs.r // args.bloc, blocs.c // args.bloc
    groupes = [g for _, g in blocs.groupby(["br", "bc"])]

    def lire_bloc(g):
        x0, y0 = int(g.c.min() * pas0), int(g.r.min() * pas0)
        x1, y1 = int(g.c.max() * pas0 + patch0), int(g.r.max() * pas0 + patch0)
        w, h = int(np.ceil((x1 - x0) / dsL)) + 1, int(np.ceil((y1 - y0) / dsL)) + 1
        zone = np.asarray(cd.rgb_fond_blanc(pool.get().read_region((x0, y0), L, (w, h))))
        images, gardes = [], []
        for rr, cc, ff in zip(g.r, g.c, g.frac):
            px, py = int(round((cc * pas0 - x0) / dsL)), int(round((rr * pas0 - y0) / dsL))
            img = zone[py:py + taille_lue, px:px + taille_lue]
            if img.shape[:2] != (taille_lue, taille_lue):  # bord de la lame : on complète en blanc
                tmp = np.full((taille_lue, taille_lue, 3), 255, np.uint8)
                tmp[:img.shape[0], :img.shape[1]] = img
                img = tmp
            if taille_lue != args.patch:                   # remis à 224 pixels, comme read_and_save
                img = cv2.resize(img, (args.patch, args.patch),
                                 interpolation=cv2.INTER_AREA if taille_lue > args.patch else cv2.INTER_LINEAR)
            # Même revérification du tissu que pour le découpage (sur le patch en pleine résolution)
            if ep.detect_purple(img, args.violet_s_min).mean() < args.min_tissue:
                continue
            images.append(np.ascontiguousarray(img))
            gardes.append((rr, cc, ff))
        return images, gardes

    feats, pos = [], []
    with ThreadPoolExecutor(args.workers) as ex:
        # On ne lance que quelques blocs d'avance (sinon tous les blocs lus attendraient en mémoire)
        en_cours, i = [], 0
        while i < len(groupes) or en_cours:
            while i < len(groupes) and len(en_cours) < 2 * args.workers:
                en_cours.append(ex.submit(lire_bloc, groupes[i]))
                i += 1
            images, gardes = en_cours.pop(0).result()
            if images:
                feats.append(mp.caracteristiques(modele, images, appareil, args.taille_lot).astype(np.float16))
                pos += gardes

    pos = np.array(pos, dtype=np.float64).reshape(-1, 3)
    apercu = cv2.resize(thumb, (max(1, thumb.shape[1] // 4), max(1, thumb.shape[0] // 4)), interpolation=cv2.INTER_AREA)
    tmp = sortie / (ligne["slide"] + ".tmp.npz")
    np.savez_compressed(tmp,
                        r=pos[:, 0].astype(np.int32), c=pos[:, 1].astype(np.int32), tissu=pos[:, 2].astype(np.float32),
                        caracteristiques=np.concatenate(feats) if feats else np.zeros((0, 512), np.float16),
                        pas0=pas0, patch0=patch0, mpp=mpp, niveau=L, W0=W0, H0=H0,
                        apercu=apercu, ds_apercu=ds_t * thumb.shape[1] / apercu.shape[1])
    tmp.replace(sortie / (ligne["slide"] + ".npz"))      # écrit d'abord sous un autre nom : jamais de fichier à moitié écrit
    return len(r), len(pos), time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niveau", type=int, default=P["patch_level"][0], help="niveau de lecture des patchs (comme le découpage)")
    ap.add_argument("--sets", nargs="+", default=["validation", "test"], help="sets à traiter, dans cet ordre")
    ap.add_argument("--out", default="cartes")
    ap.add_argument("--slides", nargs="+", default=None, help="seulement ces lames")
    ap.add_argument("--max-slides", type=int, default=None)
    ap.add_argument("--workers", type=int, default=P["workers"], help="blocs lus en même temps")
    ap.add_argument("--bloc", type=int, default=16, help="côté d'un bloc de lecture, en cases")
    ap.add_argument("--taille-lot", type=int, default=64, help="patchs par lot pour ResNet18")
    args = ap.parse_args()
    for cle in ["selection", "patch_um", "patch", "centre_um", "level", "min_tissue", "violet_s_min"]:
        setattr(args, cle, P[cle])     # mêmes réglages que le découpage

    selection = pd.read_csv(args.selection)
    index = cd.build_remote_index()
    lames = []
    for s in args.sets:                # l'ordre des sets est respecté : validation d'abord
        lames.append(selection[selection.set == s])
    lames = pd.concat(lames).merge(index[["slide", "tif_path"]], on="slide", how="left")
    if args.slides:
        lames = lames[lames.slide.isin(args.slides)]
    if lames.tif_path.isna().any():
        raise SystemExit(f"Lames introuvables dans l'index : {list(lames[lames.tif_path.isna()].slide)}")

    sortie = Path(args.out) / f"niveau_{args.niveau}"
    sortie.mkdir(parents=True, exist_ok=True)
    a_faire = [l for _, l in lames.iterrows() if not (sortie / (l["slide"] + ".npz")).exists()]
    if args.max_slides:
        a_faire = a_faire[:args.max_slides]
    appareil = mp.choisir_appareil()
    modele = mp.charger_resnet(appareil)
    print(f"{len(lames)} lames ({', '.join(args.sets)}), {len(lames) - len(a_faire)} déjà faites, {len(a_faire)} à traiter "
          f"| niveau {args.niveau} | calculs sur {appareil} -> {sortie.resolve()}")

    t_start = time.time()
    for i, ligne in enumerate(a_faire, 1):
        try:
            n_cand, n_gardes, secs = traiter_lame(ligne, modele, appareil, args, sortie)
        except Exception as e:          # une lame en erreur n'arrête pas les autres (elle sera refaite au prochain lancement)
            print(f"[{i}/{len(a_faire)}] {ligne['slide']} ({ligne['set']}) : ERREUR {e}")
            continue
        reste = (time.time() - t_start) / i * (len(a_faire) - i)
        print(f"[{i}/{len(a_faire)}] {ligne['slide']} ({ligne['set']}) : {n_gardes} patchs de tissu "
              f"({n_cand} candidats) en {secs / 60:.1f} min | reste ~{reste / 60:.0f} min")


if __name__ == "__main__":
    main()
