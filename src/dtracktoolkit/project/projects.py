"""Project vulnerability analysis, age tracking, and lifecycle management for Dependency-Track."""
import sys
import copy
import asyncio
from datetime import datetime, timedelta
from loguru import logger

from dtracktoolkit.project.urls import URLs
from dtracktoolkit.urls import ProjectNotFoundError
from dtracktoolkit.query_language import get_lambda_filter_by_name
from dtracktoolkit.utility import user_approval, handle_errors_gracefully
from dtracktoolkit.constants import Valid_Classifiers, Severities, summary_dict_template


async def try_to_fetch_project_findings(
    tasks: list[asyncio.Task], projects: list[dict]
) -> tuple[list[dict], list[dict]]:
    """Gracefully handles gathering asyncio tasks for fetching project findings, among them the ProjectNotFoundError raised by urls.

    ProjectNotFoundError can occur, when a project from dependencytrack is removed between the operation of fetching projects(get their uuids and overall data) and fetching their findings (by using the uuid). If this is the case, the url the function that fetches the findings does not exist anymore and the asnycio tasks that gathers the calls will not crash but just skip the project, where it could not get the findings via the uuid.
    Args:
        tasks list[asyncio.Task]: asyncio tasks to collect project findings
        projects list[dict]: list of projets obtained by fetch_projects* function

    Returns:
        projects: Cleaned list of projects. In case of no caught exception, the original input parameter. In case of a caught exception, the projects, where no exception occured during fetching its project findings.
        all_findings: List of findings where no exception occured during fetch.
    """
    all_findings = []
    try:
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(all_results):
            if isinstance(result, ProjectNotFoundError):
                logger.debug(
                    f"Findings for project with uuid {projects[i].get('uuid')} were not found, because the project was probably deleted in the meantime. Skipping its findings. Error: {result}"
                )
            elif isinstance(result, Exception):
                logger.debug(
                    f"An unexpected error occurred for project with uuid {projects[i].get('uuid')} : {result}. Skipping its findings."
                )
            else:
                all_findings.append(result)
    except Exception as e:
        logger.error(
            f"A critical error occurred during the asyncio.gather operation: {e}. Returning no findings."
        )
        # make sure, that an empty projects list is returned in case of error by setting all_results to an empty list
        all_results = []

    if not (len(projects) == len(all_findings)):
        logger.warning(
            f"An error occured and the findings for {len(projects) - len(all_findings)} projects could not be obtained, thus skipping their analysis."
        )

    # remove all projects where no findings were found
    projects = [
        item
        for result, item in zip(all_results, projects)
        if not isinstance(result, Exception)
    ]
    return projects, all_findings


async def __fetch_filtered_projects(
    urls,
    tag_query: str = None,
    name_query: str = None,
    parent_pattern: str = None,
) -> list | None:
    if tag_query:
        projects = await urls.fetch_projects_by_tagquery(tag_query)
        if name_query:
            projects = list(filter(get_lambda_filter_by_name(name_query), projects))
    elif name_query:
        projects = await urls.fetch_projects_by_namequery(name_query)
    elif parent_pattern:
        projects = await urls.fetch_children_by_parent_project(parent_pattern)
        if not projects:
            logger.info("No projects found for parent pattern '{}'", parent_pattern)
            return None
    else:
        projects = await urls.fetch_all_projects()
    return projects


