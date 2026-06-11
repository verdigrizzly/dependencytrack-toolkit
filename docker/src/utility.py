import os
import toml
from loguru import logger

def opener(file, flags):
    """Modify default file permission on newly created log files
    https://www.cvedetails.com/cve/CVE-2022-0338/
    """
    return os.open(file, flags, 0o640)

def init_core_config_from_env(path="core_config.toml"):
    VALID_KEYWORDS = ["base_url", "api_key", "ca_path", "timeout", "retries", "parallel_requests"]
    config = {}
    for key in VALID_KEYWORDS:
        env_value = os.getenv(key)
        if env_value is not None:
            config[key] = env_value
    dtrack_config = {}
    dtrack_config["dependencytrack"] = config
    with open(path, "w") as fh:
        toml.dump(dtrack_config, fh)
    logger.debug("Core config initialized from environment variables")
