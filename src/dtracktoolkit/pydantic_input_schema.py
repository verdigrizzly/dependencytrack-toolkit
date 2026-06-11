"""Pydantic validation models for Dependency-Track API response schemas."""
from typing import List, Optional, Dict, Union, Any, Annotated
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    StringConstraints,
    model_validator,
    UUID4,
)

# --- Constants ---
MAX_NAME_LENGTH = 300
MAX_DESCRIPTION_LENGTH = 300000
MAX_DEPENDENCY_LENGTH = 10000000

# --- Shared Constraints ---
# Regex patterns extracted strictly from the baseline schema
UUID_REGEX = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
API_KEY_REGEX = r"^[a-zA-Z0-9]{32}$"
MASKED_KEY_REGEX = r"^\*{28}[a-zA-Z0-9]{4}$"

# Annotated Types for Strict Validation
NameStr = Annotated[str, StringConstraints(max_length=MAX_NAME_LENGTH)]
DescStr = Annotated[str, StringConstraints(max_length=MAX_DESCRIPTION_LENGTH)]
DepStr = Annotated[str, StringConstraints(max_length=MAX_DEPENDENCY_LENGTH)]
UuidPatternStr = Annotated[str, StringConstraints(pattern=UUID_REGEX)]
ApiKeyStr = Annotated[str, StringConstraints(pattern=API_KEY_REGEX)]
MaskedKeyStr = Annotated[str, StringConstraints(pattern=MASKED_KEY_REGEX)]


# --- Base Model ---
class StrictModel(BaseModel):
    """Base model that forbids additional properties by default."""

    model_config = ConfigDict(extra="forbid")


# ==========================================
# 1. Project Schema
# ==========================================


class Contact(StrictModel):
    """Contact person with name, email, and phone."""

    name: Optional[NameStr] = None
    email: Optional[NameStr] = None
    phone: Optional[NameStr] = None


class ProjectManufacturer(StrictModel):
    """Manufacturer of a project, including contacts and URLs."""

    name: Optional[NameStr] = None
    urls: Optional[List[NameStr]] = None
    contacts: Optional[List[Contact]] = None


class ProjectSupplier(StrictModel):
    """Supplier of a project, including contacts and URLs."""

    name: Optional[NameStr] = None
    urls: Optional[List[NameStr]] = None
    contacts: Optional[List[Contact]] = None


class ProjectVersion(StrictModel):
    """Lightweight reference to a specific project version."""

    # Schema specifies format: uuid (standard UUID4), not the regex pattern used elsewhere
    uuid: Optional[UUID4] = None
    version: Optional[str] = None
    active: Optional[bool] = None


class ExternalReference(StrictModel):
    """External reference with type, URL, and optional comment."""

    type: Optional[NameStr] = None
    url: Optional[NameStr] = None
    comment: Optional[NameStr] = None


class Property(StrictModel):
    """Key-value property attached to a project."""

    groupName: Optional[NameStr] = None
    propertyName: Optional[NameStr] = None
    propertyValue: Optional[NameStr] = None
    # Schema: ["boolean", "string"]
    propertyType: Optional[Union[bool, NameStr]] = None
    description: Optional[NameStr] = None


class Project(StrictModel):
    """Full Dependency-Track project record."""

    # Base Properties
    author: Optional[NameStr] = None
    authors: Optional[List[Any]] = Field(default=None, max_length=30)
    publisher: Optional[NameStr] = None
    isLatest: Optional[bool] = None
    purl: Optional[NameStr] = None

    # Nested Objects
    manufacturer: Optional[ProjectManufacturer] = None
    supplier: Optional[ProjectSupplier] = None

    group: Optional[NameStr] = None
    name: Optional[NameStr] = None
    description: Optional[DescStr] = None
    version: Optional[NameStr] = None
    classifier: Optional[NameStr] = None
    cpe: Optional[NameStr] = None
    swidTagId: Optional[NameStr] = None

    # Dependencies
    directDependencies: Optional[DepStr] = None

    # REQUIRED: UUID with Regex
    uuid: UuidPatternStr

    versions: Optional[List[ProjectVersion]] = None
    parent: Optional[Dict[str, Any]] = None  # Schema: ["object", "null"]
    children: Optional[List[Dict[str, Any]]] = None

    # Tags: items are objects with additionalProps string
    tags: Optional[List[Dict[str, str]]] = Field(default=None, max_length=30)

    lastBomImport: Optional[int] = None
    lastBomImportFormat: Optional[NameStr] = None
    lastInheritedRiskScore: Optional[float] = None
    active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, max_length=30)
    collectionLogic: Optional[NameStr] = None
    lastVulnerabilityAnalysis: Optional[int] = None

    # Metrics: additionalProperties oneOf number, string, boolean
    metrics: Optional[Dict[str, Union[float, str, bool]]] = Field(
        default=None, max_length=50
    )

    externalReferences: Optional[List[ExternalReference]] = None
    properties: Optional[List[Property]] = None


