import pytest
import respx
from httpx import Response
from tests.sample import TEAM_SELF_URL, TEAM_ALL_URL, TEAM_RESPONSE
from src.dtracktoolkit.api_token_manager.token_manager import check_token_permissions, check_token_permissions_self

pytestmark = pytest.mark.asyncio(loop_scope="module")
@pytest.fixture(autouse=True)
def run_before_each_test():
    respx.reset()
    respx.get(TEAM_SELF_URL).mock(return_value=Response(200, json=TEAM_RESPONSE))
    respx.get(TEAM_ALL_URL).mock(return_value=Response(200, json=TEAM_RESPONSE))

@respx.mock
async def test_permission_base():
    output = await check_token_permissions("team-test2")
    team_team = output["matched teams"][0]

    assert isinstance(output, dict)
    assert team_team["team"] == "team-test2"
    assert team_team["keys"][0] == "***45"
    assert team_team["level"] == "ADMIN"
    
@respx.mock
async def test_permission_api():
    output = await check_token_permissions("team-api-permissions")
    team_team = output["matched teams"][0]

    assert isinstance(output, dict)
    assert team_team["team"] == "team-api-permissions"
    assert team_team["keys"][0] == "***IcKW"
    assert team_team["level"] == "API"

@respx.mock
async def test_permission_self():
    output = await check_token_permissions_self()
    assert isinstance(output, dict)
    assert output["matched teams"]

@respx.mock
async def test_permissions_wrong_pattern():
    output = await check_token_permissions("teamasd")
    assert isinstance(output, dict)
    assert not output["matched teams"]

