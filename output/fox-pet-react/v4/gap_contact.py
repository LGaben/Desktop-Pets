"""Compare preserved pre-fix and regenerated PNGs on three backgrounds."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import json

HERE = Path(__file__).parent
sheet = Image.new('RGB', (6*276, 2*250), '#999999')
draw = ImageDraw.Draw(sheet)
for row, filename in enumerate(('diagnostic-before-frame-2.png', 'frames/frame_2.png')):
    source = Image.open(HERE / filename).convert('RGBA')
    for side in range(2):
        image = ImageOps.mirror(source) if side else source
        enlarged = image.resize((276, 222), Image.Resampling.NEAREST)
        for style, background in enumerate(('#f0f0f0', '#20252c', 'checker')):
            x, y = (side*3+style)*276, row*250
            tile = Image.new('RGBA', enlarged.size, background if style < 2 else '#cccccc')
            if style == 2:
                cells = ImageDraw.Draw(tile)
                for cy in range(0, 222, 12):
                    for cx in range(0, 276, 12):
                        if (cx//12+cy//12)%2:
                            cells.rectangle((cx,cy,cx+11,cy+11), fill='#eeeeee')
            tile.alpha_composite(enlarged)
            sheet.paste(tile.convert('RGB'), (x,y+28))
            draw.text((x+8,y+8), f'{"AFTER" if row else "BEFORE"} / {"left" if side else "right"} / {background}', fill='black')
sheet.save(HERE / 'gap-before-after-backgrounds.png')
after = []
for i in range(1,9):
    im = Image.open(HERE / 'frames' / f'frame_{i}.png').convert('RGBA')
    after.append({'frame':i,'neck_row28_alpha_x24_to38':[im.getpixel((x,28))[3] for x in range(24,39)]})
(HERE / 'gap-diagnosis-after.json').write_text(json.dumps(after,indent=2),encoding='utf8')
