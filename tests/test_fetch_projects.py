import pytest
import respx
from httpx import Response
from copy import deepcopy

from src.dtracktoolkit.urls import UrlBase
from tests.sample import FIRSTTAG_URL, FIRSTTAG_RESPONSE

pytestmark = pytest.mark.asyncio(loop_scope="module")
@pytest.fixture(autouse=True)
def run_before_each_test():
    respx.reset()
    respx.get(FIRSTTAG_URL).mock(return_value=Response(200, json=FIRSTTAG_RESPONSE))

@respx.mock
async def test_with_tagquery():
    url = UrlBase()
    response = await url.fetch_projects_by_tagquery("FIRSTTAG")
    project_v1 = response[0]
    project_v2 = response[1]

    assert len(response) == 2
    assert project_v1['version'] == "1.0"
    assert project_v1['uuid'] == "44f3c5fd-0806-47b1-b22b-caa3d3d91281"
    assert project_v2['version'] == "2.0"
    assert project_v2['uuid'] == "c9330fff-dbb9-4e82-b675-d08bd94a4c17"

@respx.mock
async def test_with_tagquery_duplicate():
    TMP_FIRSTTAG_RESPONSE = deepcopy(FIRSTTAG_RESPONSE)
    TMP_FIRSTTAG_RESPONSE.append(FIRSTTAG_RESPONSE[0])
    respx.get(FIRSTTAG_URL).mock(return_value=Response(200, json=FIRSTTAG_RESPONSE))
    url = UrlBase()
    
    response = await url.fetch_projects_by_tagquery("FIRSTTAG")
    # Duplicate should not be included
    assert len(response) == 2