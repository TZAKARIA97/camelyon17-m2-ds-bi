"""Exporter une miniature et des patches bornés, avec labels d'annotation exploratoires."""
import argparse
import csv
import json
from pathlib import Path
from .annotations import read_xml, local_mask


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wsi', required=True)
    parser.add_argument('--xml', required=True)
    parser.add_argument('--coords', required=True, help='CSV x,y en pixels niveau 0')
    parser.add_argument('--out', required=True, help='Nouveau dossier de sortie')
    parser.add_argument('--size', type=int, default=224)
    parser.add_argument('--level', type=int, default=0)
    parser.add_argument('--max-patches', type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.size <= 4096 or not 1 <= args.max_patches <= 100:
        parser.error('Test borné : taille 1..4096 et 1..100 patches.')
    import openslide  # Dépendance optionnelle, aucun besoin pour l'audit CSV.
    from PIL import Image, ImageDraw
    polygons = read_xml(args.xml)
    if Path(args.wsi).stem != Path(args.xml).stem:
        parser.error('La lame et le XML doivent porter le même identifiant.')
    with open(args.coords, newline='', encoding='utf-8') as stream:
        coordinates = list(csv.DictReader(stream))
    if not coordinates:
        parser.error('Fichier de coordonnées vide.')
    out = Path(args.out)
    with openslide.OpenSlide(args.wsi) as slide:
        if not 0 <= args.level < slide.level_count:
            parser.error('Niveau de résolution inexistant.')
        ds = slide.level_downsamples[args.level]
        chosen = [(int(row['x']), int(row['y'])) for row in coordinates[:args.max_patches]]
        for x, y in chosen:
            if x < 0 or y < 0 or x+args.size*ds > slide.dimensions[0] or y+args.size*ds > slide.dimensions[1]:
                parser.error('Patch hors de la lame : corriger les coordonnées.')
        out.mkdir(parents=True, exist_ok=False)
        thumbnail = slide.get_thumbnail((1600, 1600)).convert('RGB')
        thumbnail.save(out / 'thumbnail.png')
        annotated = thumbnail.copy()
        draw = ImageDraw.Draw(annotated)
        for polygon in polygons:
            points = [(px * annotated.width / slide.dimensions[0],
                       py * annotated.height / slide.dimensions[1]) for px, py in polygon.points]
            draw.line(points + [points[0]], fill='red' if polygon.group == 'metastases' else 'blue', width=2)
        annotated.save(out / 'thumbnail_annotations.png')
        metadata = {'wsi': str(Path(args.wsi)), 'dimensions': slide.dimensions,
                    'level_dimensions': slide.level_dimensions,
                    'downsamples': slide.level_downsamples,
                    'mpp_x': slide.properties.get('openslide.mpp-x'),
                    'mpp_y': slide.properties.get('openslide.mpp-y'),
                    'status': 'inspection_only_not_training_dataset'}
        (out / 'slide_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        rows = []
        for x, y in chosen:
            image = slide.read_region((x, y), args.level, (args.size, args.size)).convert('RGB')
            filename = f'x_{x}_y_{y}_level_{args.level}.png'
            image.save(out / filename)
            mask = local_mask(polygons, x, y, args.size, ds)
            mask_image = Image.fromarray((mask * 255).astype('uint8'))
            mask_image.save(out / f'mask_{filename}')
            tinted = Image.blend(image, Image.new('RGB', image.size, 'red'), 0.35)
            Image.composite(tinted, image, mask_image).save(out / f'overlay_{filename}')
            fraction = float(mask.mean())
            rows.append({'path': filename, 'x': x, 'y': y, 'level': args.level,
                         'size': args.size, 'tumor_fraction': fraction,
                         'annotation_label_any': int(fraction > 0)})
        with (out / 'inspection.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    print(f'{len(rows)} patches exportés pour inspection. Label any : règle exploratoire, non validée.')


if __name__ == '__main__':
    main()