@handle_errors_gracefully
async def delete_expired(
    days_since: int, safe_tag: list = None, force: bool = False, dryrun: bool = False
) -> dict:
    """Permanently delete projects that have not been updated in a specified number of days

    Args:
        days_since (int): days since the last update of the project
        safe_tag (list): list of tags that will be excluded from the deletion
        force (bool): auto approves the deletion
        dryrun (bool): runs command wihtout executing irreversible actions

    Returns:
        dict: summary of the command dump
    """
    urls = URLs()
    summary_dict = copy.deepcopy(summary_dict_template)
    all_projects = await urls.fetch_all_projects()

    # protected projects are those which have the safe tag[s]
    protected_projects = []
    if safe_tag:
        for tag in safe_tag:
            protected_projects += await urls.fetch_projects_with_tag(tag)

    # cut-off date for outdated entries
    expiration_date = datetime.now() - timedelta(days=days_since)

    # Filter projects based on last activity
    outdated_projects = []
    for project in all_projects:
        # filter out any projects protected by the safe tags
        found = any(
            filter(
                lambda protected_project: protected_project["uuid"] == project["uuid"],
                protected_projects,
            )
        )
        if found:
            continue

        project_metrics = project.get("metrics")
        if not project_metrics:
            logger.error(
                "No metrics found on project {} ({})!",
                project.get("name"),
                project.get("uuid"),
            )
            continue
        deletion_scheduled = False

        project_registration = __convert_timestamp(
            project_metrics.get("firstOccurrence")
        )  # epoch in milli
        project_import = __convert_timestamp(
            project.get("lastBomImport")
        )  # epoch in milli

        if not project_import and not project_registration:
            # probably brand new, do not delete!
            deletion_scheduled = False
        elif not project_import and project_registration < expiration_date:
            # no initial bom uploaded to project since x days
            deletion_scheduled = True
        elif project_import and project_import < expiration_date:
            # no new bom uploaded to (active) project since x days
            deletion_scheduled = True

        if deletion_scheduled:
            outdated_projects.append(project)

    logger.info("Projects without activity since {} days", days_since)
    for outdated_project in outdated_projects:
        logger.info(
            "Project: {}:{} [DELETE]",
            outdated_project.get("name"),
            outdated_project.get("version", "N/A"),
        )
        summary_dict["projects"].append(
            {
                "name": outdated_project.get("name"),
                "version": outdated_project.get("version"),
                "uuid": outdated_project.get("uuid"),
            }
        )

    if dryrun:
        return summary_dict
    user_approval("Permanently delete projects from portfolio?:(y/N)", force=force)
    for project in outdated_projects:
        urls.delete_project(project=project)
    return summary_dict


