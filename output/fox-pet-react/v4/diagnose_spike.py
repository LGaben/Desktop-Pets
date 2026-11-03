"""Freeze the actual residual outline and inspect coordinates before repairing."""
from pathlib import Path
from PIL import Image, ImageDraw
import json

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
paths = [ROOT / 'assets/sprites/fox/idle/frame_1.png', HERE/'frames/frame_2.png', HERE/'frames/frame_3.png']
report = []
sheet = Image.new('RGB', (3*330, 660), '#eeeeee')
draw = ImageDraw.Draw(sheet)
for i, path in enumerate(paths):
    im = Image.open(path).convert('RGBA')
    if i:
        im.save(HERE/f'spike-before-frame-{i+1}.png')
    pixels = [{'x':x,'y':y,'rgba':list(im.getpixel((x,y)))} for y in range(5,27) for x in range(18,29)]
    report.append({'image':str(path),'pixels':pixels})
    draw.text((i*330+8,8), 'original' if not i else f'before frame {i+1}', fill='black')
    crop = im.crop((18,5,29,27)).resize((330,660),Image.Resampling.NEAREST)
    bg = Image.new('RGBA',crop.size,'#303030');bg.alpha_composite(crop)
    sheet.paste(bg.convert('RGB'),(i*330,28))
    for y in range(5,26):
        for x in range(18,29):
            draw.text((i*330+(x-18)*30,(y-5)*30+28),f'{x},{y}',fill='#aaaaaa')
(HERE/'spike-diagnosis-before.json').write_text(json.dumps(report,indent=2),encoding='utf8')
sheet.save(HERE/'spike-coordinate-before.png')
