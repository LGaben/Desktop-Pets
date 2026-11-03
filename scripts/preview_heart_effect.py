"""Render actual code-native heart keyframes for review; not a GUI test."""
from pathlib import Path
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ui.heart_effect import HEART_MASK, HEIGHT, WIDTH, hearts_at  # noqa: E402
from pet.fox_reaction import FoxReaction  # noqa: E402

times = (0, .12, .3, .55, .8, .95)
sheet = Image.new('RGB', (6 * WIDTH * 4, 3 * (HEIGHT * 4 + 24)), '#999999')
labels = ImageDraw.Draw(sheet)
for row, background in enumerate(('#f0f0f0', '#20252c', 'checker')):
    for column, elapsed in enumerate(times):
        tile = Image.new('RGBA', (WIDTH, HEIGHT), background if row < 2 else '#cccccc')
        if row == 2:
            cells = ImageDraw.Draw(tile)
            for cy in range(0, HEIGHT, 4):
                for cx in range(0, WIDTH, 4):
                    if (cx // 4 + cy // 4) % 2:
                        cells.rectangle((cx, cy, cx + 3, cy + 3), fill='#eeeeee')
        effect = Image.new('RGBA', tile.size)
        draw = ImageDraw.Draw(effect)
        for x, y, scale, alpha in hearts_at(elapsed):
            color = (255, 100 if scale == 2 else 145, 160 if scale == 2 else 185, alpha)
            for py, pixels in enumerate(HEART_MASK):
                for px, filled in enumerate(pixels):
                    if filled == '1':
                        left, top = x + px * scale, y + py * scale
                        draw.rectangle((left, top, left + scale - 1, top + scale - 1), fill=color)
        tile.alpha_composite(effect)
        x, y = column * WIDTH * 4, row * (HEIGHT * 4 + 24)
        labels.text((x + 8, y + 6), f'{elapsed:.2f}s / {background}', fill='black')
        sheet.paste(tile.convert('RGB').resize((WIDTH * 4, HEIGHT * 4), Image.Resampling.NEAREST), (x, y + 24))
output = ROOT / 'output/fox-pet-react/heart-effect/keyframes.png'
output.parent.mkdir(parents=True, exist_ok=True)
sheet.save(output)
print(output)

# Code-rendered demonstration, not a screenshot or a claim of GUI verification.
poses = {(head, phase): Image.open(ROOT / f'assets/sprites/fox/pet_react/head_{head}/frame_{phase + 1}.png').convert('RGBA')
         for head in range(3) for phase in range(5)}
frames = []
for ms in range(0, 1584, 33):
    reaction = FoxReaction()
    reaction.start()
    reaction.advance(ms / 1000)
    frame = Image.new('RGBA', (112, 96), '#e9edf1')
    frame.alpha_composite(poses[reaction.head, (ms // 264) % 5], (33, 55))
    effect = Image.new('RGBA', frame.size)
    draw = ImageDraw.Draw(effect)
    # Same desktop anchor as HeartOverlay: fox.x + head_x - WIDTH/2, fox.y -48.
    for x, y, scale, alpha in hearts_at(ms / 1000):
        color = (255, 100 if scale == 2 else 145, 160 if scale == 2 else 185, alpha)
        for py, pixels in enumerate(HEART_MASK):
            for px, filled in enumerate(pixels):
                if filled == '1':
                    left, top = 27 + x + px * scale, 7 + y + py * scale
                    draw.rectangle((left, top, left + scale - 1, top + scale - 1), fill=color)
    frame.alpha_composite(effect)
    frames.append(frame)
for zoom in (1, 4):
    images = [frame.resize((112 * zoom, 96 * zoom), Image.Resampling.NEAREST) for frame in frames]
    path = output.parent / f'petting-hearts-{zoom}x.apng'
    images[0].save(path, save_all=True, append_images=images[1:], duration=33, loop=1, disposal=0, blend=0)
    decoded = Image.open(path)
    assert decoded.info['loop'] == 1
    elapsed = 0
    for i in range(decoded.n_frames):
        decoded.seek(i)
        expected = frames[round(elapsed / 33)].resize((112 * zoom, 96 * zoom), Image.Resampling.NEAREST)
        assert decoded.convert('RGBA').tobytes() == expected.tobytes()
        elapsed += decoded.info['duration']
    assert elapsed == 1584
    print(f'{path}: {decoded.n_frames} decoded-exact frames, {elapsed}ms, plays=1')
