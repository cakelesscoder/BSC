#!/usr/bin/env python3
"""
index_images.py — rescan images/ and rebuild data/images.json

When you add or remove images from the images/ folder, run:

    python3 scripts/index_images.py

Then rebuild:

    python3 build.py

Image filenames must follow the convention <option-code><sequence>.<ext>:
  10101.jpg → option 101, image #1
  20305.jpeg → option 203, image #5
  65601.jpg → option 656, image #1

The folder structure under images/ uses 3-digit folder names matching the
'folder' field in data/questions.json:

    images/
        100/  -- MIG/TIG (process)
        150/  -- material
        200/  -- arm reach
        ...

Files that don't match the pattern are filed under the question's '_generic'
bucket and shown across all options (e.g. the touch sense diagram).
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent.resolve()
IMAGES_DIR = ROOT / 'images'
DATA_DIR = ROOT / 'data'

# Mapping of question keys to image folder names (mirror of data/questions.json)
DEFAULT_FOLDER_MAP = {
    'process':  '01-process',
    'material': '02-material',
    'reach':    '03-reach',
    'amperage': '04-amperage',
    'cooling':  '05-cooling',
    'conduit':  '06-conduit',
    'fume':     '07-fume',
    'wire':     '08-wire',
    'touch':    '09-touch',
    'tables':   '10-tables',
    'guarding': '11-guarding',
    'install':  None,
    'training': None,
}


def main():
    if not IMAGES_DIR.exists():
        print(f"ERROR: images dir not found at {IMAGES_DIR}", file=sys.stderr)
        sys.exit(1)

    # Load questions if available so we use the same folder map; otherwise
    # fall back to the defaults above.
    folder_map = DEFAULT_FOLDER_MAP.copy()
    qpath = DATA_DIR / 'questions.json'
    if qpath.exists():
        try:
            qs = json.loads(qpath.read_text(encoding='utf-8'))
            folder_map = {q['key']: q.get('folder') for q in qs}
        except Exception as e:
            print(f"  [warn] could not read questions.json ({e}); using defaults")

    out = {}
    total = 0
    for qkey, folder in folder_map.items():
        out[qkey] = {}
        if not folder:
            continue
        folder_path = IMAGES_DIR / folder
        if not folder_path.exists():
            print(f"  [info] {qkey}: no folder at images/{folder}/")
            continue
        files = sorted(p.name for p in folder_path.iterdir() if p.is_file())
        for fname in files:
            m = re.match(r'^(\d{3})(\d{2})\.', fname)
            if m:
                code = m.group(1)
                out[qkey].setdefault(code, []).append(fname)
            else:
                # Non-conforming files (e.g. touch_sense.jpg) go to a shared bucket
                out[qkey].setdefault('_generic', []).append(fname)
            total += 1

    out_path = DATA_DIR / 'images.json'
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f"Indexed {total} files across {sum(1 for v in out.values() if v)} question folders.")
    for qk, by_code in out.items():
        if by_code:
            counts = sum(len(v) for v in by_code.values())
            codes = sorted(by_code.keys())
            print(f"  {qk:10s}: {counts:3d} files across {len(codes)} codes ({', '.join(codes)})")
    print(f"\nWrote {out_path.relative_to(ROOT)}.")


if __name__ == '__main__':
    main()
