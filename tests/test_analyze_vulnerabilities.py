import pytest
import respx
from httpx import Response
from copy import deepcopy
from freezegun import freeze_time
from src.dtracktoolkit.project import analyze_vulnerabilities
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
async def test_analyze_vulnerabilities_base():
    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG")

    assert type(output) == dict
    assert len(output) == 4
    assert output['result']['amount_projects'] == 2
    assert output['result']['vulnerable_projects'] == 2

@respx.mock
async def test_analyze_vulnerabilities_output():
    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG")
    project_v1 = output['projects'][0]
    project_v2 = output['projects'][1]
    assert project_v1['relevant_findings_count'] == 3
    assert project_v1['relevant_vulns_count'] == 2
    assert project_v1['grouped_vulns'] == {0: 1, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0}
    assert project_v1['grouped_vulns_fixable'] == {0: 1, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    assert project_v2['relevant_findings_count'] == 1
    assert project_v2['relevant_vulns_count'] == 1
    assert project_v2['grouped_vulns'] == {0: 0, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0}
    assert project_v2['grouped_vulns_fixable'] == {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

@respx.mock
async def test_analyze_vulnerabilities_no_projects():
    # Mock no projects found
    rsp = respx.get(FIRSTTAG_URL)
    rsp.return_value = Response(200, json=[])

    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG")
    assert output['result']['amount_projects'] == 0
    assert output['result']['vulnerable_projects'] == 0
    assert output['projects'] == []

@respx.mock
async def test_analyze_vulnerabilities_no_findings():
    # Mock findings with no vulnerabilities
    rsp = respx.get(FINDINGS_V1_URL)
    rsp.return_value = Response(200, json=[])
    rsp = respx.get(FINDINGS_V2_URL)
    rsp.return_value = Response(200, json=[])

    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG")
    assert output['result']['amount_projects'] == 2
    assert output['result']['vulnerable_projects'] == 0
    assert output['projects'][0]['grouped_vulns'] == {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    assert output['projects'][1]['grouped_vulns'] == {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

@respx.mock
async def test_analyze_vulnerabilities_critical():
    output = await analyze_vulnerabilities(crit="CRITICAL", tag_query="FIRSTTAG")
    assert output['result']['amount_projects'] == 2
    assert output['result']['vulnerable_projects'] == 1

    # We still want all information in the output, even though we are filtering for critical
    assert output['projects'][0]['grouped_vulns'] == {0: 1, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0}
    assert output['projects'][1]['grouped_vulns'] == {0: 0, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0}

@respx.mock
async def test_analyze_vulnerabilities_supressed():
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
  
    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG")
    assert output['result']['vulnerable_projects'] == 0
    assert output['projects'][0]['grouped_vulns'] == {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

@respx.mock
async def test_analyze_vulnerabilities_exclude_classifier():
    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG", exclude_classifiers=["LIBRARY"])
    assert output['result']['amount_projects'] == 1

@respx.mock
async def test_analyze_vulnerabilities_shallow_call_count():
    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG", shallow=True)

    rsp_v1 = respx.get(FINDINGS_V1_URL)
    rsp_v2 = respx.get(FINDINGS_V2_URL)
    assert rsp_v1.call_count == 0
    assert rsp_v2.call_count == 0

@respx.mock
async def test_analyze_vulnerabilities_shallow_information():
    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG", shallow=True)

    project_v1 = output['projects'][0]
    project_v2 = output['projects'][1]
    assert output['result']['amount_projects'] == 2
    assert output['result']['vulnerable_projects'] == 2
    assert project_v1['relevant_vulns_count'] == 2
    assert project_v2['relevant_vulns_count'] == 1
    assert output.get('relevant_fixable_vulns_count', None) == None
    assert output['projects'][0].get('grouped_vulns', None) == None
    assert output['projects'][0].get('grouped_vulns_fixable', None) == None

"""
@respx.mock
async def test_analyze_vulnerabilities_parent_search():
    output = await analyze_vulnerabilities(crit="low", parent_pattern="parent-project")
    assert output["result"]["vulnerable_projects"] == 0
    assert len(output["projects"]) == 3
    
    output = await analyze_vulnerabilities(crit="low", parent_pattern="parent-project:1.0")
    assert output["result"]["vulnerable_projects"] == 0
    assert len(output["projects"]) == 1
    
    output = await analyze_vulnerabilities(crit="low", parent_pattern="parent-project:1.")
    assert not output["stats"] and not summary["projects"]
"""

@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_average_finding_base():
    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG")

    assert type(output) == dict
    assert len(output) == 4
    assert len(output['projects']) == 2

@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_average_finding_output():
    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG")

    project_v1 = output['projects'][0]
    project_v2 = output['projects'][1]

    assert project_v1['oldest_finding_days'] == 31
    assert project_v2['oldest_finding_days'] == 51
    assert output['result']['total_open_findings'] == 4
    # Resulting in inflated numbers
    # V1 has 3 findings (attributed at the same time), V2 has 1 finding
    assert output['result']['average_finding_age_days'] == int((3*31 + 51) / 4)

@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_average_finding_critical():
    output = await analyze_vulnerabilities(crit="CRITICAL", tag_query="FIRSTTAG")

    assert output['result']['total_open_findings'] == 1
    assert output['result']['average_finding_age_days'] == 31

    project = output['projects'][0]
    assert project['findings'][0]['vulnId'] == "CVE-2023-40267"
    assert project['findings'][0]['severity'] == "CRITICAL"
    assert project['findings'][0]['age_days'] == 31


@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_average_finding_no_findings():
    rsp = respx.get(FINDINGS_V1_URL)
    rsp.return_value = Response(200, json=[])
    rsp = respx.get(FINDINGS_V2_URL)
    rsp.return_value = Response(200, json=[])
    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG")

    assert output['result']['total_open_findings'] == 0
    assert output['result']['average_finding_age_days'] == 0
    assert len(output['projects']) == 2

@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_average_finding_output_exclude_classifier():
    output = await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG", exclude_classifiers=["LIBRARY"])

    project_v2 = output['projects'][0]
    assert project_v2['oldest_finding_days'] == 51
    assert output['result']['average_finding_age_days'] == 51
    assert len(project_v2['findings']) == 1
    assert project_v2['findings'][0]['vulnId'] == "CVE-2022-0338"
    assert project_v2['findings'][0]['severity'] == "MEDIUM"
    assert project_v2['findings'][0]['age_days'] == 51
    
