# General
PROJECT_URL = "https://dependency-track.example/api/v1/project?page=1&limit=1000&excludeInactive=true"
NOTIFICATION_URL = "https://dependency-track.example/api/v1/notification/rule?page=1&limit=1000"
FIRSTTAG_URL = "https://dependency-track.example/api/v1/project/tag/FIRSTTAG?page=1&limit=1000&excludeInactive=true"
FIRSTTAG_URL_2 = "https://dependency-track.example/api/v1/project/tag/FIRSTtag?page=1&limit=1000&excludeInactive=true"
# Notification
ADD_NOTIFY_V1_URL = "https://dependency-track.example/api/v1/notification/rule/6d490fd5-9787-4190-8493-3e6eb3e0ba31/project/44f3c5fd-0806-47b1-b22b-caa3d3d91281"
ADD_NOTIFY_V2_URL = "https://dependency-track.example/api/v1/notification/rule/6d490fd5-9787-4190-8493-3e6eb3e0ba31/project/c9330fff-dbb9-4e82-b675-d08bd94a4c17"
DELETE_NOTIFY_V1_URL = "https://dependency-track.example/api/v1/notification/rule/6d490fd5-9787-4190-8493-3e6eb3e0ba31/project/44f3c5fd-0806-47b1-b22b-caa3d3d91281"
DELETE_NOTIFY_V2_URL = "https://dependency-track.example/api/v1/notification/rule/6d490fd5-9787-4190-8493-3e6eb3e0ba31/project/c9330fff-dbb9-4e82-b675-d08bd94a4c17"
# Project
DELETE_PROJECT_URL = "https://dependency-track.example/api/v1/project/"
FINDINGS_V1_URL = "https://dependency-track.example/api/v1/finding/project/44f3c5fd-0806-47b1-b22b-caa3d3d91281?page=1&limit=1000"
FINDINGS_V2_URL = "https://dependency-track.example/api/v1/finding/project/c9330fff-dbb9-4e82-b675-d08bd94a4c17?page=1&limit=1000"
# Token
TEAM_SELF_URL = (
    "https://dependency-track.example/api/v1/team/self?page=1&limit=1000"
)
TEAM_ALL_URL = (
    "https://dependency-track.example/api/v1/team?page=1&limit=1000"
)

PROJECT = {
    "name": "happy-test",
    "uuid": "44f3c5fd-0806-47b1-b22b-caa3d3d91281",
    "tag": "FIRSTTAG",
}

NOTIFICATION = {
    "name": "team-test-mail",
    "uuid": "6d490fd5-9787-4190-8493-3e6eb3e0ba31",
}

FIRSTTAG_RESPONSE = [
    {
        "name": "happy-test",
        "version": "1.0",
        "classifier": "LIBRARY",
        "uuid": "44f3c5fd-0806-47b1-b22b-caa3d3d91281",
        "tags": [
            {"name": "firsttag"},
            {"name": "foo"},
            {"name": "secondtag"},
            {"name": "foo"},
            {"name": "thirdtag"},
        ],
        "lastBomImport": 1692172184500,
        "lastBomImportFormat": "CycloneDX 1.4",
        "lastInheritedRiskScore": 23.0,
        "active": True,
        "metrics": {
            "critical": 1,
            "high": 0,
            "medium": 1,
            "low": 0,
            "unassigned": 0,
            "vulnerabilities": 2,
            "vulnerableComponents": 2,
            "components": 57,
            "suppressed": 0,
            "findingsTotal": 3,
            "findingsAudited": 0,
            "findingsUnaudited": 1,
            "inheritedRiskScore": 23.0,
            "policyViolationsFail": 0,
            "policyViolationsWarn": 0,
            "policyViolationsInfo": 0,
            "policyViolationsTotal": 0,
            "policyViolationsAudited": 0,
            "policyViolationsUnaudited": 0,
            "policyViolationsSecurityTotal": 0,
            "policyViolationsSecurityAudited": 0,
            "policyViolationsSecurityUnaudited": 0,
            "policyViolationsLicenseTotal": 0,
            "policyViolationsLicenseAudited": 0,
            "policyViolationsLicenseUnaudited": 0,
            "policyViolationsOperationalTotal": 0,
            "policyViolationsOperationalAudited": 0,
            "policyViolationsOperationalUnaudited": 0,
            "firstOccurrence": 1692379930741,
            "lastOccurrence": 1693821114308,
        },
    },
    {
        "name": "happy-test",
        "version": "2.0",
        "classifier": "APPLICATION",
        "uuid": "c9330fff-dbb9-4e82-b675-d08bd94a4c17",
        "tags": [{"name": "firsttag"}],
        "lastBomImport": 1692189442111,
        "lastBomImportFormat": "CycloneDX 1.4",
        "lastInheritedRiskScore": 23.0,
        "active": True,
        "metrics": {
            "critical": 0,
            "high": 0,
            "medium": 1,
            "low": 0,
            "unassigned": 0,
            "vulnerabilities": 1,
            "vulnerableComponents": 1,
            "components": 57,
            "suppressed": 0,
            "findingsTotal": 1,
            "findingsAudited": 0,
            "findingsUnaudited": 1,
            "inheritedRiskScore": 23.0,
            "policyViolationsFail": 0,
            "policyViolationsWarn": 0,
            "policyViolationsInfo": 0,
            "policyViolationsTotal": 0,
            "policyViolationsAudited": 0,
            "policyViolationsUnaudited": 0,
            "policyViolationsSecurityTotal": 0,
            "policyViolationsSecurityAudited": 0,
            "policyViolationsSecurityUnaudited": 0,
            "policyViolationsLicenseTotal": 0,
            "policyViolationsLicenseAudited": 0,
            "policyViolationsLicenseUnaudited": 0,
            "policyViolationsOperationalTotal": 0,
            "policyViolationsOperationalAudited": 0,
            "policyViolationsOperationalUnaudited": 0,
            "firstOccurrence": 1692379929129,
            "lastOccurrence": 1693821112709,
        },
    },
]

