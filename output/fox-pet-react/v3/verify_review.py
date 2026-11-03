"""Verify saved artifacts and static preview links without a browser."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import re

HERE = Path(__file__).parent
BASE = HERE.parent
ROOT = HERE.parents[2]
audit = json.loads((BASE / 'original-audit.json').read_text(encoding='utf8'))
assert all(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256']
           for row in audit['frames'])
source = Image.open(ROOT / 'assets/sprites/fox/idle/frame_1.png').convert('RGBA')
anchor_pixels = [(x, y) for y in range(35, 37) for x in range(46)
                 if source.getpixel((x, y))[3] >= 128]
for index in range(1, 7):
    im = Image.open(HERE / 'frames' / f'frame_{index}.png').convert('RGBA')
    assert im.size == (46, 37)
    assert [(x, y) for y in range(35, 37) for x in range(46)
            if im.getpixel((x, y))[3] >= 128] == anchor_pixels
html = (BASE / 'preview.html').read_text(encoding='utf-8-sig')
refs = re.findall(r'(?:href|src)="([^"]+)"', html)
assert all((BASE / ref).exists() for ref in refs)
assert 'let playing = false' in html
assert 'step%5' not in html and 'originals[' not in html
assert 'imageSmoothingEnabled = false' in html
assert re.findall(r'<canvas[^>]*width="(\d+)" height="(\d+)"', html) == [
    ('46', '37'), ('276', '222'), ('46', '37'), ('276', '222'), ('46', '37'), ('276', '222')]
apngs = {}
for name in ('pet-react-1x.apng', 'pet-react-8x.apng'):
    im = Image.open(HERE / name)
    durations = []
    for i in range(im.n_frames):
        im.seek(i)
        durations.append(im.info['duration'])
    assert sum(durations) == 1100
    apngs[name] = {'n_frames': im.n_frames, 'durations_ms': durations, 'total_ms': sum(durations)}
(HERE / 'apng-verification.json').write_text(json.dumps(apngs, indent=2), encoding='utf8')
provenance = json.loads((BASE / 'provenance.json').read_text(encoding='utf8'))
provenance['v1_v2_user_decision'] = 'rejected_style'
provenance['current_candidate'] = {'version': 'v3', 'status': 'pending_user_review',
                                  'workflow': 'explicitly user-authorized pixel edit of original copies',
                                  'generator_used': False, 'verification': 'v3/verification.json'}
(BASE / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf8')
report = {'all_30_original_hashes_match': True, 'feet_band_exact_all_6_pngs': True,
          'shared_viewport': [46, 37], 'shared_scale': 1, 'display_zoom': [1, 6],
          'destination_anchor': [26.5, 36], 'static_html_links_checked': len(refs),
          'static_html_missing_links': [], 'default_paused': True,
          'reference_fixed': True, 'browser_qa': 'unavailable',
          'exe_sha256_current': hashlib.sha256((ROOT / 'dist/DesktopPet.exe').read_bytes()).hexdigest()}
(HERE / 'review-checks.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print(json.dumps(report))
