# transon — Documentation-site content roadmap

> **Status of this document**: living backlog for the **content** of the docs site /
> playground at <https://transon-org.github.io/> (separate from the engine roadmap in
> [`docs/ROADMAP.md`](ROADMAP.md), which tracks engine semantics `R-01…R-22`). Every
> entry follows the same format: problem → impact of not fixing → options (with a
> recommendation when one is clearly better).
>
> **Scope**: content only — wording, accuracy, completeness, discoverability, and
> example coverage. Page *engineering* (the React/PyScript stack, build, perf) is out
> of scope here except where a content stopgap is called out.
>
> **Where the content actually lives** (important): the site is a CRA SPA whose words
> are *generated*, not hand-written. The pipeline is:
> `public/index.html` boots PyScript/Pyodide → `pip install transon` (latest from PyPI,
> unpinned) → `public/script.py` calls `transon.docs.get_all_docs()` → React renders.
> So almost every content fix lands in the **engine repo**:
>
> | Page region | Source of truth |
> |---|---|
> | Title + "transforms json" + tagline + version line | `transon-org.github.io/src/App.tsx` (static) + `transon-org.github.io/public/index.html` |
> | Intro prose under the title | `Transformer` class docstring (`transon/transformers.py`) |
> | Each rule's heading + body | rule docstrings (`transon/rules.py`) |
> | Parameter docs | `register_rule(..., <param>="…")` kwargs (`transon/rules.py`) |
> | Examples (rule- and param-level) | tagged `TableDataBaseCase` corpus (`transon/tests/`) |
> | `<title>` / `<meta description>` | `transon-org.github.io/public/index.html` |
>
> Verified against the live site (v0.0.11) and the source on 2026-06-13.

**Statuses**: `needs-decision` (maintainer must pick an option) ·
`accepted` (option chosen, ready to implement) · `in-progress` · `done` ·
`rejected` (decided not to do it — record why).

## Checklist

| ID | Title | Theme | Severity | Status |
|---|---|---|---|---|
| D-01 | "Homogenous" misspelling in the tagline (and everywhere) | A. Correctness | high | done |
| D-02 | Grammar/typos in the intro docstring | A. Correctness | medium | done |
| D-03 | `attr` "either name **of** names" typo (error text) | A. Correctness | low | done |
| D-04 | Broken JSON in the headline intro example | A. Correctness | high | done |
| D-06 | Accessor docstrings omit `filter` scope | A. Correctness | medium | done |
| D-05 | Intro is stale vs. v0.0.11 capabilities | B. Freshness | high | done |
| D-11 | `file` rule has zero examples | C. Completeness | high | needs-decision |
| D-12 | Parameters rendered with no example | C. Completeness | medium | needs-decision |
| D-08 | Operators and functions are not discoverable | C. Completeness | medium | needs-decision |
| D-07 | No install / getting-started / outbound links | D. Discoverability | medium | needs-decision |
| D-09 | No rule index, table of contents, or anchors | D. Discoverability | medium | needs-decision |
| D-10 | No conceptual framing (what/why/analogues) | D. Discoverability | low | needs-decision |
| D-13 | Thin page `<title>` and `<meta description>` | D. Discoverability | low | needs-decision |
| D-14 | Blank gray screen during Pyodide load | E. First impression | medium | needs-decision |

---

## Theme A — Correctness (factual / language errors visible on the page)

### D-01. "Homogenous" misspelling in the tagline (and everywhere)

**Status**: done · **Severity**: high · **Source**: live site + source audit · **Decision**: option 1 (fix everywhere) · **Shipped**: corrected to "Homogeneous" in `App.tsx`, `pyproject.toml`, and `README.md` (`pyproject.toml` ships on next release)

The tagline rendered directly under the title reads **"Homogenous JSON template
engine"** (`transon-org.github.io/src/App.tsx`). The intended word is
**"Homogeneous"**. The same misspelling propagates from `pyproject.toml`
(`description`), the package README, and the PyPI summary. ("Homogenous" is a real but
unrelated biology term, so spell-checkers may not flag it.)

**Impact if not fixed**: a spelling error in the single most prominent line of the
landing page undercuts the "professional presentation" goal on first glance.

**Options**:

1. **(Recommended)** Fix every occurrence to "Homogeneous": `App.tsx` tagline,
   `pyproject.toml` description (ships to PyPI on next release), README/PyPI text.
   One coordinated pass; cheap, high visibility payoff.
2. Fix only the on-page `App.tsx` tagline now; leave packaging strings for the next
   release. Faster, but leaves PyPI/README inconsistent.

### D-02. Grammar/typos in the intro docstring

