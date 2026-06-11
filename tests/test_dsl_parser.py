import pytest
from dtracktoolkit.query_language import LambdaFilterTag, LambdaFilterName, MinimalFetcher, dependo_script


def test_lambdafilter_string():
    ast = dependo_script.parse("tag1")
    filter_function = LambdaFilterTag().transform(ast)
    data = [{"name": "Project1", "tags": [{"name": "tag1"}, {"name": "tag2"}]}]
    assert list(filter(filter_function, data)) == data

    ast = dependo_script.parse("tag3")
    filter_function = LambdaFilterTag().transform(ast)
    assert list(filter(filter_function, data)) == []

def test_lambdafilter_and():
    ast = dependo_script.parse("tag1 AND tag2")
    filter_function = LambdaFilterTag().transform(ast)
    data = [
        {"name": "Project1", "tags": [{"name": "tag1"}, {"name": "tag2"}]},
        {"name": "Project2", "tags": [{"name": "tag1"}, {"name": "tag3"}]},
    ]
    assert list(filter(filter_function, data)) == [data[0]]


def test_lambdafilter_or():
    ast = dependo_script.parse("tag1 OR tag3")
    filter_function = LambdaFilterTag().transform(ast)
    data = [
        {"name": "Project1", "tags": [{"name": "tag1"}, {"name": "tag2"}]},
        {"name": "Project2", "tags": [{"name": "tag1"}, {"name": "tag3"}]},
        {"name": "Project3", "tags": [{"name": "tag4"}]},
    ]
    assert list(filter(filter_function, data)) == [data[0], data[1]]


def test_lambdafilter_not():
    ast = dependo_script.parse("NOT tag1")
    filter_function = LambdaFilterTag().transform(ast)
    data = [
        {"name": "Project1", "tags": [{"name": "tag1"}]},
        {"name": "Project2", "tags": [{"name": "tag2"}]},
    ]
    assert list(filter(filter_function, data)) == [data[1]]


def test_lambdafilter_complex():
    ast = dependo_script.parse("(tag1 AND tag2) OR tag3")
    filter_function = LambdaFilterTag().transform(ast)
    data = [
        {"name": "Project1", "tags": [{"name": "tag1"}, {"name": "tag2"}]},
        {"name": "Project2", "tags": [{"name": "tag1"}, {"name": "tag3"}]},
        {"name": "Project3", "tags": [{"name": "tag4"}]},
    ]
    assert list(filter(filter_function, data)) == [data[0], data[1]]


def test_lambdafilter_empty_data():
    ast = dependo_script.parse("tag1")
    filter_function = LambdaFilterTag().transform(ast)
    data = []
    assert list(filter(filter_function, data)) == []


def test_lambdafilter_no_matching_tags():
    ast = dependo_script.parse("tag1")
    filter_function = LambdaFilterTag().transform(ast)
    data = [{"name": "Project1", "tags": [{"name": "tag2"}]}]
    assert list(filter(filter_function, data)) == []

def test_lambdafiltername_string():
    ast = dependo_script.parse("Project1")
    filter_function = LambdaFilterName().transform(ast)
    data = [{"name": "Project1", "tags": [{"name": "tag1"}, {"name": "tag2"}]}]
    assert list(filter(filter_function, data)) == data

    ast = dependo_script.parse("Project2")
    filter_function = LambdaFilterName().transform(ast)
    assert list(filter(filter_function, data)) == []


def test_lambdafiltername_and():
    ast = dependo_script.parse("Project1 AND PY")
    filter_function = LambdaFilterName().transform(ast)
    data = [
        {"name": "Project1.PY"},
        {"name": "Project1"},
    ]
    assert list(filter(filter_function, data)) == [data[0]]


def test_lambdafiltername_or():
    ast = dependo_script.parse("Project1 OR Project3")
    filter_function = LambdaFilterName().transform(ast)
    data = [
        {"name": "Project1_test"},
        {"name": "Project2_random"},
        {"name": "Project3_substrings"}
    ]
    assert list(filter(filter_function, data)) == [data[0], data[2]]


def test_lambdafiltername_not():
    ast = dependo_script.parse("NOT Project1")
    filter_function = LambdaFilterName().transform(ast)
    data = [
        {"name": "Project1", "tags": [{"name": "tag1"}]},
        {"name": "Project2", "tags": [{"name": "tag2"}]},
    ]
    assert list(filter(filter_function, data)) == [data[1]]


def test_lambdafiltername_empty_data():
    ast = dependo_script.parse("Project1")
    filter_function = LambdaFilterName().transform(ast)
    data = []
    assert list(filter(filter_function, data)) == []


def test_lambdafiltername_no_matching_names():
    ast = dependo_script.parse("Project1")
    filter_function = LambdaFilterName().transform(ast)
    data = [{"name": "Project2", "tags": [{"name": "tag2"}]}]
    assert list(filter(filter_function, data)) == []

def test_tagfetcher_simple():
    ast = dependo_script.parse("tag1")
    tag_list = MinimalFetcher().transform(ast)
    assert tag_list == "tag1"


def test_tagfetcher_multiple_and():
    ast = dependo_script.parse("tag1 AND tag2 AND tag3 AND tag4")
    tag_list = MinimalFetcher().transform(ast)
    assert tag_list == "tag1"


def test_tagfetcher_multiple_complex():
    ast = dependo_script.parse("(tag1 AND tag2) OR tag4")
    tag_list = MinimalFetcher().transform(ast)
    assert tag_list == ["tag1", "tag4"]
