"""Global constants, configuration model, and shared data structures for the toolkit."""
import os
import sys
from enum import IntEnum
from typing import Final, final
# third-party imports
import toml
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict
from decouple import config as env_config


class Config(BaseSettings):
    """Pydantic settings model for Dependency-Track connection parameters."""

    base_url: str
    api_key: str
    ca_path: str
    timeout: int = 15
    retries: int = 5
    backoff: float = 0.2
    parallel_requests: int = (
        20  # parallel_requests is set to 20, seems to be a good value for the dependency track api
    )

    model_config = SettingsConfigDict(
        env_prefix="dependencytrack_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )


def ask_yes_no(question):
    """
    Prompts the user with a yes/no question in the terminal.
    Returns True for 'yes' and False for 'no'.
    Handles case-insensitivity and strips whitespace.
    Repeats the prompt until a valid 'yes'/'no' answer is given.
    """
    while True:
        # Display the question and append (yes/no) for clarity
        response = input(f"{question} (Y/n): ").strip().lower()

        if response in ["y", "yes", ""]:
            return True
        if response in ["n", "no"]:
            return False
        print("Invalid input. Please answer 'Y' or 'n'.")


def get_integer_input(prompt):
    """Prompt the user until a valid integer is entered and return it."""
    while True:
        user_input = input(prompt)
        try:
            # Attempt to convert the string to an integer
            num = int(user_input)
            return num
        except ValueError:
            print("Invalid input. Please enter a whole number.")


def get_float_input(prompt):
    """Prompt the user until a valid float is entered and return it."""
    while True:
        user_input = input(prompt)
        try:
            # Attempt to convert the string to a float
            f_num = float(user_input)
            return f_num
        except ValueError:
            print("Invalid input. Please enter a decimal number.")


CONFIG_PATH_VAR = "CONFIG_PATH"
DEFAULT_CONFIG_PATH = "./config/config.toml"
config_path = env_config(CONFIG_PATH_VAR, None)

if config_path not in ["", "None", "ENV", None] and os.path.exists(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            config_toml = toml.load(config_file)
            config = Config(**config_toml["dependencytrack"])
            logger.info(f"Loaded configuration from {config_path}")
    except FileNotFoundError:
        logger.error(f"Configuration file {config_path} not found!")
        sys.exit(1)
# check if default config at ./config/config.toml exists
elif os.path.exists("./config/config.toml"):
    with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_toml = toml.load(config_file)
        config = Config(**config_toml["dependencytrack"])
        logger.info(f"Loaded configuration from default at: {DEFAULT_CONFIG_PATH}")
else:
    if not os.path.exists("./config"):
        os.mkdir("./config")
    logger.info("./config/config.toml does not exist, start asking user for input")
    print("./config/config.toml does not exist, let's do it together:")

    # Do I need to check availablity of the server?
    base_url = input(
        "Please enter the url of the dependancy tracker you want to connect to: "
    )
    api_key = input("Please enter the api key: ")
    # Do I need to check existence of the path?
    ca_path = input("Please enter ca_path: ")

    if ask_yes_no(
        f"Do you want to use the default value of {Config.model_fields['timeout'].default} for the parameter timeout? "
    ):
        timeout = Config.model_fields["timeout"].default
    else:
        timeout = get_integer_input("Please enter the timeout value: ")
    if ask_yes_no(
        f"Do you want to use the default value of {Config.model_fields['retries'].default} for the parameter retries? "
    ):
        retries = Config.model_fields["retries"].default
    else:
        retries = get_integer_input("Please enter the retries value: ")
    if ask_yes_no(
        f"Do you want to use the default value of {Config.model_fields['backoff'].default} for the parameter backoff? "
    ):
        backoff = Config.model_fields["backoff"].default
    else:
        backoff = get_float_input("Please enter the backoff value: ")
    if ask_yes_no(
        f"Do you want to use the default value of {Config.model_fields['parallel_requests'].default} for the parameter parallel requests? "
    ):
        parallel_requests = Config.model_fields["parallel_requests"].default
    else:
        parallel_requests = get_integer_input(
            "Please enter the parallel requests value: "
        )

    print("Creating the toml file for you now")

    # Using variable here?
    with open("./config/config.toml", "w+", encoding="utf-8") as config_file:
        config_file.write("[dependencytrack]\n")
        config_file.write(f'base_url="{base_url}"\n')
        config_file.write(f'api_key="{api_key}"\n')
        config_file.write(f'ca_path="{ca_path}"\n')
        config_file.write(f"timeout = {timeout}\n")
        config_file.write(f"retries = {retries}\n")
        config_file.write(f"backoff = {backoff}\n")
        config_file.write(f"parallel_requests={parallel_requests}\n")

        # set file pointer to beginning to enable read operation for toml.load
        config_file.seek(0)

        config_toml = toml.load(config_file)
        print(config_toml)
        config = Config(**config_toml["dependencytrack"])

    logger.info("Created config.toml file under ./config")


summary_dict_template = {
    "stats": {},
    "projects": [],
    "missing_projects": [],
    "result": {},
}


Valid_Classifiers: Final[list[str]] = [
    "APPLICATION",
    "CONTAINER",
    "DEVICE",
    "FILE",
    "FIRMWARE",
    "FRAMEWORK",
    "LIBRARY",
    "OPERATING_SYSTEM",
]


@final
class Severities(IntEnum):
    """Vulnerability Severities"""

    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    UNKNOWN = 4
    UNASSIGNED = 5

    @classmethod
    def get_names(cls) -> list[str]:
        """Return name as string for all severities"""
        return [k.name for k in cls]
