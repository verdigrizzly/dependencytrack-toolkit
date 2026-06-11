"""Constants and validation helpers for Dependency-Track API token permissions."""
from typing import Final


class TokenInput:
    """
    Class used to parse the CLI arguments.
    """

    def __init__(self, PATTERN: str) -> None:
        self.PATTERN: Final[str] = PATTERN
