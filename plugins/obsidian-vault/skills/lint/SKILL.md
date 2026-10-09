---
name: lint
description: Use to health-check the user's Obsidian vault. Triggers on "lint", "health-check the vault", "/lint", "check vault health", "is the vault healthy", "scan for broken links", "find orphan notes", or any request to audit the vault for problems. Read-only scan for broken wikilinks, orphan notes, `index.md` drift, missing concept pages, stale claims, frontmatter gaps, and possible contradictions. Reports findings — never writes. Pair with the `capture` skill to act on findings.
---

# lint

Read-only vault health check for the user's Obsidian vault. **Never writes.** Only reports.

If the user wants fixes, they invoke the `capture` skill for individual items afterward.

## Vault root

The script reads the vault path from `~/.claude/obsidian-vault.json`, written by the `setup` skill. It runs from any working directory. If the config is missing, run `setup` first.

## When to run

The user says: "lint", "health-check the vault", "/lint", "check vault health", or similar.

## How to run

```
python3 "<this skill's base directory>/lint.py"
```

That script is the canonical implementation — it does every check below. When a check needs to be refined or a new one added, edit `lint.py` directly (not this doc), then update the corresponding check description here. The script and this skill must stay in sync.

## Checks

### 1. Broken wikilinks
Extract all `[[...]]` references *outside fenced code blocks and inline code spans* (so example wikilinks in schema docs aren't false positives). Verify each resolves using Obsidian's rules: filename match first, path match second. Report any that don't resolve.

### 2. Orphan notes
For each note in `40 Knowledge/`, `60 Resources/`, `30 Learning/Articles/`: check whether it has any inbound *or* outbound wikilinks. Report notes with zero links.

**Exempt:** templates, session notes, project index notes, `index.md`, `CLAUDE.md`.

### 3. `index.md` drift
- Files in `40 Knowledge/`, `60 Resources/`, `30 Learning/{Articles,Books,Courses}/`, `20 Projects/`, `50 Areas/` not listed in `index.md`.
- Entries in `index.md` whose target file no longer exists.

### 4. Missing concept pages
Scan notes for repeated capitalized terms or hyphenated phrases that appear in 3+ notes but lack their own page in `40 Knowledge/`. Propose candidates — don't claim certainty.

### 5. Contradictions
Compare notes that share tags or topics. Look for explicit factual conflicts (e.g., one note says "max 5V", another says "max 7V" for the same component). Report pairs to review.

### 6. Stale claims
Look for year references older than (current year − 2) that are *not* embedded in a longer numeric token and *not* in datasheet/revision context (heuristic skip list: "rev", "version", "datasheet", "spec no", "copyright", "©", "isbn", "sourced from", "published", "issued", etc.). Notes tagged `archive` are exempt. Reports the first match per note.

### 7. Frontmatter gaps
Notes missing `date` or `tags`. The parser handles three YAML forms: scalar (`tags: foo`), inline array (`tags: [a, b]`), and multi-line list (`tags:\n  - a\n  - b`). Templates and `index.md` exempt.

## Output format

```
# Vault Lint — YYYY-MM-DD HH:MM

## 🔴 Broken wikilinks (N)
- `path/to/Note A.md` → `[[Missing Note]]`

## 🟠 Orphan notes (N)
- `40 Knowledge/Foo.md` — no links in or out

## 🟡 index.md drift (N)
Missing from index:
- `60 Resources/Hardware/New Component.md`
Stale entries (target missing):
- `[[Old Note]]`

## 🟡 Possible missing concept pages (N)
- "series resistor" — mentioned in 4 notes, no page

## 🟡 Possible contradictions (N)
- `[[L298N Motor Driver]]` says max 46V; `[[Some Other Note]]` says max 50V

## 🟡 Stale claims (N)
- `[[Foo]]` references "as of 2024-…"

## 🟡 Frontmatter gaps (N)
- `40 Knowledge/Bar.md` — missing `tags`
```

Severity legend: 🔴 likely a bug, 🟠 worth investigating, 🟡 informational.

## Anti-fix discipline

This skill does not modify files. If a finding warrants a fix, summarize it for the user and stop. Do not invoke `capture` from within this skill.
