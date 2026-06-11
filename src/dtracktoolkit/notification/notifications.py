"""
dependency track notification management
"""

import copy
from itertools import groupby
from operator import itemgetter
from typing import List, Optional
from loguru import logger

from dtracktoolkit.notification.urls import URLs
from dtracktoolkit.utility import (
    remove_duplicate_projects,
    user_approval,
    handle_errors_gracefully,
)
from dtracktoolkit.constants import summary_dict_template


@handle_errors_gracefully
async def alerts_update_projects(rule_name, force=False, dryrun: bool = False):
    """Add all versions of an already added project to the provided alert rule"""
    # fetch a list of all notification rules and extract project by name
    urls = URLs()
    summary_dict = copy.deepcopy(summary_dict_template)
    rule = await urls.fetch_notification_rule(rule_name)
    if not rule:
        logger.error(
            "can't find alert rule for given name ({rule_name}). Nothing to be done - exiting.",
            rule_name=rule_name,
        )
        return

    rule_id = rule["uuid"]
    # Extract projects currently assigned to rule
    projects = rule.get("projects")

    # group projects by project name
    projects = sorted(projects, key=itemgetter("name"))
    project_groups = {k: list(v) for k, v in groupby(projects, key=itemgetter("name"))}

    # Find all versions of a listed project
    # and compare to the list of projects already assigned
    # to the notification rule
    # TODO: this should be an threaded task...
    missing_projects = {}
    for project_name in project_groups.keys():
        if project_name not in missing_projects:
            missing_projects[project_name] = []

        # List of already to rule assigned versions
        versions = [project.get("version") for project in project_groups[project_name]]
        # filter None values
        versions = list(filter(lambda v: v is not None, versions))

        # Fetch all versions of a project from api
        url, param = urls.get_project_data_endpoint_by_name(project_name=project_name)
        data = await urls.async_get_json_from_endpoint(url, url_param=param)

        # compare fetched projects version
        # with already assigned versions
        logger.info("Project: {}:", project_name)
        for project in data:
            version = project.get("version")
            summary_dict["projects"].append({"name": project_name, "version": version})
            if version is None:
                logger.info("  NO VERSION INFO")
            elif version not in versions:
                missing_projects[project_name].append(project)
                summary_dict["missing_projects"].append(
                    {"name": project_name, "version": version}
                )
                logger.info("  {} [MISSING]", version)
            else:
                logger.info("  {}", version)

    if dryrun:
        return summary_dict

    # Asks user to add missing projects, if not sys.exit
    user_approval(
        f"Add missing projects to notification rule ({rule_name})?:(y/N)", force=force
    )
    add_projects_to_notification(
        urls, rule_id=rule_id, missing_projects=missing_projects
    )
    return summary_dict


def add_projects_to_notification(
    urls: URLs, rule_id: str, missing_projects: dict
) -> bool:
    """Add a project to a notification/alert rule"""
    if rule_id:
        for versions in missing_projects.values():
            for project in versions:
                urls.add_project_to_rule(rule_id, project)
        logger.info("Done - bye")


async def __sync_notification_rule_projects(
    rule_name: str,
    tag: list,
    operation: str,
    force: bool,
    dryrun: bool,
):
    urls = URLs()
    summary_dict = copy.deepcopy(summary_dict_template)
    all_fetched_projects = []
    if tag:
        for t in tag:
            all_fetched_projects += await urls.fetch_projects_with_tag(t)
    tagged_projects = remove_duplicate_projects(all_fetched_projects)

    rule = await urls.fetch_notification_rule(rule_name)
    if not rule:
        logger.error(
            "can't find alert rule for given name ({rule_name}). Nothing to be done - exiting.",
            rule_name=rule_name,
        )
        return
    projects_from_rule = rule.get("projects", [])

    if operation == "add":
        affected = [
            p
            for p in tagged_projects
            if not any(r["uuid"] == p["uuid"] for r in projects_from_rule)
        ]
        for p in affected:
            summary_dict["missing_projects"].append(
                {"name": p.get("name"), "version": p.get("version")}
            )
        logger.info("Tagged projects not part of {}:", rule_name)
        for p in affected:
            logger.info(
                "  Project: {}:{} [MISSING]", p.get("name"), p.get("version", "N/A")
            )
        approval_msg = f"Add missing projects to notification rule ({rule_name})?:(y/N)"
    else:
        affected = (
            projects_from_rule
            if not tag
            else [
                p
                for p in tagged_projects
                if any(r["uuid"] == p["uuid"] for r in projects_from_rule)
            ]
        )
        for p in affected:
            summary_dict["projects"].append(
                {"name": p.get("name"), "version": p.get("version")}
            )
        logger.info("Projects part of {} to remove:", rule_name)
        for p in affected:
            logger.info(
                "  Project: {}:{} [REMOVE]", p.get("name"), p.get("version", "N/A")
            )
        approval_msg = (
            f"Remove surplus projects from notification rule ({rule_name})?:(y/N)"
        )

    if dryrun:
        return summary_dict
    user_approval(approval_msg, force=force)
    for p in affected:
        if operation == "add":
            urls.add_project_to_rule(rule_id=rule["uuid"], project=p)
        else:
            urls.remove_project_from_rule(rule_id=rule["uuid"], project=p)
    return summary_dict


@handle_errors_gracefully
async def assign_projects_with_tag(
    rule_name: str, tag: list, force: bool = False, dryrun: bool = False
):
    """Add all tagged projects to a notification rule"""
    return await __sync_notification_rule_projects(rule_name, tag, "add", force, dryrun)


@handle_errors_gracefully
async def remove_projects_with_tag(
    rule_name: str,
    tag: Optional[List[str]] = None,
    force: bool = False,
    dryrun: bool = False,
):
    """Remove projects with given tag from notification rule

    Args:
        rule_name (str): name of the rule used for removal
        tag (list): optional list of tags which limit the operation
        force (bool, optional): If set to true all actions will be executed immediately. Defaults to False.
    """
    return await __sync_notification_rule_projects(
        rule_name, tag or [], "remove", force, dryrun
    )
