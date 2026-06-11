"""CLI entry point for the Dependency-Track Toolkit."""
import argparse
import json
import os
import signal
import sys
import asyncio
import pyfiglet
from loguru import logger

from dtracktoolkit.notification.notifications import (
    alerts_update_projects,
    assign_projects_with_tag,
    remove_projects_with_tag,
)
from dtracktoolkit.project.projects import (
    analyze_vulnerabilities,
    average_finding_age,
    count_vulnerable,
    delete_expired,
    remove_tag,
)
from dtracktoolkit.urls import UrlBase
from dtracktoolkit.utility import (
    opener,
    convert_cli_to_config,
    convert_args_to_dict,
    setup_logger,
)
from dtracktoolkit.api_token_manager.token_manager import (
    check_token_permissions,
    check_token_permissions_self,
)


def signal_handler(sig, frame):
    """Handle SIGINT by logging and exiting cleanly."""
    logger.info("Closed via user interaction")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def fetch_args():
    """Build and parse the CLI argument parser, returning (args, parser)."""
    parser = argparse.ArgumentParser(
        prog="Dependency-Track-Toolkit",
        description="CLI Tool used to trigger different actions via DP API",
    )
    subparsers = parser.add_subparsers(dest="command")

    # this flag will be applied to all subparsers where parents=[dummy], not using parser directly to preserver help
    dummy_parent = argparse.ArgumentParser(add_help=False)

    dummy_parent.add_argument(
        "-d", "--debug", action="store_true", help="shows debug logging"
    )
    dummy_parent.add_argument(
        "-dr",
        "--dryrun",
        action="store_true",
        help="only runs the output of a command without executing irreversible actions",
    )
    dummy_parent.add_argument(
        "-tc",
        "--to-config",
        action="store_true",
        help="converts the command into the config format for jobs (no execution of command)",
    )
    dummy_parent.add_argument(
        "-o",
        "--output",
        type=str,
        help="name a filepath used for json output",
    )

    # Notification commands
    parser_notifications = subparsers.add_parser(
        "notification", help="Manage Dependency Track notifications"
    )
    subparser_notifications = parser_notifications.add_subparsers(
        title="Notification Commands", dest="subcommand"
    )

    # notification: update projects
    subparser_notifications_manage_projects = subparser_notifications.add_parser(
        "update_projects",
        help="Update list of projects assigned to rule",
        parents=[dummy_parent],
    )
    subparser_notifications_manage_projects.add_argument(
        "-n", "--rule-name", type=str, required=True
    )
    subparser_notifications_manage_projects.add_argument(
        "-f", "--force", action="store_true"
    )

    # notification: assign projects
    subparser_notifications_assign_projects = subparser_notifications.add_parser(
        "assign_projects",
        help="assign additional project to  notification rule",
        parents=[dummy_parent],
    )
    subparser_notifications_assign_projects.add_argument(
        "-t",
        "--from-tag",
        type=str,
        required=True,
        nargs="+",
        help="Dependency-track tags separated by spaces (Logical OR)",
    )
    subparser_notifications_assign_projects.add_argument(
        "-n", "--rule-name", type=str, required=True
    )
    subparser_notifications_assign_projects.add_argument(
        "-f", "--force", action="store_true"
    )

    # notification: remove projects
    subparser_notifications_remove_projects = subparser_notifications.add_parser(
        "remove_projects",
        help="remove assigned project from notification rule",
        parents=[dummy_parent],
    )
    subparser_notifications_remove_projects.add_argument(
        "-t",
        "--from-tag",
        type=str,
        nargs="+",
        help="Dependency-track tags separated by spaces (Logical OR)",
    )
    subparser_notifications_remove_projects.add_argument(
        "-n", "--rule-name", type=str, required=True
    )
    subparser_notifications_remove_projects.add_argument(
        "-f", "--force", action="store_true"
    )

    # Project commands
    parser_projects = subparsers.add_parser(
        "project", help="Manage Dependency Track project portfolio"
    )
    subparser_projects = parser_projects.add_subparsers(
        title="Project Commands", dest="subcommand"
    )

    # project: delete expired projects
    subparser_projects_delete_expired = subparser_projects.add_parser(
        "delete_expired",
        help="permanently delete outdated projects",
        parents=[dummy_parent],
    )
    subparser_projects_delete_expired.add_argument(
        "-s", "--days-since", type=int, required=True
    )
    subparser_projects_delete_expired.add_argument(
        "-st",
        "--safe-tag",
        type=str,
        required=False,
        nargs="+",
        help="project with these tags (separated by spaces) are excluded from deletion",
    )
    subparser_projects_delete_expired.add_argument("-f", "--force", action="store_true")

    # projects: analyze vulnerabilities
    subparser_projects_analyze_vulnerabilities = subparser_projects.add_parser(
        "analyze_vulnerabilities",
        help="analyze the age and counts by severity level for findings and vulnerabilties of projecs",
        parents=[dummy_parent],
    )
    subparser_projects_analyze_vulnerabilities.add_argument(
        "-c", "--min-crit", type=str, required=True
    )
    subparser_projects_analyze_vulnerabilities.add_argument(
        "-t",
        "--from-tag",
        type=str,
        help='Tagquery, a string enclosed with quotation marks using "AND", "NOT", "OR" combined with tags; example "(TAG1 AND TAG2) OR TAG3"',
    )
    subparser_projects_analyze_vulnerabilities.add_argument(
        "-n",
        "--from-name",
        type=str,
        help='Namequery, a string enclosed with quotation marks using "AND", "NOT", "OR" combined with names; example "(NAME1 AND NAME2) OR NAME3", NAME refers to all projects which names include the substring NAME',
    )
    subparser_projects_analyze_vulnerabilities.add_argument(
        "-xc",
        "--exclude-classifier",
        type=str,
        nargs="+",
        help="exclude one or more classifiers from the search",
    )
    subparser_projects_analyze_vulnerabilities.add_argument(
        "-p",
        "--parent",
        type=str,
        help="Parent project name to filter the search for its children. Format: -p <parent_name>(:<version> OPTIONAL)",
    )

    subparser_projects_analyze_vulnerabilities.add_argument(
        "-s",
        "--shallow",
        action="store_true",
        help="if set to true, reduce requests by skipping in-depth vuln lookup",
    )

    # projects: count vulnerable projects
    subparser_projects_count_vulnerable = subparser_projects.add_parser(
        "count_vulnerable",
        help="count projects with vulnerable findings",
        parents=[dummy_parent],
    )
    subparser_projects_count_vulnerable.add_argument(
        "-c", "--min-crit", type=str, required=True
    )
    subparser_projects_count_vulnerable.add_argument(
        "-t",
        "--from-tag",
        type=str,
        help='Tagquery, a string enclosed with quotation marks using "AND", "NOT", "OR" combined with tags; example "(TAG1 AND TAG2) OR TAG3"',
    )
    subparser_projects_count_vulnerable.add_argument(
        "-n",
        "--from-name",
        type=str,
        help='Namequery, a string enclosed with quotation marks using "AND", "NOT", "OR" combined with names; example "(NAME1 AND NAME2) OR NAME3", NAME refers to all projects which names include the substring NAME',
    )
    subparser_projects_count_vulnerable.add_argument(
        "-xc",
        "--exclude-classifier",
        type=str,
        nargs="+",
        help="exclude one or more classifiers from the search",
    )
    subparser_projects_count_vulnerable.add_argument(
        "-p",
        "--parent",
        type=str,
        help="Parent project name to filter the search for its children. Format: -p <parent_name>(:<version> OPTIONAL)",
    )
    subparser_projects_count_vulnerable.add_argument(
        "-s",
        "--shallow",
        action="store_true",
        help="if set to true, reduce requests by skipping in-depth vuln lookup",
    )

    # projects: calculate average finding age
    subparser_projects_average_finding_age = subparser_projects.add_parser(
        "average_finding_age",
        help="calculate the average age of open findings",
        parents=[dummy_parent],
    )
    subparser_projects_average_finding_age.add_argument(
        "-c", "--min-crit", type=str, required=True
    )
    subparser_projects_average_finding_age.add_argument(
        "-t",
        "--from-tag",
        type=str,
        help='Tagquery, a string enclosed with quotation marks using "AND", "NOT", "OR" combined with tags; example "(TAG1 AND TAG2) OR TAG3"',
    )
    subparser_projects_average_finding_age.add_argument(
        "-xc",
        "--exclude-classifier",
        type=str,
        nargs="+",
        help="exclude one or more classifiers from the search",
    )
    subparser_projects_average_finding_age.add_argument(
        "-s",
        "--shallow",
        action="store_true",
        help="if set to true, reduce requests by skipping in-depth vuln lookup",
    )

    # projects: remove tag
    subparser_projects_remove_tag = subparser_projects.add_parser(
        "remove_tag",
        help="Remove a tag",
        parents=[dummy_parent],
    )
    subparser_projects_remove_tag.add_argument(
        "-r",
        "--removed-tag",
        type=str,
        required=True,
        help="tag to be removed",
    )
    subparser_projects_remove_tag.add_argument(
        "-t",
        "--from-tag",
        type=str,
        nargs="+",
        help="Dependency-track tags separated by spaces (Logical OR)",
    )
    subparser_projects_remove_tag.add_argument(
        "-xc",
        "--exclude-classifier",
        type=str,
        nargs="+",
        help="exclude one or more classifiers from the search",
    )
    subparser_projects_remove_tag.add_argument("-f", "--force", action="store_true")

    # token commands
    parser_tokens = subparsers.add_parser("token", help="Manage API tokens")
    subparser_tokens = parser_tokens.add_subparsers(
        title="Token Commands", dest="subcommand"
    )

    # tokens: show permissions
    subparser_token_permissions = subparser_tokens.add_parser(
        "show_permissions",
        help="Check permissions for a team",
        parents=[dummy_parent],
    )
    subparser_token_permissions.add_argument(
        "-n",
        "--name",
        type=str,
        required=False,
        help="Substring of the team's name in a regex pattern",
    )

    args = parser.parse_args()
    return args, parser


