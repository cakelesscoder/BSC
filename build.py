#!/usr/bin/env python3
"""
build.py — assemble index.html from src/template.html + data/*.json + images/

Usage:
    python3 build.py            # rebuild index.html
    python3 build.py --watch    # rebuild on every change to data/ or src/
    python3 build.py --serve    # rebuild and run a local server on :8000

Output is written to ./index.html in the project root.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DATA_DIR = ROOT / 'data'
SRC_DIR = ROOT / 'src'
TEMPLATE = SRC_DIR / 'template.html'
OUTPUT = ROOT / 'index.html'

DATA_FILES = [
    'questions.json',
    'options.json',
    'option_order.json',
    'rules.json',
    'images.json',
    'help.json',
    'blurbs.json',
]


def load_data():
    """Load and combine all the JSON data files into the shape the JS expects."""
    out = {}
    for fname in DATA_FILES:
        path = DATA_DIR / fname
        if not path.exists():
            print(f"  [warn] missing data file: {path}", file=sys.stderr)
            continue
        with open(path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        # Map filenames to JS keys
        key = {
            'questions.json': 'questions',
            'options.json': 'options',
            'option_order.json': 'order',
            'rules.json': 'rules',
            'images.json': 'images',
            'help.json': 'help',
            'blurbs.json': 'blurbs',
        }[fname]
        out[key] = content
    return out


def validate(data):
    """Sanity-check the data before shipping it to the browser."""
    issues = []
    qkeys = [q['key'] for q in data['questions']]

    # Every option in options must have an order entry
    for qkey, opts in data['options'].items():
        if qkey not in data['order']:
            issues.append(f"options.{qkey} has no entry in order.json")
            continue
        ordered = data['order'][qkey]
        missing = [c for c in opts if c not in ordered]
        extra = [c for c in ordered if c not in opts]
        if missing:
            issues.append(f"options.{qkey}: codes missing from order: {missing}")
        if extra:
            issues.append(f"order.{qkey}: codes not in options: {extra}")

    # Every option should have a blurb (warn-level only)
    for qkey, opts in data['options'].items():
        for code in opts:
            if code not in data['blurbs']:
                issues.append(f"  [warn] no blurb for {qkey}.{code}")

    # Every question key should have help text
    for qkey in qkeys:
        if qkey not in data['help']:
            issues.append(f"  [warn] no help text for question '{qkey}'")

    return issues


def build(image_base=None):
    if not TEMPLATE.exists():
        print(f"ERROR: template not found at {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    print(f"  Loading data from {DATA_DIR.relative_to(ROOT)}/")
    data = load_data()

    issues = validate(data)
    warns = [i for i in issues if i.lstrip().startswith('[warn]')]
    errs = [i for i in issues if not i.lstrip().startswith('[warn]')]
    for w in warns:
        print(w)
    if errs:
        print("VALIDATION ERRORS:")
        for e in errs:
            print(f"  {e}")
        sys.exit(1)

    template = TEMPLATE.read_text(encoding='utf-8')

    # Inject DATA — find the placeholder marker and replace.
    marker_open = '/* @@DATA_START@@ */'
    marker_close = '/* @@DATA_END@@ */'
    if marker_open not in template or marker_close not in template:
        print(f"ERROR: template missing markers '{marker_open}' / '{marker_close}'", file=sys.stderr)
        sys.exit(1)

    data_json = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    pattern = re.compile(re.escape(marker_open) + r'.*?' + re.escape(marker_close), re.DOTALL)
    output = pattern.sub(
        marker_open + ' const DATA = ' + data_json + '; ' + marker_close,
        template,
    )

    # Inject IMAGE_BASE if provided via --image-base flag.
    if image_base is not None:
        url = image_base.rstrip('/')
        output = re.sub(
            r"const IMAGE_BASE = '[^']*';",
            f"const IMAGE_BASE = '{url}';",
            output,
            count=1,
        )
        print(f"  IMAGE_BASE set to '{url}'")

    OUTPUT.write_text(output, encoding='utf-8')
    print(f"  Wrote {OUTPUT.relative_to(ROOT)}  ({len(output):,} bytes, {sum(len(v) for v in data['options'].values())} options, {sum(len(v) for v in data['rules'].values())} rules)")


def watch(image_base=None):
    print("Watching for changes in data/ and src/ ... (Ctrl-C to stop)")
    last = {}
    def stamp():
        s = {}
        for d in (DATA_DIR, SRC_DIR):
            for p in d.rglob('*'):
                if p.is_file():
                    s[str(p)] = p.stat().st_mtime
        return s
    last = stamp()
    build(image_base=image_base)
    try:
        while True:
            time.sleep(0.5)
            now = stamp()
            if now != last:
                print()
                print(f"[{time.strftime('%H:%M:%S')}] Change detected, rebuilding...")
                try:
                    build(image_base=image_base)
                except SystemExit:
                    pass
                last = now
    except KeyboardInterrupt:
        print("\nStopped.")


def serve(image_base=None):
    """Build once, then run a local server. Auto-rebuild is not enabled here —
    use --watch in another terminal if you want live rebuild."""
    import http.server
    import socketserver

    build(image_base=image_base)
    PORT = 8000
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(('', PORT), handler) as httpd:
        print(f"\n  Serving http://localhost:{PORT}  (Ctrl-C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


def main():
    ap = argparse.ArgumentParser(description='Build the Orion Base System Configurator')
    ap.add_argument('--watch', action='store_true', help='Rebuild on file change')
    ap.add_argument('--serve', action='store_true', help='Build and serve on :8000')
    ap.add_argument(
        '--image-base',
        metavar='URL',
        default=None,
        help='Set IMAGE_BASE in the output (e.g. https://you.github.io/orion-bsc/images)',
    )
    args = ap.parse_args()

    if args.watch:
        watch(image_base=args.image_base)
    elif args.serve:
        serve(image_base=args.image_base)
    else:
        build(image_base=args.image_base)


if __name__ == '__main__':
    main()
