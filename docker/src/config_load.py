import sys
import toml
import base64
import requests
from decouple import config
from loguru import logger


def build_url(server: str, repo_owner: str, repo_name: str, file_location: str) -> str:
    """Create URL to download single file from gitea repo

    Args:
        server (str): hostname (FQDN) of the server
        repo_owner (str): owner of the repository
        repo_name (str): name of the repository
        file_location (str): location of the file in the main branch

    Returns:
        str: expected url
    """
    url = f"https://{server}/api/v1/repos/{repo_owner}/{repo_name}/contents/{file_location}"
    return url


def fetch_config_from_git(url: str, api_key: str, config_file_location: str) -> bool:
    """Download a single file based on give url from an gitea repo

    Args:
        url (str): gitea api url
        api_key (str): valid api key with permission to read from repo

    Returns:
        bool: operation success
    """
    url_params = {"ref": "master", "token": api_key}
    headers = {"accept": "application/json"}
    response = requests.get(
        url=url, params=url_params, headers=headers
    )  # TODO: catch exception
    print(f"status:{response.status_code}")
    if response.status_code == 404:
        logger.error(
            "Can't collect configuration file from git - perhaps misspelled? uri ({})",
            url,
        )
        sys.exit(1)

    data = response.json()
    config_data = base64.b64decode(data["content"])

    # Make sure config is valid toml
    toml.loads(config_data.decode())  # TODO: catch exception

    # store config.toml in file
    with open(config_file_location, "wb") as fh:
        fh.write(config_data)

    return True


if __name__ == "__main__":
    # DENY ALL SWITCH
    gitea_api_key: str = config("config_from_git", "True")
    if gitea_api_key == "False":
        logger.info("config_from_git is set to false - skipping")
        sys.exit(0)

    # load config
    gitea_api_key: str = config("gitea_api_key")
    gitea_host: str = config("gitea_host", "gite.example")
    repo_owner: str = config("repo_owner", "team")
    repo_name: str = config("repo_name", "dtrack-toolkit_config")
    repo_file_location: str = config("repo_file_location", "config.toml")

    config_file_location: str = sys.argv[1]
    # load config
    url = build_url(gitea_host, repo_owner, repo_name, repo_file_location)
    print(url)
    fetch_config_from_git(
        url=url, api_key=gitea_api_key, config_file_location=config_file_location
    )
