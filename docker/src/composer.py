"""Manges invocation of dependency track toolkit"""

import os
import sys
import toml
from typing import List
# from mailer import send_mail
from loguru import logger

from src.schema import AbstractTask, Config
from src.utility import opener, init_core_config_from_env
# setup core config, need to do this before importing the module
# monkeypatch solution to work with existing configuration
path = "./config/core_config.toml"
init_core_config_from_env(path)
os.environ["CONFIG_PATH"] = path
logger.debug(f"CONFIG_PATH for core configuration set to {path}")


async def main(config: str = "config/config.toml") -> bool:
    # Open, parse and validate config file
    with open(config, "r") as fh:
        config = toml.load(fh)

    config: Config = Config(**config)

    # Setup logger used for dtrack-aas
    logger.remove()
    logger.add(sys.stdout, format="[<level>{level}</level>] {message}", level="DEBUG")
    logger.add(
        "log/dtrack_service_{time}.log",
        format="{time:YYYY-MM-DD at HH:mm:ss} [{level}] {message}",
        level="DEBUG",
        opener=opener,
    )
    # Collect batch jobs
    tasks: List[AbstractTask] = []
    if project_tasks := config.toolkit.project:
        tasks.extend(project_tasks.count_vulnerable)
        tasks.extend(project_tasks.average_finding_age)
        tasks.extend(project_tasks.delete_expired)
        tasks.extend(project_tasks.remove_tag)

    if notification_tasks := config.toolkit.notification:
        tasks.extend(notification_tasks.assign_projects)
        tasks.extend(notification_tasks.update_projects)
        tasks.extend(notification_tasks.remove_projects)

    # Sort by execution oder by priority
    tasks.sort(key=lambda t: t.priority, reverse=True)
    logger.debug("Execution order: {}", [(t.title, t.task_type) for t in tasks])

    # Execute batch jobs
    for task in tasks:
        await task.execute_task()

    # Send mail with output and logs attached
    # send_mail.main()
    return True
