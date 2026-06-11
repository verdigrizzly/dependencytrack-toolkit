import pytest
import respx
from httpx import Response
from src.dtracktoolkit.notification.notifications import (
    assign_projects_with_tag,
    remove_projects_with_tag,
)
from tests.sample import (
    NOTIFICATION_URL,
    NOTIFICATION_RESPONSE,
    FIRSTTAG_URL,
    FIRSTTAG_URL_2,
    FIRSTTAG_RESPONSE,
    ADD_NOTIFY_V1_URL,
    ADD_NOTIFY_V2_URL,
    DELETE_NOTIFY_V1_URL,
    DELETE_NOTIFY_V2_URL
)

pytestmark = pytest.mark.asyncio(loop_scope="module")
@pytest.fixture(autouse=True)
def run_before_each_test():
    respx.reset()
    respx.get(FIRSTTAG_URL).mock(return_value=Response(200, json=FIRSTTAG_RESPONSE))
    respx.get(FIRSTTAG_URL_2).mock(return_value=Response(200, json=[]))
    respx.get(NOTIFICATION_URL).mock(return_value=Response(200, json=NOTIFICATION_RESPONSE))
    

@respx.mock
async def test_add_notification_general():
    rsp_add_notification_1 = respx.post(ADD_NOTIFY_V1_URL).mock(Response(200))
    rsp_add_notification_2 = respx.post(ADD_NOTIFY_V2_URL).mock(Response(200))
    
    await assign_projects_with_tag("team-test-mail", tag=["FIRSTTAG"], force=True)
    # Project 1 is already part of the notification, should not be called
    assert rsp_add_notification_1.call_count == 0
    assert rsp_add_notification_2.call_count == 1

@respx.mock
async def test_add_notification_caps_sensitive():
    rsp_add_notification_1 = respx.post(ADD_NOTIFY_V1_URL).mock(Response(200))
    rsp_add_notification_2 = respx.post(ADD_NOTIFY_V2_URL).mock(Response(200))
    
    await assign_projects_with_tag("team-test-mail", tag=["FIRSTtag"], force=True)
    # Should not be called, since the tag is case sensitive 
    assert rsp_add_notification_1.call_count == 0
    assert rsp_add_notification_2.call_count == 0

@respx.mock
async def test_remove_notification():
    rsp_del_notification_1 = respx.delete(DELETE_NOTIFY_V1_URL).mock(Response(200))
    rsp_del_notification_2 = respx.delete(DELETE_NOTIFY_V2_URL).mock(Response(200))
    
    await remove_projects_with_tag("team-test-mail", tag=["FIRSTTAG"], force=True)
    # Project 2 is not part of the notification, should not be called
    assert rsp_del_notification_1.call_count == 1
    assert rsp_del_notification_2.call_count == 0

@respx.mock
async def test_add_notification_no_tag():
    rsp_add_notification_1 = respx.post(ADD_NOTIFY_V1_URL).mock(Response(200))
    rsp_add_notification_2 = respx.post(ADD_NOTIFY_V2_URL).mock(Response(200))
    
    await assign_projects_with_tag("team-test-mail", tag=[], force=True)
    assert rsp_add_notification_1.call_count == 0
    assert rsp_add_notification_2.call_count == 0

@respx.mock
async def test_remove_notification_no_tag():
    rsp_del_notification_1 = respx.delete(DELETE_NOTIFY_V1_URL).mock(Response(200))
    rsp_del_notification_2 = respx.delete(DELETE_NOTIFY_V2_URL).mock(Response(200))
    
    await remove_projects_with_tag("team-test-mail", tag=[], force=True)
    assert rsp_del_notification_1.call_count == 1
    assert rsp_del_notification_2.call_count == 0
