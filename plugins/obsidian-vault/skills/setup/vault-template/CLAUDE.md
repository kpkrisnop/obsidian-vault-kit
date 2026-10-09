# Claude — {{NAME}}'s Obsidian Vault

How {{NAME}}'s vault is organised, and how notes get into it. The `capture` skill follows these rules. The `lint` skill checks them.

Vault path: `{{VAULT}}`

Write notes in **{{LANGUAGE}}**. Folder names, frontmatter keys and tags stay in English, because the skills depend on them.

## What {{NAME}} keeps notes about

{{USES}}

## Where notes go

Walk this list in order and use the first folder that fits.

1. **Session note** → `10 Sessions/YYMMDD-HHMM.md`. One rolling note per conversation, created at the first capture.
2. About a **project**, meaning something with a finish line (a trip, a renovation, an event) → `20 Projects/<Project Name>/`. Each project gets one folder, with an index note named the same as the folder.
3. A **cleaned copy of a web page or PDF** {{NAME}} shared → `30 Learning/Articles/`. Never edited after it's saved.
4. A **book or course** note → `30 Learning/Books/` or `30 Learning/Courses/`.
5. An **idea or piece of know-how** in {{NAME}}'s own words, meant to stay true over time → `40 Knowledge/`.
6. An **ongoing part of life** with no end date (health, family, cooking, the garden) → `50 Areas/`.
7. A **reference document**, such as a manual, a spec or contact details → `60 Resources/`.
8. **Finished or no longer active** → `70 Archive/`.

`Templates/` holds note templates and never real notes. `index.md` is the catalog of every note.

## Session notes

- Created at the first capture of a conversation and named for when the conversation **started**.
- Updated as the conversation goes: each capture adds a line to "Topics touched", and anything left unresolved goes under "Loose ends".
- The "Summary" paragraph is rewritten every five captures or so.

## `index.md`

- Lists every note except session notes, grouped by folder. Each entry is a wikilink plus a one-line summary.
- Updated on every new or substantially changed note.
- **Read it first** when answering a question from the notes.

## Rules (load-bearing)

1. **Only link notes that are really related.** Two notes that came up in the same conversation are not related for that reason alone.
2. **Never duplicate.** If a note on the topic exists, update it.
3. **Search before answering.** When {{NAME}} names a topic, search the vault first.
4. **Write, then report.** Save the note without asking, then tell {{NAME}} what was written. They correct it afterwards if needed.
5. **Saved web pages and PDFs are never edited.** Notes about them are.
6. **No new top-level folders** without asking {{NAME}} first.

## Conventions

- Every note has frontmatter with at least `date` and `tags`.
- Tags are lowercase and hyphenated, like `recipe` or `blood-pressure`.
- Cross-references use wikilinks: `[[Note Name]]`.
