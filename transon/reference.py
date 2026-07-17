"""Author-facing Language Reference export.

A dedicated, versioned export — separate from the docs API — that serves the
packaged ``LANGUAGE.md`` (the template language's **cross-cutting** semantics:
evaluation model, scoping, ``NO_CONTENT``, error taxonomy, ``expr``/``call``
machinery, composition patterns) to consumers that need it offline and pinned to
an engine version, the way ``get_editor_metadata()`` serves the catalog (see
``docs/proposals/0008-language-reference-export.md``).

The export states **language facts only** — no consumer-specific shapes. It is
**engine-global**: it documents the built-in language of the base ``Transformer``
only; unlike ``get_all_docs(cls=...)`` there is no class parameter.
"""
import importlib.metadata
import importlib.resources
import re

REFERENCE_VERSION = '1.0'

#: Characters kept by the GitHub-style heading slugger (besides spaces → hyphens).
_SLUG_KEEP = re.compile(r'[^0-9a-z _-]')


def _engine_version():
    """The installed ``transon`` distribution version, or ``None`` when unavailable.

    Same degradation contract as the metadata export: the reference must be
    usable when ``transon`` is merely importable from source and not installed
    as a distribution.
    """
    try:
        return importlib.metadata.version('transon')
    except importlib.metadata.PackageNotFoundError:
        return None


def _load_content():
    """The packaged ``LANGUAGE.md`` as UTF-8 text with ``\\n`` newlines."""
    resource = importlib.resources.files('transon').joinpath(
        'resources/LANGUAGE.md'
    )
    text = resource.read_bytes().decode('utf-8')
    return text.replace('\r\n', '\n').replace('\r', '\n')


def _slugify(title):
    """GitHub-style slug of a heading title.

    Lowercase; markdown backticks dropped with the rest of the punctuation;
    spaces become hyphens; alphanumerics, underscores, and hyphens survive.
    """
    slug = _SLUG_KEEP.sub('', title.lower())
    return slug.replace(' ', '-')


def _split_sections(content):
    """Split ``content`` into the flat, ordered ``sections`` list.

    Deterministic rules (RFC 0008 Deliverable 3): the split is on top-level
    ``##`` headings only (``###``+ stays inside its parent; fenced code blocks
    are opaque). Each section includes its own heading line. Content before the
    first ``##`` heading becomes a leading ``preamble`` section, present only
    when non-empty. Slug collisions get ``-2``, ``-3``, … suffixes in document
    order. The concatenation of all sections reproduces ``content`` exactly.
    """
    lines = content.splitlines(keepends=True)
    boundaries = []
    in_fence = False
    for index, line in enumerate(lines):
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
            continue
        if not in_fence and line.startswith('## '):
            boundaries.append(index)

    sections = []
    seen_ids = {}

    def _unique(slug):
        count = seen_ids.get(slug, 0) + 1
        seen_ids[slug] = count
        return slug if count == 1 else f'{slug}-{count}'

    first = boundaries[0] if boundaries else len(lines)
    preamble = ''.join(lines[:first])
    if preamble.strip():
        sections.append({
            'id': _unique('preamble'),
            'title': '',
            'heading_level': None,
            'content': preamble,
        })

    for position, start in enumerate(boundaries):
        end = boundaries[position + 1] if position + 1 < len(boundaries) else len(lines)
        title = lines[start][len('## '):].strip()
        sections.append({
            'id': _unique(_slugify(title)),
            'title': title,
            'heading_level': 2,
            'content': ''.join(lines[start:end]),
        })
    return sections


def get_language_reference():
    """Return the versioned Language Reference document.

    The result carries a standalone ``reference_version`` (minor bump =
    additive: a new section, appended prose, a new optional field; major bump =
    breaking: a removed/renamed section ``id``, a changed ``sections`` shape, a
    dropped/renamed top-level field — consumers MUST fail loudly on an
    unsupported major), the ``engine_version``, the byte-exact ``content``, and
    ``sections`` — a flat, ordered split of ``content`` so consumers can serve
    targeted per-section lookups instead of the whole document.
    """
    content = _load_content()
    return {
        'reference_version': REFERENCE_VERSION,
        'engine_version': _engine_version(),
        'format': 'markdown',
        'content': content,
        'sections': _split_sections(content),
    }


if __name__ == '__main__':  # pragma: no cover
    import json
    print(json.dumps(get_language_reference(), indent=4))