APP_PROJECT = {
    "name": "application",
    "description": 'This is the description.',
    "version": "1.0.0",
    "classifier": "APPLICATION",
    "uuid": "41e79d38-72ef-422a-a3b7-3c39a6f676cc",
    "tags": [{"name": "foo"}],
    "lastBomImport": 1658850613950,
    "lastBomImportFormat": "CycloneDX 1.4",
    "lastInheritedRiskScore": 50,
    "active": True,
    "metrics": {
        "critical": 0,
        "high": 6,
        "medium": 6,
        "low": 2,
        "unassigned": 0,
        "vulnerabilities": 14,
        "vulnerableComponents": 8,
        "components": 35,
        "suppressed": 0,
        "findingsTotal": 14,
        "findingsAudited": 0,
        "findingsUnaudited": 14,
        "inheritedRiskScore": 50,
        "policyViolationsFail": 0,
        "policyViolationsWarn": 0,
        "policyViolationsInfo": 0,
        "policyViolationsTotal": 0,
        "policyViolationsAudited": 0,
        "policyViolationsUnaudited": 0,
        "policyViolationsSecurityTotal": 0,
        "policyViolationsSecurityAudited": 0,
        "policyViolationsSecurityUnaudited": 0,
        "policyViolationsLicenseTotal": 0,
        "policyViolationsLicenseAudited": 0,
        "policyViolationsLicenseUnaudited": 0,
        "policyViolationsOperationalTotal": 0,
        "policyViolationsOperationalAudited": 0,
        "policyViolationsOperationalUnaudited": 0,
        "firstOccurrence": 1684804662413,
        "lastOccurrence": 1685017171324,
    },
}
PROJECT_LIST_RESPONSE = [APP_PROJECT]

NOTIFICATION_RESPONSE = [
    {
        "name": "team-test-mail",
        "enabled": False,
        "notifyChildren": False,
        "scope": "PORTFOLIO",
        "notificationLevel": "INFORMATIONAL",
        "projects": [
            {
                "name": "happy-test",
                "version": "1.0",
                "classifier": "APPLICATION",
                "uuid": "44f3c5fd-0806-47b1-b22b-caa3d3d91281",
                "lastInheritedRiskScore": 0.0,
                "active": True,
            }
        ],
        "notifyOn": [
            "NEW_VULNERABILITY",
            "NEW_VULNERABLE_DEPENDENCY",
            "PROJECT_AUDIT_CHANGE",
            "BOM_CONSUMED",
            "BOM_PROCESSED",
            "VEX_CONSUMED",
            "VEX_PROCESSED",
            "POLICY_VIOLATION",
        ],
        "publisher": {},
        "publisherConfig": '{"destination":"user@mail.example"}',
        "uuid": "6d490fd5-9787-4190-8493-3e6eb3e0ba31",
    },
]

