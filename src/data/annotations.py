"""Lire les polygones ASAP CAMELYON17 et calculer un masque local uniquement."""
from dataclasses import dataclass
from math import isfinite
from xml.etree import ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw


@dataclass
class Polygon:
    group: str
    points: list


def read_xml(path):
    """Accepter les groupes CAMELYON17 connus ; échouer plutôt que deviner."""
    root = ET.parse(path).getroot()
    polygons = []
    for annotation in root.findall('.//Annotation'):
        group = annotation.get('PartOfGroup', '').lower()
        # La paire officielle patient_089_node_3 utilise « Tumor ».
        # Normaliser cet alias documenté, sans accepter un groupe inconnu.
        if group == 'tumor':
            group = 'metastases'
        if group not in {'metastases', 'normal'}:
            raise ValueError(f'Groupe XML non pris en charge : {group!r}')
        coordinates = sorted(annotation.findall('./Coordinates/Coordinate'),
                             key=lambda c: int(c.get('Order', '0')))
        points = [(float(c.attrib['X']), float(c.attrib['Y'])) for c in coordinates]
        if len(points) < 3 or not all(isfinite(v) for xy in points for v in xy):
            raise ValueError('Polygone invalide.')
        polygons.append(Polygon(group, points))
    if not polygons:
        raise ValueError('Aucun polygone dans ce XML ; ne pas conclure que la lame est saine.')
    return polygons


def local_mask(polygons, x, y, size, downsample=1.0):
    """Rasteriser le patch ; x/y sont toujours dans le repère du niveau 0.

    Les régions normal soustraient des trous dans les régions metastases.
    Les ITC ne sont pas toutes annotées : ce masque n'est pas une vérité clinique exhaustive.
    """
    if size <= 0 or downsample <= 0:
        raise ValueError('Taille et facteur de réduction strictement positifs requis.')
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    for group, value in [('metastases', 1), ('normal', 0)]:
        for polygon in polygons:
            if polygon.group == group:
                points = [((px-x)/downsample, (py-y)/downsample) for px, py in polygon.points]
                draw.polygon(points, fill=value)
    return np.asarray(mask)
