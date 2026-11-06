"""Recenser les TIFF locaux sans les ouvrir ni inventer des labels."""
import argparse
import csv
import re
from pathlib import Path

FIELDS = ['slide_id', 'patient_id', 'node_id', 'center_id', 'wsi_path',
          'xml_path', 'size_bytes', 'slide_label', 'pn_label', 'annotation_status']
NAME = re.compile(r'patient_(\d+)_node_(\d+)$')
CENTER = re.compile(r'cent(?:re|er)_(\d+)$', re.I)


def inventory(root):
    """Retrouver patient/nœud depuis le nom ; centre depuis le dossier seulement."""
    root = Path(root)
    if not root.is_dir():
        return []
    xmls = {}
    for path in root.rglob('*.xml'):
        xmls.setdefault(path.stem, []).append(path)
    rows = []
    for path in sorted(root.rglob('*')):
        if path.suffix.lower() not in {'.tif', '.tiff'}:
            continue
        match = NAME.fullmatch(path.stem)
        centers = [m.group(1) for p in path.relative_to(root).parts[:-1]
                   if (m := CENTER.fullmatch(p))]
        annotations = xmls.get(path.stem, [])
        rows.append(dict(zip(FIELDS, [
            path.stem, match.group(1) if match else '', match.group(2) if match else '',
            centers[-1] if centers else '', str(path),
            str(annotations[0]) if len(annotations) == 1 else '', path.stat().st_size,
            '', '', 'present_unverified' if len(annotations) == 1 else
            ('ambiguous' if annotations else 'missing')
        ])))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    rows = inventory(args.root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f'{len(rows)} lame(s) recensée(s). Les labels absents restent inconnus.')
    if not rows:
        print('Aucune WSI disponible : ajouter une paire TIFF/XML avant le test image.')


if __name__ == '__main__':
    main()