@handle_errors_gracefully
async def analyze_vulnerabilities(
    crit: str,
    tag_query: str = None,
    name_query: str = None,
    parent_pattern: str = None,
    exclude_classifiers: list = None,
    shallow: bool = False,
) -> dict:
    """
    Analyzes projects to count vulnerabilities and findings and determines the age of both vulnerabilities and findings.

    This function fetches project data based on specified filters and performs a
    comprehensive analysis. It counts total projects, identifies vulnerable ones,
    groups vulnerabilities by severity, determines fixability, and calculates
    the age of each open finding and unique vulnerability.

    Args:
        crit (str): Minimum criticality level (e.g., 'HIGH', 'CRITICAL').
        tag_query (str): A query to filter projects by tags.
        name_query (str): A query to filter projects by name.
        parent_pattern (str): A pattern to find projects by their parent's name.
        exclude_classifiers (list): A list of project classifiers to exclude.
        shallow (bool): If True, uses project metrics for a faster but less
                        detailed analysis. If False, fetches detailed findings
                        for precise age and fixability calculations.

    Returns:
        dict: A summary dictionary containing detailed results for each project
              and an overall summary of the analysis.
    """
    urls = URLs()
    summary_dict = copy.deepcopy(summary_dict_template)
    projects = []
    severity_score = __convert_severity_to_int(crit)

    fetch_start = datetime.now()
    projects = await __fetch_filtered_projects(
        urls, tag_query, name_query, parent_pattern
    )
    if projects is None:
        return summary_dict

    projects = __remove_projects_with_excluded_classifiers(
        projects, exclude_classifiers
    )
    logger.info(
        f"Fetched {len(projects)} projects in {(datetime.now() - fetch_start).total_seconds():.2f} seconds"
    )

    all_findings = []
    if not shallow and projects:
        fetch_start = datetime.now()
        tasks = [
            asyncio.create_task(urls.fetch_project_findings(p["uuid"]))
            for p in projects
        ]
        projects, all_findings = await try_to_fetch_project_findings(tasks, projects)

    logger.info(
        f"Fetched findings for {len(all_findings)} projects in {(datetime.now() - fetch_start).total_seconds():.2f} seconds"
    )
    # Process Projects to calculate all metrics
    total_projects = 0
    vulnerable_projects = 0
    total_relevant_findings_count = 0
    total_relevant_vulns_count = 0
    total_relevant_fixable_vulns_count = 0
    sum_age_open_findings = timedelta()
    sum_age_open_vulns = timedelta()
    start = datetime.now()

    for i, project in enumerate(projects):
        relevant_findings_count_by_project = 0
        relevant_vulns_count_by_project = 0
        relevant_fixable_vulns_count_by_project = 0
        grouped_findings = {sev.value: 0 for sev in Severities}
        grouped_vulns = {sev.value: 0 for sev in Severities}
        grouped_vulns_fixable = {sev.value: 0 for sev in Severities}
        oldest_finding = timedelta()
        oldest_vulnerability = timedelta()
        relevant_vulns = []
        relevant_findings = []

        project_metrics = project.get("metrics")
        if not project_metrics:
            logger.debug(
                f"Project {project.get('uuid')} is missing metrics and will be skipped."
            )
            continue

        total_projects += 1
        oldest_vuln = datetime.now()

        if project_metrics.get("findingsTotal", 0) == 0:
            logger.info(
                f"Project {project.get('name')}:{project.get('version')} has no findings."
            )
        elif shallow:
            attributiondate = __convert_timestamp(project.get("lastBomImport", None))
            if attributiondate:
                oldest_vuln = start - attributiondate
                logger.debug(
                    f"Generic vulnerability in {project.get('name')}:{project.get('version')} probably attributed since {attributiondate}"
                )
            for score in Severities.get_names():
                if Severities[score] <= Severities[crit.upper()]:
                    relevant_vulns_count_by_project += project_metrics.get(
                        score.lower(), 0
                    )
            sum_age_open_vulns = oldest_vuln * relevant_vulns_count_by_project
            # in shallow mode, fetch project findings is skipped, thus project_metrics.get(score.lower(), 0) returns vulnerabilties (no duplicate aliases) and not findings, but do cover shallow findings as well, the same value is taken although it is impossible to find the the number of findings with the shallow method
            sum_age_open_findings = sum_age_open_vulns
            # to satisfy test requirements defined in test_analyze_vulnerabilities_shallow_information
            grouped_findings = None
            grouped_vulns = None
            grouped_vulns_fixable = None

        else:
            relevant_findings_by_project = [
                f
                for f in all_findings[i]
                if (
                    not f["analysis"]["isSuppressed"]
                    and __vulnerable_analysis(f["analysis"].get("state"))
                )
            ]
            unique_vulns_by_project = __deduplicate_findings_by_aliases(
                relevant_findings_by_project
            )

            # Calculate metrics based on unique vulnerabilities and all findings
            for severity in Severities:
                relevant_findings_by_severity = []
                relevant_vulns_by_severity = []
                # first create a list of all the relevant findings
                for finding in relevant_findings_by_project:
                    if finding["vulnerability"]["severityRank"] == severity.value:
                        attributiondate = __convert_timestamp(
                            finding["attribution"]["attributedOn"]
                        )
                        logger.debug(
                            f"Finding: {finding['vulnerability']['vulnId']} in {project.get('name')}:{project.get('version')} attributed on {attributiondate}"
                        )
                        age = start - attributiondate
                        # to satisfy test function in test_average_finding_critical, only consider relevant findings
                        if severity.value <= severity_score:
                            sum_age_open_findings += age
                        oldest_finding = max(age, oldest_finding)

                        relevant_findings_by_severity.append(
                            {
                                "vulnId": finding["vulnerability"].get(
                                    "vulnId", "Unknown"
                                ),
                                # TODO implement severity as value of loop iterator?
                                "severity": __convert_int_to_severity(
                                    finding["vulnerability"].get("severityRank", "-1")
                                ),
                                "age_days": age.days,
                            }
                        )

                        if finding in unique_vulns_by_project:
                            logger.debug(
                                f"Vulnerability: {finding['vulnerability']['vulnId']} in {project.get('name')}:{project.get('version')} attributed on {attributiondate}"
                            )
                            sum_age_open_vulns += age
                            oldest_vulnerability = max(age, oldest_vulnerability)

                            relevant_vulns_by_severity.append(
                                {
                                    "vulnId": finding["vulnerability"].get(
                                        "vulnId", "Unknown"
                                    ),
                                    "severity": __convert_int_to_severity(
                                        finding["vulnerability"].get(
                                            "severityRank", "-1"
                                        )
                                    ),
                                    "age_days": age.days,
                                    "component": {
                                        "version": finding["component"].get(
                                            "version", None
                                        ),
                                        "latestVersion": finding["component"].get(
                                            "latestVersion", None
                                        ),
                                    },
                                }
                            )

                # group by severity level
                grouped_findings[severity.value] = len(relevant_findings_by_severity)
                grouped_vulns[severity.value] = len(relevant_vulns_by_severity)
                fixable_vulns_by_severity = list(
                    filter(
                        lambda x: x["component"].get("version", 0)
                        != x["component"].get("latestVersion", 0),
                        relevant_vulns_by_severity,
                    )
                )
                grouped_vulns_fixable[severity.value] = len(fixable_vulns_by_severity)

                # copy by severity findings and vulns into new variable to include it in the summary_dict
                relevant_findings.extend(relevant_findings_by_severity)
                relevant_vulns.extend(relevant_vulns_by_severity)

                if severity.value <= severity_score:
                    relevant_findings_count_by_project += len(
                        relevant_findings_by_severity
                    )
                    relevant_vulns_count_by_project += len(relevant_vulns_by_severity)
                    relevant_fixable_vulns_count_by_project += len(
                        fixable_vulns_by_severity
                    )

            if relevant_findings_count_by_project:
                logger.info(
                    f"Project {project.get('name')}:{project.get('version')} has findings as old as {oldest_finding.days} days!"
                )
                # total_findings_count += sum(grouped_findings.values())
                total_relevant_findings_count += relevant_findings_count_by_project

                if relevant_vulns:
                    logger.info(
                        f"Project {project.get('name')}:{project.get('version')} has a total of {relevant_vulns_count_by_project} vulnerabilities of the specified severity or higher. {relevant_fixable_vulns_count_by_project} of those are fixable."
                    )
                    total_relevant_vulns_count += sum(grouped_vulns.values())
                    # total_relevant_vulns_count += relevant_vulns_count_by_project
                    # total_fixable_vulns_count = sum(grouped_vulns_fixable.values())
                    # relevant_fixable_vulns_count = sum(value for key, value in grouped_vulns_fixable.items() if key <= severity_score)

        if relevant_vulns_count_by_project:
            vulnerable_projects += 1
        summary_dict["projects"].append(
            {
                "name": project.get("name"),
                "version": project.get("version"),
                "tags": project.get("tags"),
                "uuid": project.get("uuid"),
                "lastBomImport": project.get("lastBomImport", 0),
                "oldest_finding_days": oldest_finding.days,
                "relevant_findings_count": relevant_findings_count_by_project,
                "grouped_findings": grouped_findings,
                "findings": relevant_findings,
                "relevant_vulns_count": relevant_vulns_count_by_project,
                "grouped_vulns": grouped_vulns,
                "relevant_fixable_vulns_count": total_relevant_fixable_vulns_count,
                "grouped_vulns_fixable": grouped_vulns_fixable,
                "vulnerabilities": relevant_vulns,
            }
        )

    # 4. Finalize overall summary
    avg_finding_age = (
        (sum_age_open_findings / total_relevant_findings_count).days
        if total_relevant_findings_count > 0
        else 0
    )
    avg_vuln_age = (
        (sum_age_open_vulns / total_relevant_vulns_count).days
        if total_relevant_vulns_count > 0
        else 0
    )

    summary_dict["result"] = {
        "amount_projects": total_projects,
        "vulnerable_projects": vulnerable_projects,
        "criticality": crit,
        "total_open_findings": total_relevant_findings_count,
        "average_finding_age_days": avg_finding_age,
        "total_open_vulnerabilities": total_relevant_vulns_count,
        "average_vulnerability_age_days": avg_vuln_age,
    }

    logger.info(
        f"RESULT: Of {total_projects} projects, {vulnerable_projects} are vulnerable "
        f"with findings of severity '{crit}' or higher."
    )
    if not shallow:
        logger.info(
            f"Found {total_relevant_findings_count} open findings with an average age of {avg_finding_age} days."
        )
        logger.info(
            f"Found {total_relevant_vulns_count} unique open vulnerabilities with an average age of {avg_vuln_age} days."
        )

    return summary_dict


