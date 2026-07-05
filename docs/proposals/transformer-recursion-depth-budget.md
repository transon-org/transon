# RFC: Bounded per-level recursion budget (make self-`include` depth reachable)

- **Status:** Accepted (2026-07-05) — decision recorded as Roadmap **R-32** (`accepted`); ready to
  implement. **Awaiting implementation** (the engine change lands with the SPEC invariant + the
  regression guard below, and only then does `transon-blockly` raise its codec depth cap).
- **Type:** Recursion-safety fix. **Behavior-preserving for every existing template** — no output
  changes, no error-message changes for in-range templates. It only *raises the nesting depth at
  which the transformer stops working*, and converts a class of raw `RecursionError`s into the
  already-documented `include` depth-limit `TransformationError`.
- **Roadmap:** tracked as **R-32** in `docs/ROADMAP.md`.
- **Driver:** the engine-side counterpart of a `transon-blockly` self-hosting limit. The editor
  derives its encoder/decoder as Transon-template *projections* run by this engine (no hand-written
  codec, `transon-blockly` AD-030). The generated codec **self-`include`s once per document node**,
  so its reachable nesting depth is bounded by *this engine's* per-level call-stack cost — not by
  `max_include_depth`. Today that ceiling sits below the editor's own deepest generator.

## Why

### Two independent depth limits, and only one is documented

A running transform is bounded by **two** limits:

| Limit | What it counts | How it fails |
|---|---|---|
| `max_include_depth` (default **50**) | *logical* nested-`include` levels | clean `TransformationError`: `include depth limit (N) exceeded: …` |
| `sys.getrecursionlimit()` (default **1000**) | *actual* Python call-stack frames | raw `RecursionError`: `maximum recursion depth exceeded` |

Only the first is in `SPECIFICATION.md`. The second is invisible — until a self-`include`ing
template (the codec's own shape) walks deep enough that the **Python call stack overflows before
`max_include_depth` is ever reached**. When that happens the caller gets a raw, uncatalogued
`RecursionError` instead of the documented include-depth error, and `max_include_depth`'s nominal
50 is fiction: a self-`include`ing template cannot get near it.

### The multiplier: the `walk` / `_walk` doubling

`walk()` does no work of its own — it opens the template-path context and delegates to `_walk()`
(`transon/transformers.py`):

```python
def walk(self, template, context, path=()):
    with self._walk_with_path(path):        # a @contextmanager
        return self._walk(template, context, path)

def _walk(self, template, context, path):
    if isinstance(template, list):  return self.walk_list(template, context, path)
    if isinstance(template, dict):
        if self.marker in template: return self.walk_rule(template, context, path)
        return self.walk_dict(template, context, path)
    return self.walk_scalar(template, context, path)
```

So **every** descent through a template node costs a `walk` **and** a `_walk` frame where one would
do. This is not marginal, because the codec walks a *rule at every level*. Profiling the committed
editor encoder over a 30-deep input (peak 801 live frames) shows the recursion is dominated by a
lockstep triple:

```
 184  walk        ← 46% of the whole stack is the walk/_walk pair …
 184  _walk       ← … and exactly half of that is the redundant _walk layer
 184  walk_rule
  62  rule_object
  31  walk_param / rule_switch / transform
  30  rule_include / rule_map / rule_cond
```

The redundant `_walk` layer alone is **184 of 801 frames — ~23% of the stack**.

### Measured impact (this engine, CPython 3.x default limit 1000)

- Encoding the committed editor codec over nested input hits `RecursionError` at input **depth 38**.
- `transon-blockly`'s deepest generator, `G_encode`, is nesting **depth 41** → it cannot be loaded
  into the editor at all; it fails as a raw stack overflow.
- Collapsing `walk`/`_walk` (below) lifts the codec's reach **37 → 49**, and **`G_encode` (41) now
  encodes**, with margin. A self-contained self-`include` walk template goes **57 → 75**.

None of this changes any in-range template's behavior — it only moves the wall outward and makes
the last stretch before it degrade *cleanly*.

## The fix — collapse `walk` into `_walk`

Fold `_walk`'s body into `walk` and set the template-path `ContextVar` inline (a `try/finally`
instead of a `@contextmanager` generator), so one template level costs one core recursion frame:

