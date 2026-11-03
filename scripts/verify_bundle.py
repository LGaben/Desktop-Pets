"""Read a PyInstaller bundle as data; never launch it or extract files to disk."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

MAGIC = b'MEI\014\013\012\013\016'
MAX_DLL_BYTES = 64 * 1024 * 1024


def archive_entries(blob):
    cookie = blob.rfind(MAGIC)
    if cookie < 0 or cookie + 88 > len(blob):
        raise ValueError('Missing PyInstaller archive cookie')
    _, size, toc_offset, toc_size, python_tag, library = struct.unpack('!8sIIII64s', blob[cookie:cookie + 88])
    start = cookie + 88 - size
    pos, end = start + toc_offset, start + toc_offset + toc_size
    if start < 0 or pos < start or end > cookie:
        raise ValueError('Invalid archive bounds')
    entries = {}
    while pos < end:
        if pos + 18 > end:
            raise ValueError('Truncated archive entry')
        length, offset, packed, unpacked, compressed, kind = struct.unpack('!IIIIBc', blob[pos:pos + 18])
        if length < 18 or pos + length > end or start + offset + packed > start + toc_offset:
            raise ValueError('Invalid entry bounds')
        name = blob[pos + 18:pos + length].rstrip(b'\0').decode('utf8')
        if name in entries or compressed not in (0, 1):
            raise ValueError('Duplicate entry or invalid compression flag')
        entries[name] = (start + offset, packed, unpacked, compressed, kind)
        pos += length
    return python_tag, library.rstrip(b'\0').decode('ascii'), entries


def entry_bytes(blob, entry):
    offset, size, unpacked, compressed, _ = entry
    if unpacked > MAX_DLL_BYTES or offset < 0 or offset + size > len(blob):
        raise ValueError('DLL entry exceeds inspection limits')
    raw = blob[offset:offset + size]
    if compressed:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(raw, MAX_DLL_BYTES + 1)
        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError('Invalid or oversized compressed DLL')
    if len(raw) != unpacked:
        raise ValueError('DLL size differs from archive metadata')
    return raw


def inspect(path, expected_qt='6.12.0'):
    import pefile
    blob = Path(path).read_bytes()
    tag, library, entries = archive_entries(blob)
    if tag != 313 or library != 'python313.dll':
        raise ValueError('Bundle must contain the selected CPython 3.13 runtime')
    if any('pyqt5' in name.lower() or Path(name.replace('\\', '/')).name.startswith('Qt5') for name in entries):
        raise ValueError('Old Qt5/PyQt5 components remain in the bundle')
    pe = pefile.PE(data=blob, fast_load=True)
    pe.parse_data_directories(directories=[2])
    manifests = [pe.get_data(c.data.struct.OffsetToData, c.data.struct.Size).decode('utf8')
                 for a in pe.DIRECTORY_ENTRY_RESOURCE.entries if a.id == 24
                 for b in a.directory.entries for c in b.directory.entries]
    from xml.etree import ElementTree
    levels = [node.attrib for text in manifests for node in ElementTree.fromstring(text).iter()
              if node.tag.endswith('requestedExecutionLevel')]
    if levels != [{'level': 'asInvoker', 'uiAccess': 'false'}]:
        raise ValueError('Unexpected privilege request in EXE manifest')
    if pe.FILE_HEADER.Machine != 0x8664 or pe.OPTIONAL_HEADER.DllCharacteristics & 0x140 != 0x140:
        raise ValueError('AMD64, ASLR and DEP are required')
    libraries = []
    for dll in ('Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll', 'Qt6Svg.dll'):
        names = [name for name in entries if Path(name.replace('\\', '/')).name == dll]
        if not names and dll == 'Qt6Svg.dll':
            continue
        if len(names) != 1:
            raise ValueError(f'Missing or duplicate {dll}')
        raw = entry_bytes(blob, entries[names[0]])
        native = pefile.PE(data=raw, fast_load=True)
        native.parse_data_directories(directories=[2])
        info = native.VS_FIXEDFILEINFO[0]
        version = '.'.join(str(value) for value in (info.FileVersionMS >> 16, info.FileVersionMS & 65535,
                                                   info.FileVersionLS >> 16, info.FileVersionLS & 65535))
        if version != expected_qt + '.0':
            raise ValueError(f'Unexpected Qt DLL version: {dll} {version}')
        libraries.append({'name': names[0], 'version': version, 'sha256': hashlib.sha256(raw).hexdigest()})
    return {'exe': str(Path(path).resolve()), 'sha256': hashlib.sha256(blob).hexdigest(),
            'bytes': len(blob), 'python_tag': tag, 'python_library': library,
            'manifest': levels[0], 'aslr': True, 'dep': True, 'qt_libraries': libraries,
            'exe_executed': False, 'files_extracted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    text = json.dumps(inspect(args.exe), indent=2)
    if args.output:
        args.output.write_text(text + '\n', encoding='utf8')
    print(text)


if __name__ == '__main__':
    main()
