import pytest
import respx
from httpx import Response
from datetime import datetime, timedelta
from freezegun import freeze_time
from src.dtracktoolkit.project.projects import delete_expired
from tests.sample import (
    DELETE_PROJECT_URL,
    PROJECT_URL,
    PROJECT_LIST_RESPONSE,
    APP_PROJECT,
)

pytestmark = pytest.mark.asyncio(loop_scope="module")
@pytest.fixture(autouse=True)
def run_before_each_test():
    respx.reset()


@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_delete_expired_normal():
    rsp = respx.get(PROJECT_URL)
    rsp.return_value = Response(200, json=PROJECT_LIST_RESPONSE)
    rsp_del = respx.delete(DELETE_PROJECT_URL + APP_PROJECT["uuid"]).mock(Response(204))
    await delete_expired(0, force=True)
    assert rsp_del.call_count == 1


@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_delete_just_after_threshold():
    new_bom_upload = datetime.now() - timedelta(days=10, seconds=1)
    APP_PROJECT["lastBomImport"] = int(new_bom_upload.timestamp() * 1000)
    rsp = respx.get(PROJECT_URL)
    rsp.return_value = Response(200, json=PROJECT_LIST_RESPONSE)
    rsp_del = respx.delete(DELETE_PROJECT_URL + APP_PROJECT["uuid"]).mock(Response(204))

    await delete_expired(10, force=True)
    assert rsp_del.call_count == 1


@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_delete_expired_created_now():
    new_bom_upload = datetime.now() - timedelta(seconds=1)
    APP_PROJECT["lastBomImport"] = int(new_bom_upload.timestamp() * 1000)
    rsp = respx.get(PROJECT_URL)
    rsp.return_value = Response(200, json=PROJECT_LIST_RESPONSE)
    rspdel = respx.delete(DELETE_PROJECT_URL + APP_PROJECT["uuid"]).mock(Response(204))

    await delete_expired(0, force=True)
    assert rspdel.call_count == 1

@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_delete_just_before_threshold():
    new_bom_upload = datetime.now() - timedelta(days=9, hours=23, minutes=59, seconds=59)
    APP_PROJECT["lastBomImport"] = int(new_bom_upload.timestamp() * 1000)
    rsp = respx.get(PROJECT_URL)
    rsp.return_value = Response(200, json=PROJECT_LIST_RESPONSE)
    rsp_del = respx.delete(DELETE_PROJECT_URL + APP_PROJECT["uuid"]).mock(Response(204))

    await delete_expired(10, force=True)
    assert rsp_del.call_count == 0
