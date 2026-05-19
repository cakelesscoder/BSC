#!/usr/bin/env python3
"""
extract_from_xlsx.py — refresh data/ from the source spreadsheet

When a new version of the BSC spreadsheet ships, run:

    python3 scripts/extract_from_xlsx.py path/to/System_Configurator_VXX.xlsx

This rewrites:
  - data/options.json       (option codes and labels for each question)
  - data/rules.json         (dependency rules between questions)
  - data/option_order.json  (display order for options within each question)

It does NOT touch:
  - data/blurbs.json    (your option taglines — preserve hand-edited copy)
  - data/help.json      (your "more info" panel text — preserve hand-edited copy)
  - data/questions.json (titles, subtitles, icons — hand-edited)
  - data/images.json    (run scripts/index_images.py to rebuild)

After extracting, run:
    python3 build.py

to rebuild index.html with the new data.

CAUTION: spreadsheet column positions are hard-coded in this script. If the
spreadsheet author changes the layout, update the QUESTION_COLS table below.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = ROOT / 'data'

# Column layout in the spreadsheet (locked to V15). If the layout changes
# in a future version, update these positions.
#   label_col: column with the human-readable option labels (and codes)
#   this_q:    column with the option code being defined ("This Q")
#   and_cols:  list of "And" columns holding required prior-question codes,
#              in question order (1..n-1)
QUESTION_COLS = [
    {'n':1,  'key':'process',   'label_col':2,   'this_q':3,   'and_cols':[]},
    {'n':2,  'key':'material',  'label_col':8,   'this_q':10,  'and_cols':[9]},
    {'n':3,  'key':'reach',     'label_col':15,  'this_q':18,  'and_cols':[16, 17]},
    {'n':4,  'key':'amperage',  'label_col':23,  'this_q':27,  'and_cols':[24, 25, 26]},
    {'n':5,  'key':'cooling',   'label_col':32,  'this_q':37,  'and_cols':[33, 34, 35, 36]},
    {'n':6,  'key':'conduit',   'label_col':42,  'this_q':48,  'and_cols':[43, 44, 45, 46, 47]},
    {'n':7,  'key':'fume',      'label_col':53,  'this_q':60,  'and_cols':[54, 55, 56, 57, 58, 59]},
    {'n':8,  'key':'wire',      'label_col':65,  'this_q':73,  'and_cols':[66, 67, 68, 69, 70, 71]},
    {'n':9,  'key':'touch',     'label_col':78,  'this_q':87,  'and_cols':[79, 80, 81, 82, 83, 84, 85, 86]},
    {'n':10, 'key':'tables',    'label_col':92,  'this_q':102, 'and_cols':[93, 94, 95, 96, 97, 98, 99, 100, 101]},
    {'n':11, 'key':'jigs',      'label_col':107, 'this_q':118, 'and_cols':[108, 109, 110, 111, 112, 113, 114, 115, 116, 117]},
    {'n':12, 'key':'guarding',  'label_col':123, 'this_q':135, 'and_cols':[124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134]},
    {'n':13, 'key':'install',   'label_col':140, 'this_q':153, 'and_cols':[141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152]},
    {'n':14, 'key':'training',  'label_col':158, 'this_q':172, 'and_cols':[159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171]},
]

# Known typos / corrections in the source spreadsheet. If you find more,
# add them here — the alternative is hand-fixing every regen.
LABEL_FIXES = {
    'parallet': 'parallel',
    'Extration': 'Extraction',
}

# Code remappings: spreadsheet has a typo where the label column shows '343'
# for the Drum Pack option but the rules consistently use '453'. We always
# treat the rules as authoritative.
CODE_REMAP = {
    'wire': {'343': '453'},
}

# Word fragments that appear in label columns but aren't part of the
# user-facing label (they're internal annotations / model name flags).
LABEL_ANNOTATIONS = {'WG4', 'SAWP', 'TAWERS TIG DC', 'TAWERS TIG AC', 'Rules', '1 x Jig Table Frame'}


def is_code(v):
    if v is None:
        return False
    s = str(v).strip()
    if s == '' or s.lower() == 'nan':
        return False
    return bool(re.match(r'^\d{3}$', s))


def extract_options(df, q):
    """Walk the label column, pulling out (code, label) pairs.

    The pattern is: a 3-digit code, immediately followed (next non-empty
    row in this column) by the human label. Some labels span two rows
    (e.g. "No training required as" / "not first system"). After the label,
    annotation words like "WG4" or "SAWP" appear and should be skipped.
    """
    options = {}
    rows = []
    for r in range(3, df.shape[0]):
        v = df.iat[r, q['label_col']]
        if v is not None and str(v).strip() and str(v).strip().lower() != 'nan':
            rows.append((r, str(v).strip()))

    i = 0
    while i < len(rows):
        r, txt = rows[i]
        if re.match(r'^\d{3}$', txt):
            code = txt
            label_parts = []
            i += 1
            label_collected = False
            while i < len(rows):
                r2, txt2 = rows[i]
                if re.match(r'^\d{3}$', txt2):
                    break
                if not label_collected:
                    label_parts.append(txt2)
                    label_collected = True
                    j = i + 1
                    if j < len(rows):
                        r3, txt3 = rows[j]
                        if (r3 - r2 == 1) and txt3 not in LABEL_ANNOTATIONS and not re.match(r'^\d{3}$', txt3):
                            label_parts.append(txt3)
                            i = j
                i += 1
            label = ' '.join(label_parts).strip()
            for bad, good in LABEL_FIXES.items():
                label = label.replace(bad, good)
            # Apply code remapping (e.g. 343 -> 453)
            remap = CODE_REMAP.get(q['key'], {})
            code = remap.get(code, code)
            options[code] = label
        else:
            i += 1
    return options


def extract_rules(df, q):
    """For each row where the question's this_q col has a 3-digit code,
    record (code, [prereq_codes_or_None_per_prior_question])."""
    rules = []
    for r in range(3, df.shape[0]):
        code = df.iat[r, q['this_q']]
        if not is_code(code):
            continue
        sc = str(code).strip()
        # Apply code remapping
        remap = CODE_REMAP.get(q['key'], {})
        sc = remap.get(sc, sc)
        prereqs = []
        for c in q['and_cols']:
            v = df.iat[r, c]
            if is_code(v):
                prereqs.append(str(v).strip())
            else:
                prereqs.append(None)
        rules.append([sc, prereqs])
    # Dedupe
    seen = set()
    unique = []
    for sc, p in rules:
        key = (sc, tuple(p))
        if key not in seen:
            seen.add(key)
            unique.append([sc, p])
    return unique


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('xlsx', help='Path to the source spreadsheet')
    ap.add_argument('--sheet', default='BSC 1', help='Sheet name (default: "BSC 1")')
    ap.add_argument('--dry-run', action='store_true', help='Show what would change, don\'t write')
    args = ap.parse_args()

    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas not installed. Run: pip install pandas openpyxl", file=sys.stderr)
        sys.exit(1)

    src = Path(args.xlsx)
    if not src.exists():
        print(f"ERROR: file not found: {src}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {src} (sheet: {args.sheet}) ...")
    df = pd.read_excel(src, sheet_name=args.sheet, header=None)
    print(f"  Sheet shape: {df.shape[0]} rows × {df.shape[1]} cols")

    options = {}
    rules = {}
    order = {}

    for q in QUESTION_COLS:
        opts = extract_options(df, q)
        rls = extract_rules(df, q)
        options[q['key']] = opts
        rules[q['key']] = rls
        # Default order = sorted by code
        order[q['key']] = sorted(opts.keys())
        print(f"  Q{q['n']:2d} {q['key']:10s}: {len(opts)} options, {len(rls)} rules")

    # Sanity: report missing options vs rules
    print()
    for q in QUESTION_COLS:
        opts_codes = set(options[q['key']].keys())
        rule_codes = set(r[0] for r in rules[q['key']])
        missing_in_rules = opts_codes - rule_codes
        if missing_in_rules:
            print(f"  [info] {q['key']}: {len(missing_in_rules)} option(s) have no rules: {sorted(missing_in_rules)} (will be permissive)")

    if args.dry_run:
        print("\n--dry-run: no files written")
        return

    # Preserve existing option_order if it has entries for all current options;
    # otherwise overwrite with the default sorted order.
    order_path = DATA_DIR / 'option_order.json'
    if order_path.exists():
        existing_order = json.loads(order_path.read_text(encoding='utf-8'))
        new_order = {}
        for qkey, opts in options.items():
            old = existing_order.get(qkey, [])
            ordered = [c for c in old if c in opts]
            extras = [c for c in opts if c not in ordered]
            new_order[qkey] = ordered + sorted(extras)
        order = new_order

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / 'options.json').write_text(json.dumps(options, indent=2, ensure_ascii=False), encoding='utf-8')
    (DATA_DIR / 'rules.json').write_text(json.dumps(rules, indent=2, ensure_ascii=False), encoding='utf-8')
    (DATA_DIR / 'option_order.json').write_text(json.dumps(order, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f"\nWrote:")
    print(f"  data/options.json")
    print(f"  data/rules.json")
    print(f"  data/option_order.json (preserved hand-ordered codes; new codes appended)")
    print(f"\nNext: run `python3 build.py` to rebuild index.html.")


if __name__ == '__main__':
    main()