@handle_errors_gracefully
async def count_vulnerable(
    crit: str,
    tag_query: str = None,
    name_query: str = None,
    exclude_classifiers: list = None,
    parent_pattern: str = None,
    shallow: bool = False,
) -> dict:
    """
    Count total projects and those vulnerable with at least one (not suppressed) finding of specified severity or above

    Args:
        crit (str): minimum criticality
        tag_query (str): filter projects by basic boolean logic according to tags (details in query_language.py)
        exclude_classifiers (list): certain classifiers to exclude from the search

    Returns:
        dict: summary of the found projects
    """
    urls = URLs()
    summary_dict = copy.deepcopy(summary_dict_template)
    projects = await __fetch_filtered_projects(
        urls, tag_query, name_query, parent_pattern
    )
    if projects is None:
        return summary_dict
    projects = __remove_projects_with_excluded_classifiers(
        projects, exclude_classifiers
    )
    severity_score = __convert_severity_to_int(crit)

    total_projects = 0
    vulnerable_projects = 0
    findings = {}

    logger.debug("Calculating vulnerable projects")

    if not shallow:
        # async fetch findings for each project
        logger.debug(f"Fetching findings for {len(projects)} projects")
        tasks_calls = []
        for project in projects:
            t = asyncio.create_task(urls.fetch_project_findings(project["uuid"]))
            tasks_calls.append(t)
        projects, findings = await try_to_fetch_project_findings(tasks_calls, projects)

    for index, project in enumerate(projects):
        if project.get("metrics"):
            projectmetrics = project["metrics"]
        else:
            logger.error(
                "Missing metrics section project excluded '{}'", project.get("uuid")
            )
            logger.debug(
                "Project data not included in result (raw:{})",
                project,
            )
            continue

        total_projects += 1
        total_findings = 0
        relevant_vulns = 0
        fixable_vulns = 0
        grouped_vulns = {}
        grouped_vulns_fixable = {}
        # check if findings up to threshold are audited
        if projectmetrics["findingsTotal"] == 0:
            logger.info(
                "Project {}:{} not vulnerable!",
                project.get("name"),
                project.get("version"),
            )
        elif shallow:
            num_vulnerabilites = 0
            for score in Severities.get_names():
                if Severities[score] <= Severities[crit.upper()]:
                    num_vulnerabilites += projectmetrics.get(
                        score.lower(), 0
                    )  # take metrics as truth
            relevant_vulns = num_vulnerabilites  # cannot list or detail findings
            fixable_vulns = 0  # fixability cannot be determined
        else:
            # Identify vulnerabilites (distinct root causes) by filtering findings -> remove aliases, keep entry with highest vuln score
            project_findings = findings[index]
            total_findings = len(project_findings)
            vulns = __deduplicate_findings_by_aliases(project_findings)
            # compute metrics
            for severity in Severities:
                vulns_severity = []
                # first create a list of all the relevant findings
                for vulnerability in vulns:
                    if (
                        vulnerability["vulnerability"]["severityRank"] == severity.value
                        and not vulnerability["analysis"]["isSuppressed"]
                        and __vulnerable_analysis(
                            vulnerability["analysis"].get("state")
                        )
                    ):
                        vulns_severity.append(vulnerability)
                grouped_vulns[severity.value] = len(vulns_severity)
                vulns_severity_fixable = list(
                    filter(
                        lambda x: x["component"].get("version", 0)
                        != x["component"].get("latestVersion", 0),
                        vulns_severity,
                    )
                )
                grouped_vulns_fixable[severity.value] = len(vulns_severity_fixable)
                if severity.value <= severity_score:
                    relevant_vulns += grouped_vulns[severity.value]
                    fixable_vulns += grouped_vulns_fixable[severity.value]
        if relevant_vulns:
            log_string = f"Project {project.get("name")}:{project.get("version")} vulnerable with {relevant_vulns} vulnerabilities"
            vulnerable_projects += 1
            if not shallow:
                log_string += f" ({total_findings} findings)! {fixable_vulns} of those are fixable."
            else:
                log_string += "!"
            logger.info(log_string)
        else:
            logger.info(
                "Project {}:{} not vulnerable!",
                project.get("name"),
                project.get("version"),
            )

        # TODO: relevant_findings and fixable_vulns are depracted in this version and mostly used for backwards compatibility
        project_summary = {
            "name": project.get("name"),
            "version": project.get("version"),
            "tags": project.get("tags"),
            "uuid": project.get("uuid"),
            "vulnerabilities": relevant_vulns,
            "findings": total_findings,
            "lastBomImport": project.get("lastBomImport", 0),
        }
        if not shallow:
            project_summary["fixable_vulnerabilities"] = fixable_vulns
            project_summary["vulnerabilities_dict"] = grouped_vulns
            project_summary["vulnerabilities_fixable_dict"] = grouped_vulns_fixable
        summary_dict["projects"].append(project_summary)

    logger.info(
        "RESULT: Of {} projects, {} have been found to be vulnerable with at least one finding"
        + " of severity rank {}.",
        total_projects,
        vulnerable_projects,
        crit,
    )
    total_summary = {
        "amount_projects": total_projects,
        "vulnerable_projects": vulnerable_projects,
    }
    summary_dict["result"] = total_summary
    return summary_dict


