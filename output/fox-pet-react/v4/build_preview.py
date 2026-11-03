"""Original-derived head poses over every untouched idle tail phase."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import hashlib
import json

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
source_paths = [ROOT / f'assets/sprites/fox/idle/frame_{i}.png' for i in range(1, 6)]
sources = [Image.open(p).convert('RGBA') for p in source_paths]
HEAD_SOURCE = (24, 4, 46, 27)
HEAD_EDGE = (22, 4, 24, 23)
TAIL_MS = 264
# Union of head changes and the uninterrupted original tail ticks.
states = [(0, 0), (1, 0), (2, 1), (2, 2), (2, 3), (1, 4), (0, 4), (0, 0)]
durations = [132, 132, 264, 264, 264, 132, 132, 264]

def head_roi(x, y):
    return (24 <= x < 46 and 4 <= y < 29) or (22 <= x < 24 and 4 <= y < 25)

def compose(source, drop):
    frame = source.copy()
    if drop:
        # Move the soft left contour, preserving the back underneath at y>=23.
        frame.paste((0, 0, 0, 0), HEAD_EDGE)
        frame.alpha_composite(source.crop(HEAD_EDGE), (22, 4 + drop))
        # A 1px dip retains neck row28; clear only the actual moved union.
        frame.paste((0, 0, 0, 0), (24, 4, 46, 27 + drop))
        frame.paste(source.crop(HEAD_SOURCE), (24, 4 + drop))
        if drop == 2:
            for x in (33, 34):
                frame.putpixel((x, 19), source.getpixel((32, 17)))
    assert all(frame.getpixel((x, y)) == source.getpixel((x, y))
               for y in range(37) for x in range(46) if not head_roi(x, y))
    return frame

(HERE / 'poses').mkdir(exist_ok=True)
poses = {}
for drop in range(3):
    for phase, source in enumerate(sources):
        frame = compose(source, drop)
        frame.save(HERE / 'poses' / f'head_{drop}_tail_{phase + 1}.png')
        poses[drop, phase] = frame
frames = [poses[state] for state in states]
for index, frame in enumerate(frames, 1):
    frame.save(HERE / 'frames' / f'frame_{index}.png')
for zoom in (1, 8):
    images = [f.resize((46 * zoom, 37 * zoom), Image.Resampling.NEAREST) for f in frames]
    images[0].save(HERE / f'pet-react-{zoom}x.apng', save_all=True, append_images=images[1:],
                   duration=durations, loop=1, disposal=0, blend=0)
sheet = Image.new('RGB', (5 * 276, 3 * 250), '#e5e5e5')
draw = ImageDraw.Draw(sheet)
for (drop, phase), frame in poses.items():
    x, y = phase * 276, drop * 250
    draw.text((x + 8, y + 8), f'head +{drop}px / original idle {phase+1}', fill='black')
    enlarged = frame.resize((276, 222), Image.Resampling.NEAREST)
    sheet.paste(enlarged, (x, y + 28), enlarged)
sheet.save(HERE / 'contact-sheet.png')
for direction in ('right', 'left'):
    for style, color in (('light', '#f0f0f0'), ('dark', '#20252c'), ('checker', '#cccccc')):
        sheet = Image.new('RGB', (5 * 184, 3 * 170), color)
        draw = ImageDraw.Draw(sheet)
        for (drop, phase), frame in poses.items():
            x, y = phase * 184, drop * 170
            draw.text((x + 4, y + 4), f'head +{drop} / idle {phase+1}', fill='white' if style == 'dark' else 'black')
            tile = Image.new('RGBA', (184, 148), color)
            if style == 'checker':
                cells = ImageDraw.Draw(tile)
                for cy in range(0, 148, 8):
                    for cx in range(0, 184, 8):
                        if (cx // 8 + cy // 8) % 2:
                            cells.rectangle((cx, cy, cx + 7, cy + 7), fill='#eeeeee')
            image = ImageOps.mirror(frame) if direction == 'left' else frame
            tile.alpha_composite(image.resize((184, 148), Image.Resampling.NEAREST))
            sheet.paste(tile.convert('RGB'), (x, y + 22))
        sheet.save(HERE / f'contact-{style}-{direction}.png')
report = {'status': 'candidate_pending_review', 'head_source': HEAD_SOURCE,
          'head_edge_source': HEAD_EDGE, 'head_roi': '[24,4,46,29) OR [22,4,24,25)',
          'pose_count': 15, 'tail_cadence_ms': TAIL_MS,
          'head_change_ms': [0, 132, 264, 1056, 1188],
          'head_drops': [0, 1, 2, 1, 0],
          'demo_states_head_tail0': states, 'durations_ms': durations, 'apng_plays': 1,
          'body_paws_reference': 'current original idle phase; untouched by petting',
          'source_hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}}
(HERE / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print(json.dumps(report))
