import pytest
import respx
from httpx import Response
from freezegun import freeze_time
from src.dtracktoolkit.project import average_finding_age, count_vulnerable
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
    
    # Findings V1 31 Days
    # Finding V2 49 Days
    rsp = respx.get(FINDINGS_V1_URL)
    rsp.return_value = Response(200, json=FINDINGS_HAPPY_TEST_V1)
    rsp = respx.get(FINDINGS_V2_URL)
    rsp.return_value = Response(200, json=FINDINGS_HAPPY_TEST_V2)

@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_average_finding_base():
    output = await average_finding_age(crit="UNASSIGNED", tag="FIRSTTAG")

    assert type(output) == dict
    assert len(output) == 4
    assert len(output['projects']) == 2

@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_average_finding_output():
    output = await average_finding_age(crit="UNASSIGNED", tag="FIRSTTAG")

    project_v1 = output['projects'][0]
    project_v2 = output['projects'][1]

    assert project_v1['oldest_finding_days'] == 31
    assert project_v2['oldest_finding_days'] == 51
    assert output['result']['open_findings'] == 4
    # Resulting in inflated numbers
    # V1 has 3 findings (attributed at the same time), V2 has 1 finding
    assert output['result']['average_age'] == int((3*31 + 51) / 4)

@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_average_finding_critical():
    output = await average_finding_age(crit="CRITICAL", tag="FIRSTTAG")

    assert output['result']['open_findings'] == 1
    assert output['result']['average_age'] == 31

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
    output = await average_finding_age(crit="UNASSIGNED", tag="FIRSTTAG")

    assert output['result']['open_findings'] == 0
    assert output['result']['average_age'] == 0
    assert len(output['projects']) == 0

@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_average_finding_output_exclude_classifier():
    output = await average_finding_age(crit="UNASSIGNED", tag="FIRSTTAG", exclude_classifiers=["LIBRARY"])

    project_v2 = output['projects'][0]
    assert project_v2['oldest_finding_days'] == 51
    assert output['result']['average_age'] == 51
    assert len(project_v2['findings']) == 1
    assert project_v2['findings'][0]['vulnId'] == "CVE-2022-0338"
    assert project_v2['findings'][0]['severity'] == "MEDIUM"
    assert project_v2['findings'][0]['age_days'] == 51
    
@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_average_finding_number_of_vulns():
    output_average_age = await average_finding_age(crit="UNASSIGNED", tag="FIRSTTAG")
    output_count_vuln = await count_vulnerable(crit="UNASSIGNED", tag_query="FIRSTTAG")
    
    no_of_vulns_project_average_age_v1 = len(output_average_age['projects'][0]['vulnerabilities'])
    no_of_vulns_project_count_vulns_v1 = output_count_vuln['projects'][0]['vulnerabilities']

    assert no_of_vulns_project_average_age_v1 == no_of_vulns_project_count_vulns_v1

