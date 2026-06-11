"""Project-specific REST API endpoints for Dependency-Track."""
import json
from loguru import logger

from dtracktoolkit.urls import UrlBase


class URLs(UrlBase):
    """Extends Base REST API Endpoints and utility with project specific endpoints"""

    def __init__(self):
        super().__init__()

    def delete_project(self, project: dict[str, str]) -> None:
        """Delete a project based on the given dict"""
        url, param = self.delete_project_endpoint(project["uuid"])
        responsecode = self.send_data_to_endpoint("DELETE", url, url_param=param)
        logger.info(
            "Removing {}:{} - Status {}",
            project["name"],
            project.get("version", "n/a"),
            responsecode,
        )

    def delete_tag(self, project: dict[str, str], tag: str) -> None:
        """Update project to remove given tag"""
        new_tags = json.dumps([t for t in project["tags"] if t["name"] != tag])
        tag_data = "".join(['{"tags":', new_tags, "}"])

        url, param = self.delete_project_endpoint(project_id=project["uuid"])
        responsecode = self.send_data_to_endpoint(
            "PATCH", url, url_param=param, bodydata=tag_data
        )

        logger.info(
            "Updating {}:{} - Status {}",
            project["name"],
            project.get("version", "n/a"),
            responsecode,
        )

    def delete_project_endpoint(self, project_id: str) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used to delete a given project"""
        endpoint = super().normalize_endpoint(f"/api/v1/project/{project_id}")
        return (endpoint, {})

    async def fetch_project_findings(self, project_id: str) -> dict:
        """Return all findings of a given project"""
        url, param = self.get_project_findings_endpoint(project_id)
        return await self.async_get_json_from_endpoint(url, url_param=param)

    def get_project_findings_endpoint(
        self, project_id: str
    ) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used return a list of findings for a given project"""
        endpoint = super().normalize_endpoint(f"/api/v1/finding/project/{project_id}")
        return (endpoint, {})
