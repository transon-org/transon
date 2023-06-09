# transon

![PyPI](https://img.shields.io/pypi/v/transon)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/transon)
![Codecov](https://img.shields.io/codecov/c/github/transon-org/transon)
![PyPI - Downloads](https://img.shields.io/pypi/dm/transon)

Homogenous JSON template engine.
`transon` creates JSON out of template and JSON input.

```
                    ┌─────────────────┐
                    │  JSON Template  │
                    └────────┬────────┘
                             │
┌──────────────┐    ┌────────▼────────┐    ┌───────────────┐
│  JSON Input  ├────►     transon     ├────►  JSON Output  │
└──────────────┘    └─────────────────┘    └───────────────┘
```

Documentation and playground: https://transon-org.github.io/

`transon` is a powerful and flexible JSON template engine that enables developers to transform JSON data using a customizable set of rules. 
With `transon`, you can generate dynamic templates, manipulate JSON data, and produce new JSON structures that meet your specific requirements.

## Development Principles

`transon` was built with a set of key development principles in mind, including:

 - **Flexibility and Extensibility**: `transon` is designed to be highly flexible and extensible, allowing you to add new rules and types of placeholders to suit your unique needs.
 - **Valid JSON Structure**: `transon` templates are defined as valid JSON structures, making them easy to work with and compatible with a wide range of tools and applications.
 - **Composable Rules**: `transon` rules are highly composable, allowing you to define complex behavior patterns using a combination of nested rules. 
For example, arithmetic expressions can be defined with nested rules, where each rule represents a specific operation. 
This approach eliminates the need for a domain-specific language (DSL) for arithmetic expressions.
 - **Marker-Based Templates**: The most important aspect of a `transon` template is the use of the `$` marker. 
This marker is a special key within the JSON structure that distinguishes it from other types of JSON data. 
By default, the `$` key is used as the marker, but you can change it to any other value you prefer.
 
By using a marker-based approach, `transon` ensures that templates are easy to work with and can be easily distinguished from other types of JSON data. 
This makes it simple to generate dynamic templates, manipulate JSON data, and produce new JSON structures that meet your specific requirements. 
Additionally, the composable rules approach allows for advanced behavior patterns that can be defined using a combination of nested rules, making `transon` highly flexible and extensible.

## Installation
`transon` can be installed using pip, the Python package manager. 
Simply run the following command:

```shell
pip install transon
```

## Inspired by
 - [XSLT](https://en.wikipedia.org/wiki/XSLT)
 - [JsonLogic](https://jsonlogic.com/)

## Analogues

[json-template](https://github.com/datavis-tech/json-templates) - a lightweight JSON template engine for JavaScript that provides a simple way to generate JSON data from templates. 
It supports placeholders for data values, expressions, and conditions, and can be used to generate complex JSON data structures.

[jsonnet](https://github.com/google/jsonnet) - a flexible templating language for generating JSON data that is used by companies like Google, Uber, and Red Hat. 
It allows developers to define templates using a domain-specific language that supports expressions, conditions, and functions.

[jolt](https://github.com/bazaarvoice/jolt) - a JSON-to-JSON transformation library that allows developers to define transformation specifications using a simple and intuitive syntax. 
It supports a wide range of transformation operations, including mapping, filtering, sorting, and grouping. 

[jsonata](https://github.com/jsonata-js/jsonata) - a powerful data transformation language for JSON data that supports complex queries, transformations, and aggregations. 
It can be used to generate JSON output from input data or transform JSON data into other formats.
