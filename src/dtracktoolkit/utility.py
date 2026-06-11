"""
Contains global utilities like user interaction and common datastructures
"""

import os
import sys
import argparse
import functools

from loguru import logger


def handle_errors_gracefully(func):
    """A decorator to catch and handle errors."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(
                f"An error occured in function '{func.__name__}': {e}. The likely cause is a connection error."
            )
            return []

    return wrapper


def user_approval(approval_text="Execute changes? (y/N)", force=False) -> bool:
    """User interaction to approve an irreversible action"""
    if force:
        logger.info("due to force flag auto approve action")
        return True
    logger.info(approval_text)
    result = input()
    if str(result).upper() != "Y":
        logger.info("Nothing to do - bye")
        sys.exit(0)
    else:
        return True


def setup_logger(log_level: str = "INFO") -> None:
    """Configure loguru to output to stderr at the given log level."""
    logger.remove()
    logger.enable("dtracktoolkit")
    logger.add(
        sys.stdout,
        format="[<level>{level}</level>] {message}",
        level=log_level,
        diagnose=False,
    )
    logger.add(
        "log/file_{time}.log",
        format="{time:YYYY-MM-DD at HH:mm:ss} [{level}] {message}",
        level=log_level,
        opener=opener,
        diagnose=False,
    )


def remove_duplicate_projects(projects: list[dict]) -> list[dict]:
    """removes duplicate projects in a list of dicts (projects) based on their uuid"""
    non_duplicates = []
    for project in projects:
        project_uuid = project["uuid"]
        duplicate_detected = False
        for non_duplicate_projects in non_duplicates:
            if non_duplicate_projects["uuid"] == project_uuid:
                duplicate_detected = True
        if not duplicate_detected:
            non_duplicates.append(project)
    return non_duplicates


def convert_cli_to_config(args: argparse.Namespace) -> str:
    """converts a cli command to the equivalent config"""
    custom_config = f"[[toolkit.{args.command}.{args.subcommand}]]\ntitle='newtask'\n"
    for arg in vars(args):
        arg_val = getattr(args, arg)
        if (
            arg_val is not None and
            arg != "command" and
            arg != "subcommand" and
            arg != "to_config" and
            arg != "force"
        ):
            arg_val = "'" + arg_val + "'" if isinstance(arg_val, str) else arg_val
            arg_val = str(arg_val).lower() if isinstance(arg_val, bool) else arg_val
            custom_config += f"{arg}={arg_val}\n"
    return custom_config


def convert_args_to_dict(args: argparse.Namespace) -> dict:
    """converts the arguments of the current command to a dict"""
    all_args = {}
    for arg in vars(args):
        arg_val = getattr(args, arg)
        all_args[arg] = arg_val
    return all_args


def opener(file, flags):
    """Modify default file permission on newly created log files
    https://www.cvedetails.com/cve/CVE-2022-0338/
    """
    return os.open(file, flags, 0o640)