# ==========================================
# 2. Search Project Schema
# ==========================================


class SearchProjectItem(StrictModel):
    """Single project item returned in a search result."""

    # REQUIRED fields based on schema
    name: NameStr
    uuid: NameStr

    description: Optional[NameStr] = None
    version: Optional[NameStr] = None

    # Allows additional properties, but schema restricts them to String + MaxLength.
    # Pydantic's extra='allow' is too loose, so we validate manually.
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_extras(self):
        """Validate extra properties against schema string and maxProperties constraints."""
        # iterate over fields that are not in the model fields
        for key, value in self.model_extra.items() if self.model_extra else {}:
            if not isinstance(value, str):
                raise ValueError(f"Extra property '{key}' must be a string")
            if len(value) > MAX_NAME_LENGTH:
                raise ValueError(
                    f"Extra property '{key}' exceeds max length {MAX_NAME_LENGTH}"
                )

        # Schema also specifies maxProperties: 16 for the whole object
        total_props = len(
            self.model_fields_set
        )  # This counts set fields (including extras in v2)
        if total_props > 16:
            raise ValueError("Object exceeds maxProperties: 16")
        return self


class SearchResults(StrictModel):
    """Container for a list of search project items."""

    project: List[SearchProjectItem]


class SearchProject(StrictModel):
    """Top-level wrapper for a project search response."""

    results: SearchResults


# ==========================================
# 3. Finding Schema
# ==========================================


class Vulnerability(StrictModel):
    """Vulnerability record including CVSS scores, severity, and aliases."""

    uuid: Optional[UuidPatternStr] = None
    source: Optional[NameStr] = None
    vulnId: Optional[NameStr] = None
    published: Optional[int] = None

    cvssV2BaseScore: Optional[float] = None
    cvssV2Vector: Optional[NameStr] = None
    cvssV3BaseScore: Optional[float] = None
    cvssV3Vector: Optional[NameStr] = None
    cvssV4Score: Optional[float] = None
    cvssV4Vector: Optional[NameStr] = None

    severity: Optional[NameStr] = None
    severityRank: Optional[float] = None
    title: Optional[NameStr] = None
    subtitle: Optional[NameStr] = None
    epssScore: Optional[float] = None
    epssPercentile: Optional[float] = None
    cweId: Optional[float] = None
    cweName: Optional[NameStr] = None
    cwes: Optional[List[Dict[str, Any]]] = None

    # Aliases: array of objects, additionalProperties string, maxProperties 16
    aliases: Optional[List[Dict[str, NameStr]]] = None

    description: Optional[DescStr] = None
    recommendation: Optional[DescStr] = None
    references: Optional[DescStr] = None


class FindingAnalysis(StrictModel):
    """Analysis state and suppression flag for a finding."""

    isSuppressed: Optional[bool] = None
    state: Optional[NameStr] = None


class FindingAttribution(StrictModel):
    """Attribution metadata for when and how a finding was identified."""

    analyzerIdentity: Optional[NameStr] = None
    attributedOn: Optional[int] = None
    alternateIdentifier: Optional[NameStr] = None
    referenceUrl: Optional[NameStr] = None


class Finding(StrictModel):
    """Single finding linking a component to a vulnerability."""

    # Component: object, additionalProperties string, maxProperties 16.
    # Since there are no named properties, we use a Dict with Field constraints.
    component: Dict[str, NameStr] = Field(..., max_length=16)

    vulnerability: Optional[Vulnerability] = None
    analysis: Optional[FindingAnalysis] = None
    attribution: Optional[FindingAttribution] = None
    matrix: Optional[NameStr] = None


# ==========================================
# 4. Notification Schema
# ==========================================


