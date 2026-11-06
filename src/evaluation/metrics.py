"""Métriques binaires : conserver les dénominateurs et les cas indéfinis."""
import numpy as np
from sklearn.metrics import confusion_matrix, roc_auc_score, average_precision_score


def binary_metrics(labels, scores, threshold=0.5):
    """Évaluer des scores de classe 1 ; seuil fixé avant la lecture du test."""
    y, p = np.asarray(labels), np.asarray(scores, dtype=float)
    if y.ndim != 1 or p.ndim != 1 or len(y) != len(p) or not len(y):
        raise ValueError('Vecteurs non vides de même longueur attendus.')
    if not set(y.tolist()) <= {0, 1} or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('Labels 0/1 et probabilités finies entre 0 et 1 attendus.')
    if not 0 <= threshold <= 1:
        raise ValueError('Seuil hors [0,1].')
    tn, fp, fn, tp = map(int, confusion_matrix(y, p >= threshold, labels=[0, 1]).ravel())
    def ratio(a, b):
        return float(a / b) if b else None
    both = len(np.unique(y)) == 2
    return dict(n=len(y), threshold=threshold, tn=tn, fp=fp, fn=fn, tp=tp,
                sensitivity=ratio(tp, tp+fn), specificity=ratio(tn, tn+fp),
                precision=ratio(tp, tp+fp), f1=ratio(2*tp, 2*tp+fp+fn),
                accuracy=ratio(tp+tn, len(y)), prevalence=float(y.mean()),
                roc_auc=float(roc_auc_score(y, p)) if both else None,
                average_precision=float(average_precision_score(y, p)) if both else None)
