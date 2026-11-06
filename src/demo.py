"""Exécuter toute la chaîne sur du bruit artificiel, sans téléchargement ni données médicales."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='outputs/demo_synthetic', help='Nouveau dossier uniquement')
    args = parser.parse_args(argv)
    root = Path(args.out).resolve()
    root.mkdir(parents=True, exist_ok=False)
    (root / 'SYNTHETIC_ONLY.txt').write_text(
        'Images de bruit fabriquées : aucun résultat de cette démonstration ne valide CAMELYON17.\n', encoding='utf-8')
    images = root / 'images'
    images.mkdir()
    rng = np.random.default_rng(42)
    rows = []
    # Plusieurs patchs par patiente : les groupes restent entièrement dans un seul ensemble.
    for split, center in [('train', '0'), ('val', '1'), ('test', '2')]:
        for patient in range(4):
            for patch in range(2):
                identifier = f'synthetic_{split}_{patient}'
                image_path = images / f'{identifier}_{patch}.png'
                pixels = rng.integers(0, 256, (96, 96, 3), dtype=np.uint8)
                Image.fromarray(pixels).save(image_path)
                rows.append(dict(path=str(image_path), patient_id=identifier, slide_id=identifier,
                                 center_id=center, label=patch, split=split, source='synthetic'))
    manifest = root / 'manifest.csv'
    pd.DataFrame(rows).to_csv(manifest, index=False)
    project = Path(__file__).resolve().parents[1]
    config = json.loads((project / 'configs/baseline.json').read_text(encoding='utf-8'))
    config.update(epochs=1, batch_size=4, num_workers=0)
    config_path = root / 'demo_config.json'
    config_path.write_text(json.dumps(config, indent=2), encoding='utf-8')
    from .data.explore import main as explore
    from .models.train import main as train
    from .evaluation.evaluate import main as evaluate
    from .visualization.report import main as report
    from .visualization.explain import main as explain
    print('DÉMONSTRATION SYNTHÉTIQUE : 24 images de bruit, poids aléatoires, CPU.')
    explore(['--manifest', str(manifest), '--out', str(root / 'exploration'), '--examples-per-class', '2'])
    train(['--manifest', str(manifest), '--config', str(config_path), '--out', str(root / 'run'), '--demo'])
    checkpoint = root / 'run/best.pt'
    evaluate(['--manifest', str(manifest), '--checkpoint', str(checkpoint),
              '--split', 'test', '--out', str(root / 'evaluation')])
    report(['--evaluation', str(root / 'evaluation'), '--out', str(root / 'report')])
    explain(['--manifest', str(manifest), '--checkpoint', str(checkpoint),
             '--evaluation', str(root / 'evaluation'), '--out', str(root / 'gradcam'), '--per-category', '1'])
    summary = {'status': 'completed', 'dataset_kind': 'synthetic', 'patches': len(rows),
               'medical_results': False, 'stages': ['audit', 'exploration', 'train', 'evaluate', 'report', 'gradcam']}
    (root / 'demo_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(f'Démonstration terminée : {root}. Ne pas utiliser ses scores dans les résultats du projet.')


if __name__ == '__main__':
    main()
