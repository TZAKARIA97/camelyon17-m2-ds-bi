"""Règles CAMELYON17 à partir de catégories par ganglion, PAS de patches isolés."""


def stage_patient(nodes):
    """Classer les cinq ganglions connus. Toute donnée manquante bloque le calcul.

    Entrée : cinq valeurs negative/itc/micro/macro.
    Ce module ne détermine pas la taille des lésions ni leurs catégories.
    """
    nodes = list(nodes)
    if len(nodes) != 5 or any(n not in {'negative', 'itc', 'micro', 'macro'} for n in nodes):
        raise ValueError('Cinq catégories valides de ganglions sont requises.')
    positives = sum(n in {'micro', 'macro'} for n in nodes)
    if 'macro' in nodes:
        return 'pN1' if positives <= 3 else 'pN2'
    if 'micro' in nodes:
        return 'pN1mi'
    if 'itc' in nodes:
        return 'pN0(i+)'
    return 'pN0'
