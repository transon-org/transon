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


def test_all_docs_expose_worked_examples():
    docs = get_all_docs()
    examples = docs['worked_examples']
    assert examples, "the worked-examples block (D-15) must not be empty"
    names = {example['name'] for example in examples}
    assert {
        'WorkedExampleNestedArithmetic',
        'WorkedExampleReshapeRecords',
        'WorkedExampleRenameAndFlatten',
        'WorkedExampleFilterAndProject',
        'WorkedExampleIndexByKey',
        'WorkedExampleOptionalFieldsAndDefaults',
        'WorkedExampleConditionalEnrichmentInsideMap',
    } <= names
    for example in examples:
        assert example['doc'] and 'TBD' not in example['doc']


def test_all_docs_expose_recipes():
    docs = get_all_docs()
    recipes = docs['recipes']
    assert recipes, "the recipes block (D-16) must not be empty"
    names = {recipe['name'] for recipe in recipes}
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
    } <= names
    for recipe in recipes:
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
    used = set()
    for case in (*docs['worked_examples'], *docs['recipes']):
        _collect_rule_names(case['template'], used)
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
