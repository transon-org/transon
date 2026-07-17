# transon — Documentation-site content roadmap

> **Status of this document**: living backlog for the **content** of the docs site /
> playground at <https://transon-org.github.io/> (separate from the engine roadmap in
> [`docs/ROADMAP.md`](ROADMAP.md), which tracks engine semantics as `R-xx` items). Every
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
| D-20 | Migrate to the engine Language Reference (RFC 0008 release) | B. Freshness | medium | accepted |
| D-11 | `file` rule has zero examples | C. Completeness | high | done |
| D-12 | Parameters rendered with no example | C. Completeness | medium | done |
| D-08 | Operators and functions are not discoverable | C. Completeness | medium | done |
| D-07 | No install / getting-started / outbound links | D. Discoverability | medium | done |
| D-09 | No rule index, table of contents, or anchors | D. Discoverability | medium | done |
| D-10 | No conceptual framing (what/why/analogues) | D. Discoverability | low | done |
| D-13 | Thin page `<title>` and `<meta description>` | D. Discoverability | low | done |
| D-19 | No "when to pick what" comparison table vs. other tools | D. Discoverability | medium | done |
| D-14 | Blank gray screen during Pyodide load | E. First impression | medium | done |
| D-15 | Examples are minimal — no composition / realistic cases | F. Depth & learnability | medium | done |
| D-16 | No task-oriented recipes / common-patterns section | F. Depth & learnability | medium | done |
| D-17 | Error model described but never shown | F. Depth & learnability | low | done |
| D-18 | Core semantics documented only in the spec, not on-page | F. Depth & learnability | medium | done |

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

### D-20. Migrate to the engine Language Reference (RFC 0008 release)

**Status**: accepted · **Severity**: medium ·
**Source**: engine [`proposals/0008-language-reference-export.md`](proposals/0008-language-reference-export.md) (Sequencing) — **hard dependency of that engine release (atomic)**

