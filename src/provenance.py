"""Conserver des empreintes de fichiers sans charger les images en mémoire."""
import hashlib
import subprocess


def sha256_file(path):
    """Identifier exactement un fichier ; une empreinte n'en valide pas le contenu."""
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def code_version():
    """Signaler aussi les modifications non commitées, au lieu de les masquer."""
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True,
                                         stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True))
        return {'commit': commit, 'working_tree_dirty': dirty}
    except (OSError, subprocess.CalledProcessError):
        return {'commit': None, 'working_tree_dirty': None}