def dump_to_file(path, data):
    """Write data as JSON to path if the parent directory exists."""
    if os.path.exists(os.path.dirname(path)):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        logger.debug("Dumped report to file {}", path)
    else:
        logger.error("{} is not a valid filepaths", path)


async def main():
    """Dispatch CLI arguments to the appropriate toolkit command."""
    args, parser = fetch_args()
    result = {}

    LOG_LEVEL = "DEBUG" if (hasattr(args, "debug") and args.debug is True) else "INFO"
    setup_logger(log_level=LOG_LEVEL)

    if hasattr(args, "to_config") and args.to_config:
        print(convert_cli_to_config(args))
        sys.exit(0)
    else:
        print(pyfiglet.figlet_format("D-Track-Toolkit"))

    urlbase = UrlBase()
    if not urlbase.BASE_URL.startswith("https://"):
        logger.warning(
            "Base URL is not HTTPS, consider changing to a secure connection in the config file"
        )

    if hasattr(args, "command") and args.command == "notification":
        if hasattr(args, "subcommand") and args.subcommand == "update_projects":
            logger.info("Command: NOTIFICATION MANAGER - UPDATE NOTIFICATION PROJECTS")
            logger.info(f"Endpoint: {urlbase.BASE_URL}")
            logger.debug(args)
            result = await alerts_update_projects(
                args.rule_name, force=args.force, dryrun=args.dryrun
            )
        elif hasattr(args, "subcommand") and args.subcommand == "assign_projects":
            logger.info(
                "Command: NOTIFICATION MANAGER - ASSIGN TAGGED PROJECTS TO NOTIFICATION"
            )
            logger.info(f"Endpoint: {urlbase.BASE_URL}")
            logger.debug(args)
            result = await assign_projects_with_tag(
                args.rule_name, tag=args.from_tag, force=args.force, dryrun=args.dryrun
            )
        elif hasattr(args, "subcommand") and args.subcommand == "remove_projects":
            logger.info(
                "Command: NOTIFICATION MANAGER - REMOVE TAGGED PROJECTS FROM NOTIFICATION"
            )
            logger.info(f"Endpoint: {urlbase.BASE_URL}")
            logger.debug(args)
            result = await remove_projects_with_tag(
                args.rule_name, tag=args.from_tag, force=args.force, dryrun=args.dryrun
            )
        else:
            parser.print_help()
    elif hasattr(args, "command") and args.command == "project":
        if hasattr(args, "subcommand") and args.subcommand == "delete_expired":
            logger.info("Command: PROJECT MANAGER - DELETE OUTDATED PROJECTS")
            logger.info(f"Endpoint: {urlbase.BASE_URL}")
            logger.debug(args)
            result = await delete_expired(
                args.days_since,
                safe_tag=args.safe_tag,
                force=args.force,
                dryrun=args.dryrun,
            )

        elif (
            hasattr(args, "subcommand") and args.subcommand == "analyze_vulnerabilities"
        ):
            logger.info("Command: PROJECT MANAGER - ANALYZE VULNERABILITIES")
            logger.info(f"Endpoint: {urlbase.BASE_URL}")
            logger.debug(args)
            result = await analyze_vulnerabilities(
                args.min_crit,
                tag_query=args.from_tag,
                name_query=args.from_name,
                exclude_classifiers=args.exclude_classifier,
                parent_pattern=args.parent,
                shallow=args.shallow,
            )

        elif hasattr(args, "subcommand") and args.subcommand == "count_vulnerable":
            logger.info("Command: PROJECT MANAGER - COUNT VULNERABLE PROJECTS")
            logger.info(f"Endpoint: {urlbase.BASE_URL}")
            logger.debug(args)
            result = await count_vulnerable(
                args.min_crit,
                tag_query=args.from_tag,
                name_query=args.from_name,
                exclude_classifiers=args.exclude_classifier,
                parent_pattern=args.parent,
                shallow=args.shallow,
            )
        elif hasattr(args, "subcommand") and args.subcommand == "average_finding_age":
            logger.info("Command: PROJECT MANAGER - CALC AVERAGE FINDING AGE")
            logger.info(f"Endpoint: {urlbase.BASE_URL}")
            logger.debug(args)
            result = await average_finding_age(
                args.min_crit,
                tag=args.from_tag,
                exclude_classifiers=args.exclude_classifier,
                shallow=args.shallow,
            )
        elif hasattr(args, "subcommand") and args.subcommand == "remove_tag":
            logger.info("Command: PROJECT MANAGER - REMOVE TAG")
            logger.info(f"Endpoint: {urlbase.BASE_URL}")
            logger.debug(args)
            result = await remove_tag(
                tag=args.from_tag,
                removed_tag=args.removed_tag,
                exclude_classifiers=args.exclude_classifier,
                dryrun=args.dryrun,
                force=args.force,
            )
        else:
            parser.print_help()
    elif hasattr(args, "command") and args.command == "token":
        if hasattr(args, "subcommand") and args.subcommand == "show_permissions":
            logger.info("Command: TOKEN MANAGER - SHOW TOKEN PERMISSIONS")
            logger.info(f"Endpoint: {urlbase.BASE_URL}")
            logger.debug(args)
            if args.name:
                result = await check_token_permissions(name=args.name)
            else:
                result = await check_token_permissions_self()
        else:
            parser.print_help()
    else:
        parser.print_help()

    # all methods return their output as a summary, if specified write to file
    if hasattr(args, "output") and args.output:
        result["stats"] = convert_args_to_dict(args)
        dump_to_file(args.output, result)


def binary_main():
    """Synchronous entry point for the installed console script."""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
