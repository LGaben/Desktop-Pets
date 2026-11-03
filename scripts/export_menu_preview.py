"""Export the existing menu fragment as an offline standalone preview."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ICONS = {
    'menu': '<path d="M4 6h16M4 12h16M4 18h16"/>',
    'pause': '<path d="M9 5v14M15 5v14"/>',
    'x': '<path d="m6 6 12 12M6 18 18 6"/>',
    'heart': '<path d="M20 5c-3-3-6-1-8 1-2-2-5-4-8-1-5 5 3 11 8 15 5-4 13-10 8-15Z"/>',
    'circle-dot': '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="1"/>',
    'moon': '<path d="M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11Z"/>',
    'mouse-pointer-2': '<path d="m4 3 7 18 2-8 8-2L4 3Z"/>',
    'settings-2': '<path d="M3 6h6m6 0h6M3 18h10m6 0h2"/><circle cx="12" cy="6" r="3"/><circle cx="16" cy="18" r="3"/>',
    'ellipsis': '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
}


def offline_fragment(fragment):
    def replace(match):
        name = match.group(1)
        if name not in ICONS:
            raise ValueError(f'Missing reviewed local icon: {name}')
        return ('<svg aria-hidden="true" viewBox="0 0 24 24" width="17" height="17" '
                'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
                'stroke-linejoin="round">' + ICONS[name] + '</svg>')
    result = re.sub(r'<i data-lucide="([a-z0-9-]+)"[^>]*></i>', replace, fragment)
    if re.search(r'<(?:script|link|iframe)[^>]+(?:src|href)=|\b(?:fetch|XMLHttpRequest|WebSocket)\s*\(', result):
        raise ValueError('The standalone preview must not depend on external resources or network APIs')
    return result


def export(source, destination, force=False, stack_variants=False):
    if destination.exists() and not force:
        raise FileExistsError('Preview already exists; use --force to update the authorized export')
    fragment = source.read_text(encoding='utf8')
    content = offline_fragment(fragment)
    if stack_variants:
        content = re.sub(r'(<section\b[^>]*data-variant="[^"]+"[^>]*)\s+hidden(>)', r'\1\2', content)
        content += '<style>#native-pet-menu-design section:before{content:attr(data-variant);display:block;text-align:center;padding-top:16px;font:14px "Segoe UI",sans-serif;color:light-dark(#292723,#f3f0ea)}</style>'
    digest = hashlib.sha256(fragment.encode()).hexdigest()
    header = '''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; font-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'">
<title>Desktop Pet menu preview</title>
<style>:root{color-scheme:light dark}body{margin:0;background:light-dark(#f4f6f0,#171d19)}main{max-width:736px;margin:auto}.cursor-interaction{cursor:pointer}.viz-dotted-background{background-image:radial-gradient(light-dark(#c5cdbf,#384235) 1px,transparent 1px);background-size:16px 16px}button:focus-visible,select:focus-visible{outline:2px solid light-dark(#426b39,#bad6a7);outline-offset:3px}</style>
</head><body>
<script>
(()=>{const key='desktop-pet-menu-preview';let state=null;try{state=JSON.parse(localStorage.getItem(key));}catch{}
window.openai={widgetState:state,setWidgetState:async value=>{window.openai.widgetState=value;try{localStorage.setItem(key,JSON.stringify(value));}catch{}}};})();
</script><main>
'''
    destination.write_text(header + '<!-- source-sha256:' + digest + ' -->\n' + content
                           + '\n</main></body></html>\n', encoding='utf8')
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'output/menu-concepts/pet-reactive-menus.html')
    parser.add_argument('--output', type=Path, default=ROOT / 'output/menu-concepts/menu-preview.html')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--stack-variants', action='store_true', help='Show all design variants in the offline export')
    args = parser.parse_args()
    print(export(args.source, args.output, args.force, args.stack_variants))
    print(args.output)


if __name__ == '__main__':
    main()
