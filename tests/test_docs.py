from transon import Transformer
from transon.docs import (
    get_all_docs,
    get_operators_docs,
    get_functions_docs,
)


def test_docs():
    get_all_docs()


def test_operators_docs_match_registry():
    documented = set()
    for operator in get_operators_docs():
        documented.add(operator['name'])
        documented.add(operator['alternative'])
    assert documented == set(Transformer._operators)


def test_functions_docs_match_registry():
    documented = {function['name'] for function in get_functions_docs()}
    assert documented == set(Transformer._functions)


def test_all_docs_expose_operators_and_functions():
    docs = get_all_docs()
    assert {entry['operator']['name'] for entry in docs['operators']} == {
        operator['name'] for operator in get_operators_docs()
    }
    assert {entry['function']['name'] for entry in docs['functions']} == {
        function['name'] for function in get_functions_docs()
    }


def _corpus_by_name(docs):
    return {example['name']: example for example in docs['examples']}


def test_all_docs_expose_worked_examples():
    docs = get_all_docs()
    names = docs['worked_examples']
    assert names, "the worked-examples block (D-15) must not be empty"
    assert {
        'WorkedExampleNestedArithmetic',
        'WorkedExampleReshapeRecords',
        'WorkedExampleRenameAndFlatten',
        'WorkedExampleFilterAndProject',
        'WorkedExampleIndexByKey',
        'WorkedExampleOptionalFieldsAndDefaults',
        'WorkedExampleConditionalEnrichmentInsideMap',
    } <= set(names)
    by_name = _corpus_by_name(docs)
    for name in names:
        example = by_name[name]
        assert example['doc'] and 'TBD' not in example['doc']


def test_all_docs_expose_recipes():
    docs = get_all_docs()
    names = docs['recipes']
    assert names, "the recipes block (D-16) must not be empty"
    assert {
        'RecipeReadNestedValue',
        'RecipeDefaultForMissingField',
        'RecipePluckFieldFromEach',
        'RecipeSwapKeysAndValues',
        'RecipeJoinListToString',
        'RecipeBuildStringFromFields',
        'RecipeConvertType',
        'RecipeMapCodeToLabel',
        'RecipeBucketValueByRanges',
        'RecipeComputeOnceUseTwice',
        'RecipePairUpTwoLists',
        'RecipeKeepItemsMatchingCondition',
    } <= set(names)
    by_name = _corpus_by_name(docs)
    for name in names:
        recipe = by_name[name]
        assert recipe['doc'] and 'TBD' not in recipe['doc']


def _collect_rule_names(template, found):
    if isinstance(template, dict):
        if '$' in template:
            found.add(template['$'])
        for value in template.values():
            _collect_rule_names(value, found)
    elif isinstance(template, list):
        for item in template:
            _collect_rule_names(item, found)


def test_curated_corpus_covers_first_user_rule_families():
    """Roadmap R-30: every rule family a first-time user meets appears in at
    least one curated case (worked example or recipe)."""
    docs = get_all_docs()
    by_name = _corpus_by_name(docs)
    used = set()
    for name in (*docs['worked_examples'], *docs['recipes']):
        _collect_rule_names(by_name[name]['template'], used)
    families = [
        {'attr', 'this', 'key', 'value', 'index'},  # accessors
        {'map'},
        {'filter'},
        {'object'},
        {'expr'},
        {'switch'},
        {'cond'},
        {'set'},
        {'get'},
        {'zip'},
        {'format'},
        {'join'},
        {'call'},
    ]
    for family in families:
        assert used & family, f'no curated case demonstrates any of {family}'


# Roadmap R-31: flat example corpus + name references.

def _iter_reference_lists(docs):
    """Yield ``(owner, name_list)`` for every reference-example field."""
    for rule in docs['rules']:
        yield rule['rule']['name'], rule['examples']
        for param in rule['params']:
            yield (rule['rule']['name'], param['param']['name']), param['examples']
    for entry in docs['operators']:
        yield ('operators', entry['operator']['name']), entry['examples']
    for entry in docs['functions']:
        yield ('functions', entry['function']['name']), entry['examples']


def test_corpus_serializes_every_case_exactly_once():
    from transon.docs import get_test_cases
    docs = get_all_docs()
    names = [example['name'] for example in docs['examples']]
    assert len(names) == len(set(names))
    assert set(names) == {case.__name__ for case in get_test_cases()}
    for example in docs['examples']:
        assert set(example) == {
            'name', 'doc', 'template', 'data', 'result', 'tags',
        }
        assert example['tags'], example['name']


def test_every_reference_resolves_into_the_corpus():
    docs = get_all_docs()
    by_name = _corpus_by_name(docs)
    for owner, name_list in _iter_reference_lists(docs):
        assert isinstance(name_list, list), owner
        for name in name_list:
            assert isinstance(name, str), (owner, name)
            assert name in by_name, (owner, name)
    for block in ('worked_examples', 'recipes'):
        for name in docs[block]:
            assert name in by_name, (block, name)


def test_every_corpus_case_is_reachable():
    docs = get_all_docs()
    referenced = set()
    for _, name_list in _iter_reference_lists(docs):
        referenced.update(name_list)
    referenced.update(docs['worked_examples'])
    referenced.update(docs['recipes'])
    corpus_names = {example['name'] for example in docs['examples']}
    orphans = corpus_names - referenced
    assert not orphans, f'corpus cases referenced nowhere: {sorted(orphans)}'


def test_all_docs_expose_error_model():
    docs = get_all_docs()
    errors = docs['errors']
    assert errors, "the error-model block (D-17) must not be empty"
    names = {error['name'] for error in errors}
    assert {
        'ErrorInvalidRuleName',
        'ErrorMissingRequiredAttr',
        'ErrorAccessorOutsideScope',
        'ErrorUnknownParamOnValidate',
        'ErrorDataNotIterable',
        'ErrorIncompatibleOperands',
    } <= names
    types = {error['error_type'] for error in errors}
    assert {'DefinitionError', 'TransformationError'} <= types, (
        "both error types must be demonstrated"
    )
    for error in errors:
        assert error['doc'] and 'TBD' not in error['doc']
        assert error['error'] and 'at template' in error['error']
        assert error['error_type'] in {'DefinitionError', 'TransformationError'}