```python
def walk(self, template, context, path=()):
    token = _template_path.set(path)            # was: with self._walk_with_path(path):
    try:
        if isinstance(template, list):  return self.walk_list(template, context, path)
        if isinstance(template, dict):
            if self.marker in template: return self.walk_rule(template, context, path)
            return self.walk_dict(template, context, path)
        return self.walk_scalar(template, context, path)
    finally:
        _template_path.reset(token)
```

- **Behavior-identical.** The `ContextVar` is set to the same value over the same dynamic extent;
  `walk_list` / `walk_dict` / `walk_rule` / `walk_scalar` are unchanged. `_walk_with_path` (still
  used by `walk_rule` and `validate`) stays. Only the redundant per-node `_walk` frame is removed.
- **No public-API change.** `walk()`'s signature and semantics are unchanged; the ~dozen `t.walk(…)`
  call sites in `rules.py` are untouched.

`walk_rule` opens its **own** `_walk_with_path(rule_path)`; inlining that too buys further headroom
(codec reach ~70). It is **out of scope here** — the single `walk`/`_walk` collapse already clears
the editor's deepest generator, and keeping the change minimal keeps it obviously behavior-safe.

## Requirement — lock it so it can't silently degrade

This fix is a stack-frame optimization, and stack-frame optimizations rot: the next refactor that
adds a per-node wrapper, a decorator, or a helper method quietly re-doubles the cost and drops the
reachable depth back below `G_encode` — with **no visible failure** until someone tries to load a
deep template months later. So the fix ships **with a normative invariant and a regression guard**.

### SPEC change (lands with the implementation)

Add a **Recursion budget** invariant near the `include` / `max_include_depth` documentation in
`SPECIFICATION.md` (§ describing `max_include_depth` and the `include` rule):

> **Recursion budget.** Walking one level of template nesting consumes a bounded, small number of
> Python call-stack frames — one core recursion frame per node (no `walk`/`_walk`-style doubling).
> Because the generated `transon-blockly` editor codec self-`include`s once per document node
> (AD-030), its reachable nesting depth is governed by this budget, not by `max_include_depth`. The
> engine therefore transforms self-`include`ing templates at nesting depths well past the editor's
> deepest generator (`G_encode`, depth 41) within CPython's default recursion limit (1000).
> Exceeding `max_include_depth` MUST surface as the `include` depth-limit `TransformationError`,
> never a raw `RecursionError`.

### Regression guard (lands with the implementation)

Add `tests/test_recursion_depth.py`. Two complementary guards — a **structural** one (version-robust,
points straight at the cause) and a **black-box** one (user-facing, catches *any* per-level frame
bloat, not just this named pair):

