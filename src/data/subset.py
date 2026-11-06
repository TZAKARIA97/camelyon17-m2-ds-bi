"""Réduire un manifeste par groupes sans modifier ses ensembles officiels."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .audit import read_manifest, audit
from ..provenance import sha256_file


def subset(frame, patients_per_group=2, patches_per_patient=128, seed=42):
    """Tirer des patientes par (split, centre), puis des patchs sans regarder les labels.

    Les plafonds réduisent le coût d'un pilote. Ce résultat n'est pas le benchmark
    complet et ne garantit pas la présence des deux classes dans un très petit lot.
    """
    audit(frame)
    if patients_per_group < 1 or patches_per_patient < 1:
        raise ValueError('Les plafonds doivent être strictement positifs.')
    rng = np.random.default_rng(seed)
    parts = []
    for _, group in frame.groupby(['split', 'center_id'], sort=True):
        patients = sorted(group.patient_id.unique())
        selected = rng.choice(patients, min(len(patients), patients_per_group), replace=False)
        for patient in sorted(selected):
            rows = group[group.patient_id == patient].sort_values('path')
            positions = rng.choice(len(rows), min(len(rows), patches_per_patient), replace=False)
            parts.append(rows.iloc[sorted(positions)])
    result = pd.concat(parts).sort_values(['split', 'patient_id', 'path']).reset_index(drop=True)
    audit(result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--patients-per-group', type=int, default=2)
    parser.add_argument('--patches-per-patient', type=int, default=128)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args(argv)
    out = Path(args.out)
    sidecar = out.with_suffix('.selection.json')
    if out.exists() or sidecar.exists():
        raise FileExistsError('Choisir de nouveaux noms de fichiers de sortie.')
    frame = read_manifest(args.manifest)
    selected = subset(frame, args.patients_per_group, args.patches_per_patient, args.seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(out, index=False)
    metadata = {'input_sha256': sha256_file(args.manifest), 'output_sha256': sha256_file(out),
                'seed': args.seed, 'patients_per_split_center': args.patients_per_group,
                'patches_per_patient': args.patches_per_patient, 'input_patches': len(frame),
                'selected_patches': len(selected), 'uses_labels_for_selection': False,
                'patients': sorted(selected.patient_id.unique().tolist()),
                'purpose': 'pilot_not_full_benchmark'}
    sidecar.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(audit(selected))
    print('Pilote créé sans ouvrir ni télécharger les images. Vérifier les deux classes avant apprentissage.')


if __name__ == '__main__':
    main()
