"""Échouer avant entraînement si les labels ou les séparations sont incohérents."""
import argparse
from pathlib import Path
import pandas as pd

REQUIRED = {'path', 'patient_id', 'slide_id', 'center_id', 'label', 'split'}
SPLITS = {'train', 'val', 'id_val', 'test', 'id_test'}


def read_manifest(path):
    """Conserver les zéros initiaux des identifiants patients."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def audit(df, check_files=False):
    """Valider un manifeste complet ; les chemins sont relatifs à la racine du dépôt."""
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f'Colonnes absentes : {sorted(missing)}')
    if df.empty:
        raise ValueError('Manifeste vide : aucun entraînement possible.')
    if df[list(REQUIRED)].isna().any().any() or (df[list(REQUIRED)].astype(str).apply(lambda c: c.str.strip()) == '').any().any():
        raise ValueError('Métadonnées obligatoires vides.')
    if not set(df.label.astype(str)) <= {'0', '1'}:
        raise ValueError('Labels attendus : 0 ou 1, pas de label inconnu.')
    if not set(df.split) <= SPLITS:
        raise ValueError('Split inconnu.')
    if df.path.map(lambda p: str(Path(p).resolve())).duplicated().any():
        raise ValueError('Chemin de patch dupliqué.')
    # Interdire aussi la fuite patient, même si les lames sont distinctes.
    for key in ('patient_id', 'slide_id'):
        if (df.groupby(key).split.nunique() > 1).any():
            raise ValueError(f'Fuite de données : {key} présent dans plusieurs splits.')
    if (df.groupby('slide_id').patient_id.nunique() > 1).any():
        raise ValueError('Une lame est associée à plusieurs patients.')
    if (df.groupby('slide_id').center_id.nunique() > 1).any():
        raise ValueError('Une lame est associée à plusieurs centres.')
    if (df.groupby('patient_id').center_id.nunique() > 1).any():
        raise ValueError('Un groupe patient est associé à plusieurs centres : contrôler les identifiants.')
    if 'train' in set(df.split):
        train_centers = set(df.loc[df.split == 'train', 'center_id'])
        for split in ('val', 'test'):
            if train_centers & set(df.loc[df.split == split, 'center_id']):
                raise ValueError(f'{split} doit être hors centres train dans ce protocole OOD.')
    if set(df.loc[df.split == 'val', 'center_id']) & set(df.loc[df.split == 'test', 'center_id']):
        raise ValueError('Le centre de validation OOD ne doit pas être le centre de test OOD.')
    if check_files:
        missing_files = [p for p in df.path if not Path(p).is_file()]
        if missing_files:
            raise ValueError(f'{len(missing_files)} image(s) introuvable(s), exemple : {missing_files[0]}')
    return df.groupby(['split', 'center_id', 'label']).size().to_string()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('--check-files', action='store_true')
    args = parser.parse_args()
    print(audit(read_manifest(args.manifest), args.check_files))
    print('Contrôles structurels réussis. Les copies renommées nécessitent un contrôle de contenu supplémentaire.')


if __name__ == '__main__':
    main()
