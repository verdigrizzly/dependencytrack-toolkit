# Dependency-Tracker-Toolkit
CLI Tool used to trigger different actions via Dependency Tracker API

## Requirements
+ Python3.10
+ Dependency-Track api-key


## Setup
### User
The packaging functionality was removed from the project for now, the preferred way of running this client at this time is to use the dtracktoolkit directly from your python environment:

`.venv/bin/python -m dtracktoolkit`

See 'Development' for further information.

### Development
Add a virtual environment and install dependencies from `pyproject.toml`
```
python -m venv .venv
source .venv/bin/activate
pip install . 
pip freeze # show installed packages
deactivate
```
The script can now be executed within the virtual env 
`.venv/bin/python -m dtracktoolkit`

or by manually calling main module
`.venv/bin/python src/dtracktoolkit/__main__.py`

For the initial configuration see section **Configuration** 

## Configuration
Please add a "config.toml" file, with the category dependencytrack in the application base directory an update the config values according to your usecase. The default location is in a separate config/ folder, meaning "./config/config.toml"; if you want to use a different location you can set the environment variable `CONFIG_PATH` to the path of the config file. The file shoud look like this:
```
[dependencytrack]
base_url="https://dependency-track.example/"
api_key="<KEY>>"
ca_path="./custom-ca.crt"
timeout = 15
retries = 5
parallel_requests=20
```
timeout and retries refer to HTTP parameters
parallel_requests is the amount of requests done at the same time using httpx.

## Features
The current version includes the following functionalities:

