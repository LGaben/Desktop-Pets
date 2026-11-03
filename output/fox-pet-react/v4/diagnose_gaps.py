"""Read actual old frames and record lost dense neck pixels before repair."""
from PIL import Image, ImageDraw
from pathlib import Path
import json

HERE = Path(__file__).parent
assert not (HERE / 'gap-diagnosis-before.json').exists(), 'Preserve original before-fix evidence; do not overwrite.'
ROOT = HERE.parents[2]
original = Image.open(ROOT / 'assets/sprites/fox/idle/frame_1.png').convert('RGBA')
report = []
for i in range(1, 10):
    im = Image.open(HERE / 'frames' / f'frame_{i}.png').convert('RGBA')
    lost = [(x, y, im.getpixel((x, y))[3]) for y in range(24, 29) for x in range(24, 39)
            if original.getpixel((x, y))[3] >= 250 and im.getpixel((x, y))[3] < 250]
    report.append({'frame': i, 'lost_dense_neck_pixels': lost})
(HERE / 'gap-diagnosis-before.json').write_text(json.dumps(report, indent=2), encoding='utf8')
sheet = Image.new('RGB', (3*368, 336), '#20252c')
draw = ImageDraw.Draw(sheet)
for j, index in enumerate((1, 2, 3)):
    im = Image.open(HERE / 'frames' / f'frame_{index}.png').convert('RGBA')
    im.save(HERE / f'diagnostic-before-frame-{index}.png')
    draw.text((j*368+8, 8), f'BEFORE frame {index}', fill='white')
    im = im.resize((368,296), Image.Resampling.NEAREST)
    sheet.paste(im, (j*368,32), im)
sheet.save(HERE / 'gaps-before-dark.png')
print(json.dumps(report))
