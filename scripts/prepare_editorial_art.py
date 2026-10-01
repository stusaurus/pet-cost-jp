"""Offline crop/resize/export only; never part of product or Pages builds.

Run with Pillow installed and the six approved generated PNGs in source_dir.
No painting, background removal, colour changes, or replacement of alpha.
"""
import argparse
import io
import json
from pathlib import Path

from PIL import Image


SCENES = {
    'pet-sheets': 'exec-d333cc31-28f1-407b-a021-15782d25aacc.png',
    'cat-litter': 'exec-6c017d68-8375-4695-a577-a23e5d0242f3.png',
    'system-toilet-sheets': 'exec-4819dd5b-d286-4831-ad0a-99b901b025e2.png',
}
PLATES = {
    'sheet': 'exec-86f05d03-0558-42c2-8459-69779ed0b37d.png',
    'litter': 'exec-4f07dc24-d3b4-4796-a270-82e254ccf3d5.png',
    'system': 'exec-d023268c-eebf-4e49-91b3-217c6d822712.png',
}


def export(source_dir, destination):
    destination.mkdir(parents=True, exist_ok=True)
    records = []

    def save(image, name, size, source, crop, role):
        image = image.resize(size, Image.Resampling.LANCZOS)
        path = destination / (name + '.webp')
        encoded = io.BytesIO()
        image.save(encoded, 'WEBP', quality=88, method=6, exact=True)
        # Atomic export: readers never observe a partially written image.
        temporary = path.with_suffix('.webp.tmp')
        temporary.write_bytes(encoded.getvalue())
        temporary.replace(path)
        with Image.open(path) as check:
            check.load()
            assert check.size == size and check.mode == 'RGBA', path
        assert path.stat().st_size > 0, path
        records.append(dict(file=path.name, width=size[0], height=size[1],
                            bytes=path.stat().st_size, source=source, crop=crop, role=role))

    for category, filename in SCENES.items():
        image = Image.open(source_dir / filename).convert('RGBA')
        # Full household scene for entry, closer natural composition for header.
        save(image, 'scene-' + category, (352, 264), filename, None, 'home')
        box = (0, 180, 1448, 1086) if category != 'cat-litter' else (0, 240, 1448, 1086)
        close = image.crop(box)
        # Fit without stretching or cutting off animal/body/pad anatomy.
        canvas = Image.new('RGBA', (1448, 1086))
        canvas.alpha_composite(close, ((1448-close.width)//2, (1086-close.height)//2))
        save(canvas, 'key-' + category, (352, 264), filename, box, 'category')

    image = Image.open(source_dir / PLATES['sheet']).convert('RGBA')
    # Unequal source placements: preserve their COMMON SCALE in identical canvases.
    for group, box in zip(('regular', 'wide', 'super_wide'),
                          ((0, 0, 585, 724), (585, 0, 1300, 724), (1300, 0, 2172, 724))):
        cut = image.crop(box)
        canvas = Image.new('RGBA', (966, 724))
        canvas.alpha_composite(cut, ((966-cut.width)//2, 0))
        save(canvas, 'filter-sheet-' + group, (240, 180), PLATES['sheet'], box, 'filter')

    image = Image.open(source_dir / PLATES['litter']).convert('RGBA')
    for i, group in enumerate(('paper', 'okara', 'wood', 'mineral', 'mixed', 'system')):
        x, y = (i % 3)*512, (i // 3)*512
        box = (x, y, x+512, y+512)
        cut = image.crop(box)
        canvas = Image.new('RGBA', (684, 512))
        canvas.alpha_composite(cut, (86, 0))
        save(canvas, 'filter-litter-' + group, (240, 180), PLATES['litter'], box, 'filter')

    image = Image.open(source_dir / PLATES['system']).convert('RGBA')
    for group, box in zip(('deotoilet', 'nyantomo', 'universal'),
                          ((0, 0, 753, 724), (753, 0, 1440, 724), (1440, 0, 2172, 724))):
        cut = image.crop(box)
        canvas = Image.new('RGBA', (966, 724))
        canvas.alpha_composite(cut, ((966-cut.width)//2, 0))
        save(canvas, 'filter-system-' + group, (240, 180), PLATES['system'], box, 'filter')

    (destination / 'manifest.json').write_text(json.dumps({
        'version': 'editorial-art-1', 'medium': 'digital gouache / colored pencil',
        'illustrative_only': True, 'assets': records,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'assets': len(records), 'total_bytes': sum(r['bytes'] for r in records)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_dir', type=Path)
    parser.add_argument('--destination', type=Path, default=Path(__file__).resolve().parents[1] / 'assets' / 'illustrations')
    args = parser.parse_args()
    export(args.source_dir, args.destination)
