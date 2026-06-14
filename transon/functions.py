from transon import (
    Transformer,
)


Transformer.register_function(
    'str', input_type='any', output_type='str',
    doc='Convert any value to its string representation (Python `str`).',
)(str)
Transformer.register_function(
    'int', input_type='str', output_type='int',
    doc='Parse a string (or number) into an integer (Python `int`). An optional base can '
        'be passed as a second value.',
)(int)
Transformer.register_function(
    'float', input_type='str', output_type='float',
    doc='Parse a string (or number) into a floating-point number (Python `float`).',
)(float)