@handle_errors_gracefully
async def average_finding_age(
    crit: str, tag: str = None, exclude_classifiers: list = None, shallow: bool = False
) -> dict:
    """
    Average over the age of findings of a specified severity that have not yet been suppressed or audited.
    Can also find the age of each vulnerability of the specified severity, but not the average age of the
    vulnerabities of a project.

    Args:
        crit (str): minimum criticality
        tag (str): filter projects by basic boolean logic according to tags (details in query_language.py)
        exclude_classifiers (list): certain classifiers to exclude from the search

    Returns:
        dict: summary of the command dump and result
    """
    urls = URLs()
    summary_dict = copy.deepcopy(summary_dict_template)
    projects = []

    projects = await __fetch_filtered_projects(urls, tag_query=tag)
    projects = __remove_projects_with_excluded_classifiers(
        projects, exclude_classifiers
    )
    severity_score = __convert_severity_to_int(crit)

    # async fetch findings for each project
    logger.debug(f"Fetching findings for {len(projects)} projects")
    tasks_calls = []
    for project in projects:
        t = asyncio.create_task(urls.fetch_project_findings(project["uuid"]))
        tasks_calls.append(t)
    projects, findings = await try_to_fetch_project_findings(tasks_calls, projects)

    # compute metrics
    open_findings = 0
    open_vulns = 0
    start = datetime.now()
    sum_age_open = timedelta()
    vuln_sum_age_open = timedelta()
    # relevant_findings = []
    # vulns = []

    logger.debug("Calculating the average finding age")
    for index, project in enumerate(projects):
        oldest_finding = timedelta()
        oldest_vulnerability = timedelta()

        if project.get("metrics"):
            if project["metrics"]["findingsTotal"] == 0:
                logger.info(
                    "Project {}:{} has no findings!",
                    project.get("name"),
                    project.get("version"),
                )
                continue
            if shallow:
                # guess how long the vulns exist: since last BOM import
                attributiondate = __convert_timestamp(
                    project.get("lastBomImport", None)
                )
                if attributiondate:
                    oldest_finding = start - attributiondate
                    logger.debug(
                        f"Generic finding in {project.get('name')}:{project.get('version')} probably attributed since {attributiondate}"
                    )
                    for score in Severities.get_names():
                        if Severities[score] <= Severities[crit.upper()]:
                            open_findings += project["metrics"].get(score.lower(), 0)
                    sum_age_open = oldest_finding * open_findings
            else:
                relevant_findings = [
                    f
                    for f in findings[index]
                    if (
                        f["vulnerability"]["severityRank"] <= severity_score
                        and not f["analysis"]["isSuppressed"]
                    )
                ]
                for finding in relevant_findings:
                    analysisstate = finding["analysis"].get("state")
                    if not analysisstate or analysisstate == "NOT_SET":
                        attributiondate = __convert_timestamp(
                            finding["attribution"]["attributedOn"]
                        )
                        logger.debug(
                            f"Finding: {finding['vulnerability']['vulnId']} in {project.get('name')}:{project.get('version')} attributed on {attributiondate}"
                        )
                        age = start - attributiondate
                        open_findings += 1
                        sum_age_open += age
                        oldest_finding = max(age, oldest_finding)

                # Identify vulnerabilites (distinct root causes) by filtering findings -> remove aliases, keep entry with highest vuln score
                vulns = __deduplicate_findings_by_aliases(relevant_findings)

                for vuln in vulns:
                    analysisstate = vuln["analysis"].get("state")
                    if not analysisstate or analysisstate == "NOT_SET":
                        attributiondate = __convert_timestamp(
                            vuln["attribution"]["attributedOn"]
                        )
                        logger.debug(
                            f"Vulnerability: {vuln['vulnerability']['vulnId']} in {project.get('name')}:{project.get('version')} attributed on {attributiondate}"
                        )
                        vuln_age = start - attributiondate
                        open_vulns += 1
                        vuln_sum_age_open += age
                        oldest_vulnerability = max(vuln_age, oldest_vulnerability)

                if relevant_findings:
                    logger.info(
                        f"Project {project.get('name')}:{project.get('version')} has findings as old as {oldest_finding.days} days!"
                    )
                    summary_dict["projects"].append(
                        {
                            "name": project.get("name"),
                            "version": project.get("version"),
                            "oldest_finding_days": oldest_finding.days,
                            "uuid": project.get("uuid"),
                            "findings": [],
                        }
                    )
                    for finding in relevant_findings:
                        if not finding["analysis"][
                            "isSuppressed"
                        ] and __vulnerable_analysis(
                            finding["analysis"].get("state", "")
                        ):
                            summary_dict["projects"][-1]["findings"].append(
                                {
                                    "vulnId": finding["vulnerability"].get(
                                        "vulnId", "Unknown"
                                    ),
                                    "severity": __convert_int_to_severity(
                                        finding["vulnerability"].get(
                                            "severityRank", "-1"
                                        )
                                    ),
                                    "age_days": (
                                        start
                                        - __convert_timestamp(
                                            finding["attribution"]["attributedOn"]
                                        )
                                    ).days,
                                }
                            )
                else:
                    logger.info(
                        "Project {}:{} with uuid {} has no findings!",
                        project.get("name"),
                        project.get("version"),
                        project.get("uuid"),
                    )

                if vulns:
                    logger.info(
                        f"Project {project.get('name')}:{project.get('version')} has vulnerabilities as old as {oldest_vulnerability.days} days!"
                    )
                    summary_dict["projects"][-1][
                        "oldest_vulnerability_days"
                    ] = oldest_vulnerability.days
                    summary_dict["projects"][-1]["vulnerabilities"] = []

                    for vuln in vulns:
                        if not vuln["analysis"][
                            "isSuppressed"
                        ] and __vulnerable_analysis(vuln["analysis"].get("state", "")):
                            summary_dict["projects"][-1]["vulnerabilities"].append(
                                {
                                    "vulnId": vuln["vulnerability"].get(
                                        "vulnId", "Unknown"
                                    ),
                                    "severity": __convert_int_to_severity(
                                        vuln["vulnerability"].get("severityRank", "-1")
                                    ),
                                    "age_days": (
                                        start
                                        - __convert_timestamp(
                                            vuln["attribution"]["attributedOn"]
                                        )
                                    ).days,
                                }
                            )
                else:
                    logger.info(
                        "Project {}:{} with uuid {} has no vulnerabilities!",
                        project.get("name"),
                        project.get("version"),
                        project.get("uuid"),
                    )

        else:
            logger.error(
                "Missing metrics section project excluded '{}'", project.get("uuid")
            )
            logger.debug(
                "Project data not included in result (raw:{})",
                project,
            )

    # calculate average
    avg_age = timedelta(days=0)
    if open_findings != 0:
        avg_age = sum_age_open / open_findings
    logger.info(
        "RESULT: there are {} open findings of severity {} with an average age of {} days",
        open_findings,
        crit,
        avg_age.days,
    )
    result_summary = {
        "open_findings": open_findings,
        "criticality": crit,
        "average_age": avg_age.days,
    }
    summary_dict["result"] = result_summary
    return summary_dict