# This project contains 3 vulnerabilities: 1 MEDIUM, 1 CRITICAL, 1 UNASSGINED
# However the Critical and Unassigned are the same (share an alias)
FINDINGS_HAPPY_TEST_V1 = [
    {
        "component": {
            "uuid": "8263a901-60c3-4386-b11a-0d77a220b453",
            "name": "GitPython",
            "version": "3.1.31",
            "purl": "pkg:pypi/gitpython@3.1.31",
            "project": "44f3c5fd-0806-47b1-b22b-caa3d3d91281",
            "latestVersion": "3.1.34",
        },
        "vulnerability": {
            "uuid": "f24ed952-8f92-4e4b-996d-9812560678eb",
            "source": "NVD",
            "vulnId": "CVE-2023-40267",
            "cvssV3BaseScore": 9.8,
            "severity": "CRITICAL",
            "severityRank": 0,
            "epssScore": 0.00063,
            "epssPercentile": 0.24936,
            "aliases": [{"cveId": "CVE-2023-40267", "ghsaId": "GHSA-248v-346w-9cwc"}],
            "description": "GitPythonbefore 3.1.32 does not block insecure non-multi options in clone and clone_from.NOTE: this issue exists because of an incomplete fix for CVE-2022-24439.",
            "recommendation": None,
        },
        "analysis": {"isSuppressed": False},
        "attribution": {
            "analyzerIdentity": "OSSINDEX_ANALYZER",
            "attributedOn": 1692172188412,
        },
        "matrix": "44f3c5fd-0806-47b1-b22b-caa3d3d91281:8263a901-60c3-4386-b11a-0d77a220b453:f24ed952-8f92-4e4b-996d-9812560678eb",
    },
    {
        "component": {
            "uuid": "8263a901-60c3-4386-b11a-0d77a220b453",
            "name": "GitPython",
            "version": "3.1.31",
            "purl": "pkg:pypi/gitpython@3.1.31",
            "project": "44f3c5fd-0806-47b1-b22b-caa3d3d91281",
            "latestVersion": "3.1.34",
        },
        "vulnerability": {
            "uuid": "c662c8e2-6878-47fc-a5fe-a357fa6342f4",
            "source": "GITHUB",
            "vulnId": "GHSA-248v-346w-9cwc",
            "title": "GitPython Blablabla",
            "description": "GitPython before 3.1.32 does not block insecure non-multi options in clone and clone_from.",
            "severity": "UNASSIGNED",
            "severityRank": 5,
            "cweId": 345,
            "cweName": "Insufficient Verification of Data Authenticity",
            "cwes": [
                {"cweId": 345, "name": "Insufficient Verification of Data Authenticity"}
            ],
            "aliases": [{"cveId": "CVE-2023-40267", "ghsaId": "GHSA-248v-346w-9cwc"}],
        },
        "analysis": {"isSuppressed": False},
        "attribution": {
            "analyzerIdentity": "OSSINDEX_ANALYZER",
            "attributedOn": 1692172188412,
        },
        "matrix": "44f3c5fd-0806-47b1-b22b-caa3d3d91281:8263a901-60c3-4386-b11a-0d77a220b453:f24ed952-8f92-4e4b-996d-9812560678eb",
    },
    {
        "component": {
            "uuid": "026ebf37-f308-4082-91dc-3e37d567cd8d",
            "name": "loguru",
            "version": "0.7.0",
            "purl": "pkg:pypi/loguru@0.7.0",
            "project": "44f3c5fd-0806-47b1-b22b-caa3d3d91281",
            "latestVersion": "0.7.0",
        },
        "vulnerability": {
            "uuid": "8a95424e-4989-47a7-9c9b-a22727b3ae88",
            "source": "NVD",
            "vulnId": "CVE-2022-0338",
            "cvssV2BaseScore": 4.0,
            "cvssV3BaseScore": 4.3,
            "severity": "MEDIUM",
            "severityRank": 2,
            "epssScore": 0.00046,
            "epssPercentile": 0.14002,
            "cweId": 532,
            "cweName": "Inclusionof Sensitive Information in Log Files",
            "cwes": [
                {"cweId": 532, "name": "Inclusionof Sensitive Information in Log Files"}
            ],
            "aliases": [],
            "description": "Insertion of Sensitive Information into Log File in Conda loguru prior to 0.5.3.\n\n",
            "recommendation": None,
        },
        "analysis": {"isSuppressed": False},
        "attribution": {
            "analyzerIdentity": "OSSINDEX_ANALYZER",
            "attributedOn": 1692172189785,
        },
        "matrix": "44f3c5fd-0806-47b1-b22b-caa3d3d91281:026ebf37-f308-4082-91dc-3e37d567cd8d:8a95424e-4989-47a7-9c9b-a22727b3ae88",
    },
]

