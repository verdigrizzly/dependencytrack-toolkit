import pytest
import respx
from httpx import Response
from copy import deepcopy

from src.dtracktoolkit.project import count_vulnerable
from tests.sample import (
    FIRSTTAG_URL,
    FIRSTTAG_RESPONSE,
    FINDINGS_V1_URL,
    FINDINGS_V2_URL,
    FINDINGS_HAPPY_TEST_V1,
    FINDINGS_HAPPY_TEST_V2
)

pytestmark = pytest.mark.asyncio(loop_scope="module")
@pytest.fixture(autouse=True)
def run_before_each_test():
    respx.reset()
    respx.get(FIRSTTAG_URL).mock(return_value=Response(200, json=FIRSTTAG_RESPONSE))
    
    # Mock findings
    rsp = respx.get(FINDINGS_V1_URL)
    rsp.return_value = Response(200, json=FINDINGS_HAPPY_TEST_V1)
    rsp = respx.get(FINDINGS_V2_URL)
    rsp.return_value = Response(200, json=FINDINGS_HAPPY_TEST_V2)

@respx.mock
async def test_count_vulnerable_base():
    output = await count_vulnerable(crit="UNASSIGNED", tag_query="FIRSTTAG")

    assert type(output) == dict
    assert len(output) == 4
    assert output['result']['amount_projects'] == 2
    assert output['result']['vulnerable_projects'] == 2

@respx.mock
async def test_count_vulnerable_output():
    output = await count_vulnerable(crit="UNASSIGNED", tag_query="FIRSTTAG")
    project_v1 = output['projects'][0]
    project_v2 = output['projects'][1]
    assert project_v1['findings'] == 3
    assert project_v1['vulnerabilities'] == 2
    assert project_v1['vulnerabilities_dict'] == {0: 1, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0}
    assert project_v1['vulnerabilities_fixable_dict'] == {0: 1, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    assert project_v2['findings'] == 1
    assert project_v2['vulnerabilities'] == 1
    assert project_v2['vulnerabilities_dict'] == {0: 0, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0}
    assert project_v2['vulnerabilities_fixable_dict'] == {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

@respx.mock
async def test_count_vulnerable_no_projects():
    # Mock no projects found
    rsp = respx.get(FIRSTTAG_URL)
    rsp.return_value = Response(200, json=[])

    output = await count_vulnerable(crit="UNASSIGNED", tag_query="FIRSTTAG")
    assert output['result']['amount_projects'] == 0
    assert output['result']['vulnerable_projects'] == 0
    assert output['projects'] == []

@respx.mock
async def test_count_vulnerable_no_findings():
    # Mock findings with no vulnerabilities
    rsp = respx.get(FINDINGS_V1_URL)
    rsp.return_value = Response(200, json=[])
    rsp = respx.get(FINDINGS_V2_URL)
    rsp.return_value = Response(200, json=[])

    output = await count_vulnerable(crit="UNASSIGNED", tag_query="FIRSTTAG")
    assert output['result']['amount_projects'] == 2
    assert output['result']['vulnerable_projects'] == 0
    assert output['projects'][0]['vulnerabilities_dict'] == {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    assert output['projects'][1]['vulnerabilities_dict'] == {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

@respx.mock
async def test_count_vulnerable_critical():
    output = await count_vulnerable(crit="CRITICAL", tag_query="FIRSTTAG")
    assert output['result']['amount_projects'] == 2
    assert output['result']['vulnerable_projects'] == 1

    # We still want all information in the output, even though we are filtering for critical
    assert output['projects'][0]['vulnerabilities_dict'] == {0: 1, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0}
    assert output['projects'][1]['vulnerabilities_dict'] == {0: 0, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0}

@respx.mock
async def test_count_vulnerable_supressed():
    # Set all three projects to supressed
    TMP_V1 = deepcopy(FINDINGS_HAPPY_TEST_V1)
    TMP_V2 = deepcopy(FINDINGS_HAPPY_TEST_V2)
    for finding in TMP_V1:
        finding["analysis"]["isSuppressed"] = True
    for finding in TMP_V2:
        finding["analysis"]["isSuppressed"] = True
    rsp = respx.get(FINDINGS_V1_URL)
    rsp.return_value = Response(200, json=TMP_V1)
    rsp = respx.get(FINDINGS_V2_URL)
    rsp.return_value = Response(200, json=TMP_V2)
  
    output = await count_vulnerable(crit="UNASSIGNED", tag_query="FIRSTTAG")
    assert output['result']['vulnerable_projects'] == 0
    assert output['projects'][0]['vulnerabilities_dict'] == {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

@respx.mock
async def test_count_vulnerable_exclude_classifier():
    output = await count_vulnerable(crit="UNASSIGNED", tag_query="FIRSTTAG", exclude_classifiers=["LIBRARY"])
    assert output['result']['amount_projects'] == 1

@respx.mock
async def test_count_vulnerable_shallow_call_count():
    output = await count_vulnerable(crit="UNASSIGNED", tag_query="FIRSTTAG", shallow=True)

    rsp_v1 = respx.get(FINDINGS_V1_URL)
    rsp_v2 = respx.get(FINDINGS_V2_URL)
    assert rsp_v1.call_count == 0
    assert rsp_v2.call_count == 0

@respx.mock
async def test_count_vulnerable_shallow_information():
    output = await count_vulnerable(crit="UNASSIGNED", tag_query="FIRSTTAG", shallow=True)

    project_v1 = output['projects'][0]
    project_v2 = output['projects'][1]
    assert output['result']['amount_projects'] == 2
    assert output['result']['vulnerable_projects'] == 2
    assert project_v1['vulnerabilities'] == 2
    assert project_v2['vulnerabilities'] == 1
    assert output.get('fixable_vulnerabilities', None) == None
    assert output['projects'][0].get('vulnerabilities_dict', None) == None
    assert output['projects'][0].get('vulnerabilities_fixable_dict', None) == None

"""
@respx.mock
async def test_count_vulnerable_parent_search():
    output = await count_vulnerable(crit="low", parent_pattern="parent-project")
    assert output["result"]["vulnerable_projects"] == 0
    assert len(output["projects"]) == 3
    
    output = await count_vulnerable(crit="low", parent_pattern="parent-project:1.0")
    assert output["result"]["vulnerable_projects"] == 0
    assert len(output["projects"]) == 1
    
    output = await count_vulnerable(crit="low", parent_pattern="parent-project:1.")
    assert not output["stats"] and not summary["projects"]
"""
    
