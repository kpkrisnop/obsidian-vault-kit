#!/usr/bin/env python3
"""
Vault lint — read-only health check for an Obsidian vault.

Run: python3 lint.py  (vault path comes from ~/.claude/obsidian-vault.json)

This is the canonical implementation referenced by SKILL.md. Refine here when
checks need to be improved.
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path

CONFIG = Path.home() / '.claude' / 'obsidian-vault.json'


EXCLUDE_DIRS = {'.obsidian', '.claude', '.git', 'Templates', '10 Sessions'}
EXCLUDE_FILES = {'index.md', 'CLAUDE.md'}
INDEX_FOLDERS = [
    '40 Knowledge', '60 Resources', '30 Learning/Articles',
    '30 Learning/Books', '30 Learning/Courses', '20 Projects', '50 Areas',
]
ORPHAN_FOLDERS = ['40 Knowledge', '60 Resources', '30 Learning/Articles']

# Datasheet/revision-date context — exempted from stale-claim check.
DATE_CTX_EXEMPT = (
    'rev', 'version', 'datasheet', 'spec no', 'copyright', '©',
    'isbn', 'sourced from', 'official datasheet', 'dated ', 'effective ',
    'published', 'release notes', 'revision', 'issued',
)


def collect_files(vault: Path) -> list[Path]:
    files = []
    for root, dirs, fnames in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        for fn in fnames:
            if fn.endswith('.md') and fn not in EXCLUDE_FILES:
                files.append(Path(root) / fn)
    return files


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter — handles multi-line lists, inline arrays, scalars."""
    if not text.startswith('---'):
        return {}, text
    end = text.find('\n---', 3)
    if end < 0:
        return {}, text
    yaml_text = text[3:end].strip()
    body = text[end + 4:]
    fm = {}
    lines = yaml_text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r'^(\w+):\s*(.*)$', lines[i])
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if not val:
            # Multi-line list following
            items = []
            j = i + 1
            while j < len(lines) and re.match(r'^\s+-\s+', lines[j]):
                items.append(re.sub(r'^\s+-\s+', '', lines[j]).strip())
                j += 1
            fm[key] = items if items else ''
            i = j if items else i + 1
        elif val.startswith('[') and val.endswith(']'):
            fm[key] = [x.strip() for x in val[1:-1].split(',') if x.strip()]
            i += 1
        else:
            fm[key] = val
            i += 1
    return fm, body


def strip_code(text: str) -> str:
    """Remove fenced code blocks and inline code spans so we don't read examples as real content."""
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`\n]+`', '', text)
    return text


WIKILINK_RE = re.compile(r'\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]+?)?\]\]')


def extract_wikilinks(text: str) -> list[str]:
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(strip_code(text))]


