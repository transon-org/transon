# Fix a roadmap item

Implement one improvement from `docs/ROADMAP.md`. The item ID (e.g. `R-03`) is given
as the argument; if none is given, pick the first item with status `accepted`, or ask
which `needs-decision` item to decide on.

## Preconditions

1. Read the item's section in `docs/ROADMAP.md` and the spec sections describing
   the current behavior in `docs/SPECIFICATION.md`.
2. If the item's status is `needs-decision`, do NOT implement. Present the options
   to the user (use the recommendation from the roadmap) and wait for a choice.
   Record the choice: set status to `accepted` and note the chosen option in the
   item's section.
3. Behavior changes must never be silent: the recorded decision in step 2 IS the
   deliberate decision the project rules require; reflect the new behavior in the
   spec text and the changelog.

## Implementation checklist

1. Set the item status to `in-progress` in `docs/ROADMAP.md`.
2. Implement in the engine (`transon/transformers.py`, `transon/rules.py`,
   `transon/operators.py`, `transon/functions.py`). Respect the always-on rules:
   Python 3.9+ compatibility, stdlib only, no input/template mutation.
3. Tests:
   - behavior visible to template authors → table-driven example case(s) in
     `transon/tests/` with proper `tags` and docstrings (they become documentation);
   - error paths and engine mechanics → plain pytest tests in `tests/`.
4. Update documentation in lockstep:
   - rule docstrings / `register_rule` param docs if user-facing behavior changed;
   - `docs/SPECIFICATION.md`: update the normative sections describing the (new)
     current behavior, including any inline `R-xx` mentions that are now resolved;
   - `README.md` if the public API surface changed.
5. If behavior changed for existing templates: add a changelog entry (create
   `CHANGELOG.md` if absent) describing old vs new behavior and the migration.
6. Run the full suite: `uv run pytest .` (or `pytest .`). All green, coverage
   not reduced.
7. Set the item status to `done` in `docs/ROADMAP.md`, with a one-line note of what
   was shipped (and the chosen option number).

## Hard rules

- One roadmap item per run; resist scope creep into neighboring items unless they
  are listed as interlocked (e.g. R-15/R-22, the NO_CONTENT batch R-06/07/08/10).
- Never downgrade a `rejected` item to implemented without an explicit user request.