```python
import sys
import inspect
import pytest
from transon import Transformer

# R-32 — per-level recursion budget. The transon-blockly editor codec (AD-030) self-`include`s
# once per document node; a doubled per-level frame cost overflows the host call stack with a raw
# RecursionError before max_include_depth is reached, and makes the codec's own deepest generator
# (G_encode, nesting depth 41) un-loadable. These guards fail if that doubling is reintroduced.

WALK = {  # recurse into {"k": <child>} once per level, via self-`include`
    "$": "switch",
    "key": {"$": "call", "name": "type", "value": {"$": "this"}},
    "cases": {"object": {"k": {"$": "chain", "funcs": [
        {"$": "attr", "name": "k"},
        {"$": "include", "name": "walk"},
    ]}}},
    "default": {"$": "this"},
}

def _loader(name, context=None):
    return context.transformer(WALK) if context is not None else Transformer(WALK)

def _nest(n):
    node = "leaf"
    for _ in range(n):
        node = {"k": node}
    return node

# Calibrated between the pre-fix reach (~57 on CPython 3.x) and the post-fix reach (~75), ~8 levels
# of margin each side, and comfortably above the editor codec's deepest self-`include` target
# (G_encode, depth 41). Re-confirm on the CI matrix (3.9–3.13) when landing.
MIN_SELF_INCLUDE_DEPTH = 65

def test_self_include_reaches_min_depth_within_default_recursion_limit():
    assert sys.getrecursionlimit() <= 1000, "guard is only meaningful at the default recursion limit"
    t = Transformer(WALK, template_loader=_loader, max_include_depth=MIN_SELF_INCLUDE_DEPTH + 50)
    # Must NOT raise RecursionError. Reintroducing walk/_walk doubling drops the reach below this.
    assert t.transform(_nest(MIN_SELF_INCLUDE_DEPTH)) == "leaf"

def test_exceeding_max_include_depth_is_a_clean_transformation_error_not_recursionerror():
    # The *logical* limit must still trip first, cleanly, well inside the call-stack budget.
    from transon import TransformationError
    t = Transformer(WALK, template_loader=_loader, max_include_depth=10)
    with pytest.raises(TransformationError, match=r"include depth limit \(10\) exceeded"):
        t.transform(_nest(40))

def test_no_redundant_per_node_walk_frame():
    # Structural guard: dispatching one node must not add a `walk` -> `_walk` indirection pair.
    frames = []
    orig = Transformer.walk_scalar
    def probe(self, template, context, path):
        frames.extend(f.function for f in inspect.stack(0))
        return orig(self, template, context, path)
    Transformer.walk_scalar = probe
    try:
        Transformer(_nest(4)).transform("x")
    finally:
        Transformer.walk_scalar = orig
    assert "_walk" not in frames, "walk/_walk doubling reintroduced (R-32 regression)"
```

> These three tests are **red on today's engine** and go green with the collapse — which is exactly
> why they must be added *in the same commit as the implementation*, not before.

## Rollout — a coordinated two-repo change (`transon-blockly` is engine-free)

1. **This repo:** land the `walk`/`_walk` collapse + the SPEC invariant + `tests/test_recursion_depth.py`
   in one commit; flip R-32 → `done`; changelog entry (recursion-safety, no behavior change to
   existing templates). Bump the minor version.
2. **`transon-blockly`** (separate change, after this ships): raise `CODEC_MAX_INCLUDE_DEPTH`
   (`packages/editor-core/src/codec/run.ts`, currently **25**) to ~**40** — below the new ~49 wall,
   keeping the clean `"depth limit"` guard as the backstop — and flip the self-hosting test so
   `G_encode`/`G_decode` move from *rejected* to *loads + round-trips* (`docs/SPEC.md` §6.5,
   `docs/traceability.md`).

**Portability caveat.** `transon-blockly` runs against *any* host engine (AD-008) and in the browser
under Pyodide (a *smaller* stack than CPython). The editor keeps **25** as its portable-safe default
and only raises the cap for a host known to carry this fix (or gates it on engine metadata, AD-012).
This RFC's guarantee is about *this* engine; it does not license the editor to assume it everywhere.

## Out of scope (declined / deferred)

- **`sys.setrecursionlimit(…)`.** Raising the interpreter limit *also* clears `G_encode`, but it
  moves the guard rather than lowering cost, and set too high it trades a catchable `RecursionError`
  for a hard C-stack segfault — worse on constrained hosts (Pyodide/WASM). The collapse is strictly
  better: fewer frames helps every host. **Rejected.**
- **Folding `walk_rule`'s own `_walk_with_path` too.** Extra headroom (~70), not needed to clear the
  editor's deepest generator; keep this RFC minimal and obviously safe. **Deferred** — revisit only
  if a deeper self-referential template appears.
- **An iterative / trampolined evaluator.** A rewrite of the recursion into an explicit work-stack
  would remove the host-stack dependency entirely, but it is a large change with real behavior risk
  and is unjustified by the current need. **Deferred.**
- **Raising `max_include_depth`'s default above 50.** Independent knob; not what bounds
  self-`include`ing codecs today (the call stack is). **Out of scope.**
