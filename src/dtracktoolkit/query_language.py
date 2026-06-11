"""Boolean query language parser for filtering Dependency-Track projects by tag or name."""
from typing import Callable
from lark import Lark, Transformer

NOT_TOKEN = "NOT_"

"""
DSL that gets used to parse the input from an operation of Tags. Operations that get accepted
are AND, OR and NOT. With the parse() Function from Lark this gets converted into an AST,
using normal boolean Logic.

Input: "NAME1 OR (NAME2 AND NAME3)"
Output using dependoscript.parse():
or_op
  string        NAME1
  and_op
    string      NAME2
    string      NAME3
"""
dependo_script = Lark(
    r"""
    ?value: string | cond

    ?cond: and_op
        | or_op
        | not_op
        | "(" value ")"

    and_op : value "AND" value
    or_op : value "OR" value
    not_op : "NOT" value
    string: CNAME

    CNAME: (SPECIALCHARS|LETTER|DIGIT) (SPECIALCHARS|LETTER|DIGIT)*
    SPECIALCHARS: "_" | "-" | "&" | "." | "$" | "%" | "+" | "," | "/" | ":" | ";" | "=" | "?" | "@" | "#" | "|" | "^"
    %import common.LETTER
    %import common.DIGIT
    %import common.WS
    %ignore WS
    """,
    start="value",
)


class MinimalFetcher(Transformer):
    """
    This class transforms an AST with basic boolean logic AND, OR, NOT into
    a list of names that have to be fetched to complete the query correctly.
    If tags are (NAME1 and NAME2) only NAME1 has to be fetched and we can filter by NAME2.

    Input: "NAME1 OR (NAME2 AND NAME3)" [AST Form]
    Output: ["NAME1", "NAME2"]
    """

    def string(self, s) -> str:
        """Return the token string value."""
        (s,) = s
        return s[0:]

    def and_op(self, items: tuple) -> list:
        """Return the left operand, skipping NOT tokens since only the other side needs fetching."""
        if isinstance(items[0], str) and items[0] == NOT_TOKEN:
            return items[1]
        if isinstance(items[1], str) and items[1] == NOT_TOKEN:
            return items[0]
        return items[0]

    def or_op(self, items: tuple) -> list:
        """Return the union of both operands as a flat list of names to fetch."""
        if isinstance(items[0], list):
            return items[0] + [items[1]]
        if isinstance(items[1], list):
            return items[1] + [items[0]]
        return [items[0], items[1]]

    def not_op(self, items: tuple) -> list:
        """Return the NOT sentinel so the parent and_op knows to skip this side."""
        return NOT_TOKEN


class LambdaFilterTag(Transformer):
    """
    This class transforms an AST with basic boolean logic AND, OR, NOT into
    a corresponding lambda function used for filtering tags.
    The string functions filters if the tag is contained in the list provided

    Input: "NAME1 OR (NAME2 AND NAME3)" [AST Form]
    Output: lambda x: NAME1 in x OR (NAME2 in x and NAME3 in x)
    """

    def string(self, s) -> Callable:
        """Return a filter that matches projects whose tags contain the given string."""
        (s,) = s
        return lambda x: ("tags" in x) and ({"name": s[0:].lower()} in x["tags"])

    def and_op(self, items: tuple) -> Callable:
        """Return a filter that is the logical AND of two sub-filters."""
        return lambda x: items[0](x) and items[1](x)

    def or_op(self, items: tuple) -> Callable:
        """Return a filter that is the logical OR of two sub-filters."""
        return lambda x: items[0](x) or items[1](x)

    def not_op(self, items: Callable) -> Callable:
        """Return a filter that negates a sub-filter."""
        return lambda x: not items[0](x)


class LambdaFilterName(Transformer):
    """
    Clone of LambdaFilterTag, but this time string() filters the name of the project.
    """

    def string(self, s) -> Callable:
        """Return a filter that matches projects whose name contains the given string."""
        (s,) = s
        return lambda x: ("name" in x) and (s[0:] in x["name"])

    def and_op(self, items: tuple) -> Callable:
        """Return a filter that is the logical AND of two sub-filters."""
        return lambda x: items[0](x) and items[1](x)

    def or_op(self, items: tuple) -> Callable:
        """Return a filter that is the logical OR of two sub-filters."""
        return lambda x: items[0](x) or items[1](x)

    def not_op(self, items: Callable) -> Callable:
        """Return a filter that negates a sub-filter."""
        return lambda x: not items[0](x)


def get_lambda_filter_by_name(query: str):
    """Parse a query string and return a callable that filters projects by name."""
    ast_tree = dependo_script.parse(query)
    return LambdaFilterName().transform(ast_tree)


def get_lambda_filter_by_tag(query: str):
    """Parse a query string and return a callable that filters projects by tag."""
    ast_tree = dependo_script.parse(query)
    return LambdaFilterTag().transform(ast_tree)
