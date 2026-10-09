---
name: capture
description: Use to capture knowledge, ideas, sources, or session loose-ends into the user's Obsidian vault. Triggers on auto-detected conversation conclusions (a fact established, a decision made, a concept clarified, a problem solved), explicit phrases like "capture this", "save this as a note", "/capture", "loose end:", "remember:", "jot this down", "file this under X", when the user drops a URL/PDF/pasted source to ingest, or when a substantive question produces real synthesis worth filing back. Owns capture, ingest, and query-as-artifact paths — all roads from "knowledge in" to a durable note in the vault. Use this skill whenever something durable about a topic emerges in conversation with the user — don't wait for an explicit request.
---

# capture

The front door to the user's Obsidian vault. Three procedures, one skill. Pick by input:

- **Conversation produced durable knowledge** → capture path
- **The user dropped a URL/PDF or pasted source text** → ingest path
- **Substantive question produced real synthesis** → query-as-artifact path

All three end the same: write the note, update `index.md`, append to the session note — then tell the user what was written. **No approval step.** Write first, report after.

## Vault root

Read `~/.claude/obsidian-vault.json` once per session. It holds `vault` (the absolute vault root), `name` (what to call the user) and `language` (the language to write notes in). **If the file is missing, stop and run the `setup` skill first.**

Write every note in the configured `language`, and pass `name` and `language` to both sub-agents.

All paths (`10 Sessions/`, `30 Learning/Articles/`, `index.md`, `CLAUDE.md`, `Templates/`, etc.) are relative to that vault root. Prepend the vault root when invoked from outside the vault directory.

The vault's `CLAUDE.md` is the canonical schema — filing decision tree, note types, folder structure. **Read it once at the start of any capture session** if not already loaded.

---

## Execution model — two-phase sub-agents (load-bearing)

**Never read or write vault files in the main session.** It floods the context window. Every capture uses two foreground sub-agents, run back to back without stopping. The main session only describes what to capture and reports the result to the user afterwards.

### Phase 1 — Research + Stage sub-agent

Dispatched immediately when a capture is triggered.

**Give it:**
- A 2–5 sentence description of the knowledge to capture, drawn from the conversation
- The vault root path
- The staging directory to write into: `/tmp/obsidian-capture-staging/<YYMMDDHHMMSS>/` (Phase 1 picks the timestamp)

**It does (all in its own context):**
1. Searches the vault — grep for filenames and content, reads any relevant existing notes in full
2. Decides: create new note or update existing
3. Picks the correct destination using the filing decision tree in `CLAUDE.md`
4. Drafts full note content (new) or precise changes (update)
5. Saves all drafts + a `plan.json` manifest to the staging directory
6. Returns **only the file plan** to the main session — no draft content

**`plan.json` structure:**
```json
{
  "staging": "/tmp/obsidian-capture-staging/<timestamp>/",
  "files": [
    {
      "action": "create|update",
      "vault_path": "40 Knowledge/My Note.md",
      "staging_file": "note.md",
      "description": "one-line description of the knowledge being written"
    },
    {
      "action": "update",
      "vault_path": "index.md",
      "staging_file": "index-entry.txt",
      "description": "add entry for [[My Note]]"
    },
    {
      "action": "create|update",
      "vault_path": "10 Sessions/YYMMDD-HHMM.md",
      "staging_file": "session-line.txt",
      "description": "append to Topics touched"
    }
  ]
}
```

**Phase 1 returns to main session** (no draft text — only this):
```
Staging: /tmp/obsidian-capture-staging/<timestamp>/

Files:
- [CREATE|UPDATE] <vault_path> — <one-line knowledge description>
- [UPDATE] index.md — add entry for [[Note Title]]
- [UPDATE] 10 Sessions/YYMMDD-HHMM.md — append to Topics touched
```

**Main session does not show this to the user or wait.** It goes straight to Phase 2.

### Phase 2 — Write sub-agent

Dispatched immediately after Phase 1 returns.

**Give it:**
- The vault root path
- The staging directory path (from the Phase 1 return)

**It does:**
1. Reads `plan.json` from the staging directory
2. For each file in the plan:
   - `create`: write the staged content to the vault path (create parent dirs if needed)
   - `update` (main note): read the existing vault file, apply the staged changes, write it back
   - `update` (index.md): read `index.md`, add or replace the entry, write it back
   - `create|update` (session note): read it (create from template if missing — see Session note setup), append the staged line under `## Topics touched`, write it back