@handle_errors_gracefully
async def cve_info(tag_query: str = None) -> list:
    """Return a deduplicated list of CVEs with affected project counts, optionally filtered by tag."""
    urls = URLs()
    projects = await __fetch_filtered_projects(urls, tag_query=tag_query)

    # Fetch findings
    logger.debug(f"Fetching findings for {len(projects)} projects")
    tasks_calls = []
    for project in projects:
        t = asyncio.create_task(urls.fetch_project_findings(project["uuid"]))
        tasks_calls.append(t)

    # TODO Exception handling is done here as well for completeness purposes, because asyncio.gather was originally called in this function, although not necessary for use in dtrack-metrics, is cve_info deprecated (no documentation in gitty for this function)?
    projects, findings_per_project = await try_to_fetch_project_findings(
        tasks_calls, projects
    )

    # retrive cve information
    cve_hashmap = {}
    for findings_project in findings_per_project:
        for finding in findings_project:
            vuln_id = finding["vulnerability"]["vulnId"]
            if vuln_id[:3] != "CVE":
                continue
            if vuln_id not in cve_hashmap:
                cve_hashmap[vuln_id] = {
                    "cve_name": vuln_id,
                    "aliases": finding["vulnerability"].get("aliases"),
                    "severity": finding["vulnerability"].get("severity"),
                    "cvss_v3": finding["vulnerability"].get("cvssV3BaseScore"),
                    "affected": 1,
                }
            else:
                cve_hashmap[vuln_id]["affected"] += 1
    cve_list = list(cve_hashmap.values())
    return cve_list


