"""Schemata to validate config sections for automated execution"""

from __future__ import annotations
import json
from loguru import logger
from typing import List, Optional, Coroutine
from pydantic import BaseModel, ConfigDict, Field

from src.utility import opener
# hack to use dtracktoolkit without installing it
import sys
sys.path.insert(0, './src')
from dtracktoolkit.notification import notifications
from dtracktoolkit.project import projects

class AbstractTask(BaseModel):
    task_type: str = "Task"
    title: Optional[str] = "None"
    log_file: Optional[str] = Field(alias="log-file", default=None)
    output_file: Optional[str] = Field(alias="output", default=None)
    priority: int = 0
    debug: Optional[bool] = True
    dryrun: Optional[bool] = False

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    async def execute_task(self) -> bool:
        logger.info(f"###{self.task_type} - {self.title}###")
        # TODO: uniform the task_type in stats to match output of cli tool
        stats = {}
        for k, v in self.__dict__.items():
            if v:
                logger.info(f"{k}: {v}")
                stats[k] = v
        index = self._add_log_sink()
        result = await self._task()
        if self.output_file and result:
            with open(self.output_file, "w+") as fh:
                result["stats"] = stats
                json.dump(result, fh)
        if index:
            logger.remove(index)
        return True

    def _add_log_sink(self):
        LOG_LEVEL = "DEBUG" if self.debug else "INFO"
        sink_index = None
        if self.log_file:
            logger.enable("dtracktoolkit")
            sink_index = logger.add(
                self.log_file,
                format="{time:YYYY-MM-DD at HH:mm:ss} [{level}] {message}",
                level=LOG_LEVEL,
                opener=opener,
            )
        return sink_index

    def _task(self) -> Coroutine:
        raise NotImplementedError


class DeleteExpiredItem(AbstractTask):
    task_type: str = "Delete Expired"
    days_since: int = Field(..., alias="days-since")
    safe_tag: Optional[List[str]] = Field(default=None, alias="safe-tag")

    def _task(self) -> Coroutine:
        return projects.delete_expired(
            days_since=self.days_since,
            safe_tag=self.safe_tag,
            force=True,
            dryrun=self.dryrun,
        )


class CountVulnerableItem(AbstractTask):
    task_type: str = "Count Vulnerable"
    min_crit: str = Field(..., alias="min-crit")
    from_name: str = Field(default=None, alias="from-name")
    from_tag: str = Field(default=None, alias="from-tag")
    exclude_classifier: Optional[List] = Field(default=None, alias="exclude-classifier")
    shallow: Optional[bool] = Field(alias="shallow", default=False)

    def _task(self) -> Coroutine:
        return projects.count_vulnerable(
            crit=self.min_crit,
            tag_query=self.from_tag,
            name_query=self.from_name,
            exclude_classifiers=self.exclude_classifier,
            shallow=self.shallow,
        )


class AverageFindingAgeItem(AbstractTask):
    task_type: str = "Average Finding Age"
    min_crit: str = Field(..., alias="min-crit")
    from_tag: str = Field(default=None, alias="from-tag")
    exclude_classifier: Optional[List] = Field(default=None, alias="exclude-classifier")
    shallow: Optional[bool] = Field(default=False, alias="shallow")

    def _task(self) -> Coroutine:
        return projects.average_finding_age(
            crit=self.min_crit,
            tag=self.from_tag,
            exclude_classifiers=self.exclude_classifier,
            shallow=self.shallow,
        )


class RemoveTagItem(AbstractTask):
    task_type: str = "Remove Tag"
    removed_tag: str = Field(default=None, alias="removed-tag")
    from_tag: str = Field(default=None, alias="from-tag")
    exclude_classifier: Optional[List] = Field(default=None, alias="exclude-classifier")

    def _task(self) -> Coroutine:
        return projects.remove_tag(
            removed_tag=self.removed_tag,
            tag=self.from_tag,
            exclude_classifiers=self.exclude_classifier,
            force=True,
            dryrun=self.dryrun,
        )


class UpdateProjectItem(AbstractTask):
    task_type: str = "Update projects to rule"
    rule_name: str = Field(..., alias="rule-name")

    def _task(self) -> Coroutine:
        return notifications.alerts_update_projects(
            rule_name=self.rule_name, force=True, dryrun=self.dryrun
        )


class AssignProjectItem(AbstractTask):
    task_type: str = "Assign additional projects to rule"
    rule_name: str = Field(..., alias="rule-name")
    from_tag: List[str] = Field(..., alias="from-tag")

    def _task(self) -> Coroutine:
        return notifications.assign_projects_with_tag(
            rule_name=self.rule_name, tag=self.from_tag, force=True, dryrun=self.dryrun
        )


class RemoveProjectItem(AbstractTask):
    task_type: str = "Remove assigned project from rule"
    rule_name: str = Field(..., alias="rule-name")
    from_tag: List[str] = Field(..., alias="from-tag")

    def _task(self) -> Coroutine:
        return notifications.remove_projects_with_tag(
            rule_name=self.rule_name, tag=self.from_tag, force=True, dryrun=self.dryrun
        )


class Notification(BaseModel):
    update_projects: List[UpdateProjectItem] = []
    assign_projects: List[AssignProjectItem] = []
    remove_projects: List[RemoveProjectItem] = []


class Project(BaseModel):
    delete_expired: List[DeleteExpiredItem] = []
    count_vulnerable: List[CountVulnerableItem] = []
    average_finding_age: List[AverageFindingAgeItem] = []
    remove_tag: List[RemoveTagItem] = []


class Toolkit(BaseModel):
    project: Optional[Project] = None
    notification: Optional[Notification] = None


class Config(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    toolkit: Optional[Toolkit]