- [Dependency-Tracker-Toolkit](#dependency-tracker-toolkit)
  - [Requirements](#requirements)
  - [Setup](#setup)
    - [User](#user)
    - [Development](#development)
  - [Configuration](#configuration)
  - [Features](#features)
     - [Analyze the number of vulnerable projects, as well as number and age of vulnerabilities and findings](#Analyze the number of vulnerable projects, as well as number and age of vulnerabilities and findings)
    - [Analyze the number of vulnerable projects](#analyze-the-number-of-vulnerable-projects)
    - [Analyze the age of open findings](#analyze-the-age-of-open-findings)
    - [Add missing project version]
    - [Add or remove all tagged projects to notification rule]
    - [Delete outdated project(-version)s](#delete-outdated-project-versions)
    - [Show API token permissions](#show-api-token-permissions)
    - [Remove a tag from project(s)](#remove-a-tag-from-projects)
- [Development](#development-1)
  - [Packaging](#packaging)
  - [Library](#library)
  - [Tests](#tests)
- [Authors](#authors)

Options that can be triggered for all commands are:
+ the gathered information of a command can be output as a json with `-o <FILE PATH>` or `--output <FILE PATH>`
+ a dryrun, which doesn't execute any actions can be invoked with `-dr` or `--dryrun`
+ logging can be in Debug Mode with `-d` or `--debug`
+ a cli command can be converted to config format with `-tc` or `--to-config`
+ forced execution, which does not propt for user approval of changes on the server, with `-f` or `--force`

### Analyze the number of vulnerable projects, as well as number and age of vulnerabilities and findings
Count total projects and those vulnerable with at least one (not suppressed) finding of specified severity or above.
Groups both vulnerabilities (not sharing same alias) and findings (sharing same alias) by severity level and finds the age of each finding and vulnerability. 
Calculates the average age of vulnerabilites and findings (not surpressed) of specified severity or above.
Possible severities are: critical, high, medium, low, unknown and unassigned. 
Tagquery should be a string enclosed with quotation marks using "AND", "NOT", "OR" combined with tags example "(TAG1 AND TAG2) OR TAG3".
Shallow: Reduce number of requests by skipping in-depth vulnerability lookups. Careful - this may impact the result quality.
```
.venv/bin/python -m dtracktoolkit project analyze_vulnerabilities -c <CRITICALITY-NAME> (OPTIONAL: -t "<TAG-QUERY>", -xc <EXCLUDED CLASSIFIER/S>, -p <PARENT_NAME>:<PARENT_VERSION>, --shallow)
```

### Analyze the number of vulnerable projects
Count total projects and those vulnerable with at least one (not suppressed) finding of specified severity or above.
Possible severities are: critical, high, medium, low  
Tagquery should be a string enclosed with quotation marks using "AND", "NOT", "OR" combined with tags example "(TAG1 AND TAG2) OR TAG3".
Shallow: Reduce number of requests by skipping in-depth vulnerability lookups. Careful - this may impact the result quality.
```
.venv/bin/python -m dtracktoolkit project count_vulnerable -c <CRITICALITY-NAME> (OPTIONAL: -t "<TAG-QUERY>", -xc <EXCLUDED CLASSIFIER/S>, -p <PARENT_NAME>:<PARENT_VERSION>, --shallow)
```

### Analyze the age of open findings
Average over the age of findings of a specified severity that have not yet been suppressed or audited. Can find the age of each vulnerability in days, that has a unique vulnID.
Possible severities are: critical, high, medium, low  
Tagquery should be a string enclosed with quotation marks using "AND", "NOT", "OR" combined with tags example "(TAG1 AND TAG2) OR TAG3".
Shallow: Reduce number of requests by skipping in-depth vulnerability lookups. Careful - this may impact the result quality.
```
.venv/bin/python -m dtracktoolkit project average_finding_age -c <CRITICALITY-NAME> (OPTIONAL: -t "<TAG-QUERY>", -xc <EXCLUDED CLASSIFIER/S>, --shallow)
```


### Add missing project version
Add missing project version to a notification rule:
This function requires an **API-key** with permission **SYSTEM_MANAGEMENT**

```
.venv/bin/python -m dtracktoolkit notification update_projects -n <NOTIFICATION-RULE-NAME>
```

### Add or remove all tagged projects to notification rule
fetch projects tag with provided tag and update the notification rule to either add or remove them
Tagquery is currently not supported.
This function requires an **API-key** with permission **SYSTEM_MANAGEMENT**

```
.venv/bin/python -m dtracktoolkit notification assign_projects -n <NOTIFICATION-RULE-NAME> -t <TAG-NAME/S>
```

```
.venv/bin/python -m dtracktoolkit notification remove_projects -n <NOTIFICATION-RULE-NAME> (OPTIONAL: -t <TAG-NAME/S>)
```

### Delete outdated project(-version)s
Permanently delete projects that have not been updated in a specified number of days.
Optionally a list of tag/s can be included, which will prevent projects from being deleted by this function.
Tagquery is currently not supported.
This function requires an **API-key** with permission **PORTFOLIO_MANAGEMENT**

```
.venv/bin/python -m dtracktoolkit project delete_expired -s <NUMBER-OF-DAYS> (OPTIONAL: -st <TAG-NAME/S>)
```

### Show API token permissions
Retrieve the permissions of all API keys assigned to teams that match a given RegEx-Pattern if provided.
Otherwise, it returns information about the current team of the user. 
This function requires an **API-key** with permission **ACCESS_MANAGEMENT**
```
.venv/bin/python -m dtracktoolkit token show_permissions (OPTIONAL: -n <PYTHON-REGEX-PATTERN>)
```

### Remove a tag from project(s)
Remove a tag in bulk, if no `-t` tag(s) are specified, the tag is removed from the whole portfolio.
Tagquery is currently not supported.
```
.venv/bin/python -m dtracktoolkit project remove_tag -r <REMOVED TAG> (OPTIONAL: -t <TAG-NAME/S>, -xc <EXCLUDED CLASSIFIER>) 
```

### Retrieve CVE Information
Retrieves the CVE information of projects. The projects can optionally be filtered by a tag query, but the normal case is that all projects are included in this metric. This functionality is only available in the library version of the dtracktoolkit. As such one can call:
```python
output = asyncio.run(cve_info())
```
Output is a list, which contains an entry for each vulnerability. The entries are of type dict, with the following values:
```
{'cve_name': str, 'aliases': list, 'severity': str, 'cvss_v3': int, 'affected': int}
```

# Development

> **Note**
> [PDM](https://pdm-project.org/latest/) is the recommended package manager for this project. It uses the `pyproject.toml` file to manage dependencies and a lock file to ensure deterministic builds.

The following section describes how to setup a development environment and how to run the application for development purposes.

Setup a virtual environment and install the required dependencies with `pdm`:
+ Open a terminal and navigate inside the project folder
+ Run `pdm install` if you want to install all dependencies including dev or `pdm install --prod` without dev dependencies 
+ Run `pdm update` this will update the lockfile and update dependencies to their newest version

## Packaging
In order to build a package out of this application simply call `pdm build`. This will create a wheel and packaged tarball in the `dist` folder. Important parameters for this step are `distribution = true` in the pyproject.toml file, this will tell pdm to include all dependencies (all folders under src) in the package. After running the command, you can include the package below the src folder by using `import dtrack`. This will use the the [PDM Backend](https://backend.pdm-project.org/), but other build options can be configured in the pyproject toml.
If you need additional files you can add them in the include section like so `includes = ["basepackage/"]` 

## Library
After installing dtracktoolkit as a package, you can use classes and functions in other scripts. The main module is called dtracktoolkit and can be used to import project, notification and token functions. The parameters are the same as in the CLI commands. For exact naming conventions, we refer directly to the code as it includes type hints for all parameters.
```python
from dtracktoolkit import setup_logger
from dtracktoolkit.project import delete_expired, count_vulnerable, average_finding_age, cve_info, remove_tag
from dtracktoolkit.notification import alerts_update_projects, add_projects_to_notification, assign_projects_with_tag, remove_projects_with_tag
from dtracktoolkit.token import check_token_permissions, check_token_permissions_self
```

The new version of dtracktoolkit is implemented with async calls and allows parallel requests. This means functions have to be called with asyncio.run like so:
```python
from asyncio import run
output = run(project.average_finding_age(crit='low', tag='foo'))
```

## Tests
The project contains test files in the *tests/* folder. The tests follow the [Pytest](https://docs.pytest.org/) schema, which should be used for future additions. In order to mock dependency track API calls we make use of two python libraries.

**[RespX](https://lundberg.github.io/respx/)**
 that allows mocking calls that are done using the httpx module. This also includes calls that are done outside of the test method. Some things to keep in mind:
 - responses can be populated from files with calling the request via respx. After registering a route you can provide return values as shown here: \
 <code>my_route = respx.get("https://foo.bar/")</code> \
 <code>my_route.return_value = httpx.Response(200, json={"foo": "bar"})</code>
 - resetting before running a test with <code>respx.reset()</code> is good practice to not get confused with previous populated responses
 - seeing if a response has been called is possible with <code>my_route.call_count</code>
 - a good starting point, are the responses found in the test_count_vulnerable file

*Usage* add the following decorator above the test method: <code>@respx.mock</code>

**[FreezeGun](https://github.com/spulec/freezegun)**
that allows "traveling through time". This library mocks the datetime module and a fixed time can be set, which will be used in calls from the test cases. 

*Usage* add the following decorator above the test method:
<code>@freeze_time("2023-09-17 01:23:45")</code>

--- 

The *pyproject.toml* contains configurations for [Coverage](https://coverage.readthedocs.io/) and Pytest.
- <code>pdm coverage</code> runs all pytests and gives an overview of the coverage

