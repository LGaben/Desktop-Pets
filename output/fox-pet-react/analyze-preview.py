"""Read-only PNG analysis; writes measurements, never image pixels."""
from pathlib import Path
import json
from PIL import Image

base = Path(__file__).parent
im = Image.open(base / 'pet-react-candidate-v1.png').convert('RGBA')
regions = [(0, 0, 570, 460), (570, 0, 1138, 460), (1138, 0, 1706, 460),
           (0, 460, 570, 922), (570, 460, 1138, 922), (1138, 460, 1706, 922)]
frames = []
for region in regions:
    x0, y0, x1, y1 = region
    points = [(x, y) for y in range(y0, y1) for x in range(x0, x1)
              if im.getpixel((x, y))[3] >= 128]
    box = [min(x for x, y in points), min(y for x, y in points),
           max(x for x, y in points) + 1, max(y for x, y in points) + 1]
    # Bottom dense band includes feet; center is stable against single edge pixels.
    bottom = box[3] - 1
    feet = [(x, y) for x, y in points if y >= bottom - 10]
    anchor = [(min(x for x, y in feet) + max(x for x, y in feet)) / 2, bottom]
    frames.append({'region': list(region), 'dense_bbox': box, 'anchor': anchor,
                   'feet_band_y': [bottom - 10, bottom]})
result = {'alpha_threshold': 128, 'frames': frames,
          'source_reference': 'assets/sprites/fox/idle/frame_1.png'}
def measure(path, band):
    image = Image.open(path).convert('RGBA')
    points = [(x, y) for y in range(image.height) for x in range(image.width)
              if image.getpixel((x, y))[3] >= 128]
    box = [min(x for x, y in points), min(y for x, y in points),
           max(x for x, y in points) + 1, max(y for x, y in points) + 1]
    bottom = box[3] - 1
    feet = [(x, y) for x, y in points if y >= bottom - band]
    return {'dense_bbox': box, 'anchor': [(min(x for x, y in feet) + max(x for x, y in feet)) / 2, bottom]}
root = base.parent.parent
result['reference'] = measure(root / result['source_reference'], 1)
result['keyframe_v2'] = measure(base / 'pet-react-keyframe-v2.png', 20)
result['v1_common_scale'] = 0.08
result['viewport'] = [46, 37]
result['destination_anchor'] = result['reference']['anchor']
for frame in frames:
    box, anchor = frame['dense_bbox'], frame['anchor']
    scale = result['v1_common_scale']
    dest = result['destination_anchor']
    frame['destination_bbox'] = [dest[0] + (box[0] - anchor[0]) * scale,
                                 dest[1] + (box[1] - anchor[1]) * scale,
                                 dest[0] + (box[2] - anchor[0]) * scale,
                                 dest[1] + (box[3] - anchor[1]) * scale]
    assert all(0 <= frame['destination_bbox'][i] <= result['viewport'][i % 2] for i in range(4))
(base / 'preview-alignment.json').write_text(json.dumps(result, indent=2), encoding='utf8')
print(json.dumps(result))
