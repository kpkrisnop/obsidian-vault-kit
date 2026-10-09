# Obsidian Vault Kit

A Claude Code plugin that sets up an Obsidian vault and lets Claude file notes into it.

| Skill | What it does |
|---|---|
| `setup` | Asks a few questions (name, note language, topics, location), builds the vault and points Claude at it |
| `capture` | Files notes as you talk. Say "save this", or share a link or a PDF |
| `lint` | Checks the vault for broken links, notes missing from the index, and similar problems. Read-only |

## Install

Requirements: the Claude Mac app (use the **Code** tab) or the Claude Code CLI, and [Obsidian](https://obsidian.md).

In a Claude Code session, run:

```
/plugin marketplace add kpkrisnop/obsidian-vault-kit
/plugin install obsidian-vault@obsidian-vault-kit
```

Then say **"set up my vault"**.

A local folder path also works in place of `kpkrisnop/obsidian-vault-kit`.

## Where things live

- `~/.claude/obsidian-vault.json` holds the vault path, the user's name and the note language.
- A marked block in `~/.claude/CLAUDE.md` tells every session where the vault is.
- `<vault>/CLAUDE.md` holds the filing rules, personalised by `setup`.

To change any answer later, run `setup` again.

The skills come from KP's own `obsidian-capture` and `obsidian-lint` skills. A fix to either belongs in both copies.