The engine's RFC 0008 release relocates content the site renders today: the `Transformer`
class docstring (`get_all_docs()['doc']`) shrinks to an embedder-facing narrative (its language
sections move to the new `docs/LANGUAGE.md`, its pitch to `README.md`), and rule docstrings
grow richer (spec §4's per-rule facts fold in). In the same release window the site must:

1. render `LANGUAGE.md` as a language-guide section/page (source: `get_language_reference()`
   sections or the packaged file);
2. build its landing/pitch from `README.md` at build time instead of the class docstring;
3. repurpose the slimmed `doc` field as an "Embedding" (Python API) page.

Per-rule pages need no site work — they render whatever docstring text arrives, now richer.

**Impact if not fixed**: shipping against the new engine release without this leaves a slim
embedder intro as the landing and no language narrative anywhere on the site — a regression of
D-05/D-10/D-18.

---

## Theme C — Completeness (gaps in what the page documents)

### D-11. `file` rule has zero examples

**Status**: done · **Severity**: high · **Source**: `transon/tests/` audit · **Decision**: option 1 (corpus example; no playground bridge) · **Shipped**: `FileWriteViaMap` corpus case tagged `file`/`file:name`/`file:content` — `map` over `file` yields `[]`, docstring explains side-effect / `NO_CONTENT` semantics

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

**Status**: done · **Severity**: medium · **Source**: `transon/tests/` tag audit · **Decision**: option 1 (backfill tagged corpus cases) · **Shipped**: param tags on `SetVisibleToLaterSiblingKey` (`set:name`, `get:name`), `ChainWithAttr` (`chain:funcs`), `JoinTwoBase` (`join:items`), `ConvertNoParameters` (`call:name`); new `IncludeWithDefault` + `LookupMissingAttr` for `include:default` (`filter:cond` already covered by D-06)

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

**Status**: done · **Severity**: medium · **Source**: page structure · **Decision**: option 1 (first-class doc blocks — `docs.get_all_docs()` emits `operators`/`functions` arrays rendered as their own sections) · **Shipped**: engine repo — `docs.py` now emits `operators` (14, name/alternative/kind/types/result/doc) and `functions` (3, name/input/output/doc) arrays with examples harvested by `op:<alt>`/`func:<name>` tags; tagged existing `expr`/`call` corpus cases and added `test_operators.py` + a `float` case so every operator/function has a worked example; drift-guard tests in `tests/test_docs.py` keep the documented sets in sync with the registry. Site repo — new `Operator.tsx`/`Function.tsx`, `types.ts` shapes, and "Operators"/"Functions" sections in `App.tsx` (engine docstring changes appear on the live site after the next PyPI release)

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

**Status**: done · **Severity**: medium · **Source**: page audit · **Decision**: option 1 (Install & get started block in class docstring) · **Shipped**: new `## Install & get started` section at the top of the `Transformer` class docstring — `pip install transon`, a runnable 3-line transform snippet, and outbound links to PyPI, GitHub, the spec, and the changelog

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

**Status**: done · **Severity**: medium · **Source**: page structure (`Rule.tsx` renders rules as `<dt>`) · **Decision**: option 1 (anchored headings + compact reference index/TOC at the top, ungrouped — category grouping deferred to D-10) · **Shipped**: site repo (`transon-org.github.io`) — each rule/operator/function `<dl>` now carries a stable `id` (`rule-<name>`/`operator-<alt>`/`function-<name>`) and its heading is a self-linking `heading-anchor` for deep links; new `TableOfContents.tsx` renders a compact "Reference" index (flat, ungrouped) above the Rules section linking every rule/operator/function plus the `#rules`/`#operators`/`#functions` section anchors (moved onto the `<h3>`s); supporting CSS in `App.css` (`.toc*`, `.heading-anchor`, `scroll-margin-top`). Build verified green via `npm run build`

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

**Status**: done · **Severity**: low · **Source**: README/spec vs. page · **Decision**: option 1 (add a condensed "What is transon / inspired by / compared to" block near the top of the class docstring, grouped with the D-07 intro) · **Shipped**: new `## What is transon?` section at the top of the `Transformer` class docstring — one-line problem statement, "inspired by" (XSLT / JsonLogic), the design principles (valid-JSON templates, composable nested rules / no DSL, configurable `$` marker), and a "Compared to alternatives" list (jsonnet, jsonata, jolt, json-templates), condensed from the README; appears on the live site after the next PyPI release

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

**Status**: done · **Severity**: low · **Source**: `transon-org.github.io/public/index.html` · **Decision**: option 1 + og:image · **Shipped**: site repo (`transon-org.github.io`) — descriptive `<title>` ("Transon — homogeneous JSON-to-JSON template engine & playground"), a one-sentence `<meta description>`, full Open Graph (`og:type`/`site_name`/`url`/`title`/`description`/`image`+dims+alt) and Twitter `summary_large_image` tags in `public/index.html`, plus a committed 1200×630 branded preview at `public/og-image.png` (light minimalist card matching the site, "transon / transforms json" wordmark + tagline "Homogeneous JSON-to-JSON template engine"). `npm run build` verified green; tags and image present in `build/`

`<title>` is just "Transon" and `<meta name="description">` is "Transon
documentation". No descriptive title, no Open Graph/Twitter card content for link
previews.

**Impact if not fixed**: poor search snippets and bland/blank social-share previews.

**Options**:

1. **(Recommended)** Set a descriptive `<title>` (e.g. "Transon — homogeneous
   JSON-to-JSON template engine & playground") and a one-sentence `description`; add
   basic Open Graph/Twitter meta. Static edit in the site repo's `index.html`.
2. Title/description only, skip social cards. Minimal.

### D-19. No "when to pick what" comparison table vs. other tools

**Status**: done · **Severity**: medium · **Source**: README "Analogues" prose + page audit · **Decision**: option 1 (README comparison table + dedicated docs-site "transon vs alternatives" page + side-by-side JSONata-vs-transon snippet) · **Shipped**: engine repo (`transon`) — replaced the README "Analogues" prose with a "## Comparison" section: a "best when" decision table (transon, JSONata, jq, JSLT, Jolt, JsonLogic, JSON-e, Jsonnet, json-templates), an explicit "where transon is _not_ the best pick" list (expression conciseness; maturity/Python-only), and a side-by-side "same transform in JSONata vs transon" snippet (verified to evaluate to `[6, 35]`). Site repo (`transon-org.github.io`) — new `src/Comparison.tsx` renders the same content via the existing GFM `Markdown` component as an anchored `#comparison` section, wired into `App.tsx` above the Rules section, with a "Comparison" link added to `TableOfContents.tsx`; `npm run build` green. Static React content, so it does not depend on the next PyPI release. · **Relates to**: D-10 (shipped a condensed prose analogues list — jsonnet/jsonata/jolt/json-templates — in the class docstring)

The category is crowded (jq, JSONata, JSLT, Jolt, JsonLogic, JSON-e, Jsonnet,
json-templates), and the single hardest question a newcomer asks is *"why this over
the tool I already know?"*. The project answers it only in prose: the README has an
"Analogues" paragraph (`README.md`), and D-10 condensed that into the class docstring.
Neither is **scannable or decision-oriented** — there is no side-by-side table that
lets an evaluator place transon against the alternatives on the axes that actually
drive the choice (template format, extensibility, dependencies/footprint, language/
runtime, conciseness, maturity). A good comparison is also a promotion lever: "X vs Y
vs Z" pages are searched, and an honest table pulls in discovery traffic.

**Impact if not fixed**: in a crowded field the differentiator stays implicit. A
visitor can't tell in 10 seconds when transon is the right pick, so the project relies
on them inferring positioning from the mechanics — the weakest part of the funnel for
a niche tool competing with entrenched alternatives.

**Caveat (why this is `needs-decision`, not auto-accept)**: a self-comparison only
helps if it reads as **credibly honest**. A checkmark grid where transon wins every
row is discounted on sight and can backfire with the exact engineers it targets. The
table must (a) use decision-driving axes, not vanity features, (b) include rows where
transon *loses* (conciseness for arithmetic-heavy expressions; ecosystem maturity /
adoption), and (c) never misrepresent a competitor (people from those projects will
read it). Framing as "best when …" rather than "feature X: ✅/❌" keeps it honest and
more useful.

**Options**:

1. **(Recommended)** Add a "when to pick what" comparison block in two places: a
   compact table in the **README** (upgrading the existing "Analogues" prose) and a
   dedicated **docs-site page** ("transon vs alternatives") for SEO/discovery. Prefer a
   *"best when"* column over a boolean grid; include at least one row where transon
   loses. Pair it with a single **side-by-side "same transformation in JSONata vs
   transon"** snippet — one concrete example persuades more than the table, and it
   honestly shows the verbosity trade-off. Site page is mostly site-repo work; the
   table content can be authored once and reused in both places.
2. **Lighter touch**: upgrade only the README "Analogues" prose into a table (and,
   via the class docstring, the on-site intro that D-10 already populates). No dedicated
   comparison page. Cheaper, but forfeits the SEO landing-page value.
3. **On-page only**: extend the D-10 "Compared to alternatives" list in the
   `Transformer` class docstring into a small table so it renders on the site after the
   next PyPI release. Single source of truth (docstring), but a docstring table is
   harder to keep rich/formatted than dedicated content, and there's still no
   README/standalone comparison for evaluators arriving via GitHub.

---

## Theme E — First impression

### D-14. Blank gray screen during Pyodide load

**Status**: done · **Severity**: medium · **Source**: live site (load behavior) · **Decision**: option 1 (content stopgap — render a static intro immediately, before Pyodide loads, then let the generated docs augment it) · **Shipped**: site repo (`transon-org.github.io`) — disabled the PyScript splash spinner (`[splashscreen] enabled = false` in `public/config.toml`) and seeded `#root` in `public/index.html` with a styled static intro (title + `transforms json` tagline, the "Homogeneous JSON-to-JSON template engine" pitch line, a one-sentence framing, a `pip install transon` snippet, PyPI/GitHub/Specification/Changelog links, and a "Loading the interactive reference & playground…" spinner) shown instantly during the ~10–15s Pyodide download; `src/index.tsx` `init()` now clears `#root` before mounting so the generated docs replace the intro with no duplicate header. Static HTML, so it does not depend on the next PyPI release; `npm run build` green and the pre-load → loaded transition verified in-browser. · **Relates to**: D-05/D-07 (reuses the pitch + install content); the fuller engineering fix (preload/pin Pyodide, lazy-load the playground, or pre-bake the docs JSON) remains out of scope per option 2 and is not tracked here

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

## Theme F — Depth & learnability (reference is complete, but shallow as a tutorial)

> After D-08/D-11/D-12 closed the *coverage* gaps (every rule, parameter, operator, and
> function now has a doc block and at least one executable example), the remaining
> weakness is **depth**: the page is an excellent flat reference but a thin learning
> resource. These items add worked depth, not word count — the prose density is already
> about right; the fixes below are structural (more examples, task framing, shown
> errors, the mental model), so resist solving any of them by writing longer paragraphs.

### D-15. Examples are minimal — no composition or realistic cases

**Status**: done · **Severity**: medium · **Source**: `transon/tests/` corpus audit + page review · **Decision**: option 2 (a single dedicated, corpus-backed "Worked examples" doc block rather than spreading cases across rules) · **Shipped**: engine repo (`transon`) — new `transon/tests/test_worked_examples.py` with a gallery of **six** cases tagged only `worked-example` (kept in one block, not spread per-rule), each mapped to a canonical task the Comparison-table competitors showcase: `WorkedExampleNestedArithmetic` (`(a + b) * c` via nested `expr` — "arithmetic via nested rules, no DSL"; cf. JSONata/jq expressions), `WorkedExampleReshapeRecords` (`chain`→`attr`→`map`→`object`→`expr` line-items reshape; cf. JSONata `Price * Quantity`), `WorkedExampleRenameAndFlatten` (`object` `fields` + `attr` path + `format`; cf. Jolt `shift`), `WorkedExampleFilterAndProject` (`chain`→`filter`→`map`; cf. JSONata `users[active].name` / jq `map(select)`), `WorkedExampleIndexByKey` (`map` key/value; cf. jq `INDEX` / lodash `keyBy`), and `WorkedExampleOptionalFieldsAndDefaults` (the `NO_CONTENT` skip model + `attr` `default`; cf. JSON-e `$if`). `docs.py` `get_all_docs()` now emits a top-level `worked_examples` array (harvested via the `worked-example` tag), with a drift-guard in `tests/test_docs.py` asserting all six are present so the block can't silently empty out. Site repo (`transon-org.github.io`) — new `WorkedExamples.tsx` renders a self-linking `#worked-examples` section (intro + the existing interactive `ExamplesSection` playground, which maps over the whole array, so adding examples needs no site change) above the Rules section, `IDocsData.worked_examples` added to `types.ts`, wired into `App.tsx`, and a "Worked examples" link added to `TableOfContents.tsx` (all gated on the array being present, so it no-ops on the current PyPI build and appears after the next release). `npm run build` green; full `pytest` (217) green

Almost every rule renders a single, minimal example over toy data (e.g. `["a", "b"]`).
Two things are never shown: (a) **rule composition** — rules nested inside rules, which
is transon's headline strength (the intro and README assert "arithmetic via nested
rules, no DSL", but no example demonstrates it), and (b) a **realistic record-shaping**
transform (a non-trivial input object reshaped into a different output object).

**Impact if not fixed**: the differentiator (composability) is asserted but never
demonstrated; visitors can't see how primitives combine into real transformations.

**Options**:

1. **(Recommended)** Add a few `TableDataBaseCase` corpus cases that demonstrate
   composition (e.g. nested `expr` arithmetic; `map` + `object` + `attr` reshaping a
   list of records) and at least one realistic input→output example, tagged so they
   render under the relevant rules. Executable, so they double as regression tests.
2. Add a single dedicated "worked example" doc block (corpus- or docstring-backed)
   instead of spreading cases across rules. Less discoverable per-rule.

### D-16. No task-oriented recipes / common-patterns section

**Status**: done · **Severity**: medium · **Source**: page structure (organized by primitive) · **Decision**: option 1 (corpus-backed "Recipes" doc block) — mirror the D-15 machinery: a `recipe`-tagged `TableDataBaseCase` gallery harvested into a top-level `recipes` array by `get_all_docs()`, rendered as its own interactive `#recipes` site section. Each recipe is a short, single-task "how do I do Y?" snippet (kept deliberately smaller/more focused than the D-15 worked examples, which demonstrate composition). · **Shipped**: engine repo (`transon`) — new `transon/tests/test_recipes.py` with **seven** task-titled cases tagged only `recipe`, each a minimal answer to a common "how do I…?" question distinct from the D-15 worked examples: `RecipeReadNestedValue` (`attr` `names` path), `RecipeDefaultForMissingField` (`attr` `default`), `RecipePluckFieldFromEach` (`map` `item` + `attr` — project a list to one field), `RecipeSwapKeysAndValues` (`map` `key`/`value` over a dict using the `key`/`value` accessors), `RecipeJoinListToString` (`join` with `sep`), `RecipeBuildStringFromFields` (`format` unpacking a dict), and `RecipeConvertType` (`call` `int`). `docs.py` `get_all_docs()` now emits a top-level `recipes` array (harvested via the `recipe` tag), with a drift-guard in `tests/test_docs.py` asserting all seven are present so the block can't silently empty out. Site repo (`transon-org.github.io`) — new `Recipes.tsx` renders a self-linking `#recipes` section (task→template framing + the existing interactive `ExamplesSection` playground, mapping over the whole array, so adding recipes needs no site change) below Worked examples and above Rules, `IDocsData.recipes` added to `types.ts`, wired into `App.tsx`, and a "Recipes" link added to `TableOfContents.tsx` (all gated on the array being present, so it no-ops on the current PyPI build and appears after the next release). `npm run build` green; full `pytest` (225) green.

The docs are organized strictly by primitive (rule-by-rule, then operators/functions).
There is no goal-oriented entry point: a visitor who wants to "rename keys", "flatten a
nested list", "conditionally include a field", or "build a dict from a list" must first
know which rule(s) map to that goal.

**Impact if not fixed**: newcomers have to reverse-map their task onto primitives;
the page answers "what does rule X do?" but never "how do I do Y?".

**Options**:

1. **(Recommended)** Add a short "Recipes" / "Common patterns" section: a handful of
   task→template snippets. Best sourced from tagged corpus cases (executable, can't
   rot) surfaced as a new docs block, or as static site content if the team prefers to
   maintain it there.
2. Lighter touch: a cross-reference list in the intro that maps common tasks to the
   relevant rules, with anchor links (leans on the D-09 anchors). No new examples.

### D-17. Error model described but never shown

**Status**: done · **Severity**: low · **Source**: `Transformer` class docstring ("What you can do") vs. page · **Decision**: option 1 (show a concrete example of each error — literal message text incl. the `at template → …` location — backed by error-path corpus/doc cases so the shown text can't drift) · **Shipped**: engine repo (`transon`) — new `ErrorBaseCase` corpus type in `transon/tests/base.py` (asserts the *exact* `str(exception)`, so published error text can't drift) and a six-case gallery in `transon/tests/test_error_model.py` tagged `error`, covering both error types and the located path: `ErrorInvalidRuleName`, `ErrorMissingRequiredAttr`, `ErrorAccessorOutsideScope`, `ErrorUnknownParamOnValidate` (static `validate()`, no data), `ErrorDataNotIterable` (deep `at template → result → chain → funcs[1] → map` path), `ErrorIncompatibleOperands`. `docs.py` `get_all_docs()` now emits a top-level `errors` array (name/doc/template/data/error/error_type/action), with a drift-guard in `tests/test_docs.py` asserting all six are present and both error types are shown. Class docstring "What you can do" error bullet now points to the on-page **Error model** examples. Site repo (`transon-org.github.io`) — new `ErrorModel.tsx` renders a self-linking `#error-model` section (template + input + literal located message + error-type label per case via the existing GFM `Markdown`/syntax highlighter), `IErrorData`/`IDocsData.errors` added to `types.ts`, wired into `App.tsx` below Recipes, and an "Error model" link added to `TableOfContents.tsx` (all gated on the array being present, so it no-ops on the current PyPI build and appears after the next release); CSS in `App.css`. `npm run build` green; full `pytest` (232) green.

The intro advertises the error model — `DefinitionError` vs `TransformationError`, with
messages that include the template path (`at template → …`) — but **no actual error
message string appears anywhere on the page**. Someone debugging a real failure can't
match the message they see against the docs.

**Impact if not fixed**: the error-path UX (a genuine selling point: located, typed
errors) is claimed but undocumented by example; debugging users get no anchor.

**Options**:

1. **(Recommended)** Show a concrete example of each error — the literal message text
   including the `at template → …` location — in the intro error section and/or the
   relevant rule docstrings. (Could be backed by an error-path corpus/doc case so the
   shown text can't drift from the engine.)
2. Quote one representative message inline in the intro. Minimal; covers the shape but
   not both error types.

### D-18. Core semantics documented only in the spec, not on-page

**Status**: done · **Severity**: medium · **Source**: `docs/SPECIFICATION.md` vs. on-page intro · **Decision**: option 1 (add a "How evaluation works" section to the `Transformer` class docstring) · **Shipped**: engine repo (`transon`) — new `## How evaluation works` section in the `Transformer` class docstring (between **Templates** and **What you can do**), covering the four mechanics of the mental model in a few tight paragraphs: (1) the recursive top-down tree walk and how each JSON type is rebuilt, (2) marker-based rule detection and why parameters-are-templates makes rules nest/compose (incl. literal-`$` via `object` `fields` / configurable `marker`), (3) context/scope — `this`, the `map`/`filter` derived iteration accessors, and downward-only `set`/`get` variable flow, and (4) `NO_CONTENT` skip propagation through container rules plus `default`/top-level `no_content`. Links to SPECIFICATION.md §2 for exhaustive detail. Renders on the live site after the next PyPI release (docstring is harvested by `docs.get_all_docs()['doc']`).

The page names the key semantics — tree walk / marker-based rule detection, context and
scope nesting, and `NO_CONTENT` skip *propagation* through container rules — but their
mechanics live only in `docs/SPECIFICATION.md`, which the site does not load. A reader
on the site can learn the surface API (rules, params, examples) but not the **mental
model** needed to predict how a non-trivial template evaluates.

**Impact if not fixed**: the page teaches vocabulary without grammar; users compose
rules by trial and error instead of from an understood evaluation model.

**Options**:

1. **(Recommended)** Add a short "How evaluation works" section to the `Transformer`
   class docstring (engine repo): the recursive walk, rule detection via the marker,
   context/scoping for iteration accessors, and `NO_CONTENT` skip propagation — a few
   tight paragraphs, linking to the spec for exhaustive detail. Renders on-site after
   the next PyPI release.
2. Link to the spec from the intro only (closer to status quo). Lowest effort; the
   model still isn't readable on the page itself.

---

## Suggested sequencing

1. **Quick correctness wins** (one engine-repo pass, no decisions needed beyond
   wording): D-01, D-02, D-03, D-04, D-06.
2. **Freshness**: D-05 (intro rewrite) — unblocks reusable copy for D-07, D-10, D-14.
3. **Completeness via corpus** (additive, also tests): D-11, D-12; then D-08.
4. **Discoverability / framing** (mostly site repo): D-07, D-09, D-10, D-13, D-19
   (positioning/comparison — can build on D-10's analogues content).
5. **First impression**: D-14 (content stopgap first; engineering fix tracked
   separately).
6. **Depth & learnability** (after coverage is complete; mostly additive corpus +
   intro prose): D-15 (composition/realistic examples) and D-18 (evaluation model)
   first, since they unblock D-16 (recipes can cite the new examples) and D-17 (shown
   errors).