**Status**: done · **Severity**: medium · **Source**: `transon/transformers.py` (class docstring) · **Decision**: option 1 (copy-edit in one pass) · **Shipped**: grammar fixes in `Transformer` class docstring (except for/JSON/additional/functions; Rules section pointer)

The intro prose (rendered as the opening sections of the page) contains several
errors:

- "It will be reflected as-is in output, **except of** `rules` structures" → "except
  **for** rule structures".
- "Rules are **json** objects" → "**JSON** objects".
- "In **same** fashion you can also **add addition** operators … and **function**
  (`call`)" → "In **the** same fashion … add **additional** operators … and
  **functions**".
- "**There is a list of rules** available out of the box" — promises an inline list
  the docstring never provides (the rules render lower down under the **Rules**
  heading); reword to point there, or drop the sentence.

**Impact if not fixed**: the prose reads as unpolished in the first screenful.

**Options**:

1. **(Recommended)** Copy-edit the docstring in one pass (combine with D-04 and D-05,
   since they touch the same docstring).
2. Defer to the larger D-05 rewrite.

### D-03. `attr` "either name **of** names" typo (error text)

**Status**: done · **Severity**: low · **Source**: `transon/rules.py` (`rule_attr`) · **Decision**: fix "of" → "or" · **Shipped**: `DefinitionError` message now reads ``either `name` or `names` attribute is required``

The `DefinitionError` message reads ``either `name` of `names` attribute is
required`` — "**of**" should be "**or**". User-facing whenever `attr` is misused, and
the engine now also has `validate()` paths that surface it.

**Impact if not fixed**: a typo in an error string that template authors will read.

**Fix (single obvious option)**: change "of" → "or". Pure text fix.

### D-04. Broken JSON in the headline intro example

**Status**: done · **Severity**: high · **Source**: `transon/transformers.py` (class docstring, "Example template") · **Decision**: option 1 (fix JSON + corpus case) · **Shipped**: valid JSON in intro docstring; `MapListToNestedListWithItem` corpus case tagged `map`/`map:item`/`item`

The first code sample on the page is not valid JSON:

- `{"$": item}` uses an **unquoted** `item` (must be `{"$": "item"}`, the spelling used
  everywhere else).
- The "final result" block uses **trailing commas** (`[{"x": 1}],` … `]`,) which are
  invalid JSON.

Because the playground is a JSON tool, shipping invalid JSON in the canonical example
is especially damaging — and a curious visitor who pastes it gets a parse error.

**Impact if not fixed**: the very first example contradicts the product's premise and
won't round-trip through the playground.

**Options**:

1. **(Recommended)** Fix the example to valid JSON (`"$": "item"`, remove trailing
   commas) and verify it actually evaluates to the stated result, then promote it to a
   real corpus case so it can't silently rot again (ties into D-11/D-12 philosophy:
   examples should be executable).
2. Minimal fix: correct the two JSON errors in place without adding a corpus case.

### D-06. Accessor docstrings omit `filter` scope

**Status**: done · **Severity**: medium · **Source**: `transon/rules.py` (`item`/`key`/`value`/`index`) · **Decision**: option 1 (docstrings + filter examples) · **Shipped**: four accessor docstrings now say `map`/`filter`; tagged `FilterList`/`FilterDict` with `item`/`value`; added `FilterListByOddIndex` for `index`

The docstrings for `item`, `key`, `value`, and `index` all say *"Works inside `map`
rule"*, but the spec (§4.1) and the engine make them equally valid inside **`filter`**
(both rules iterate via the same `_iter_contexts`). The published docs are narrower
than the real contract.

**Impact if not fixed**: authors won't discover that iteration accessors work in
`filter`; the docs disagree with the spec.

**Options**:

1. **(Recommended)** Update the four docstrings to "Works inside `map`/`filter`",
   matching spec §4.1; optionally add a `filter` example that uses `index`/`value`.
2. Document at the spec level only — rejected, since the rule docstrings are what the
   site shows.

---

## Theme B — Freshness

### D-05. Intro is stale vs. v0.0.11 capabilities

**Status**: done · **Severity**: high · **Source**: `transon/transformers.py` (class docstring) · **Decision**: option 1 (rewrite the class docstring as a landing narrative) · **Shipped**: refreshed the `Transformer` class docstring — homogeneous JSON-to-JSON pitch + a skimmable "What you can do" capability list (static `validate()`, `default` family, `NO_CONTENT` skip model, `object` `fields` literal keys, configurable `marker`, `copy_output`, `DefinitionError`/`TransformationError` model, `file_writer`/`template_loader` delegates), pointing to the per-rule **Rules** section and the spec for detail; also added a ```plantuml``` input/template→`transon`→output diagram (mirrors the README, rendered on-site via the existing `remark-simple-plantuml` plugin)