@handle_errors_gracefully
async def remove_tag(
    removed_tag: str,
    tag: list = None,
    exclude_classifiers: list = None,
    dryrun: bool = False,
    force: bool = False,
) -> None:
    """
    Remove a tag from projects

    Args:
        tag (list): filter projects according to a list of tags, the tag to remove is implicitly included
        exclude_classifiers (list): certain classifiers to exclude from the search
    """
    urls = URLs()

    # fetch projects
    projects = await urls.fetch_projects_with_tag(removed_tag)
    # remove all that do not match additional tags (if provided)
    if tag:
        tagged_projects = []
        for t in tag:
            tagged_projects += await urls.fetch_projects_with_tag(t)

        projects = [p for p in projects if p in tagged_projects]
    projects = __remove_projects_with_excluded_classifiers(
        projects, exclude_classifiers
    )

    logger.info("Projects from which tag '{}' will be removed", removed_tag)
    for project in projects:
        logger.info(
            "Project: {}:{} [UPDATE]",
            project.get("name"),
            project.get("version", "N/A"),
        )

    if not dryrun:
        user_approval("Remove tag from selection?:(y/N)", force=force)
        for project in projects:
            urls.delete_tag(project=project, tag=removed_tag)


def __deduplicate_findings_by_aliases(findings: list) -> list:
    remaining = list(findings)
    result = []
    while remaining:
        candidate = remaining[0]
        aliases = [candidate["vulnerability"]["vulnId"]]
        if candidate["vulnerability"].get("aliases"):
            aliases = list(candidate["vulnerability"]["aliases"][0].values())
        matches = [
            (j, f["vulnerability"]["severityRank"])
            for j, f in enumerate(remaining)
            if f["vulnerability"]["vulnId"] in aliases
        ]
        if len(matches) > 1:
            candidate = remaining[min(matches, key=lambda x: x[1])[0]]
        result.append(candidate)
        matched_indices = {j for j, _ in matches}
        remaining = [f for j, f in enumerate(remaining) if j not in matched_indices]
    return result