3. Returns: `"Done. N files written: <list of vault paths>."`

**Main session reports to the user** — what was written, where, in one or two lines. Example:

```
Captured: 40 Knowledge/PCA9685 Clock Drift.md (new) — servo driver runs ~3% fast, calibration constant lives in firmware.
Also updated index.md and 10 Sessions/260803-1325.md.
```

If the user disagrees with the result, fix it in a follow-up turn — the note already exists, so that's an edit, not a re-run.

### Phase 1 prompt template

```
You are a vault-research-and-stage agent for the user's Obsidian vault.

VAULT ROOT: [vault path from ~/.claude/obsidian-vault.json]
USER: [name]. Write all note text in [language]. Keep folder names, frontmatter keys and tags in English.

KNOWLEDGE TO CAPTURE:
[2–5 sentence description of what was established in the conversation]

STAGING DIRECTORY: /tmp/obsidian-capture-staging/[YYMMDDHHMMSS]/
Create this directory before writing to it.

YOUR TASKS:
1. Search the vault for existing notes on this topic (grep filenames and content; read relevant notes in full).
2. Check CLAUDE.md for the filing decision tree and note-type templates.
3. Decide: create new note or update existing? Pick the correct vault destination.
4. Draft the full note content (new) or the precise changes to apply (update). Use the user's own framing — not generic AI prose. Wikilink only notes with an explicit conceptual relationship.
   **If the knowledge came from a file, folder, or project that lives outside the vault, record its absolute path in the frontmatter** — `source_folder:` for the directory, `source:` for the specific file. the user deliberately keeps projects and materials elsewhere in the filesystem; the note is the pointer back to them. Without it the original is unfindable from the vault.
5. Save staged files to the staging directory:
   - Main note draft → staging_file named "note.md" (or "note-changes.md" for updates — describe changes precisely, not vaguely)
   - index.md entry line → "index-entry.txt"
   - Session note append line → "session-line.txt" (format: "- [[Note Title]] — created/updated: <1-line>")
6. Write plan.json to the staging directory (schema above).
7. Return ONLY the file plan (staging path + file list with descriptions). No draft content in the return.

Do NOT write anything to the vault. Only write to the staging directory.
```

### Phase 2 prompt template

```
You are a vault-write agent for the user's Obsidian vault.

VAULT ROOT: [vault path from ~/.claude/obsidian-vault.json]
STAGING DIRECTORY: [path returned by Phase 1]

Read plan.json from the staging directory. Execute each entry:
- action "create": write the staged file content to vault_path (create any missing parent dirs).
- action "update" (main note): read the existing vault file, apply the changes described in the staging file, write it back.
- action "update" (index.md): read index.md, add or replace the entry line from index-entry.txt in the correct section, write it back.
- action "create|update" (session note): if it exists, read it and append the line from session-line.txt under "## Topics touched". If it does not exist, create it using the Session Note template structure (frontmatter with date/time/tags/topics fields, then ## Summary, ## Topics touched, ## Loose ends sections) and add the append line. Write it back.

Return: "Done. [N] files written: [list of vault_paths]."
```

---

## Triggers (auto and explicit are equal-priority)

| Trigger | Path | Notes |
|---------|------|-------|
| *(detected)* topic in conversation concluded with something durable | capture | Default auto behavior |
| `capture this: …`, `save this as a note: …`, `/capture` | capture | Skip "detect" — go straight to Phase 1 |
| `loose end: …`, `note for later: …`, `remember: …` | session-note-only | Append the verbatim text as a bullet under the current session note's "Loose ends." No sub-agents — dispatch Phase 2 only with a single session-note append operation. |
| `process this article: …` + URL/PDF | ingest | Fetch + clean + derive wiki note |
| `process this conversation: …` / `process this transcript: …` + pasted text | ingest | Treat pasted text as the raw source; save to `30 Learning/Articles/` with `source: pasted` in frontmatter, then derive wiki note |
| the user asks a substantive question; worked answer produced real synthesis | query-as-artifact | Propose filing the answer back as a note |

---

## Session note setup

Session note filename: `YYMMDD-HHMM.md` using the session's *start* time (not now). Phase 1 derives this from context or asks the main session. Phase 2 creates the file if missing, using `Templates/Session Note.md` structure.

Every capture appends to "Topics touched." Topic shifts may add to "Loose ends." Regenerate Summary every ~5 captures — this is Phase 1's responsibility to flag in its return if it detects the threshold has been crossed.

---

