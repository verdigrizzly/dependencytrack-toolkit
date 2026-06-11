"""Functions for checking Dependency-Track API token permissions."""
import re
from loguru import logger

from dtracktoolkit.api_token_manager.urls import URLs
from dtracktoolkit.api_token_manager.token_validator import TokenInput
from dtracktoolkit.utility import handle_errors_gracefully

PERMISSIONS = [
    "ACCESS_MANAGEMENT",
    "BOM_UPLOAD",
    "POLICY_MANAGEMENT",
    "POLICY_VIOLATION_ANALYSIS",
    "PORTFOLIO_MANAGEMENT",
    "PROJECT_CREATION_UPLOAD",
    "SYSTEM_CONFIGURATION",
    "TAG_MANAGEMENT",
    "VIEW_BADGES",
    "VIEW_POLICY_VIOLATION",
    "VIEW_PORTFOLIO",
    "VIEW_VULNERABILITY",
    "VULNERABILITY_ANALYSIS",
    "VULNERABILITY_MANAGEMENT",
]

PERMISSIONS_ADMIN = PERMISSIONS
PERMISSIONS_API = [PERMISSIONS[i] for i in [1, 3, 5, 7, 8, 9, 10, 11, 12]]
PERMISSIONS_GUI = PERMISSIONS_API + [PERMISSIONS[4]]
PERMISSIONS_JENKINS = PERMISSIONS_GUI + [PERMISSIONS[2]]


@handle_errors_gracefully
async def check_token_permissions(name: str) -> dict:
    """
    This function calls the API and uses regex/substring matching to select keys.
    Then, for every key, it checks the key's permissions.
    Returns a dict (JSON).
    """
    urlbase = URLs()
    url, param = urlbase.get_team_api_endpoint()
    data = await urlbase.async_get_json_from_endpoint(url, url_param=param)
    try:
        args = TokenInput(PATTERN=name)
    except Exception:
        logger.exception("Input parsing went wrong.")
        return None

    pattern = re.compile(args.PATTERN, re.IGNORECASE)
    # Build a dict entry for each team with needed information
    output = []
    for current_team in data:
        if pattern.search(current_team["name"]) is not None:
            entry = __initialize_entry()
            entry["team"] = current_team["name"]
            if "apiKeys" in current_team:
                entry["keys"] = []
                # get permission level of API key
                entry["level"], entry["permissions"] = (
                    ("UNKNOWN", [])
                    if "permissions" not in current_team
                    else __get_permission_level(current_team["permissions"])
                )
                # retrieve all masked api keys
                for key_pair in current_team["apiKeys"]:
                    entry["keys"].append(key_pair["maskedKey"])
            output.append(entry)
    for entry in output:
        __print_entry(entry)
    if not output:
        logger.info("No teams matched the given name")
    return {"matched teams": output}


@handle_errors_gracefully
async def check_token_permissions_self() -> dict:
    """
    This function calls the API and returns information about the current team.
    Returns a dict (JSON).
    """
    urlbase = URLs()
    url, param = urlbase.get_team_self_api_endpoint()
    data = await urlbase.async_get_json_from_endpoint(url, url_param=param)
    data = data[0]
    # Build a dict entry for each team with needed information
    output = []
    entry = __initialize_entry()
    entry.pop("keys")
    entry["team"] = data["name"]
    entry["level"], entry["permissions"] = (
        ("UNKNOWN", [])
        if "permissions" not in data
        else __get_permission_level(data["permissions"])
    )
    output.append(entry)
    for out_entry in output:
        __print_entry(out_entry)
    if not output:
        logger.info("No teams matched the given name")
    return {"matched teams": output}


def __get_permission_level(perms_raw) -> str:
    perms = []
    # perms_raw is a list of dictionaries. Collect all the names of the permissions first.
    for current_permissions in perms_raw:
        if "name" in current_permissions:
            perms.append(current_permissions["name"])

    # comparing subsets is easier when working with sets. This prevents unreadable nested ifs.
    perms = set(perms)
    level = "UNKNOWN"
    if set(PERMISSIONS_ADMIN) <= perms:
        level = "ADMIN"
    elif set(PERMISSIONS_JENKINS) <= perms:
        level = "JENKINS"
    elif set(PERMISSIONS_GUI) <= perms:
        level = "GUI"
    elif set(PERMISSIONS_API) <= perms:
        level = "API"
    return (level, list(perms))


def __initialize_entry():
    return {
        "team": "TEAM",
        "keys": ["no keys available for this team"],
        "level": "",
        "permissions": "",
    }


def __print_entry(entry):
    level = entry["level"]
    if level and level == "UNKNOWN":
        logger.info(f"'{entry['team']}' has permissions: {entry['permissions']}")
    elif level:
        logger.info(f"'{entry['team']}' is role {level}")

    for key in entry.get("keys", []):
        logger.info(f"'{entry['team']}' {key}")
        if entry["level"] == "UNKNOWN":
            logger.info(f"'{entry['team']}' has permissions: {entry['permissions']}")
        else:
            logger.info(f"'{entry['team']}' is role {entry['level']}")
