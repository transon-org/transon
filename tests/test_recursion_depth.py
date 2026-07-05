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
# (G_encode, depth 41). Re-confirm on the CI matrix (3.9-3.13) when landing.
MIN_SELF_INCLUDE_DEPTH = 65


def test_self_include_reaches_min_depth_within_default_recursion_limit():
    assert sys.getrecursionlimit() <= 1000, "guard is only meaningful at the default recursion limit"
    t = Transformer(WALK, template_loader=_loader, max_include_depth=MIN_SELF_INCLUDE_DEPTH + 50)
    # Must NOT raise RecursionError. Reintroducing walk/_walk doubling drops the reach below this.
    # WALK is an identity rebuild ({"k": <child>} in, {"k": <child>} out), so a completed transform
    # reproduces the nested input — the guarantee under test is that it completes at this depth.
    assert t.transform(_nest(MIN_SELF_INCLUDE_DEPTH)) == _nest(MIN_SELF_INCLUDE_DEPTH)


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
