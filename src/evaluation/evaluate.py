"""Évaluer un checkpoint figé et conserver les scores patch par patch."""
import argparse
import json
from pathlib import Path
from ..data.audit import read_manifest, audit
from .metrics import binary_metrics
from ..models.inference import load_run
from ..provenance import sha256_file


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--split', choices=['val', 'id_val', 'test', 'id_test'], required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        raise FileExistsError(f'Le dossier de sortie existe déjà : {out}')
    frame = read_manifest(args.manifest)
    audit(frame, check_files=True)
    import torch
    from torch.utils.data import DataLoader
    from ..models.train import PatchDataset, predict
    model, transform, config = load_run(args.checkpoint, args.manifest)
    selected = frame[frame.split == args.split].copy()
    if selected.empty:
        raise ValueError('Aucun patch dans ce split.')
    device = 'cpu' if config['dataset_kind'] == 'synthetic' else ('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    loader = DataLoader(PatchDataset(selected, transform),
                        batch_size=config['batch_size'], shuffle=False, num_workers=0)
    labels, scores = predict(model, loader, device)
    selected['score'] = scores
    selected['prediction'] = (selected.score >= config['threshold']).astype(int)
    report = {'split': args.split, 'dataset_kind': config['dataset_kind'],
              'overall': binary_metrics(labels, scores, config['threshold']),
              'by_center': {str(c): binary_metrics(g.label.astype(int), g.score, config['threshold'])
                            for c, g in selected.groupby('center_id')},
              'by_slide': {str(s): binary_metrics(g.label.astype(int), g.score, config['threshold'])
                           for s, g in selected.groupby('slide_id')}}
    out.mkdir(parents=True, exist_ok=False)
    selected.to_csv(out / 'predictions.csv', index=False)
    (out / 'metrics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    provenance = {'manifest_sha256': config['manifest_sha256'],
                  'checkpoint_sha256': sha256_file(args.checkpoint),
                  'predictions_sha256': sha256_file(out / 'predictions.csv'),
                  'dataset_kind': config['dataset_kind'], 'split': args.split,
                  'threshold': config['threshold'], 'code_version': config['code_version']}
    (out / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
