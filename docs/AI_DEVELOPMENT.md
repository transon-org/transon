# AI-driven development setup

This project is set up for AI-assisted development with [Cursor](https://cursor.com).
This document describes the infrastructure: rules, skills, and recommended MCP servers.

## Rules (`.cursor/rules/`)

Project-specific rules are hand-written and committed to the repo (no external rule
packages exist that could replace domain knowledge):

| Rule | Scope | Purpose |
|---|---|---|
| `transon-overview.mdc` | always applied | Engine architecture map and invariants |
| `testing-conventions.mdc` | test files | Table-driven test corpus conventions |
| `adding-rules.mdc` | rules/operators/functions | How to add engine rules correctly |
| `python37-compat.mdc` | `**/*.py` | Forbidden post-3.7 syntax and stdlib features |

## Skills (`.agents/skills/`)

External, community-maintained skills are installed as packages from the
[skills.sh](https://skills.sh) registry using the
[`skills` CLI](https://github.com/vercel-labs/skills). Installed skills are
**not committed** — they are reproducibly installed from a manifest. The CLI
maintains `skills-lock.json` (content hashes per skill), which **is committed**,
like `poetry.lock`.

### Install

```bash
./scripts/install-skills.sh   # requires Node.js (npx)
```

### Manifest

The pinned skill list lives in `scripts/skills-manifest.txt`:

- `wshobson/agents@python-testing-patterns` — pytest fixtures, parametrization, mocking
- `wshobson/agents@python-code-style` — idiomatic Python style
- `github/awesome-copilot@pytest-coverage` — coverage-driven test workflows

### Managing skills

```bash
npx skills find <query>            # search the registry
npx skills add <owner/repo@skill> -a cursor --copy   # try a new skill
npx skills update -p               # update project skills to latest
npx skills list -p                 # list installed project skills
```

To make a skill permanent, add its `owner/repo@skill` spec to
`scripts/skills-manifest.txt`.

## Recommended MCP servers

| MCP | Status | Why |
|---|---|---|
| **context7** | keep enabled | Up-to-date library/API documentation lookup |
| **serena** | keep enabled | Semantic code navigation and editing for Python |
| **GitHub** | recommended to add | Issues, PRs, CI runs (install the GitHub plugin from the Cursor Marketplace) |
| **playwright** / browser | not needed | transon has no web UI; safe to disable for this project |

MCP servers are configured per-user (Cursor Settings → MCP) or via Marketplace
plugins; this table is the project recommendation.
