"""Actual pre-fix PNGs versus corrected contour, both directions/backgrounds."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).parent
sheet = Image.new('RGB', (6 * 276, 4 * 250), '#999999')
draw = ImageDraw.Draw(sheet)
for row, (index, before) in enumerate(((2, True), (2, False), (3, True), (3, False))):
    source = Image.open(HERE / (f'spike-before-frame-{index}.png' if before else f'frames/frame_{index}.png')).convert('RGBA')
    for side in range(2):
        enlarged = (ImageOps.mirror(source) if side else source).resize((276, 222), Image.Resampling.NEAREST)
        for style, background in enumerate(('#f0f0f0', '#20252c', 'checker')):
            x, y = (side * 3 + style) * 276, row * 250
            tile = Image.new('RGBA', enlarged.size, background if style < 2 else '#cccccc')
            if style == 2:
                cells = ImageDraw.Draw(tile)
                for cy in range(0, 222, 12):
                    for cx in range(0, 276, 12):
                        if (cx // 12 + cy // 12) % 2:
                            cells.rectangle((cx, cy, cx + 11, cy + 11), fill='#eeeeee')
            tile.alpha_composite(enlarged)
            sheet.paste(tile.convert('RGB'), (x, y + 28))
            draw.text((x + 8, y + 8), f'{"BEFORE" if before else "AFTER"} {index} / {"left" if side else "right"} / {background}', fill='black')
sheet.save(HERE / 'spike-before-after-backgrounds.png')