class NotificationProject(StrictModel):
    """Project reference within a notification rule."""

    # REQUIRED
    uuid: UuidPatternStr

    author: Optional[NameStr] = None
    authors: Optional[List[Any]] = Field(default=None, max_length=30)
    publisher: Optional[NameStr] = None
    group: Optional[NameStr] = None
    name: Optional[NameStr] = None
    isLatest: Optional[bool] = None
    purl: Optional[NameStr] = None

    # Manufacturer: Schema defines "items" inside "type": "object".
    # Interpreted as a Dictionary where values match the items schema.
    manufacturer: Optional[Dict[str, Optional[Union[str, Dict[str, Any]]]]] = Field(
        default=None, max_length=10
    )

    description: Optional[DescStr] = None
    version: Optional[NameStr] = None
    classifier: Optional[NameStr] = None
    cpe: Optional[NameStr] = None
    swidTagId: Optional[NameStr] = None
    directDependencies: Optional[DepStr] = None
    tags: Optional[List[Dict[str, str]]] = Field(default=None, max_length=30)
    lastBomImport: Optional[int] = None
    lastBomImportFormat: Optional[NameStr] = None
    lastInheritedRiskScore: Optional[float] = None
    active: Optional[bool] = None

    # Metrics: values are numbers
    metrics: Optional[Dict[str, float]] = Field(default=None, max_length=30)

    externalReferences: Optional[List[ExternalReference]] = None
    properties: Optional[List[Property]] = None


class NotificationPublisher(StrictModel):
    """Publisher configuration for a notification rule."""

    name: Optional[NameStr] = None
    description: Optional[DescStr] = None
    publisherClass: Optional[NameStr] = None
    template: Optional[NameStr] = None
    templateMimeType: Optional[NameStr] = None
    defaultPublisher: Optional[bool] = None
    uuid: Optional[NameStr] = None
    publisherConfig: Optional[NameStr] = None


class Notification(StrictModel):
    """Dependency-Track notification rule with scope, level, and target projects."""

    name: Optional[NameStr] = None
    enabled: Optional[bool] = None
    notifyChildren: Optional[bool] = None
    scope: Optional[NameStr] = None
    notificationLevel: Optional[NameStr] = None
    projects: Optional[List[NotificationProject]] = None

    # Teams: object, array or null.
    # Additional props: string, null, number, boolean.
    teams: Optional[Union[Dict[str, Union[str, float, bool, None]], List[Any]]] = None

    notifyOn: Optional[List[NameStr]] = None
    message: Optional[NameStr] = None
    publisher: Optional[NotificationPublisher] = None


# ==========================================
# 5. Tokens Schema
# ==========================================


class ApiKey(StrictModel):
    """API key with optional masked representation."""

    key: Optional[ApiKeyStr] = None
    maskedKey: Optional[MaskedKeyStr] = None


class Permission(StrictModel):
    """Named permission assignable to a team."""

    name: Optional[NameStr] = None
    description: Optional[DescStr] = None


class LdapUser(StrictModel):
    """LDAP-authenticated user entry."""

    username: Optional[NameStr] = None
    dn: Optional[DescStr] = None
    email: Optional[NameStr] = None


class ManagedUser(StrictModel):
    """Internally managed user account."""

    username: Optional[NameStr] = None

    # Schema uses python `int` type object
    lastPasswordChange: Optional[int] = None

    fullname: Optional[NameStr] = None
    email: Optional[NameStr] = None

    # Schema uses string literal "boolean" to denote bool type
    suspended: Optional[bool] = None
    forcePasswordChange: Optional[bool] = None
    nonExpiryPassword: Optional[bool] = None


class OidcUser(StrictModel):
    """OIDC-authenticated user entry."""

    username: Optional[NameStr] = None
    subjectIdentifier: Optional[str] = (
        None  # schema just says "string" (no length limit)
    )
    email: Optional[NameStr] = None


class MappedLdapGroup(StrictModel):
    """LDAP group mapped to a Dependency-Track team."""

    dn: Optional[DescStr] = None
    uuid: Optional[UuidPatternStr] = None


class OidcGroupItem(StrictModel):
    """Single OIDC group identifier."""

    uuid: Optional[UuidPatternStr] = None
    name: Optional[NameStr] = None


class MappedOidcGroup(StrictModel):
    """OIDC group mapped to a Dependency-Track team."""

    group: Optional[List[OidcGroupItem]] = None
    uuid: Optional[UuidPatternStr] = None


class Tokens(StrictModel):
    """Team token response including API keys, permissions, and user assignments."""

    uuid: Optional[UuidPatternStr] = None
    name: Optional[NameStr] = None
    apiKeys: Optional[List[ApiKey]] = None
    permissions: Optional[List[Permission]] = None
    ldapUsers: Optional[List[LdapUser]] = None
    managedUsers: Optional[List[ManagedUser]] = None
    oidcUsers: Optional[List[OidcUser]] = None
    mappedLdapGroups: Optional[List[MappedLdapGroup]] = None
    mappedOidcGroups: Optional[List[MappedOidcGroup]] = None


# ==========================================
# 6. Tokens Self Schema
# ==========================================


class TokensSelf(StrictModel):
    """Reduced token response for the currently authenticated team."""

    uuid: Optional[UuidPatternStr] = None
    name: Optional[NameStr] = None
    permissions: Optional[List[Permission]] = None
