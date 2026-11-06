"""Télécharger une seule paire WSI/XML publique, avec contrôle MD5 de la distribution."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from urllib.request import urlopen

BASE = 'https://camelyon-dataset.s3.us-west-2.amazonaws.com/CAMELYON17'
SLIDE = 'patient_089_node_3'
SLIDE_BYTES = 518910648


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='data/raw/wsi_example', help='Dossier nouveau, environ 520 Mo requis')
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        raise FileExistsError('Choisir un dossier nouveau pour cette paire WSI/XML.')
    out.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(out.parent).free < SLIDE_BYTES * 2:
        raise ValueError('Prévoir au moins deux fois la taille de la lame sur le disque.')
    out.mkdir()
    with urlopen(f'{BASE}/checksums.md5', timeout=30) as response:
        checksums = response.read(200_000).decode('utf-8')
    (out/'source_checksums.md5').write_text(checksums, encoding='utf-8')
    records = []
    for subdir, suffix, limit in [('annotations', '.xml', 1_000_000), ('images', '.tif', SLIDE_BYTES)]:
        name = SLIDE + suffix
        matches = [line.split()[0] for line in checksums.splitlines()
                   if line.split() and line.split()[-1].lstrip('*').split('/')[-1] == name]
        if len(matches) != 1 or len(matches[0]) != 32:
            raise ValueError(f'Somme de contrôle de référence absente ou ambiguë : {name}')
        url = f'{BASE}/{subdir}/{name}'
        target = out/name
        partial = out/(name+'.part')
        md5, sha = hashlib.md5(), hashlib.sha256()
        count, last_print = 0, 0
        with urlopen(url, timeout=60) as response, partial.open('xb') as stream:
            while block := response.read(1024*1024):
                count += len(block)
                if count > limit:
                    raise ValueError('Taille de téléchargement supérieure à celle attendue.')
                stream.write(block)
                md5.update(block)
                sha.update(block)
                if count-last_print >= 64*1024**2:
                    print(f'{name} : {count/1024**2:.0f} Mio reçus', flush=True)
                    last_print = count
        if md5.hexdigest() != matches[0]:
            raise ValueError(f'MD5 différent de la référence ; fichier .part non utilisé : {name}')
        partial.rename(target)
        records.append({'file': name, 'url': url, 'bytes': count, 'md5': md5.hexdigest(),
                        'sha256': sha.hexdigest(), 'source_md5_verified': True})
        print(f'{name} vérifié et disponible.', flush=True)
    (out/'acquisition.json').write_text(json.dumps({'purpose':'one_slide_visual_inspection',
        'files':records}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
