# Fix a docs-site item

Implement one improvement from `docs/DOCS_SITE_ROADMAP.md` (the docs-site / playground
**content** roadmap, IDs `D-xx`). The item ID (e.g. `D-04`) is given as the argument;
if none is given, pick the first item with status `accepted`, or ask which
`needs-decision` item to decide on.

This is the content sibling of `/fix-roadmap-item` (which handles engine semantics in
`docs/ROADMAP.md`, `R-xx`). Use **this** command for wording, accuracy, example
coverage, discoverability, and metadata — not engine behavior.

## Two repos

The docs site is generated, so content lives in two places (see the source-of-truth
table at the top of `docs/DOCS_SITE_ROADMAP.md`):

- **Engine repo** (`transon/`): the `Transformer` class docstring, rule docstrings,
  `register_rule` parameter docs, and the example corpus (`transon/tests/`).
- **Site repo** (`transon-org.github.io/`): the static React shell (`src/App.tsx`,
  `src/*.tsx`) and `public/index.html` (`<title>`, `<meta>`, tagline, loading screen).

Some items span both — read the item to see which. State up front which repo(s) a run
touches.

## Preconditions

1. Read the item's section in `docs/DOCS_SITE_ROADMAP.md` and the source-of-truth
   table in that file's front matter, so you edit the real source (a docstring/corpus
   case/site file) — not a generated artifact.
2. If the item's status is `needs-decision`, do NOT implement. Present the options
   (use the roadmap's recommendation) and wait for a choice. Record it: set status to
   `accepted` and note the chosen option in the item's section.
3. Keep it **content-only**. This command must not change engine behavior. If a content
   item turns out to require an engine fix (e.g. a docstring is wrong because the code
   is buggy), stop and route that part to `/fix-roadmap-item` (`docs/ROADMAP.md`).

## Implementation checklist

1. Set the item status to `in-progress` in `docs/DOCS_SITE_ROADMAP.md`.
2. Make the content change in the correct source:
   - intro / rule / parameter wording → docstrings in `transon/transformers.py` and
     `transon/rules.py` (`register_rule(..., <param>="…")` kwargs);
   - missing or broken examples → table-driven cases in `transon/tests/` with proper
     `tags` (`"<rule>"` / `"<rule>:<param>"`) and user-facing docstrings (they ARE the
     rendered examples; never leave `TBD`);
   - page shell / `<title>` / `<meta>` / tagline / loading UX → the
     `transon-org.github.io` repo (`src/`, `public/index.html`).
3. Prefer making examples executable: when fixing an inline code sample (e.g. a broken
   JSON snippet in a docstring), promote it to a real corpus case so it can't silently
   rot.
4. Verify:
   - `python -m transon.docs` → no `TBD` reported; the affected rule/parameter/example
     renders in the generated JSON;
   - corpus changes → `pytest transon/tests/` green (each example also asserts its
     `result`);
   - site-repo changes → it still type-checks / builds (`npm run build` in
     `transon-org.github.io`, if practical);
   - wording/spelling items → re-read the rendered text (the live site loads `transon`
     from PyPI, so engine-side docstring fixes appear only after a release; verify
     locally via `python -m transon.docs`).
5. Do NOT add a `CHANGELOG.md` entry — docs-site content items are intentionally not
   tracked there (the roadmap checker skips the changelog cross-check for `D-xx`).
   Exception: if the fix also edits a packaging string that ships to PyPI (e.g. the
   `pyproject.toml` description in D-01), note in the item that it rides the next
   release.
6. Set the item status to `done` in `docs/DOCS_SITE_ROADMAP.md`, with a one-line note
   of what shipped (and the chosen option number).
7. Run `python scripts/check_roadmap.py docs/DOCS_SITE_ROADMAP.md` → "consistent".

## Hard rules

- One roadmap item per run; resist scope creep into neighboring items unless they are
  interlocked (e.g. D-02/D-04/D-05 all touch the intro docstring; D-07/D-10 share an
  intro section).
- Content-only: never change engine behavior here. Route behavior changes to
  `/fix-roadmap-item`.
- Never downgrade a `rejected` item to implemented without an explicit user request.
- Status hygiene: keep the checklist table, the `### D-xx.` section header, and any
  inline `~~D-xx~~` mentions aligned (the checker enforces this).
