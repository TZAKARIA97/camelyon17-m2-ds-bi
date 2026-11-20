import argparse
from pathlib import Path

import joblib
import pandas as pd

import analyze


def lister_images(source):
    source = Path(source)
    if source.is_file() and source.suffix.lower() == ".csv":
        table = pd.read_csv(source)
        if "path" not in table.columns:
            raise ValueError("Le CSV d'entrée doit contenir une colonne 'path'.")
        return table
    if source.is_dir():
        paths = sorted(str(path) for path in source.rglob("*.png"))
        if not paths:
            raise ValueError(f"Aucun PNG trouvé dans {source}.")
        return pd.DataFrame({"path": paths})
    raise FileNotFoundError(source)


def predire(source, modele_path, sortie, seuil=None, taille_lot=64, lecteurs=0, appareil=None):
    table = lister_images(source).reset_index(drop=True)
    table_modele = table.assign(y=0)
    appareil = appareil or analyze.choisir_appareil()
    extracteur = analyze.creer_extracteur(appareil)
    X, _ = analyze.extraire_caracteristiques(
        extracteur, table_modele[["path", "y"]], appareil,
        taille_lot=taille_lot, nb_workers=lecteurs,
    )
    bundle = joblib.load(modele_path)
    if isinstance(bundle, dict):
        classifieur = bundle["classifieur"]
        seuil_modele = bundle.get("seuil")
    else:
        classifieur = bundle
        seuil_modele = None
    seuil = seuil if seuil is not None else seuil_modele
    if seuil is None:
        raise ValueError("Le modèle ne contient pas de seuil : utilisez --seuil.")
    proba = classifieur.predict_proba(X)[:, 1]
    resultat = table.copy()
    resultat["proba_tumoral"] = proba
    resultat["prediction"] = (proba >= seuil).astype(int)
    resultat["etiquette_predite"] = resultat["prediction"].map({0: "normal", 1: "tumor"})
    resultat["seuil"] = float(seuil)
    sortie = Path(sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    resultat.to_csv(sortie, index=False)
    return resultat


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prédire des patches CAMELYON17 avec le modèle final.")
    parser.add_argument("--input", required=True, help="dossier de PNG ou CSV contenant une colonne path")
    parser.add_argument("--modele", default="resultats_finaux/modele_final.joblib")
    parser.add_argument("--sortie", default="predictions_nouvelles.csv")
    parser.add_argument("--seuil", type=float, default=None)
    parser.add_argument("--taille-lot", type=int, default=64)
    parser.add_argument("--lecteurs-png", type=int, default=0)
    parser.add_argument("--appareil", choices=["cpu", "cuda", "xpu"], default=None)
    args = parser.parse_args()
    resultat = predire(args.input, args.modele, args.sortie, args.seuil,
                        args.taille_lot, args.lecteurs_png, args.appareil)
    print(resultat["etiquette_predite"].value_counts().to_string())
    print(f"{len(resultat)} prédictions enregistrées dans {args.sortie}")
