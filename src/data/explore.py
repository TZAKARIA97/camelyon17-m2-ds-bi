"""Produire les effectifs et une planche de patchs d'entraînement uniquement."""
import argparse
import json
from pathlib import Path
import pandas as pd
from PIL import Image
from .audit import read_manifest, audit
from ..provenance import sha256_file


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--examples-per-class', type=int, default=4)
    args = parser.parse_args(argv)
    if not 1 <= args.examples_per_class <= 10:
        parser.error('Entre 1 et 10 exemples par classe.')
    frame = read_manifest(args.manifest)
    audit(frame)  # Les métadonnées peuvent être explorées sans toutes les images.
    train = frame[frame.split == 'train']
    if train.empty:
        raise ValueError('Un ensemble train est nécessaire pour les exemples.')
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    stats = frame.groupby(['split', 'center_id', 'label']).agg(
        patches=('path', 'size'), patients=('patient_id', 'nunique'),
        slides=('slide_id', 'nunique')).reset_index()
    stats.to_csv(out / 'counts.csv', index=False)
    metadata = {'manifest_sha256': sha256_file(args.manifest), 'patches': len(frame),
                'patients': frame.patient_id.nunique(), 'slides': frame.slide_id.nunique(),
                'centers': frame.center_id.nunique(), 'examples_split': 'train',
                'note': 'Une patiente/lame peut contribuer aux deux classes ; ne pas sommer ces sous-effectifs.'}
    (out / 'summary.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    prefix = 'SYNTHÉTIQUE — ' if 'source' in frame and (frame.source == 'synthetic').all() else ''
    counts = stats.pivot_table(index=['split', 'center_id'], columns='label', values='patches',
                              aggfunc='sum', fill_value=0)
    ax = counts.plot.bar(stacked=True, figsize=(9, 4), color=['#536d9b', '#b65365'])
    ax.set(xlabel='Ensemble, centre', ylabel='Nombre de patchs', title=prefix + 'Composition du manifeste')
    ax.figure.tight_layout()
    ax.figure.savefig(out / 'distribution.png', dpi=160)
    plt.close(ax.figure)
    fig, axes = plt.subplots(2, args.examples_per_class,
                             figsize=(2.6 * args.examples_per_class, 5.8), squeeze=False)
    selections = []
    for label in ('0', '1'):
        candidates = train[train.label == label].sort_values('path')
        chosen = candidates.sample(min(len(candidates), args.examples_per_class), random_state=42)
        selections.append(chosen)
        for col, ax in enumerate(axes[int(label)]):
            ax.axis('off')
            if col >= len(chosen):
                ax.set_title(f'Classe {label} : aucun autre exemple')
                continue
            row = chosen.iloc[col]
            with Image.open(row.path) as image:
                width, height = image.size
                ax.imshow(image.convert('RGB'))
            ax.set_title(f'Classe {label} · centre {row.center_id}\n{width} × {height} pixels', fontsize=9)
    fig.suptitle(prefix + 'Échantillon de train — vérifier qualité et label')
    fig.tight_layout()
    fig.savefig(out / 'training_examples.png', dpi=160)
    plt.close(fig)
    pd.concat(selections).to_csv(out / 'example_selection.csv', index=False)
    print(f'Exploration disponible dans {out}. Les exemples proviennent seulement de train.')


if __name__ == '__main__':
    main()
