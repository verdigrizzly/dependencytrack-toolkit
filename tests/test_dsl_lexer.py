from lark import Token

from dtracktoolkit.query_language import dependo_script

def test_special_characters():
    special_characters = "_-&.$%+,/:;=?@#|^"

    for special in special_characters:
        ast = dependo_script.parse(special)
        assert ast.children == [Token("CNAME", special)]


def test_string_combination_characters():
    special_string = "a123&"
    ast = dependo_script.parse(special_string)
    assert ast.children == [Token("CNAME", "a123&")]
    assert ast.data == Token("RULE", "string")


def test_operation_in_string():
    special_string = "ANDst"
    ast = dependo_script.parse(special_string)
    assert ast.children == [Token("CNAME", "ANDst")]
    assert ast.data == Token("RULE", "string")
