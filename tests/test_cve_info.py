import pytest
import respx
from httpx import Response
from copy import deepcopy

from src.dtracktoolkit.project import cve_info 
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
async def test_cve_info_base():
    output = await cve_info(tag_query="FIRSTTAG")
    cve_2023_40267 = output[0]
    assert type(output) == list 
    assert len(output) == 2
    assert cve_2023_40267['cve_name'] == 'CVE-2023-40267'
    assert cve_2023_40267['aliases'] == [{'cveId': 'CVE-2023-40267', 'ghsaId': 'GHSA-248v-346w-9cwc'}]
    assert cve_2023_40267['severity'] ==  'CRITICAL'
    assert cve_2023_40267['cvss_v3'] == 9.8
    assert cve_2023_40267['affected'] == 1

@respx.mock
async def test_cve_info_multiple_projects_cve():
    output = await cve_info(tag_query="FIRSTTAG")
    cve_2022_0338 = output[1]
    assert cve_2022_0338['affected'] == 2