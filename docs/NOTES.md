# Orion Base System Configurator — local dev bundle

Source for the configurator that ships at `index.html`. This bundle is structured for hand-editing and Claude Code workflows.

## Layout

```
.
├── README.md             — this file
├── CLAUDE.md             — context for Claude Code
├── build.py              — assembles index.html from src/ + data/
├── index.html            — built output (regenerate with build.py)
├── src/
│   └── template.html     — HTML/CSS/JS template; data is injected at build time
├── data/
│   ├── questions.json    — 13 question definitions (titles, icons, folder mapping)
│   ├── options.json      — option codes and labels for each question
│   ├── option_order.json — display order for options within each question
│   ├── rules.json        — dependency rules between questions (sparse, auto-extracted)
│   ├── images.json       — image inventory (auto-generated from images/)
│   ├── help.json         — "More info" panel text per question (hand-edited)
│   └── blurbs.json       — short blurb under each option title (hand-edited)
├── images/               — option imagery, organised by numbered folder
│   ├── 01-process/  02-material/  03-reach/  04-amperage/  05-cooling/
│   ├── 06-conduit/  07-fume/  08-wire/  09-touch/  10-tables/  11-guarding/
├── docs/
│   └── dev-journal/      — design decision records
└── scripts/
    ├── extract_from_xlsx.py   — re-import options/rules from a new spreadsheet
    └── index_images.py        — rescan images/ and rebuild data/images.json
```

## Quick start

```bash
# Build once
python3 build.py

# Build + serve at http://localhost:8000
python3 build.py --serve

# Build on every change to data/ or src/
python3 build.py --watch
```

The `--serve` and `--watch` modes are mutually exclusive — for a serve-and-watch workflow, run `--watch` in one terminal and `python3 -m http.server 8000` in another.

Only requirement is Python 3.8+ for build/serve. The xlsx extractor needs `pandas` and `openpyxl`:

```bash
pip install pandas openpyxl
```

## Editing content

Most edits are JSON files under `data/`:

- **Wording on option cards** → `data/blurbs.json`
- **"More info" panel text** → `data/help.json`
- **Question titles, subtitles, icons** → `data/questions.json`
- **Option labels (e.g. "MIG", "Mild Steel")** → `data/options.json`
- **Option display order** → `data/option_order.json`

After editing JSON, run `python3 build.py` (or have `--watch` running). The rebuilt `index.html` is what you deploy.

For visual / layout / behaviour changes, edit `src/template.html` directly. Everything except the embedded `DATA` constant is hand-written there. Build will preserve your changes and only swap the `DATA` block.

## Refreshing from a new spreadsheet

When a new version of the BSC spreadsheet ships:

```bash
python3 scripts/extract_from_xlsx.py path/to/System_Configurator_V16.xlsx
python3 build.py
```

The extractor preserves your hand-edited `blurbs.json`, `help.json`, and `questions.json`. It also preserves manual ordering of options in `option_order.json` — any new codes are appended in sorted order, and you can re-rearrange them later by editing the JSON.

If the spreadsheet's column layout changes (rare), update `QUESTION_COLS` at the top of `scripts/extract_from_xlsx.py`.

## Adding or removing images

1. Drop new images into the matching `images/NN-name/` folder (e.g. `images/02-material/`).
2. Filename must follow `<3-digit-option-code><2-digit-sequence>.<ext>`, e.g. `15108.jpg` for material 151 image #8.
3. Run `python3 scripts/index_images.py` to rebuild the image inventory.
4. Run `python3 build.py` to regenerate `index.html`.

For images that should appear on every option in a question (like the touch sense diagram), use any filename that doesn't match the 5-digit pattern — it'll be filed under `_generic` and shown across all that question's option cards.

## Adding a new question

This is more involved because questions are sequential and identified by hard-coded keys throughout the codebase. Steps:

1. Add a new entry to `data/questions.json` with a unique `key`, a `folder` like `NN-name` matching the question number, a code prefix in the same hundreds range as your option codes, and decide whether to add an image folder.
2. Add the question's options to `data/options.json` and a sensible order to `data/option_order.json`.
3. Add help text to `data/help.json` and option blurbs to `data/blurbs.json`.
4. Add a (possibly empty) entry for the new question key in `data/rules.json`.
5. Update the `selOrder` arrays, `CODE_MAP`, and `SPEC_GROUPS` inside the JS in `src/template.html` to include the new question.
6. If the new question depends on others, add rules to `data/rules.json` describing valid combinations.
7. Build and test.

