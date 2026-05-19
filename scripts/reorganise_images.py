#!/usr/bin/env python3
"""
Reorganise images/ from flat per-step folders into per-option subfolders.

Before: images/02-material/15101.jpg
After:  images/02-material/151-mild-steel/15101.jpg

Also updates data/images.json so the stored filenames include the subfolder prefix.
Run from the repo root: python scripts/reorganise_images.py
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = ROOT / 'data'
IMAGES_DIR = ROOT / 'images'

# ---------------------------------------------------------------------------
# Subfolder names for every option code.
# Format: <code>-<slug> — readable and still tied to the code.
# ---------------------------------------------------------------------------
SUBFOLDERS = {
    # process
    '101': '101-mig',
    '102': '102-tig',
    # material
    '151': '151-mild-steel',
    '152': '152-stainless-steel',
    '153': '153-aluminium',
    '154': '154-galvanised-steel',
    '155': '155-titanium',
    '156': '156-hard-facing',
    # reach
    '201': '201-tm1400',
    '202': '202-tm1800',
    '203': '203-tm2000',
    '204': '204-tl1800',
    '205': '205-tl2000',
    # amperage
    '251': '251-350amp',
    '252': '252-500amp',
    # cooling
    '301': '301-gas-cooled',
    '302': '302-water-cooled',
    # conduit (kept for when it returns)
    '351': '351-separate',
    '352': '352-through-arm',
    '353': '353-external',
    # fume
    '401': '401-fume-extraction',
    '402': '402-no-fume-extraction',
    # wire
    '451': '451-wire-reel',
    '452': '452-wire-reel-cover',
    '453': '453-drum-pack',
    # tables
    '551': '551-1x-table',
    '552': '552-2x-tables',
    # guarding
    '651': '651-full-1t-panel-on-frame',
    '652': '652-full-1t-two-walls',
    '653': '653-full-2t-panel-on-frame',
    '654': '654-full-2t-two-walls',
    '655': '655-curtain-1t',
    '656': '656-curtain-2t',
    # touch generic stays as-is
    '_generic': '_generic',
}

def slugify(name: str) -> str:
    """Lowercase, strip special chars, collapse spaces/hyphens."""
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')


def main():
    images_json_path = DATA_DIR / 'images.json'
    with open(images_json_path, 'r', encoding='utf-8') as f:
        images = json.load(f)

    updated_images = {}
    moved, skipped, missing = 0, 0, 0

    for qkey, by_code in images.items():
        q_folder = next(
            (p for p in IMAGES_DIR.iterdir() if p.is_dir() and p.name.endswith(f'-{qkey}')),
            None
        )
        updated_images[qkey] = {}

        for code, filenames in by_code.items():
            subfolder_name = SUBFOLDERS.get(code)
            if not subfolder_name:
                print(f"  [warn] no subfolder mapping for code '{code}' in {qkey}, skipping")
                updated_images[qkey][code] = filenames
                skipped += len(filenames)
                continue

            new_filenames = []
            for fname in filenames:
                if not q_folder:
                    print(f"  [warn] no image folder found for qkey '{qkey}'")
                    new_filenames.append(fname)
                    skipped += 1
                    continue

                src = q_folder / fname
                dst_dir = q_folder / subfolder_name
                dst = dst_dir / fname

                # Already moved
                if dst.exists() and not src.exists():
                    new_filenames.append(f'{subfolder_name}/{fname}')
                    skipped += 1
                    continue

                if not src.exists():
                    print(f"  [missing] {src.relative_to(ROOT)}")
                    new_filenames.append(f'{subfolder_name}/{fname}')
                    missing += 1
                    continue

                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                new_filenames.append(f'{subfolder_name}/{fname}')
                moved += 1

            updated_images[qkey][code] = new_filenames

    # Write updated images.json
    with open(images_json_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(updated_images, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print(f"\nDone. Moved: {moved}  Already done/skipped: {skipped}  Missing src: {missing}")
    print(f"Updated {images_json_path.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
