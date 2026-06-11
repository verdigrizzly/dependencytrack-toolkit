import os
import sys
import toml
import pytest

PATH = "tests/test.toml"
test_configuration = """
[dependencytrack]
base_url = "https://dependency-track.example/"
api_key = "123456"
ca_path = "/etc/ssl/certs/ca-certificates.crt"
parallel_requests = 20
"""


def pytest_sessionstart():
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    parsed_toml = toml.loads(test_configuration)
    with open(PATH, "w") as f:
        toml.dump(parsed_toml, f)
    os.environ["CONFIG_PATH"] = PATH
    sys.path.insert(0, "./src")

def pytest_sessionfinish():
    os.remove(PATH)
