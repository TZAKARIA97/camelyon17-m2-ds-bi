"""Créer figures et commentaire descriptif à partir d'une évaluation traçable."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from ..evaluation.metrics import binary_metrics
from ..provenance import sha256_file


def load_evaluation(directory):
    """Refuser des prédictions remplacées ou des métriques globales incompatibles."""
    directory = Path(directory)
    metadata = json.loads((directory / 'provenance.json').read_text(encoding='utf-8'))
    if sha256_file(directory / 'predictions.csv') != metadata['predictions_sha256']:
        raise ValueError('Les prédictions ont changé depuis l’évaluation.')
    frame = pd.read_csv(directory / 'predictions.csv', dtype={'patient_id': str,
                       'slide_id': str, 'center_id': str}, keep_default_na=False)
    metrics = json.loads((directory / 'metrics.json').read_text(encoding='utf-8'))
    actual = binary_metrics(frame.label, frame.score, metadata['threshold'])
    for key, value in actual.items():
        saved = metrics['overall'].get(key)
        if (value is None) != (saved is None) or (value is not None and not np.isclose(value, saved)):
            raise ValueError(f'Métrique incohérente avec les prédictions : {key}')
    if not (frame.prediction == (frame.score >= metadata['threshold']).astype(int)).all():
        raise ValueError('Décisions incompatibles avec le seuil enregistré.')
    return frame, metrics, metadata


def categories(frame):
    """Nommer chaque cas pour sélectionner aussi des erreurs, sans les dissimuler."""
    return np.select([(frame.label == 1) & (frame.prediction == 1),
                      (frame.label == 0) & (frame.prediction == 0),
                      (frame.label == 0) & (frame.prediction == 1)],
                     ['TP', 'TN', 'FP'], default='FN')


def select_examples(frame, per_category=2):
    """Prendre les premiers chemins triés par type ; règle fixe, non clinique."""
    result = frame.copy()
    result['case'] = categories(result)
    return result.sort_values('path').groupby('case', sort=True).head(per_category).reset_index(drop=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    frame, report, provenance = load_evaluation(args.evaluation)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve, precision_recall_curve
    m = report['overall']
    synthetic = provenance['dataset_kind'] == 'synthetic'
    prefix = 'DÉMONSTRATION SYNTHÉTIQUE — ' if synthetic else ''
    matrix = np.array([[m['tn'], m['fp']], [m['fn'], m['tp']]])
    fig, ax = plt.subplots(figsize=(6.2, 5))
    ax.imshow(matrix, cmap='Blues', vmin=0)
    for (row, col), value in np.ndenumerate(matrix):
        ax.text(col, row, str(value), ha='center', va='center',
                color='white' if value > matrix.max() / 2 else 'black', fontsize=18)
    ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=['Non tumoral', 'Tumoral'],
           yticklabels=['Non tumoral', 'Tumoral'], xlabel='Prédiction', ylabel='Référence',
           title=prefix + f'Matrice de confusion\nSeuil = {m["threshold"]:.3f}')
    fig.tight_layout()
    fig.savefig(out / 'confusion_matrix.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    if frame.label.nunique() == 2:
        fpr, tpr, _ = roc_curve(frame.label, frame.score)
        precision, recall, _ = precision_recall_curve(frame.label, frame.score)
        axes[0].plot(fpr, tpr, label=f'ROC-AUC = {m["roc_auc"]:.3f}')
        axes[0].plot([0, 1], [0, 1], '--', color='gray')
        axes[1].step(recall, precision, where='post', label=f'AP = {m["average_precision"]:.3f}')
        axes[1].axhline(m['prevalence'], linestyle='--', color='gray', label='Prévalence')
        for ax in axes:
            ax.legend(loc='lower left', fontsize=9)
    else:
        for ax in axes:
            ax.text(.5, .5, 'Non définie : une seule classe', ha='center')
    axes[0].set(xlabel='Taux de faux positifs', ylabel='Sensibilité', title='Courbe ROC')
    axes[1].set(xlabel='Rappel', ylabel='Précision', title='Courbe précision-rappel')
    for ax in axes:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.03)
    fig.suptitle(prefix + 'Discrimination au niveau patch')
    fig.tight_layout()
    fig.savefig(out / 'roc_pr.png', dpi=160)
    plt.close(fig)
    pd.DataFrame(report['by_center']).T.to_csv(out / 'metrics_by_center.csv', index_label='center_id')
    pd.DataFrame(report['by_slide']).T.to_csv(out / 'metrics_by_slide.csv', index_label='slide_id')
    select_examples(frame).to_csv(out / 'examples_to_review.csv', index=False)
    def fmt(value):
        return 'Non définie' if value is None else f'{value:.3f}'
    lines = ['# Évaluation descriptive', '',
             '**DONNÉES SYNTHÉTIQUES : aucun résultat CAMELYON17.**' if synthetic else
             '**Résultats à interpréter avec la provenance et les annotations de référence.**', '',
             f'Ensemble : {provenance["split"]}. {m["n"]} patchs, '
             f'{frame.patient_id.nunique()} groupes patient et {frame.slide_id.nunique()} lames.', '',
             '| Mesure | Valeur |', '| --- | --- |']
    for key in ['accuracy', 'sensitivity', 'specificity', 'precision', 'f1', 'roc_auc', 'average_precision']:
        lines.append(f'| {key} | {fmt(m[key])} |')
    lines += ['', f'Au seuil {m["threshold"]}, {m["fn"]} patchs positifs sur {m["tp"] + m["fn"]} '
              f'ont été classés négatifs ; {m["fp"]} patchs négatifs sur {m["tn"] + m["fp"]} '
              'ont été classés positifs.', '',
              '![Matrice de confusion](confusion_matrix.png)', '', '![ROC et PR](roc_pr.png)', '',
              '## Interprétation à compléter par le groupe', '',
              '- Relier les erreurs aux images et aux annotations ; ne pas inventer une cause histologique.',
              '- Comparer les centres avec leurs effectifs ; un seul centre de test ne permet pas une comparaison entre centres de test.',
              '- Une différence validation/test combine un changement de centre et d’échantillon ; elle ne prouve pas à elle seule un effet causal du centre.',
              '- Les patchs sont corrélés au sein des lames. Aucun intervalle de confiance naïf par patch n’est fourni.',
              '- AP résume le classement des scores ; ce n’est pas une sensibilité au seuil choisi.',
              '- L’accuracy par lame décrit des patchs regroupés, pas un diagnostic de lame ni un stade pN.',
              '- Les exemples sont sélectionnés par type TP/TN/FP/FN puis chemin trié ; une catégorie absente reste absente.', '',
              '## Traçabilité', '', f'Manifeste SHA-256 : `{provenance["manifest_sha256"]}`.',
              f'Checkpoint SHA-256 : `{provenance["checkpoint_sha256"]}`.',
              f'Prédictions SHA-256 : `{provenance["predictions_sha256"]}`.', '']
    (out / 'rapport_evaluation.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Figures et commentaire descriptif : {out}')


if __name__ == '__main__':
    main()