If you're refactoring the spreadsheet at the same time, redo `QUESTION_COLS` in `scripts/extract_from_xlsx.py` to match the new layout.

## Deployment

The app is hosted on GitHub Pages and embedded in the Squarespace site via an `<iframe>`. GitHub Actions builds `index.html` and deploys it — along with `images/` — to the `gh-pages` branch on every push to `main`. You never deploy manually.

```
main branch  (source — what you edit)
  ├── src/template.html
  ├── data/*.json
  ├── images/               ← committed here
  └── .github/workflows/deploy.yml

gh-pages branch  (auto-built by CI — do not edit)
  ├── index.html            ← built by workflow
  └── images/               ← copied by workflow
```

### First-time setup

**1. Create the GitHub repository**

```bash
git init
git add .
git commit -m "Initial commit"
# Create an empty repo on github.com, then:
git remote add origin https://github.com/cakelesscoder/Base-System-Configurator.git
git branch -M main
git push -u origin main
```

**2. Enable GitHub Pages**

In the repository on GitHub: Settings → Pages → Source: Deploy from a branch → Branch: `gh-pages` / `/ (root)` → Save.

The `gh-pages` branch doesn't exist yet — it's created automatically by the first workflow run.

**3. Fill in your URLs**

In `.github/workflows/deploy.yml`, on the build step, replace:
```
https://cakelesscoder.github.io/Base-System-Configurator/images
```
with your actual URL, e.g. `https://orionau.github.io/orion-bsc/images`.

In `deploy/squarespace-embed.html`, replace `USERNAME` and `REPO` in both the `src` attribute and the `ALLOWED_ORIGIN` variable.

**4. Push to trigger the first deploy**

```bash
git add .github/workflows/deploy.yml deploy/squarespace-embed.html
git commit -m "Configure GitHub Pages URLs"
git push
```

Watch the Actions tab — the workflow should pass in ~30–60 seconds. Then visit `https://cakelesscoder.github.io/Base-System-Configurator/` to verify the configurator loads with images.

**5. Add the embed to Squarespace**

Open `deploy/squarespace-embed.html`, copy its entire contents, paste into a Squarespace Code Block on the desired page, and save.

### Ongoing update workflow

```bash
# Edit data/*.json or src/template.html
python3 build.py --serve    # optional local preview

git add <changed files>
git commit -m "Describe what changed"
git push                    # GitHub Actions builds and deploys automatically
```

GitHub Actions deploys within ~30 seconds of the push. The Squarespace embed picks up the new version on the next page load — no changes needed in Squarespace.

**After adding images:**

```bash
python3 scripts/index_images.py    # rebuilds data/images.json
python3 build.py                   # verify locally
git add images/ data/images.json
git commit -m "Add images for ..."
git push
```

### Netlify (alternative to GitHub Pages)

1. Connect the `main` branch to a Netlify site.
2. Build command: `python3 build.py --image-base https://YOUR-SITE.netlify.app/images`
3. Publish directory: `.` (Netlify serves `index.html` and `images/` from the repo root).
4. Update `deploy/squarespace-embed.html` with your Netlify URL.

## Troubleshooting

**Images not showing in the built page** — check `IMAGE_BASE` near the top of the `<script>` block in `src/template.html`. For local testing, leave it empty. For iframe-embedded production deploys, set it to the absolute URL of your `images/` folder.

**Validation errors on build** — the build script checks that every option in `options.json` is listed in `option_order.json` and vice versa. Add or remove codes to align them, then rebuild.

**An option always shows "Not available"** — your selection chain doesn't match any rule for that option. Either add a covering rule to `data/rules.json` or remove the rule for that option entirely (which makes the option permissive — see `getValidOptions()` in `src/template.html`).

**Spreadsheet rule gaps** — three questions ship with sparse rules in V15: guarding (only 651), install (only 702), training (only 752). The configurator detects this and treats those questions as fully permissive. If you want them to actually filter, add rule rows to the source spreadsheet covering each option, then re-extract.
