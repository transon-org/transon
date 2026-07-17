"""Shape, section-pin, split-parity, and packaging tests for the Language
Reference export (RFC 0008, R-34/R-35/R-36)."""
import importlib.resources
from pathlib import Path

from transon.reference import (
    REFERENCE_VERSION,
    _split_sections,
    get_language_reference,
)

#: The pinned section-id list (RFC 0008 drift protection): adding, renaming, or
#: removing a section in ``docs/LANGUAGE.md`` must update this pin **and** follow
#: the ``REFERENCE_VERSION`` policy — additive changes bump the minor, removals/
#: renames are breaking and bump the major. Never a silent edit.
PINNED_SECTION_IDS = [
    'preamble',
    'templates-and-the-marker',
    'context-and-scoping',
    'the-no_content-model',
    'error-model',
    'expressions-and-calls',
    'composition-patterns',
]

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_reference_shape():
    ref = get_language_reference()
    assert set(ref) == {
        'reference_version', 'engine_version', 'format', 'content', 'sections',
    }
    assert ref['reference_version'] == REFERENCE_VERSION == '1.0'
    assert ref['engine_version'] is None or isinstance(ref['engine_version'], str)
    assert ref['format'] == 'markdown'
    assert isinstance(ref['content'], str) and ref['content']
    assert '\r' not in ref['content']
    assert isinstance(ref['sections'], list) and ref['sections']


def test_section_ids_are_pinned():
    ref = get_language_reference()
    assert [section['id'] for section in ref['sections']] == PINNED_SECTION_IDS


def test_sections_concatenation_reproduces_content():
    ref = get_language_reference()
    joined = ''.join(section['content'] for section in ref['sections'])
    assert joined == ref['content']


def test_section_fields():
    ref = get_language_reference()
    preamble, *rest = ref['sections']
    assert preamble['id'] == 'preamble'
    assert preamble['title'] == ''
    assert preamble['heading_level'] is None
    assert preamble['content'].strip()
    for section in rest:
        assert section['heading_level'] == 2
        assert section['title']
        assert section['content'].startswith(f"## {section['title']}\n")
        assert set(section) == {'id', 'title', 'heading_level', 'content'}


def test_packaged_copy_is_served_and_matches_canonical():
    """Packaging parity (RFC 0008 Deliverable 2): the export serves the packaged
    ``transon/resources/LANGUAGE.md`` via ``importlib.resources``, and that copy
    is byte-identical (modulo line endings) to the canonical, hand-edited
    ``docs/LANGUAGE.md``."""
    ref = get_language_reference()
    packaged = (
        importlib.resources.files('transon')
        .joinpath('resources/LANGUAGE.md')
        .read_bytes()
        .decode('utf-8')
        .replace('\r\n', '\n')
        .replace('\r', '\n')
    )
    assert packaged == ref['content']
    canonical = (REPO_ROOT / 'docs' / 'LANGUAGE.md').read_text(encoding='utf-8')
    canonical = canonical.replace('\r\n', '\n').replace('\r', '\n')
    assert canonical == ref['content'], (
        'docs/LANGUAGE.md and transon/resources/LANGUAGE.md have diverged — '
        'copy the canonical docs/LANGUAGE.md over the packaged resource'
    )


def test_split_without_preamble():
    sections = _split_sections('## Only\nbody\n')
    assert [s['id'] for s in sections] == ['only']


def test_split_whitespace_only_prefix_is_preserved_as_preamble():
    """Every prefix byte belongs to the preamble — parity beats prettiness."""
    content = '\n\n## First\nbody\n'
    sections = _split_sections(content)
    assert [s['id'] for s in sections] == ['preamble', 'first']
    assert ''.join(s['content'] for s in sections) == content


def test_split_slug_collisions_get_suffixes():
    content = '## Dup\na\n## Dup\nb\n## Dup\nc\n'
    sections = _split_sections(content)
    assert [s['id'] for s in sections] == ['dup', 'dup-2', 'dup-3']
    assert ''.join(s['content'] for s in sections) == content


def test_split_ignores_headings_inside_code_fences():
    content = '# T\nintro\n\n## Real\n```\n## not a heading\n```\ntail\n'
    sections = _split_sections(content)
    assert [s['id'] for s in sections] == ['preamble', 'real']
    assert ''.join(s['content'] for s in sections) == content


def test_split_ignores_headings_inside_tilde_fences():
    content = '## Real\n~~~\n## not a heading\n~~~\ntail\n'
    sections = _split_sections(content)
    assert [s['id'] for s in sections] == ['real']
    assert ''.join(s['content'] for s in sections) == content


def test_split_fence_closes_only_on_matching_delimiter():
    # A ``` line inside a ~~~ fence does not close it, and a longer run of the
    # same character does; a shorter run does not.
    content = (
        '## A\n'
        '~~~~\n'
        '```\n'
        '## still fenced\n'
        '~~~\n'
        '## still fenced too\n'
        '~~~~~\n'
        '## B\n'
    )
    sections = _split_sections(content)
    assert [s['id'] for s in sections] == ['a', 'b']
    assert ''.join(s['content'] for s in sections) == content


def test_split_deeper_headings_stay_inside_parent():
    content = '## Top\n### Sub\nbody\n#### Deeper\n'
    sections = _split_sections(content)
    assert [s['id'] for s in sections] == ['top']
    assert '### Sub' in sections[0]['content']
