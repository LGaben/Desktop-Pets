"""Check saved poses/APNG against each current original idle phase."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import re

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
base = HERE.parent
sources = [Image.open(ROOT / f'assets/sprites/fox/idle/frame_{i}.png').convert('RGBA') for i in range(1, 6)]
audit = json.loads((base / 'original-audit.json').read_text(encoding='utf8'))
assert all(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'] for row in audit['frames'])

def neck_intact(image, source):
    return all(image.getpixel((x, y))[3] >= (250 if source.getpixel((x, y))[3] >= 250 else 128)
               for y in range(24, 29) for x in range(24, 46) if source.getpixel((x, y))[3] >= 128)

def edge_intact(image, source, drop):
    return all(image.getpixel((x, y)) == (source.getpixel((x, y-drop)) if y >= 4+drop else (0, 0, 0, 0))
               for y in range(4, 23) for x in (22, 23))

assert not neck_intact(Image.open(HERE / 'diagnostic-before-frame-2.png').convert('RGBA'), sources[0])
for index, drop in ((2, 1), (3, 2)):
    assert not edge_intact(Image.open(HERE / f'spike-before-frame-{index}.png').convert('RGBA'), sources[0], drop)

def head_roi(x, y):
    return (24 <= x < 46 and 4 <= y < 29) or (22 <= x < 24 and 4 <= y < 25)

poses = {}
assert len(list((HERE / 'poses').glob('*.png'))) == 15
for drop in range(3):
    for phase, source in enumerate(sources):
        image = Image.open(HERE / 'poses' / f'head_{drop}_tail_{phase+1}.png').convert('RGBA')
        assert image.size == (46, 37)
        assert neck_intact(image, source)
        assert edge_intact(image, source, drop)
        assert all(image.getpixel((x, y)) == source.getpixel((x, y))
                   for y in range(37) for x in range(46) if not head_roi(x, y))
        assert all(image.getpixel((x, y)) == source.getpixel((x, y))
                   for y in range(29, 37) for x in range(16, 46))
        assert all(image.getpixel((x, y)) == source.getpixel((x, y))
                   for y in range(31, 37) for x in range(46))
        if drop == 0:
            assert image.tobytes() == source.tobytes()
        else:
            # The complete main head, including soft alpha, follows its source.
            for y in range(4, 27):
                for x in range(24, 46):
                    if drop == 2 and y == 17 and x in (33, 34):
                        continue
                    assert image.getpixel((x, y + drop)) == source.getpixel((x, y))
        poses[drop, phase] = image

states = [(0, 0), (1, 0), (2, 1), (2, 2), (2, 3), (1, 4), (0, 4), (0, 0)]
durations = [132, 132, 264, 264, 264, 132, 132, 264]
assert len(list((HERE / 'frames').glob('frame_*.png'))) == 8
elapsed = 0
for i, ((drop, phase), duration) in enumerate(zip(states, durations), 1):
    image = Image.open(HERE / 'frames' / f'frame_{i}.png').convert('RGBA')
    assert image.tobytes() == poses[drop, phase].tobytes()
    assert phase == (elapsed // 264) % 5
    expected_head = 0 if elapsed < 132 else 1 if elapsed < 264 else 2 if elapsed < 1056 else 1 if elapsed < 1188 else 0
    assert drop == expected_head
    elapsed += duration
assert elapsed == 1584
apngs = {}
for zoom in (1, 8):
    im = Image.open(HERE / f'pet-react-{zoom}x.apng')
    assert im.info['loop'] == 1 and im.n_frames == 8
    actual_durations = []
    for i, (drop, phase) in enumerate(states):
        im.seek(i)
        actual_durations.append(im.info['duration'])
        decoded = im.convert('RGBA')
        expected = poses[drop, phase].resize((46 * zoom, 37 * zoom), Image.Resampling.NEAREST)
        assert decoded.tobytes() == expected.tobytes()
        native = decoded.resize((46, 37), Image.Resampling.NEAREST)
        assert neck_intact(native, sources[phase]) and edge_intact(native, sources[phase], drop)
    assert actual_durations == durations
    apngs[str(zoom)] = {'frames': 8, 'plays': 1, 'durations_ms': actual_durations, 'total_ms': elapsed, 'decoded_exact': True}

html = (base / 'preview.html').read_text(encoding='utf-8-sig')
refs = re.findall(r'(?:href|src)="([^"]+)"', html)
assert all((base / ref.split('?')[0]).exists() for ref in refs)
assert 'repeatAt' not in html and 'id="repeat"' not in html
assert 'FoxMotion.pet(motion)' in html and 'FoxMotion.advance(motion, delta)' in html
assert 'pose.head === 0 ? originals[pose.phase] : poses[pose.head][pose.phase]' in html
report = {'source_hashes_all_30_exact': True, 'poses': 15, 'demo_pngs': 8, 'size': [46, 37],
          'neck_and_left_edge_regression_all_poses_apng': True, 'actual_bad_pngs_fail_regression': True,
          'complete_head_rgba_translated_all_phases': True,
          'outside_head_roi_and_paws_exact_current_idle_phase': True,
          'head0_exact_current_original_all_5_phases': True,
          'demo_tail_phase_at_every_timestamp_exact': True, 'tail_cadence_ms': 264,
          'source_neighbor_rgba_changes': [sum(a != b for a, b in zip(sources[i].getdata(), sources[(i+1)%5].getdata())) for i in range(5)],
          'apng': apngs, 'static_links_valid': len(refs), 'browser_qa': 'unavailable',
          'motion_logic_check': 'run node v4/verify_motion.js separately',
          'exe_current_sha256': hashlib.sha256((ROOT / 'dist/DesktopPet.exe').read_bytes()).hexdigest()}
(HERE / 'review-checks.json').write_text(json.dumps(report, indent=2), encoding='utf8')
provenance = json.loads((base / 'provenance.json').read_text(encoding='utf8'))
provenance['current_candidate'] = {'version': 'v4', 'status': 'pending_user_review', 'workflow': 'original-derived head translation over uninterrupted current idle phase', 'generator_used': False}
(base / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(report))