FINDINGS_HAPPY_TEST_V2 = [
    {
        "component": {
            "uuid": "026ebf37-f308-4082-91dc-3e37d567cd8d",
            "name": "loguru",
            "version": "0.7.0",
            "purl": "pkg:pypi/loguru@0.7.0",
            "project": "44f3c5fd-0806-47b1-b22b-caa3d3d91281",
            "latestVersion": "0.7.0",
        },
        "vulnerability": {
            "uuid": "8a95424e-4989-47a7-9c9b-a22727b3ae88",
            "source": "NVD",
            "vulnId": "CVE-2022-0338",
            "cvssV2BaseScore": 4.0,
            "cvssV3BaseScore": 4.3,
            "severity": "MEDIUM",
            "severityRank": 2,
            "epssScore": 0.00046,
            "epssPercentile": 0.14002,
            "cweId": 532,
            "cweName": "Inclusionof Sensitive Information in Log Files",
            "cwes": [
                {"cweId": 532, "name": "Inclusionof Sensitive Information in Log Files"}
            ],
            "aliases": [],
            "description": "Insertion of Sensitive Information into Log File in Conda loguru prior to 0.5.3.\n\n",
            "recommendation": None,
        },
        "analysis": {"isSuppressed": False},
        "attribution": {
            "analyzerIdentity": "OSSINDEX_ANALYZER",
            "attributedOn": 1690494337785,
        },
        "matrix": "44f3c5fd-0806-47b1-b22b-caa3d3d91281:026ebf37-f308-4082-91dc-3e37d567cd8d:8a95424e-4989-47a7-9c9b-a22727b3ae88",
    }
]

TEAM_RESPONSE = [{
    "uuid": "310edb78-4607-461c-914c-98a8820df9c5",
    "name": "team-test2",
    "apiKeys": [{"keys": "12345", "maskedKey": "***45"}],
    "permissions": [
        {"name": "ACCESS_MANAGEMENT", "description": "277571"},
        {"name": "BOM_UPLOAD", "description": "277566"},
        {
            "name": "POLICY_MANAGEMENT",
            "description": "Allows the creation, modification, and deletion of policy",
        },
        {
            "name": "POLICY_VIOLATION_ANALYSIS",
            "description": "Provides the ability to make analysis decisions on policy violations",
        },
        {"name": "PORTFOLIO_MANAGEMENT", "description": "277569"},
        {"name": "PROJECT_CREATION_UPLOAD", "description": "277573"},
        {"name": "SYSTEM_CONFIGURATION", "description": "277572"},
        {
            "name": "VIEW_POLICY_VIOLATION",
            "description": "Provides the ability to view policy violations",
        },
        {"name": "VIEW_PORTFOLIO", "description": "277568"},
        {
            "name": "VIEW_VULNERABILITY",
            "description": "Provides the ability to view the vulnerabilities projects are affected by",
        },
        {"name": "VULNERABILITY_ANALYSIS", "description": "277570"},
        {
            "name": "VULNERABILITY_MANAGEMENT",
            "description": "Allows management of internally-defined vulnerabilities",
        },
        {'name': 'TAG_MANAGEMENT',
         'description': 'Allows the modification and deletion of tags'},
        {'name': 'VIEW_BADGES',
         'description': 'Provides the ability to view badges'},
    ],
},
{
    'uuid': 'd92be516-2cd6-4d97-a947-286c6c076189',
    'name': 'team-api-permissions', 
    'apiKeys': [{'keys': '12345', 'maskedKey': '***IcKW'}], 
    'permissions': [
        {'name': 'BOM_UPLOAD', 'description': '277566'},
        {'name': 'POLICY_VIOLATION_ANALYSIS',
        'description': 'Provides the ability to make analysis decisions on policy violations'},
        {'name': 'PROJECT_CREATION_UPLOAD', 'description': '277573'},
        {'name': 'SYSTEM_CONFIGURATION', 'description': '277572'},
        {'name': 'TAG_MANAGEMENT',
        'description': 'Allows the modification and deletion of tags'},
        {'name': 'VIEW_BADGES',
        'description': 'Provides the ability to view badges'},
        {'name': 'VIEW_POLICY_VIOLATION',
        'description': 'Provides the ability to view policy violations'},
        {'name': 'VIEW_PORTFOLIO', 'description': '277568'},
        {'name': 'VIEW_VULNERABILITY',
        'description': 'Provides the ability to view the vulnerabilities projects are affected by'},
        {'name': 'VULNERABILITY_ANALYSIS', 'description': '277570'},
        {'name': 'VULNERABILITY_MANAGEMENT',
        'description': 'Allows management of internally-defined vulnerabilities'}
        ]
}
]
