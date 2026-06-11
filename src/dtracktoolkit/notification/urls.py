"""Notification-specific REST API endpoints for Dependency-Track."""
from loguru import logger

from dtracktoolkit.urls import UrlBase


class URLs(UrlBase):
    """Extends Base REST API Endpoints and utility with notification specific endpoints"""

    def __init__(self):
        super().__init__()

    def add_project_to_rule(self, rule_id: str, project: dict):
        """Add a project to a notification rule via POST."""
        url, param = self.post_add_project_to_notification_endpoint(
            rule_id, project["uuid"]
        )
        responsecode = self.send_data_to_endpoint("POST", url, url_param=param)
        logger.info(
            "Adding {}:{} - Status {}",
            project["name"],
            project.get("version", "n/a"),
            responsecode,
        )

    def remove_project_from_rule(self, rule_id: str, project: dict):
        """Remove a project from a notification rule via DELETE."""
        url, param = self.post_add_project_to_notification_endpoint(
            rule_id, project["uuid"]
        )
        responsecode = self.send_data_to_endpoint("DELETE", url, url_param=param)
        logger.info(
            "Removing {}:{} - Status {}",
            project["name"],
            project.get("version", "n/a"),
            responsecode,
        )

    def post_add_project_to_notification_endpoint(
        self, notification_id: str, project_id: str
    ) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used to add a given project to a given notification rule"""
        endpoint = super().normalize_endpoint(
            f"/api/v1/notification/rule/{notification_id}/project/{project_id}"
        )
        return (endpoint, {})

    async def fetch_notification_rule(self, rule_name: str) -> dict:
        """Fetch a single notification rule by name, or None if not found."""
        url, parm = self.get_notification_rules_endpoint()
        data = await self.async_get_json_from_endpoint(url, url_param=parm)
        rule = next((rule for rule in data if rule.get("name") == rule_name), None)
        return rule

    def get_notification_rules_endpoint(self) -> tuple[str, dict[str, str]]:
        """Return url used to fetch all notification rules (no url parameter)"""
        endpoint = super().normalize_endpoint("/api/v1/notification/rule")
        return (endpoint, {})
