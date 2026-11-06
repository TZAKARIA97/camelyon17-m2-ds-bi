"""Exporter des Grad-CAM pour une sélection traçable de succès et d'erreurs."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
from .gradcam import gradcam
from .report import load_evaluation, select_examples
from ..models.inference import load_run
from ..provenance import sha256_file


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--evaluation', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--per-category', type=int, default=2)
    args = parser.parse_args(argv)
    if not 1 <= args.per_category <= 4:
        parser.error('Choisir entre 1 et 4 exemples par catégorie TP/TN/FP/FN.')
    frame, _, provenance = load_evaluation(args.evaluation)
    if sha256_file(args.checkpoint) != provenance['checkpoint_sha256']:
        raise ValueError('Le checkpoint ne correspond pas à cette évaluation.')
    if sha256_file(args.manifest) != provenance['manifest_sha256']:
        raise ValueError('Le manifeste ne correspond pas à cette évaluation.')
    model, transform, config = load_run(args.checkpoint, args.manifest)
    chosen = select_examples(frame, args.per_category)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    import torch
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    synthetic = config['dataset_kind'] == 'synthetic'
    introduction = '**DÉMONSTRATION SYNTHÉTIQUE — aucune interprétation médicale.**' if synthetic else \
        '**Analyse qualitative à confronter aux annotations et à une expertise histologique.**'
    lines = ['# Cartes Grad-CAM', '', introduction, '',
             'Classe expliquée : tumoral (classe 1), même pour une prédiction négative. '
             'Couche : layer4 de ResNet18. La couleur indique une contribution relative normalisée ; '
             'elle ne représente ni une probabilité pixel par pixel ni la taille d’une lésion.', '',
             'Sélection : premiers chemins triés dans chaque catégorie TP/TN/FP/FN, '
             'sans recherche des cartes les plus convaincantes. Les catégories absentes ne sont pas fabriquées.', '']
    files, flat_maps = [], []
    for index, row in chosen.iterrows():
        with Image.open(row.path) as source:
            image = source.convert('RGB')
            display_image = image.resize((config['image_size'], config['image_size']), Image.Resampling.BILINEAR)
            batch = transform(image).unsqueeze(0)
        # Recalculer le score détecte une image remplacée depuis l'évaluation.
        with torch.no_grad():
            score = float(model(batch).softmax(1)[0, 1])
        if not np.isclose(score, row.score, atol=1e-4, rtol=1e-4):
            raise ValueError('Score recalculé différent : contrôler image, prétraitement et checkpoint.')
        heatmap = gradcam(model, batch, target_class=1)
        flat = bool(np.max(heatmap) <= 1e-12)
        name = f'{row.case}_{index:02d}.png'
        fig, axes = plt.subplots(1, 3, figsize=(9, 3.6))
        axes[0].imshow(display_image)
        axes[0].set_title('Image présentée au modèle')
        axes[1].imshow(heatmap, cmap='inferno', vmin=0, vmax=1)
        axes[1].set_title('Grad-CAM classe 1' + (' — carte nulle' if flat else ''))
        axes[2].imshow(display_image)
        axes[2].imshow(heatmap, cmap='inferno', vmin=0, vmax=1, alpha=.45)
        axes[2].set_title('Superposition')
        for ax in axes:
            ax.axis('off')
        prefix = 'SYNTHÉTIQUE — ' if synthetic else ''
        fig.suptitle(f'{prefix}{row.case} · label={row.label} · score={score:.3f} · seuil={config["threshold"]:.3f}')
        fig.tight_layout()
        fig.savefig(out / name, dpi=160)
        plt.close(fig)
        files.append(name)
        flat_maps.append(flat)
        lines += [f'## Exemple {index+1} — {row.case}', '', f'![{row.case}]({name})', '',
                  f'Centre {row.center_id} ; lame `{row.slide_id}`. Carte nulle : {flat}.', '',
                  'Observation à compléter : zone activée, correspondance aux annotations, '
                  'artefact éventuel, incertitude. Une carte nulle n’est pas une preuve d’absence de tumeur.', '']
    chosen['figure'] = files
    chosen['flat_heatmap'] = flat_maps
    chosen.to_csv(out / 'selection.csv', index=False)
    (out / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    (out / 'index.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'{len(chosen)} cartes exportées dans {out}. Interprétation humaine requise.')


if __name__ == '__main__':
    main()