The `Transformer` docstring still describes the original 2023 engine. It never
mentions features that the changelog/spec now advertise and that are the project's
strongest selling points:

- `Transformer.validate()` / `validate=True` (static template checking);
- the `default` parameter family (`attr`/`get`/`format`/`include`/`join`);
- `object` `fields` mode (literal keys, incl. the marker `$`);
- the `NO_CONTENT` "no value" model and skip semantics;
- configurable `marker`;
- `transform(data, no_content=…, copy_output=…)`;
- the error model (`DefinitionError` vs `TransformationError`) with template-path
  locations;
- the `file_writer` / `template_loader` delegates.

**Impact if not fixed**: a visitor reading top-to-bottom forms a 2023-era impression
and never learns about the validation/defaults/error-model work that differentiates
the project today.

**Options**:

1. **(Recommended)** Rewrite the class docstring as a proper landing narrative:
   one-line pitch → minimal usage → templates/marker → a short "What you can do"
   capability list (validation, defaults, error model, extensibility) with links to
   the relevant rule sections below. Keep it skimmable; defer exhaustive detail to the
   per-rule docs and the spec.
2. Append a "Since v0.0.x" capabilities paragraph without restructuring. Lower effort,
   but the intro still buries the headline features.
3. Add a dedicated "Features"/"Highlights" section sourced from a new docstring or a
   new corpus-backed block, leaving the existing intro intact.

---

## Theme C — Completeness (gaps in what the page documents)

### D-11. `file` rule has zero examples

**Status**: needs-decision · **Severity**: high · **Source**: `transon/tests/` audit

`file` is the only rule with **no harvested examples**: its tests live in
`tests/test_file.py` as plain pytest functions (mocking `file_writer`), not as
`TableDataBaseCase` corpus entries, so `get_all_docs()` attaches nothing. On the page
`file` shows a docstring + params but an empty Examples area. It also can't be demoed
in the playground, because the bridge `transform()` in `public/script.py` wires no
`file_writer`.

**Impact if not fixed**: a documented rule looks unfinished and is undemonstrable —
the weakest spot in an otherwise example-rich page.

**Options**:

1. **(Recommended)** Add a `TableDataBaseCase` example tagged `file`/`file:name`/
   `file:content` whose `result` captures the rule's actual return (`NO_CONTENT` →
   `None`, e.g. via `map` over `file` yielding `[]`), with a docstring that explains
   the side-effect-and-no-result semantics. Documents the rule without needing a live
   writer.
2. Additionally, teach the playground bridge a capturing `file_writer` and surface
   written files in the UI, so `file` is interactively demoable. (Crosses into page
   engineering — record separately; option 1 closes the content gap on its own.)

### D-12. Parameters rendered with no example

**Status**: needs-decision · **Severity**: medium · **Source**: `transon/tests/` tag audit

Example coverage is uneven: several parameters render with documentation but no
example block. Confirmed gaps: `set:name`, `get:name`, `filter:cond`, `join:items`,
`chain:funcs`, `call:name`, `include:default` (and the rule-level `file` gap in D-11).

**Impact if not fixed**: inconsistent depth across the reference; the params most
likely to confuse newcomers (e.g. `filter:cond`, `chain:funcs`) lack a worked example.

**Options**:

1. **(Recommended)** Backfill one tagged corpus case per missing `<rule>:<param>`
   (and the rule-level cases), prioritizing `filter:cond`, `chain:funcs`, `call:name`.
   Pure additive corpus work; each new case is also a regression test.
2. Add a CI/`transon.docs` lint that flags any declared parameter with zero examples
   (extends the existing `TBD` check), so coverage can't regress. Pairs well with 1.

### D-08. Operators and functions are not discoverable

**Status**: needs-decision · **Severity**: medium · **Source**: page structure

The 14 `expr` operators are documented only *inside* the `expr.op` parameter table,
and the `str`/`int`/`float` functions only *inside* `call.name`. There is no
top-level "Operators" or "Functions" reference, so a visitor scanning rule headings
never sees them.

**Impact if not fixed**: a core part of the language (arithmetic/logic/comparison and
type conversion) is effectively hidden two levels deep.

**Options**:

1. **(Recommended)** Surface operators/functions as first-class doc blocks. Cleanest
   source-of-truth approach: have `docs.get_all_docs()` emit `operators` and
   `functions` arrays (name, doc, examples by tag) the way it does for rules, and
   render them as their own sections. Requires small additions to `docs.py`, the docs
   JSON shape, and the React renderer.
2. Lighter touch: keep the data model, but add a short "Operators" / "Functions"
   summary to the intro/`expr`/`call` docstrings with anchor links. No pipeline
   change; less structured.

