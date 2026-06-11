import pytest
from _pytest.logging import LogCaptureFixture
from loguru import logger
import respx
from httpx import Response
from freezegun import freeze_time
from src.dtracktoolkit.project import analyze_vulnerabilities, count_vulnerable, average_finding_age
from tests.sample import (
    FIRSTTAG_URL,
    FIRSTTAG_RESPONSE,
    FINDINGS_V1_URL,
    FINDINGS_V2_URL,
    FINDINGS_HAPPY_TEST_V1,
    FINDINGS_HAPPY_TEST_V2
)
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

@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=False,
    )
    yield caplog
    logger.remove(handler_id)


pytestmark = pytest.mark.asyncio(loop_scope="module")
@pytest.fixture(autouse=True)
def run_before_each_test():
    respx.reset()
    respx.get(FIRSTTAG_URL).mock(return_value=Response(200, json=FIRSTTAG_RESPONSE))
    respx.get(FIRSTTAG_URL_2).mock(return_value=Response(200, json=[]))

    # Mock findings
    rsp = respx.get(FINDINGS_V1_URL)
    rsp.return_value = Response(200, json=FINDINGS_HAPPY_TEST_V1)
    rsp = respx.get(FINDINGS_V2_URL)
    rsp.return_value = Response(200, json=FINDINGS_HAPPY_TEST_V2)

    # Mock notifications
    respx.get(NOTIFICATION_URL).mock(return_value=Response(200, json=NOTIFICATION_RESPONSE))
    respx.post(ADD_NOTIFY_V1_URL).mock(Response(200))
    respx.post(ADD_NOTIFY_V2_URL).mock(Response(200))
    respx.delete(DELETE_NOTIFY_V1_URL).mock(Response(200))
    respx.delete(DELETE_NOTIFY_V2_URL).mock(Response(200))
    
@respx.mock
@freeze_time("2023-09-17 01:23:45")
async def test_logs_analyze_vulnerabilities(caplog):
    await analyze_vulnerabilities(crit="UNASSIGNED", tag_query="FIRSTTAG")

    assert "RESULT: Of 2 projects, 2 are vulnerable with findings of severity 'UNASSIGNED' or higher." in caplog.records[-3].message
    assert 'Found 4 open findings with an average age of 36 days.' in caplog.records[-2].message
    assert 'Found 3 unique open vulnerabilities with an average age of 38 days.' in caplog.records[-1].message
    
@respx.mock
async def test_logs_count_vulnerable(caplog):
    await count_vulnerable(crit="UNASSIGNED", tag_query="FIRSTTAG")
    assert 'Project happy-test:1.0 vulnerable with 2 vulnerabilities (3 findings)! 1 of those are fixable.' in caplog.text
    assert 'RESULT: Of 2 projects, 2 have been found to be vulnerable with at least one finding of severity rank UNASSIGNED.' in caplog.text

"""
@respx.mock
async def test_logs_average_finding(caplog):
    await average_finding_age(crit="UNASSIGNED", tag="FIRSTTAG")

    assert 'Fetching findings for 2 projects' in caplog.text
    assert 'Project happy-test:1.0 has findings as old as 567 days!' in caplog.text
    assert 'Project happy-test:2.0 has findings as old as 586 days!' in caplog.text
    assert 'RESULT: there are 4 open findings of severity UNASSIGNED with an average age of 572 days' in caplog.text    
"""

@respx.mock
async def test_logs_add_notification(caplog):
    await assign_projects_with_tag("team-test-mail", tag=["FIRSTTAG"], force=True)

    assert 'Tagged projects not part of team-test-mail:' in caplog.text
    assert 'Project: happy-test:2.0 [MISSING]' in caplog.text

@respx.mock
async def test_logs_remove_notification(caplog):
    await remove_projects_with_tag("team-test-mail", tag=["FIRSTTAG"], force=True)
    
    assert 'Projects part of team-test-mail to remove:' in caplog.text
    assert 'Project: happy-test:1.0 [REMOVE]' in caplog.text