# call with project time collected from json response in dependency-track
def __convert_timestamp(timestamp: int) -> datetime:
    """Convert integer epoch timestamp in milliseconds to datetime.datetime"""
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp / 1000)


def __remove_projects_with_excluded_classifiers(
    projects: list, exclude_classifiers: list = None
) -> list:
    if exclude_classifiers:
        for classifier in exclude_classifiers:
            if classifier.upper() not in Valid_Classifiers:
                logger.error(
                    "Invalid Classifier chosen. Valid are: {}", Valid_Classifiers
                )
        for project in list(projects):
            if "classifier" in project:
                if project["classifier"] in [x.upper() for x in exclude_classifiers]:
                    projects.remove(project)
    return projects


def __convert_severity_to_int(crit: str) -> int:
    try:
        severity_score = Severities[crit.upper()]
    except Exception:
        logger.error(
            "Specified severity score {} unknown, choose from the following: {} - exiting",
            crit,
            Severities.get_names(),
        )
        severity_score = "UNKNOWN"
    return severity_score


def __convert_int_to_severity(score: int) -> str:
    try:
        severity = Severities(score).name
    except Exception:
        logger.error(
            "Specified severity score {} unknown, choose from the following: {} - exiting",
            score,
            Severities.get_names(),
        )
        sys.exit(1)
    return severity


def __vulnerable_analysis(state: str):
    """returns a boolean if the analysis is currently vulnerable"""
    if not state:
        # no analysisstate set
        return True
    if state == "NOT_SET" or state == "EXPLOITABLE" or state == "IN_TRIAGE":
        return True
    return False
