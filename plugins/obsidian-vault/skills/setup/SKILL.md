---
name: setup
description: First-time setup of the user's Obsidian vault. Asks a few questions, creates or adopts the vault folder, writes its CLAUDE.md, index.md and templates, and saves ~/.claude/obsidian-vault.json so the capture and lint skills know where the vault is. Use when the user says "set up my vault", "set up Obsidian", "/setup", or when capture or lint report that ~/.claude/obsidian-vault.json is missing. Also use to change the answers later ("rename me", "change my note language", "move my vault").
---

# setup

Sets up one Obsidian vault for the `capture` and `lint` skills. The user may not be technical. Use plain words, keep each message short, and never show them shell commands or JSON.

## 1. Check what's already there

- If `~/.claude/obsidian-vault.json` exists, read it. Say what is set up, then ask what they want to change. Change only that, then go to step 5.
- If `/Applications/Obsidian.app` is missing, tell them to download Obsidian from https://obsidian.md before they open the vault. Setup can continue without it.

## 2. Ask the questions

Use AskUserQuestion. Ask all four in one call:

1. **Name**: "What should I call you?" Offer two plausible options; they will type their own under "Other".
2. **Language**: "Which language should your notes be written in?" Options: English, Thai, both (Thai notes with English headings).
3. **Uses** (multiSelect): "What will you keep notes about?" Options: cooking and recipes, health and family, travel and places, books and learning. Their own topics come in under "Other".
4. **Location**: "Where should your vault live?"
   - "Documents (Recommended)": `~/Documents/Obsidian Vault`
   - "Google Drive": look for `~/Library/CloudStorage/GoogleDrive-*/My Drive/` and use `Obsidian Vault` inside it. If none is found, say so and fall back to Documents.
   - "I already have a vault": ask for the folder. The user can drag it from Finder into the chat to paste its path.

## 3. Build the vault

Templates live in `vault-template/`, next to this file.

1. Create the vault folder if missing, then the folders `10 Sessions`, `20 Projects`, `30 Learning/Articles`, `30 Learning/Books`, `30 Learning/Courses`, `40 Knowledge`, `50 Areas`, `60 Resources`, `70 Archive`. The skills depend on these exact names, so don't translate or rename them.
2. Copy `vault-template/Templates/` into the vault. **Never overwrite a file that already exists.**
3. Write `CLAUDE.md` from `vault-template/CLAUDE.md`, filling `{{NAME}}`, `{{LANGUAGE}}`, `{{VAULT}}` and `{{USES}}`. `{{USES}}` is a short bullet list of their chosen topics, each with the folder it files to:
   - A topic that never ends (health, family, cooking, the garden) → an area in `50 Areas/`.
   - Something with a finish line (a trip, a renovation) → a project in `20 Projects/`.
   - Books → `30 Learning/Books/`.
   If the vault already has a `CLAUDE.md`, don't overwrite it. Show the differences and ask first.
4. Write `index.md` from `vault-template/index.md` if missing, filling `{{DATE}}`.
5. Create one starter note in `50 Areas/` for each ongoing topic they picked (for example `50 Areas/Recipes.md`). Use frontmatter `date` and `tags`, a one-line purpose, and nothing else. Add each one to `index.md` under Areas. Skip any that already exist.

If the vault sits in Google Drive, tell them to right-click the vault folder in Finder and choose **Available offline**. Otherwise Claude may not see notes that haven't been downloaded yet.

## 4. Save the config

Write `~/.claude/obsidian-vault.json`:

```json
{ "vault": "<absolute vault path>", "name": "<name>", "language": "<language>" }
```

## 5. Point every session at the vault

Ensure `~/.claude/CLAUDE.md` contains this block, with the placeholders filled. Replace an existing block between the same markers, and append it if there is none. **Keep everything else in that file.**

```
<!-- obsidian-vault:start -->
## My Obsidian vault
My notes live in an Obsidian vault at `<vault path>`. When I say "my vault", "my notes" or ask to look something up, search there, reading its `index.md` first. When something worth keeping comes up, or I say "save this" or "remember this", use the `capture` skill. "Check my vault" means the `lint` skill. Call me <name> and write notes in <language>.
<!-- obsidian-vault:end -->
```

## 6. Finish

In three or four short lines, tell them:
- where the vault is, and how to open it: open Obsidian, choose "Open folder as vault", and pick that folder.
- how to use it: talk normally and say "save this" when something is worth keeping. Any URL or PDF they share gets filed too.
- that "check my vault" looks for problems.

Then offer to save a first note together.
