#!/usr/bin/env python3
"""
Export all user-facing text to a CSV spreadsheet for editorial review.

Columns: Section | ID | Existing wording | New wording (pre-filled)

Run from repo root: python scripts/export_wording.py
Output: wording_review.csv
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
DATA = ROOT / 'data'
OUT  = ROOT / 'wording_review.csv'

rows = []

def add(section, key, text):
    rows.append((section, key, text, text))

# ── Hardcoded UI text ──────────────────────────────────────────────────────
add('Welcome page', 'welcome.eyebrow',        'Robotic welding cell · welding cell')
add('Welcome page', 'welcome.h1',             'Configure your robotic welding cell')
add('Welcome page', 'welcome.body',
    'Walk through 10 design decisions and we\'ll generate a complete specification for your Panasonic robot system, especially designed for welding. Built around our Australian made, internally designed fabricated platform - proven, fast to deploy, simple to relocate in future, and engineered for Australian and New Zealand fabricators.')
add('Welcome page', 'welcome.stat_steps',     '10 Steps')
add('Welcome page', 'welcome.stat_minutes',   '~4 Minutes')
add('Welcome page', 'welcome.btn_start',      'Get started →')

add('Header / nav',  'nav.app_name',           'Welding Cell Configurator')
add('Header / nav',  'nav.restart_btn',        '↻ Start over')

add('Question pages', 'q.info_toggle_open',   'More info')
add('Question pages', 'q.info_toggle_close',  'Hide info')
add('Question pages', 'q.btn_back',           '← Back')
add('Question pages', 'q.btn_continue',       'Continue →')
add('Question pages', 'q.btn_review',         'Review →')
add('Question pages', 'q.unavailable_badge',  'Not available')
add('Question pages', 'q.photos_btn',         '📷 See all {n} photos')

add('Summary page', 'summary.eyebrow',        'Configuration complete')
add('Summary page', 'summary.h1',             'Your welding cell specification')
add('Summary page', 'summary.subtitle',       'Share this with our team to receive a detailed proposal.')
add('Summary page', 'summary.code_label',     'Config')
add('Summary page', 'summary.btn_copy',       'Copy')
add('Summary page', 'summary.btn_email',      'Email for quote')
add('Summary page', 'summary.btn_edit',       '← Edit answers')
add('Summary page', 'summary.btn_share',      'Share link')
add('Summary page', 'summary.btn_print',      'Print')
add('Summary page', 'summary.btn_restart',    'Start over')
add('Summary page', 'summary.training_note',
    'On-site training included for all new customers - Orion will commission your cell at your facility and train your operators on-site.')
add('Summary page', 'summary.start_over_confirm',
    'Start over? Your current configuration will be cleared.')

# ── Questions (title / subtitle / short label) ─────────────────────────────
questions = json.loads((DATA / 'questions.json').read_text(encoding='utf-8'))
for q in questions:
    k = q['key']
    add('Question titles',    f'q.{k}.title',    q['title'])
    add('Question subtitles', f'q.{k}.subtitle', q['subtitle'])
    add('Question labels',    f'q.{k}.short',    q['short'])

# ── Option labels ──────────────────────────────────────────────────────────
options = json.loads((DATA / 'options.json').read_text(encoding='utf-8'))
for qkey, opts in options.items():
    for code, label in opts.items():
        add('Option labels', f'option.{code}.label', label)

# ── Option blurbs ──────────────────────────────────────────────────────────
blurbs = json.loads((DATA / 'blurbs.json').read_text(encoding='utf-8'))
for code, blurb in blurbs.items():
    if blurb:
        add('Option blurbs', f'option.{code}.blurb', blurb)

# ── Help text ──────────────────────────────────────────────────────────────
help_data = json.loads((DATA / 'help.json').read_text(encoding='utf-8'))
for qkey, text in help_data.items():
    if text:
        add('Help text', f'help.{qkey}', text)

# ── Write CSV ──────────────────────────────────────────────────────────────
with open(OUT, 'w', newline='', encoding='utf-8-sig') as f:  # utf-8-sig = BOM for Excel
    w = csv.writer(f)
    w.writerow(['Section', 'ID', 'Existing wording', 'New wording'])
    w.writerows(rows)

print(f"Written {len(rows)} rows to {OUT.relative_to(ROOT)}")
