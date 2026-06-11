"""
Dependency track api interaction and endpoints
"""
# standard imports
from typing import Type, Final
import ssl
import asyncio
from datetime import datetime
from copy import deepcopy
from urllib import parse
from json.decoder import JSONDecodeError
# third-party imports
import httpx
import furl
from pydantic import BaseModel, ValidationError
from loguru import logger
# project imports
from dtracktoolkit.query_language import (
    LambdaFilterTag,
    LambdaFilterName,
    MinimalFetcher,
    dependo_script,
    NOT_TOKEN,
)
from dtracktoolkit.utility import remove_duplicate_projects
from dtracktoolkit.constants import config
from dtracktoolkit.pydantic_input_schema import (
    Project,
    Finding,
    Notification,
    TokensSelf,
    Tokens,
    SearchProject,
)


class UrlBase:
    """REST API Endpoints and utility to interact with DTrack instance"""

    async_semaphore = asyncio.Semaphore(config.parallel_requests)
    TIMEOUT: Final[int] = config.timeout
    RETRIES: Final[int] = config.retries
    BACKOFF: Final[float] = config.backoff
    STATUSLIST: Final[list] = [500, 502, 503, 504]
    HTTPMETHODS: Final[list] = ["GET", "PUT", "PATCH", "POST", "DELETE"]

    def __init__(self, baseurl: str = None, apikey: str = None, capath: str = None):
        if not baseurl or not apikey or not capath:
            self.BASE_URL: Final[str] = config.base_url
            self.API_KEY: Final[str] = config.api_key
            self.CA_PATH: Final[str] = config.ca_path
        else:
            self.BASE_URL: Final[str] = baseurl
            self.API_KEY: Final[str] = apikey
            self.CA_PATH: Final[str] = capath

    def get_search_project_endpoint(self, query: str) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used to query the dtrack database - searches for the query in name, description, etc. of projects"""
        endpoint = self.normalize_endpoint("/api/v1/search/project")
        return (endpoint, {"query": query, "excludeInactive": "true"})

    def get_project_data_endpoint_by_name(
        self, project_name: str
    ) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used to fetch data of a projects (all version) to a name - this endpoint does not retrieve metrics"""
        endpoint = furl.furl(self.BASE_URL)
        endpoint.set(path=str(endpoint.path) + "/api/v1/project")
        endpoint.set(path=endpoint.path.normalize())
        logger.debug(f"ENDPOINT: {endpoint}")
        return (endpoint, {"name": project_name})

    def get_project_data_endpoint_by_uuid(
        self, uuid: str
    ) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used to fetch data of a single project by uuid - this endpoint returns all data"""
        endpoint = self.normalize_endpoint(f"/api/v1/project/{uuid}")
        return (endpoint, {})

    def get_tagged_project_endpoint(self, tag: str) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used to fetch all projects with a given tag"""
        # ensure tags with special characters are correctly encoded
        endpoint = self.normalize_endpoint(
            f"/api/v1/project/tag/{parse.quote(tag.strip(), safe='')}"
        )
        return (endpoint, {"excludeInactive": "true"})

    def get_active_project_endpoint(self) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used to fetch all active projects"""
        endpoint = self.normalize_endpoint("/api/v1/project")
        return (endpoint, {"excludeInactive": "true"})

    def get_project_lookup_endpoint(
        self, project_name: str, version: str = None
    ) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used to fetch a single project by id"""
        endpoint = furl.furl(self.BASE_URL)
        endpoint.set(path=str(endpoint.path) + "/api/v1/project/lookup")
        endpoint.set(path=endpoint.path.normalize())
        logger.debug(f"ENDPOINT: {endpoint}")
        params = {"name": project_name}
        if version:
            params["version"] = version
        return (endpoint, params)

    def get_children_by_parent_uuid(
        self, parent_uuid: str
    ) -> tuple[str, dict[str, str]]:
        """Return url and url parameter used to fetch all child projects of a given parent project"""
        endpoint = furl.furl(self.BASE_URL)
        endpoint.set(
            path=str(endpoint.path) + f"/api/v1/project/{parent_uuid}/children"
        )
        endpoint.set(path=endpoint.path.normalize())
        logger.debug(f"ENDPOINT: {endpoint}")
        return (endpoint, {})

    async def async_get_json_from_endpoint(self, url, url_param: dict = None) -> dict:
        """
        Call a dependency track endpoint based on a given url and url parameters.
        This method uses async http requests along with a semaphore to limit the number of concurrent requests.

        In case the response contains to many items for a single request,
        this method will fetch the paged content in multiple api calls.

        Returns:
            dict: if api response contained valid json - raise ProjectNotFoundError otherwise
        """
        async with self.async_semaphore:
            ca_file = ssl.create_default_context(cafile=self.CA_PATH)
            retries = httpx.AsyncHTTPTransport(verify=ca_file, retries=UrlBase.RETRIES)
            async with httpx.AsyncClient(
                timeout=UrlBase.TIMEOUT, transport=retries
            ) as client:
                headers = {"X-Api-Key": self.API_KEY}
                page = 1
                param = {"page": page, "limit": 1000}
                if isinstance(url_param, dict):
                    param.update(url_param)
                now = datetime.now()
                try:
                    resp = await client.get(str(url), params=param, headers=headers)
                except Exception as error:
                    raise error

                if resp.status_code != 200:
                    logger.error(
                        f"api call failed (status:{resp.status_code}, error:{resp.content})"
                    )
                    # Error handling for a project not being found after search
                    if resp.content == b"The project could not be found.":
                        raise ProjectNotFoundError(
                            f"Api call failed, because a project could not be found (status:{resp.status_code}, error:{resp.content})"
                        )
                try:

                    data = resp.json()
                    self.validate_json(data, url)
                except (
                    JSONDecodeError
                ) as error:  # if the project data received was not in JSON format
                    logger.error(
                        "Received project data that was not in JSON Format from URL: " +
                        str(url) +
                        "!",
                        error,
                    )
                logger.debug(
                    (
                        "Response:{size} Bytes  latency:{latency}s - "
                        "len: {elements_in_response}/{elements_total} - "
                        "time_at:{now}"
                    ),
                    size=len(resp.content),
                    latency=resp.elapsed.total_seconds(),
                    elements_in_response=len(data),
                    elements_total=resp.headers.get("X-Total-Count"),
                    now=now.timestamp(),
                )
                # load missing data in case of paginated content

                while len(data) < int(resp.headers.get("X-Total-Count", 0)):
                    page += 1
                    param["page"] = page
                    now = datetime.now()
                    try:
                        resp = await client.get(str(url), params=param, headers=headers)
                    except Exception as error:
                        raise error

                    if resp.status_code != 200:
                        logger.error(
                            f"api call failed (status:{resp.status_code}, error:{resp.content})"
                        )
                        # Error handling for a project not being found after search
                        if resp.content == b"The project could not be found.":
                            raise ProjectNotFoundError(
                                f"Api call failed, because a project could not be found (status:{resp.status_code}, error:{resp.content})"
                            )
                    try:
                        data += resp.json()
                        self.validate_json(data, url)
                    except (
                        JSONDecodeError
                    ) as error:  # if the project data received was not in JSON format
                        logger.error(
                            "Received project data that was not in JSON Format from URL: " +
                            str(url) +
                            "!",
                            error,
                        )

                    logger.debug(
                        (
                            "PAGED-REQUEST Response:{size} Bytes  latency:{latency}s - "
                            "len: {elements_in_response}/{elements_total} - "
                            "at_time:{now}"
                        ),
                        size=len(resp.content),
                        latency=resp.elapsed.total_seconds(),
                        elements_in_response=len(data),
                        elements_total=resp.headers.get("X-Total-Count"),
                        now=now.timestamp(),
                    )
                if data is not None and isinstance(data, dict):
                    return [data]
                return [d for d in data if d is not None]

    async def fetch_all_projects(self) -> dict:
        """Return all active projects"""
        url, param = self.get_active_project_endpoint()
        return await self.async_get_json_from_endpoint(url, url_param=param)

    async def fetch_projects_by_namequery(self, query: str) -> list:
        """fetches all projects that satisfy the expression listed in tag"""
        # parse and transform the input query
        ast_tree = dependo_script.parse(query)
        filter_function = LambdaFilterName().transform(ast_tree)
        name_list = MinimalFetcher().transform(ast_tree)
        name_list = [name_list] if type(name_list) is str else name_list
        logger.debug(
            f"Project names that have to be called by the API: {name_list} {type(name_list)}"
        )
        # request tagged projects
        # If we have a NOT_TOKEN we need to fetch all projects
        if NOT_TOKEN in name_list:
            unfiltered_projects = await self.fetch_all_projects()
        else:
            all_fetched_projects = []
            for t in name_list:
                all_fetched_projects += await self.fetch_projects_with_name(t)
            unfiltered_projects = remove_duplicate_projects(all_fetched_projects)
        projects = list(filter(filter_function, unfiltered_projects))
        return projects

    async def fetch_projects_with_name(self, name: str) -> list:
        """fetch all projects with given project name - this is done in two steps:
        1. we query a search for a specific "name", this also contains projects that match with description, version, etc. Also the search does not return all project data
        2. we retrieve all data for a project with get_project_data_endpoint_by_uuid

        Args:
            name (str): The name of the project to search for.

        Returns:
            list: A list of project data.
        """
        logger.debug(f"Fetching projects with name {name}")
        url, param = self.get_search_project_endpoint(query=name)
        data = await self.async_get_json_from_endpoint(url, url_param=param)
        unzip_list = data[0]["results"]["project"]
        filter_by_name = lambda x: name in x["name"]
        project_list = list(filter(filter_by_name, unzip_list))

        # Prepare tasks for async call
        tasks_calls = []
        for project in project_list:
            uuid = project["uuid"]
            url, param = self.get_project_data_endpoint_by_uuid(uuid)
            t = asyncio.create_task(
                self.async_get_json_from_endpoint(url, url_param=param)
            )
            tasks_calls.append(t)

        project_data_raw = await asyncio.gather(*tasks_calls, return_exceptions=True)
        project_data = []
        for index, project in enumerate(project_list):
            if isinstance(project_data_raw[index], ProjectNotFoundError):
                logger.error(f"Project {name} with uuid {uuid} not found")
                continue
            if isinstance(project_data_raw[index], Exception):
                logger.exception(project_data_raw[index])
            else:
                project_data.append(project_data_raw[index][0])
        return project_data

    async def fetch_projects_by_tagquery(self, tag: str) -> list:
        """fetches all projects that satisfy the expression listed in tag"""
        # parse and transform the input query
        ast_tree = dependo_script.parse(tag)
        filter_function = LambdaFilterTag().transform(ast_tree)
        tag_list = MinimalFetcher().transform(ast_tree)
        tag_list = [tag_list] if type(tag_list) is str else tag_list
        logger.debug(
            f"Tags that have to be called by the API: {tag_list} {type(tag_list)}"
        )
        # request tagged projects
        # If we have a NOT_TOKEN we need to fetch all projects
        if NOT_TOKEN in tag_list:
            unfiltered_projects = await self.fetch_all_projects()
        else:
            all_fetched_projects = []
            for t in tag_list:
                all_fetched_projects += await self.fetch_projects_with_tag(t)
            unfiltered_projects = remove_duplicate_projects(all_fetched_projects)
        projects = list(filter(filter_function, unfiltered_projects))
        return projects

    async def fetch_children_by_parent_project(self, parent_pattern: str) -> list:
        """fetches all child projects that satisfy the expression listed in parent"""
        # split name:version pattern
        parent_split = parent_pattern.split(":")
        version = None
        if len(parent_split) >= 2:
            version = parent_split[1]
        parent = parent_split[0]
        # first get parent uuid, then get all children
        url, params = self.get_project_lookup_endpoint(parent, version)
        try:
            data = await self.async_get_json_from_endpoint(url, url_param=params)
        except ProjectNotFoundError:
            data = None
            logger.debug(
                f"Found no project {parent}{' with version ' + version if version else '.'}"
            )
        else:
            logger.debug(
                f"Found parent project {parent}{' with version ' + version if version else '.'}"
            )
        if data:
            uuid = data[0]["uuid"]
            url, params = self.get_children_by_parent_uuid(uuid)
            data = await self.async_get_json_from_endpoint(url, url_param=params)
        return data

    async def fetch_projects_with_tag(self, tag: str) -> dict:
        """fetch all projects with given tag"""
        url, param = self.get_tagged_project_endpoint(tag)
        return await self.async_get_json_from_endpoint(url, url_param=param)

    def send_data_to_endpoint(
        self, httpmethod: str, url, url_param: dict = None, bodydata: str = None
    ) -> int:
        """Send a changing HTTP request, do not process response body"""
        ca_file = ssl.create_default_context(cafile=self.CA_PATH)
        retries = httpx.HTTPTransport(verify=ca_file, retries=UrlBase.RETRIES)
        method = httpmethod.upper()
        if method not in UrlBase.HTTPMETHODS:
            logger.error(f"Forbidden http method {method}")
            raise ValueError(f"Forbidden http method {method}")

        headers = {"X-Api-Key": self.API_KEY, "Content-Type": "application/json"}
        with httpx.Client(timeout=UrlBase.TIMEOUT, transport=retries) as client:
            resp = client.request(
                method=httpmethod,
                url=str(url),
                params=url_param,
                headers=headers,
                timeout=UrlBase.TIMEOUT,
                data=bodydata,
            )
        return resp.status_code

    def validate_json(self, resp: list, endpoint: str) -> list:
        """validate given data (resp) received from endpoint, type of data is defined by url"""
        target_model: Type[BaseModel]
        search_operation = False
        input_data = deepcopy(resp)

        # identifying type of data we receive can be extended in the future
        if "api/v1/project" in endpoint.url:
            target_model = Project
        elif "api/v1/finding" in endpoint.url:
            target_model = Finding
        elif "v1/notification/rule" in endpoint.url:
            target_model = Notification
        elif "/api/v1/team/self" in endpoint.url:
            target_model = TokensSelf
        elif "/api/v1/team" in endpoint.url:
            target_model = Tokens
        elif "/api/v1/search/project" in endpoint.url:
            target_model = SearchProject
            search_operation = True
        else:
            # Default fallback
            target_model = Project

        if search_operation or not isinstance(resp, list):
            # search results are an exception and are not returned as a list
            # so we need to wrap the result in a list
            input_data = [input_data]

        result_data: list = []
        for data_point in input_data:
            try:
                target_model.model_validate(data_point)
            except ValidationError as error:

                all_errors = error.errors()
                first_error = all_errors[0]

                # Safe logging using dictionary keys 'msg' and 'loc'
                # 'loc' is a tuple like ('body', 'item', 0, 'name')
                logger.error(
                    "Input validation failed. Skipping datapoint.\nReason: {} \nLocation: {}",
                    first_error.get("msg", "Unknown error"),
                    first_error.get("loc", "Unknown location"),
                )
                result_data.append(None)
            else:
                result_data.append(data_point)

        return result_data

    def normalize_endpoint(self, route: str) -> furl.furl:
        """Append route to the base URL and return a normalised furl object."""
        endpoint = furl.furl(self.BASE_URL)
        endpoint.set(path=str(endpoint.path) + route)
        endpoint.set(path=endpoint.path.normalize())
        logger.debug(f"ENDPOINT: {endpoint}")
        return endpoint


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be found by its UUID in Dependency-Track."""
