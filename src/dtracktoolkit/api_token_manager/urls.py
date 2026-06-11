"""API token manager REST endpoints for Dependency-Track."""
from dtracktoolkit.urls import UrlBase


class URLs(UrlBase):
    """Extends Base REST API Endpoints and utility with token specific endpoints"""

    def get_team_api_endpoint(self) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used to access the API of team keys"""
        endpoint = super().normalize_endpoint("/api/v1/team")
        return (endpoint, {})

    def get_team_self_api_endpoint(self) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used to access the API of /team/self keys"""
        endpoint = super().normalize_endpoint("/api/v1/team/self")
        return (endpoint, {})