def parse(path: Path, vault: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(text)
    return {
        'path': path,
        'rel': str(path.relative_to(vault)),
        'stem': path.stem,
        'fm': fm,
        'body': body,
        'links': extract_wikilinks(text),
        'text': text,
    }


def resolve_link(link: str, by_stem: dict, rel_paths: set) -> bool:
    """Obsidian-style resolution: filename (stem) first, then path."""
    if link in by_stem:
        return True
    if (link + '.md') in rel_paths:
        return True
    return False


YEAR_RE = re.compile(r'(?<![\d-])(20[0-2]\d)(?:-\d{2})?(?![\d-])')


def find_stale_years(text: str, threshold_year: int) -> list[str]:
    """Years < threshold not embedded in longer numbers and not in datasheet/version context."""
    out = []
    cleaned = strip_code(text)
    for m in YEAR_RE.finditer(cleaned):
        year = int(m.group(1))
        if year >= threshold_year:
            continue
        ctx_start = max(0, m.start() - 50)
        ctx_end = min(len(cleaned), m.end() + 50)
        ctx = cleaned[ctx_start:ctx_end].lower()
        if any(k in ctx for k in DATE_CTX_EXEMPT):
            continue
        out.append(m.group(0))
    # dedupe preserving order
    seen = set()
    return [x for x in out if not (x in seen or seen.add(x))]


CONCEPT_RE = re.compile(r'\b[A-Z][a-z]+(?:[\s-][A-Z][a-z]+)+\b')


def concept_candidates(text: str) -> set:
    return set(CONCEPT_RE.findall(strip_code(text)))


def main():
    if not CONFIG.exists():
        print(f"ERROR: no config at {CONFIG}. Run the setup skill first.")
        return 1
    vault = Path(json.loads(CONFIG.read_text())['vault']).expanduser()
    if not vault.exists():
        print(f"ERROR: vault path does not exist: {vault}")
        return 1
    files = collect_files(vault)
    notes = [parse(p, vault) for p in files]
    by_stem = {n['stem']: n['rel'] for n in notes}
    rel_paths = {n['rel'] for n in notes}

    index_path = vault / 'index.md'
    claude_path = vault / 'CLAUDE.md'
    index_text = index_path.read_text(encoding='utf-8') if index_path.exists() else ''
    claude_text = claude_path.read_text(encoding='utf-8') if claude_path.exists() else ''
    index_links = set(extract_wikilinks(index_text))
    claude_links = set(extract_wikilinks(claude_text))

    # 1. Broken wikilinks
    broken = []
    for n in notes:
        for link in n['links']:
            if not resolve_link(link, by_stem, rel_paths):
                broken.append((n['rel'], link))
    for link in index_links:
        if not resolve_link(link, by_stem, rel_paths):
            broken.append(('index.md', link))
    for link in claude_links:
        if not resolve_link(link, by_stem, rel_paths):
            broken.append(('CLAUDE.md', link))

    # 2. Orphans
    referenced = set()
    for n in notes:
        referenced.update(n['links'])
    referenced |= index_links | claude_links
    orphans = [
        n['rel'] for n in notes
        if any(n['rel'].startswith(f) for f in ORPHAN_FOLDERS)
        and not n['links']
        and n['stem'] not in referenced
    ]

    # 3. index.md drift
    should_index = [
        n['rel'] for n in notes
        if any(n['rel'].startswith(f) for f in INDEX_FOLDERS)
        and n['stem'] not in index_links
    ]
    stale_index = [l for l in index_links if not resolve_link(l, by_stem, rel_paths)]

    # 4. Missing concept pages
    term_files = {}
    for n in notes:
        for t in concept_candidates(n['body']):
            term_files.setdefault(t, set()).add(n['stem'])
    existing = set(by_stem.keys())
    missing_concepts = sorted(
        [(t, len(fs)) for t, fs in term_files.items() if len(fs) >= 3 and t not in existing],
        key=lambda x: -x[1],
    )[:10]

    # 5. Contradictions — needs semantic comparison, skipped in v1.
    contradictions = []

    # 6. Stale claims — threshold = 2 years before today, with context exemptions.
    threshold_year = datetime.now().year - 2
    stale = []
    for n in notes:
        tags_str = str(n['fm'].get('tags', '')).lower()
        if 'archive' in tags_str:
            continue
        years = find_stale_years(n['body'], threshold_year)
        if years:
            stale.append((n['rel'], years[0]))

    # 7. Frontmatter gaps
    fm_gaps = []
    for n in notes:
        missing = [k for k in ('date', 'tags') if not n['fm'].get(k)]
        if missing:
            fm_gaps.append((n['rel'], missing))

    # Report
    now = datetime.now()
    print(f"# Vault Lint — {now.strftime('%Y-%m-%d %H:%M')}\n")

    def sect(title, items, fmt):
        print(f"## {title} ({len(items)})")
        if not items:
            print("- (none)")
        else:
            for x in items:
                print(f"- {fmt(x)}")
        print()

    sect("🔴 Broken wikilinks", broken, lambda x: f"`{x[0]}` → `[[{x[1]}]]`")
    sect("🟠 Orphan notes", orphans, lambda x: f"`{x}`")

    print(f"## 🟡 index.md drift ({len(should_index) + len(stale_index)})")
    if should_index:
        print("Missing from index:")
        for x in should_index:
            print(f"- `{x}`")
    if stale_index:
        print("Stale entries (target missing):")
        for x in stale_index:
            print(f"- `[[{x}]]`")
    if not should_index and not stale_index:
        print("- (none)")
    print()

    sect("🟡 Possible missing concept pages", missing_concepts,
         lambda x: f'"{x[0]}" — mentioned in {x[1]} notes')
    sect("🟡 Possible contradictions", contradictions, lambda x: x)
    sect(f"🟡 Stale claims (year < {threshold_year}, body only)", stale,
         lambda x: f"`{x[0]}` — references {x[1]}")
    sect("🟡 Frontmatter gaps", fm_gaps,
         lambda x: f"`{x[0]}` — missing {', '.join(x[1])}")

    print(f"---\nScanned {len(notes)} notes across {len(INDEX_FOLDERS)} folder categories.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
