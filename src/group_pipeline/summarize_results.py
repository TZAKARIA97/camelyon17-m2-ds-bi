"""Résumer de façon reproductible un fichier de prédictions de patchs.

Ce module est volontairement indépendant de PyTorch : il permet d'auditer un
CSV de prédictions sans recharger le classifieur sérialisé.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

LABELS = {"sain": 0, "tumoral": 1, "normal": 0, "tumor": 1}


def metrics_at_threshold(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    """Calcule les métriques binaires au seuil fourni, avec leurs effectifs."""
    y_pred = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "threshold": float(threshold),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
    }


def highest_threshold_for_recall(
    y_true: np.ndarray, scores: np.ndarray, target_recall: float
) -> float:
    """Renvoie le seuil ROC le plus élevé atteignant le rappel demandé."""
    if not 0 < target_recall <= 1:
        raise ValueError("target_recall doit être compris dans ]0, 1].")
    _, true_positive_rate, thresholds = roc_curve(y_true, scores)
    eligible = np.flatnonzero(true_positive_rate >= target_recall)
    if not len(eligible):
        raise ValueError("Aucun seuil ne permet d'atteindre le rappel demandé.")
    return float(thresholds[eligible[0]])


def summarize_predictions(
    predictions: pd.DataFrame,
    fixed_threshold: float = 0.5,
    target_recall: float = 0.95,
) -> dict:
    """Valide et résume les prédictions d'un ou plusieurs ensembles."""
    required = {"etiquette", "proba_tumoral"}
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {sorted(missing)}")
    if predictions.empty:
        raise ValueError("Le fichier de prédictions est vide.")

    normalized_labels = predictions["etiquette"].astype(str).str.lower()
    unknown = sorted(set(normalized_labels) - set(LABELS))
    if unknown:
        raise ValueError(f"Étiquettes inconnues : {unknown}")
    y_true = normalized_labels.map(LABELS).to_numpy(dtype=int)
    if np.unique(y_true).size != 2:
        raise ValueError("Les deux classes sont nécessaires pour calculer la ROC-AUC.")
    scores = pd.to_numeric(predictions["proba_tumoral"], errors="raise").to_numpy()
    if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
        raise ValueError("proba_tumoral doit contenir des probabilités finies entre 0 et 1.")

    recall_threshold = highest_threshold_for_recall(y_true, scores, target_recall)
    summary = {
        "n_predictions": int(len(predictions)),
        "n_negative": int((y_true == 0).sum()),
        "n_positive": int((y_true == 1).sum()),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "fixed_threshold": metrics_at_threshold(y_true, scores, fixed_threshold),
        "validation_selected_threshold": {
            "target_recall": float(target_recall),
            **metrics_at_threshold(y_true, scores, recall_threshold),
        },
    }
    for column in ("set", "lame", "niveau"):
        if column in predictions:
            counts = predictions[column].astype(str).value_counts(dropna=False)
            summary[f"counts_by_{column}"] = {str(k): int(v) for k, v in counts.items()}
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seuil-fixe", type=float, default=0.5)
    parser.add_argument("--rappel-cible", type=float, default=0.95)
    args = parser.parse_args()
    if not 0 <= args.seuil_fixe <= 1:
        parser.error("seuil-fixe doit être compris entre 0 et 1")

    summary = summarize_predictions(
        pd.read_csv(args.predictions), args.seuil_fixe, args.rappel_cible
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
