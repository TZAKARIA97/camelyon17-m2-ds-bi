"""Convertir les métadonnées CAMELYON17-WILDS locales sans télécharger d'images."""
import argparse
from pathlib import Path
import pandas as pd
from .audit import audit


def convert(root):
    """Reproduire le split officiel : centre 1 validation OOD, centre 2 test OOD.

    La numérotation est celle du paquet WILDS, pas celle d'un autre export.
    Référence : p-lambda/wilds, camelyon17_dataset.py, schéma official.
    """
    root = Path(root)
    df = pd.read_csv(root / 'metadata.csv', dtype={'patient': str})
    required = {'patient', 'node', 'x_coord', 'y_coord', 'center', 'tumor', 'split'}
    if not required <= set(df):
        raise ValueError(f'Métadonnées WILDS incomplètes : {sorted(required-set(df))}')
    split = df['split'].copy()
    split.loc[df.center == 1] = 3
    split.loc[df.center == 2] = 2
    result = pd.DataFrame({
        'patient_id': df.patient,
        'slide_id': ['patient_' + p + '_node_' + str(n) for p, n in zip(df.patient, df.node)],
        'center_id': df.center.astype(str), 'label': df.tumor.astype(str),
        'split': split.map({0: 'train', 1: 'id_val', 2: 'test', 3: 'val'}),
        'x': df.x_coord, 'y': df.y_coord,
        'label_rule': 'tumor_any_in_central_32_of_96', 'source': 'camelyon17-wilds-v1.0'
    })
    result['path'] = [str(root / 'patches' / s / f'patch_{s}_x_{x}_y_{y}.png')
                      for s, x, y in zip(result.slide_id, df.x_coord, df.y_coord)]
    audit(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, help='Dossier contenant metadata.csv et patches/')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    result = convert(args.root)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.out, index=False)
    print(audit(result))
    print('Manifeste créé ; vérifier ensuite les chemins avec audit --check-files.')


if __name__ == '__main__':
    main()
