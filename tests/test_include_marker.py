from transon import Transformer


def test_include_inherits_parent_marker():
    """An included template using the default marker inherits the parent's marker."""
    sub_template = {'@': 'this'}

    def loader(_name, context=None):
        return context.transformer(sub_template)

    parent = Transformer(
        {'@': 'include', 'name': 'sub'},
        marker='@',
        template_loader=loader,
    )
    assert parent.transform('hello') == 'hello'


def test_include_preserves_pinned_marker():
    """A sub-template that pins a non-default marker keeps it across the boundary."""
    sub_template = {'#': 'this'}

    def loader(_name, context=None):
        return context.transformer(sub_template, marker='#')

    parent = Transformer(
        {'@': 'include', 'name': 'sub'},
        marker='@',
        template_loader=loader,
    )
    assert parent.transform('hi') == 'hi'
