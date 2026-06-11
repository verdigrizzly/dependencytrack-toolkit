import pytest
import sys
import copy
from furl import furl
from loguru import logger

from tests.sample import PROJECT_LIST_RESPONSE, FINDINGS_HAPPY_TEST_V1 
from src.dtracktoolkit.urls import UrlBase

@pytest.fixture
def urlbase():
    return UrlBase()

@pytest.fixture
def url():
    return furl("api/v1/project")

def test_project_valid(urlbase, url):
    input_validated = urlbase.validate_json(PROJECT_LIST_RESPONSE, url)
    assert input_validated == PROJECT_LIST_RESPONSE

def test_project_valid_with_chinese_characters(urlbase, url):
    valid_projects_copy = copy.deepcopy(PROJECT_LIST_RESPONSE)
    valid_projects_copy[0]["name"] = "TEAM很酷" * 5
    input_validated = urlbase.validate_json(valid_projects_copy, url)
    assert input_validated == valid_projects_copy

def test_project_valid_remove_unnecessary_property(urlbase, url):
    valid_projects_copy = copy.deepcopy(PROJECT_LIST_RESPONSE)
    del valid_projects_copy[0]["lastBomImport"]
    input_validated = urlbase.validate_json(valid_projects_copy, url)
    assert input_validated == valid_projects_copy

def test_project_valid_add_invalid_field(capsys, urlbase, url):
    logger.add(sys.stderr, format="[<level>{level}</level>] {message}", level="DEBUG")
    invalid_projects = copy.deepcopy(PROJECT_LIST_RESPONSE)
    invalid_projects[0]["testattribute"] = "hello"
    input_validated = urlbase.validate_json(invalid_projects, url)

    captured = capsys.readouterr()
    
    assert "Reason: Extra inputs are not permitted" in captured.err and "Location: ('testattribute',)" in captured.err
    # we want to preserve the length of the list
    assert len(input_validated) == len(invalid_projects)
    assert input_validated == [None]

def test_project_valid_name_is_integer(capsys, urlbase, url):
    logger.add(sys.stderr, format="[<level>{level}</level>] {message}", level="DEBUG")
    invalid_projects = copy.deepcopy(PROJECT_LIST_RESPONSE)
    invalid_projects[0]["name"] = 5
    input_validated = urlbase.validate_json(invalid_projects, url)
    
    captured = capsys.readouterr()

    assert "Reason: Input should be a valid string" in captured.err and "Location: ('name',)" in captured.err
    # we want to preserve the length of the list
    assert len(input_validated) == len(invalid_projects)
    assert input_validated == [None]

def test_project_valid_no_correct_uuid(capsys, urlbase, url):
    logger.add(sys.stderr, format="[<level>{level}</level>] {message}", level="DEBUG")
    invalid_projects = copy.deepcopy(PROJECT_LIST_RESPONSE)
    invalid_projects[0]["uuid"] = "a" * 5
    input_validated = urlbase.validate_json(invalid_projects, url)

    captured = capsys.readouterr()
    
    assert "Reason: String should match pattern '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" in captured.err and "Location: ('uuid',)" in captured.err
    # we want to preserve the length of the list
    assert len(input_validated) == len(invalid_projects)
    assert input_validated == [None]


def test_finding(urlbase):
    url = furl("api/v1/finding")
    valid = urlbase.validate_json(FINDINGS_HAPPY_TEST_V1, url)
    assert valid == FINDINGS_HAPPY_TEST_V1 
