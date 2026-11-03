"""User-authorized pixel edit of copies: only two upper-eye pixels change."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib
import json

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'assets/sprites/fox/idle/frame_1.png'
original = Image.open(SOURCE).convert('RGBA')
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
# Exclusive ROI: x=33..34, y=17..18. Bottom dark row stays the original eyelid.
ROI = (33, 17, 35, 19)
half = original.copy()
closed = original.copy()
for x, donor in ((33, (35, 17)), (34, (36, 17))):
    half.putpixel((x, 17), original.getpixel(donor))
    closed.putpixel((x, 17), original.getpixel((32, 17)))
frames = [original.copy(), half, closed, closed.copy(), half.copy(), original.copy()]
durations = [180, 90, 180, 260, 90, 300]
report = []
for i, frame in enumerate(frames, 1):
    changed = [(x, y) for y in range(37) for x in range(46)
               if frame.getpixel((x, y)) != original.getpixel((x, y))]
    assert all(ROI[0] <= x < ROI[2] and ROI[1] <= y < ROI[3] for x, y in changed)
    assert frame.getchannel('A').tobytes() == original.getchannel('A').tobytes()
    assert frame.size == (46, 37)
    target = HERE / 'frames' / f'frame_{i}.png'
    target.parent.mkdir(exist_ok=True)
    frame.save(target)
    assert Image.open(target).convert('RGBA').tobytes() == frame.tobytes()
    report.append({'frame': i, 'changed_pixels': changed,
                   'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
assert frames[0].tobytes() == original.tobytes() == frames[-1].tobytes()
frames[0].save(HERE / 'pet-react-1x.apng', save_all=True, append_images=frames[1:],
               duration=durations, loop=0, disposal=0, blend=0)
large = [im.resize((368, 296), Image.Resampling.NEAREST) for im in frames]
large[0].save(HERE / 'pet-react-8x.apng', save_all=True, append_images=large[1:],
              duration=durations, loop=0, disposal=0, blend=0)
sheet = Image.new('RGB', (1104, 336), '#f1f1f1')
draw = ImageDraw.Draw(sheet)
for i, (frame, label) in enumerate(zip((original, half, closed), ('original', 'half: 2 pixels', 'closed: 2 pixels'))):
    draw.text((i * 368 + 12, 12), label, fill='#202020')
    sheet.paste(frame.resize((368, 296), Image.Resampling.NEAREST), (i * 368, 40),
                frame.getchannel('A').resize((368, 296), Image.Resampling.NEAREST))
sheet.save(HERE / 'contact-sheet.png')
result = {'status': 'candidate_pending_user_review', 'workflow': 'user-authorized direct pixel edits; no generation/resizing of frame PNGs',
          'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': source_hash,
          'roi_exclusive': ROI, 'changed_coordinates': [[33, 17], [34, 17]],
          'donors_half': [[35, 17], [36, 17]], 'donor_closed': [32, 17],
          'alpha_exact_all_frames': True, 'outside_roi_exact_all_frames': True,
          'first_last_rgba_exact_original': True, 'size_all_frames': [46, 37],
          'durations_ms': durations, 'frames': report}
(HERE / 'verification.json').write_text(json.dumps(result, indent=2), encoding='utf8')
assert source_hash == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
print(json.dumps(result))