## Capture path (conversation-driven)

1. **Detect.** Is there a conclusion worth keeping?
   - A decision was made.
   - A fact was established that the user would want again.
   - A concept got defined or clarified.
   - A problem got diagnosed or solved.

   If it was just chat, don't capture. Bias toward fewer, denser notes.

2. **Dispatch Phase 1 sub-agent.** Fill the Phase 1 prompt template with a clear description of the knowledge from the conversation. Run foreground.

3. **Dispatch Phase 2 sub-agent** with the staging path. Run foreground. No pause, no approval.

4. **Tell the user what was written** — path, new/updated, one-line summary.

---

## Ingest path (source-driven)

When the user shares a URL, drops a PDF, or pastes source text:

1. **Acquire the source** in the main session (minimal — just enough to brief Phase 1):
   - URL → pass the URL to Phase 1; Phase 1 fetches it with WebFetch in its own context.
   - PDF → pass the file path to Phase 1.
   - Pasted text → pass the text directly in the Phase 1 brief.

2. **Dispatch Phase 1 sub-agent.** Brief it with:
   - The source (URL / path / text)
   - Note that the raw source goes to `30 Learning/Articles/<title>.md` (immutable after write)
   - Instruct it to derive wiki note(s), cross-reference scan for contradictions, and stage all writes
   - **The absolute path of any local file or folder**, to be recorded in the derived note's frontmatter (`source_folder:` / `source:`). Local sources stay where the user filed them — the vault never becomes the copy of record for them, so the path is the only way back.

3. **Dispatch Phase 2 sub-agent** with the staging path. Run foreground. No approval step.

4. **Tell the user what was written** — the raw article, the derived wiki note, any related notes updated. Flag any contradictions Phase 1 found.

---

## Query-as-artifact path

When the user asks a substantive question:

1. **Dispatch Phase 1 sub-agent** to read `index.md` and drill into candidate notes. Brief it to answer the question with citations and assess whether the worked answer produced real synthesis.

2. **Phase 1 returns** the answer with `[[wikilinks]]` and, if synthesis was produced, a staged file plan.

3. **If Phase 1 staged a file plan**, dispatch Phase 2 with the staging path. No approval step.

4. **Answer the user's question**, then note in a line what got filed.

---

## Anti-jank rules (load-bearing)

1. **Recency is not a relationship.** Only wikilink notes with an explicit conceptual connection.
2. **Never duplicate.** Phase 1 must search before drafting. Update existing notes; don't create parallels.
3. **Write, then report.** Never ask the user to approve a file plan — Phase 1 and Phase 2 run back to back. The user sees what was written after the fact and corrects it in a follow-up if needed.
4. **Sources immutable.** Files in `30 Learning/Articles/` are not edited after ingest. Edit the derived wiki note instead.
5. **No new top-level folders without the user's consent.**
6. **No `Synthesis` note unless multiple sources actually exist to synthesize.**
7. **Don't capture chat.** Capture conclusions, decisions, facts, definitions — not the conversation itself.

## Red flags — STOP and re-check

| Thought | What to do |
|---------|------------|
| "I'll just create a similar note alongside the existing one" | Phase 1 must search again. Update the existing. |
| "These two notes both came up today, let me link them" | No. Recency is not a relationship. Drop it. |
| "I'll create a new folder for this" | Stop. Ask the user first. |
| "Same fact belongs in both notes" | One is the canonical home. Pick. The other can wikilink to it. |
| "Let me update this Article in `30 Learning/Articles/`" | Stop. Articles are immutable raw. Update the derived wiki note. |
| "I'll write a Synthesis note from this one source" | No. Synthesis requires multiple sources. Use Concept instead. |
| "I'll read the vault file in the main session to understand the existing note" | No. That's Phase 1's job. Brief Phase 1 and let it read. |
| "Let me show the user the plan and ask before writing" | No. Write it, then tell the user what was written. |

## Definition of done

For every capture:

- [ ] Phase 1 sub-agent ran and returned a file plan (staging path + file list with descriptions).
- [ ] Phase 2 sub-agent ran immediately after, and confirmed all files written.
- [ ] the user was told what was written, where, and whether it was new or an update.
- [ ] Note written or updated in the correct folder.
- [ ] Frontmatter has `date` and `tags`.
- [ ] Wikilinks only to actually-related notes.
- [ ] `index.md` entry added or updated.
- [ ] Session note "Topics touched" appended.
- [ ] No vault file reads or writes occurred in the main session.
