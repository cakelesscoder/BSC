# 001 — Compact Config Code & Summary Layout Redesign

**Date:** 2026-05-07
**Status:** In progress
**Author:** Claude Code (AI-assisted development session with Lachlan)

## Problem

The configurator's final summary screen had two issues:

1. **The config code was unwieldy.** A 55-character hyphenated string of 3-digit codes (`101-151-201-251-301-351-401-451-501-551-601-651-701-751`) that broke awkwardly on smaller screens and was hard to read, copy, or communicate verbally. This code is the primary handoff artifact — customers send it to Orion, where an internal tool will eventually decode it into a costed proposal.

2. **The layout was visually heavy.** A large dark box (18px bold, heavy padding) for the code, followed by a 13-cell grid that duplicated information, followed by action buttons. Too much vertical space, too much visual noise for a technical audience that values density.

## Design Decision: Compact Code Format

Each of the 13 configuration questions maps to **a single character** — a meaningful letter or digit. Questions are grouped into 5 logical sections separated by hyphens.

**Format:** `{Process}{Material}{Reach}-{Power}{Cooling}{Conduit}-{Fume}{Wire}{Touch}-{Tables}{Jigs}-{Guard}{Install}{Training}`

**Example:** `MC3-5GS-NRY-21-4OO` = MIG, Carbon steel, TM2000, 500A, Gas cooled, Separate conduit, No fume extraction, Wire reel, Touch sensing yes, 2 tables, 1 jig frame, Guarding option 4, Orion install, Orion training.

### Full Character Map

| Position | Question | Values |
|----------|----------|--------|
| 1 | Process | `M` = MIG, `T` = TIG |
| 2 | Material | `C` = Carbon/Mild Steel, `S` = Stainless, `A` = Aluminium, `G` = Galvanised, `T` = Titanium |
| 3 | Reach | `1` = TM1400, `2` = TM1800, `3` = TM2000, `4` = TL1800, `5` = TL2000 |
| — | *hyphen* | |
| 4 | Power | `3` = 350A, `5` = 500A |
| 5 | Cooling | `G` = Gas, `W` = Water |
| 6 | Conduit | `S` = Separate, `T` = Through Arm, `E` = External |
| — | *hyphen* | |
| 7 | Fume | `F` = With Extraction, `N` = No Extraction |
| 8 | Wire | `R` = Reel, `C` = Covered Reel, `D` = Drum Pack |
| 9 | Touch | `Y` = Yes, `N` = No |
| — | *hyphen* | |
| 10 | Tables | `1` = 1 Table, `2` = 2 Tables |
| — | *hyphen* | |
| 11 | Guarding | `1`–`6` (positional, matching option_order 651–656) |
| 12 | Install | `C` = Customer, `O` = Orion |
| 13 | Training | `V` = Orion VIC, `S` = Customer Site, `N` = None |

> **Note (2026-05-07):** Jigs (Q11) was removed. The spreadsheet data was poorly structured — labels included stray "nan" from empty cells, the wording "Jig Table Frame" conflated it with the Tables question, there were no images, and rules were inconsistently filled. Will be re-added when proper source data is available.

### Why This Encoding

- **Mnemonics where possible** — `M` for MIG, `G` for Gas, `W` for Water. Easier to eyeball than positional digits.
- **Digits for ordered/numeric choices** — Reach (1–5 maps to ascending model sizes), Power (3/5 maps to 350/500), Guarding (6 options, letters would be arbitrary).
- **Hyphens at semantic boundaries** — the 5 groups match how a welding engineer thinks about a cell: the robot, the power system, consumables, workholding, and deployment.
- **Round-trip decodable** — trivial to reverse for the future internal proposal tool. The `CODE_MAP` constant serves both directions.

## Design Decision: Summary Layout

Replace the monolithic dark box + 13-cell grid with:

1. **Compact code bar** — single-line flex row: small-caps label, monospace code, copy button. Slim padding, scrollable on narrow screens.
2. **Grouped spec sheet** — 5 labelled sections in a 2-column CSS multi-column layout. Each row shows question name → selected option. No per-cell code numbers (the compact code is the single source).
3. **Tightened action bar** — Email (primary CTA), Print (secondary), Start over (text link, demoted).

## Files Modified

- `src/template.html` — CSS overhaul of summary section, JS rewrite of `renderSummary()`, new `CODE_MAP` constant
- No changes to `build.py` or `data/*.json`

## Verification

- Walk all 14 steps, confirm compact code on summary
- Copy → paste → verify format matches `XX#-#XX-XXX-##-#XX`
- Email → verify body contains compact code + readable spec lines
- Print → verify clean 2-column output
- Narrow viewport → confirm single-column + scrollable code bar
