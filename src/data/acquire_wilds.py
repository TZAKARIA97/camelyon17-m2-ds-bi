"""Récupérer un pilote WILDS par lectures partielles de ZIP, sans télécharger les archives complètes.

Source : miroir communautaire fumiyau/wilds-archive, révision explicitement figée.
L'identité binaire avec l'archive CodaLab indisponible n'est pas établie.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path, PurePosixPath
import re
from urllib.request import Request, urlopen
import zipfile
from .wilds_manifest import convert
from .subset import subset
from .audit import audit
from ..provenance import sha256_file

REPOSITORY = 'fumiyau/wilds-archive'
REVISION = 'f7b0ea1de482b7dcccfd9a15af2825a4e70b335d'


class RangeReader(io.RawIOBase):
    """Un fichier distant seekable ; refus explicite d'une réponse HTTP complète."""
    def __init__(self, url, size, budget=128 * 1024**2):
        self.url, self.size, self.budget = url, size, budget
        self.resolved_url = url
        self.position = self.transferred = 0
        self.cache_start, self.cache = 0, b''

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        position = offset + (self.position if whence == 1 else self.size if whence == 2 else 0)
        if whence not in (0, 1, 2) or position < 0:
            raise ValueError('Position de lecture invalide.')
        self.position = position
        return position

    def read(self, n=-1):
        n = max(0, min(self.size-self.position, self.size if n < 0 else n))
        if not n:
            return b''
        offset = self.position-self.cache_start
        if offset < 0 or offset+n > len(self.cache):
            length = min(self.size-self.position, max(n, 65536))
            if length > 64*1024**2 or self.transferred+length > self.budget:
                raise ValueError('Budget de transfert partiel dépassé ; aucun téléchargement complet engagé.')
            end = self.position+length-1
            request = Request(self.resolved_url, headers={'Range': f'bytes={self.position}-{end}',
                                                'User-Agent': 'camelyon17-m2-pilot/1.0'})
            with urlopen(request, timeout=45) as response:
                expected = f'bytes {self.position}-{end}/{self.size}'
                if response.status != 206 or response.headers.get('Content-Range') != expected:
                    raise ValueError('Le serveur ne respecte pas la plage demandée ; transfert arrêté.')
                payload = response.read(length+1)
                # Réutiliser la destination HTTP évite une redirection par patch.
                # Cette URL temporaire reste uniquement en mémoire, hors provenance.
                self.resolved_url = response.geturl()
            if len(payload) != length:
                raise ValueError('Réponse partielle tronquée ou trop longue.')
            self.transferred += length
            self.cache_start, self.cache = self.position, payload
            offset = 0
        result = self.cache[offset:offset+n]
        self.position += n
        return result