### D-07. No install / getting-started / outbound links

**Status**: needs-decision · **Severity**: medium · **Source**: page audit

The page has no `pip install transon`, no "your first transform" snippet beyond the
abstract usage block, and no in-content links to PyPI, the GitHub repo, the spec, or
the changelog (only the corner "Fork me on GitHub" ribbon).

**Impact if not fixed**: a convinced visitor has no obvious next step to actually adopt
the library.

**Options**:

1. **(Recommended)** Add a short "Install & get started" block near the top
   (`pip install transon`, a 3-line runnable snippet, links to PyPI/GitHub/spec).
   Sourceable from the class docstring (engine repo) or as static React content
   (site repo) — pick per where the team prefers to maintain it.
2. Add only a links footer/header (PyPI, GitHub, version → release notes). Minimal.

### D-09. No rule index, table of contents, or anchors

**Status**: needs-decision · **Severity**: medium · **Source**: page structure (`Rule.tsx` renders rules as `<dt>`)

Rules render as `<dt>` definition terms, not headings, on one long page of 20 rules.
There is no table of contents, no per-rule anchor, and no way to deep-link to a rule
(e.g. share "the `map` rule").

**Impact if not fixed**: navigation and sharing are painful; the reference doesn't
scale with the rule count.

**Options**:

1. **(Recommended)** Render each rule name as an anchored heading and add a compact
   rule index / TOC at the top (optionally grouped by category — see D-10). Mostly a
   site-repo change; the grouping metadata could come from the engine.
2. Anchors only, no TOC. Smaller; enables deep links but not at-a-glance navigation.

### D-10. No conceptual framing (what / why / analogues)

**Status**: needs-decision · **Severity**: low · **Source**: README/spec vs. page

The README and spec carry framing the page omits: a one-line problem statement,
"inspired by XSLT / JsonLogic", the design principles, and the analogues comparison
(jsonnet, jolt, jsonata, json-templates). The page jumps straight into mechanics.

**Impact if not fixed**: newcomers must infer the library's positioning; the page
under-sells *why* transon exists.

**Options**:

1. **(Recommended)** Add a brief "What is transon / inspired by / compared to" block
   near the top, condensed from the README (which already has this content). Could be
   grouped with D-07 into a single intro section.
2. Link out to the README instead of restating. Lowest effort; weaker landing page.

### D-13. Thin page `<title>` and `<meta description>`

**Status**: needs-decision · **Severity**: low · **Source**: `transon-org.github.io/public/index.html`

`<title>` is just "Transon" and `<meta name="description">` is "Transon
documentation". No descriptive title, no Open Graph/Twitter card content for link
previews.

**Impact if not fixed**: poor search snippets and bland/blank social-share previews.

**Options**:

1. **(Recommended)** Set a descriptive `<title>` (e.g. "Transon — homogeneous
   JSON-to-JSON template engine & playground") and a one-sentence `description`; add
   basic Open Graph/Twitter meta. Static edit in the site repo's `index.html`.
2. Title/description only, skip social cards. Minimal.

---

## Theme E — First impression

### D-14. Blank gray screen during Pyodide load

**Status**: needs-decision · **Severity**: medium · **Source**: live site (load behavior)

On load the page shows a gray spinner ("Downloading pyodide-0.22.1… / Python
startup…") for ~10–15s while a multi-MB Python runtime downloads, with **no product
description visible** during that window — the marketing/landing value is lost exactly
when the first impression forms.

**Impact if not fixed**: many visitors see nothing but a spinner; bounce risk is high
for a landing page.

**Options**:

1. **(Recommended, content stopgap)** Render a **static** intro (title, tagline, the
   one-line pitch, install snippet — D-05/D-07 content) immediately, before Pyodide
   loads, and progressively replace/augment it once the generated docs arrive. Keeps
   this roadmap's "content" scope: the words exist regardless of the runtime.
2. Fuller engineering fix (out of scope here, record separately): pin/preload Pyodide,
   lazy-load the playground only when an example is opened, or pre-bake the docs JSON
   at build time so the reference renders without the Python runtime.

---

## Suggested sequencing

1. **Quick correctness wins** (one engine-repo pass, no decisions needed beyond
   wording): D-01, D-02, D-03, D-04, D-06.
2. **Freshness**: D-05 (intro rewrite) — unblocks reusable copy for D-07, D-10, D-14.
3. **Completeness via corpus** (additive, also tests): D-11, D-12; then D-08.
4. **Discoverability / framing** (mostly site repo): D-07, D-09, D-10, D-13.
5. **First impression**: D-14 (content stopgap first; engineering fix tracked
   separately).