def safe_target(root, name):
    """Exiger le dossier attendu et interdire toute sortie du dossier de données."""
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != 'camelyon17_v1.0':
        raise ValueError(f'Chemin ZIP refusé : {name!r}')
    target = (root / Path(*path.parts)).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Chemin en dehors du dossier de données.')
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='data/wilds/pilot_download', help='Nouveau dossier uniquement')
    parser.add_argument('--patients-per-group', type=int, default=10)
    parser.add_argument('--patches-per-patient', type=int, default=16)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--metadata-only', action='store_true')
    parser.add_argument('--split-policy', choices=['strict', 'exclude-id-val'], default='exclude-id-val')
    args = parser.parse_args(argv)
    if args.patients_per_group < 1 or args.patches_per_patient < 1:
        parser.error('Les plafonds doivent être strictement positifs.')
    root = Path(args.out).resolve()
    if root.exists():
        raise FileExistsError('Choisir un dossier nouveau ; les données existantes sont conservées.')
    root.mkdir(parents=True)
    with urlopen(f'https://huggingface.co/api/datasets/{REPOSITORY}/tree/{REVISION}?recursive=true', timeout=30) as response:
        listing = json.load(response)
    files = [entry for entry in listing if re.fullmatch(
        r'camelyon17_v1\.0_zip/camelyon17_v1\.0-\d{3}\.zip', entry.get('path', ''))]
    if len(files) != 6:
        raise ValueError('La révision attendue doit contenir exactement six archives CAMELYON17.')

    def open_archive(entry):
        url = f'https://huggingface.co/datasets/{REPOSITORY}/resolve/{REVISION}/{entry["path"]}'
        reader = RangeReader(url, entry['size'])
        archive = zipfile.ZipFile(reader)
        print(f'Index lu : {entry["path"]}, {len(archive.infolist())} entrées', flush=True)
        return entry, reader, archive

    with ThreadPoolExecutor(max_workers=6) as pool:
        archives = list(pool.map(open_archive, files))
    locations = {}
    for index, (_, _, archive) in enumerate(archives):
        for info in archive.infolist():
            if info.is_dir():
                continue
            if info.filename in locations:
                raise ValueError('Entrée dupliquée entre archives.')
            locations[info.filename] = index
    metadata_name = 'camelyon17_v1.0/metadata.csv'
    if metadata_name not in locations:
        raise ValueError('metadata.csv absent : impossible de justifier une sélection.')
    metadata_path = safe_target(root, metadata_name)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    archive = archives[locations[metadata_name]][2]
    if archive.getinfo(metadata_name).file_size > 100*1024**2:
        raise ValueError('Métadonnées trop volumineuses.')
    metadata_path.write_bytes(archive.read(metadata_name))  # zipfile vérifie le CRC.
    frame = convert(metadata_path.parent, args.split_policy)
    frame.to_csv(root / 'all_patches.csv', index=False)
    selected = subset(frame, args.patients_per_group, args.patches_per_patient, args.seed)
    selected['source'] = f'camelyon17-wilds-v1.0-community-mirror@{REVISION}'
    selected.to_csv(root / 'pilot.csv', index=False)
    print(audit(selected), flush=True)
    groups = [[] for _ in archives]
    for path in selected.path:
        name = Path(path).relative_to(root).as_posix()
        if name not in locations:
            raise ValueError(f'Image du manifeste absente des ZIP : {name}')
        groups[locations[name]].append(name)

    def extract_group(index):
        archive = archives[index][2]
        # Lire dans l'ordre physique pour profiter du petit cache HTTP.
        ordered = sorted(groups[index], key=lambda item: archive.getinfo(item).header_offset)
        for position, name in enumerate(ordered, start=1):
            info = archive.getinfo(name)
            if info.file_size > 1024**2:
                raise ValueError('Patch plus grand que prévu.')
            target = safe_target(root, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
            if position % 32 == 0:
                print(f'Archive {index+1} : {position}/{len(ordered)} patchs', flush=True)
        print(f'Archive {index+1} : {len(groups[index])} patchs récupérés', flush=True)

    if not args.metadata_only:
        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(extract_group, range(len(archives))))
        audit(selected, check_files=True)
        from PIL import Image
        for path in selected.path:
            with Image.open(path) as image:
                if image.size != (96, 96) or image.mode != 'RGB':
                    raise ValueError('Image incompatible avec le format WILDS attendu.')
                image.load()
    provenance = {'repository': REPOSITORY, 'revision': REVISION, 'official_mirror': False,
                  'equivalence_to_official_archive': 'not_verified_original_endpoint_404',
                  'metadata_sha256': sha256_file(metadata_path), 'manifest_sha256': sha256_file(root/'pilot.csv'),
                  'seed': args.seed, 'patients_per_group': args.patients_per_group,
                  'patches_per_patient': args.patches_per_patient, 'selected_patches': len(selected),
                  'retained_metadata_rows': len(frame), 'split_policy': args.split_policy,
                  'images_downloaded': not args.metadata_only,
                  'bytes_transferred_archives': sum(r.transferred for _, r, _ in archives),
                  'archive_total_bytes': sum(f['size'] for f in files),
                  'patch_sha256': {Path(p).relative_to(root).as_posix(): sha256_file(p)
                                   for p in selected.path} if not args.metadata_only else {},
                  'archives': files}
    for _, _, archive in archives:
        archive.close()
    (root/'acquisition.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print(f'Acquisition terminée : {root}. Miroir communautaire ; pilote non représentatif du benchmark complet.', flush=True)


if __name__ == '__main__':
    main()
