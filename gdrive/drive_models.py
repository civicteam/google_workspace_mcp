"""
Google Drive Data Models for Structured Output

Dataclass models representing the structured data returned by Google Drive tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import TypeAdapter


@dataclass
class DriveFileItem:
    """Summary of a file or folder in Google Drive."""

    id: str
    name: str
    mime_type: str
    web_view_link: str
    modified_time: Optional[str] = None
    size: Optional[str] = None


@dataclass
class DriveSearchResult:
    """Structured result from search_drive_files."""

    query: str
    total_found: int
    files: list[DriveFileItem]


@dataclass
class DriveListResult:
    """Structured result from list_drive_items."""

    folder_id: str
    total_found: int
    items: list[DriveFileItem]


@dataclass
class DriveFileContent:
    """Structured result from get_drive_file_content."""

    file_id: str
    name: str
    mime_type: str
    web_view_link: str
    content: str


@dataclass
class DriveDownloadResult:
    """Structured result from get_drive_file_download_url."""

    file_id: str
    name: str
    size_bytes: int
    mime_type: str
    download_url: Optional[str] = None
    stateless_mode: bool = False


@dataclass
class DriveCreateResult:
    """Structured result from create_drive_file."""

    file_id: str
    name: str
    folder_id: str
    web_view_link: str


@dataclass
class DriveImportResult:
    """Structured result from import_to_google_doc."""

    document_id: str
    name: str
    source_format: str
    folder_id: str
    web_view_link: str


@dataclass
class DrivePermission:
    """Represents a Google Drive permission."""

    id: str
    type: str
    role: str
    email_address: Optional[str] = None
    domain: Optional[str] = None
    expiration_time: Optional[str] = None


@dataclass
class DrivePermissionsResult:
    """Structured result from get_drive_file_permissions."""

    file_id: str
    name: str
    mime_type: str
    size: Optional[str] = None
    modified_time: Optional[str] = None
    is_shared: bool = False
    web_view_link: Optional[str] = None
    web_content_link: Optional[str] = None
    has_public_link: bool = False
    permissions: list[DrivePermission] = field(default_factory=list)


@dataclass
class DrivePublicAccessResult:
    """Structured result from check_drive_file_public_access."""

    file_id: str
    name: str
    mime_type: str
    is_shared: bool
    has_public_link: bool
    drive_image_url: Optional[str] = None


@dataclass
class DriveUpdateResult:
    """Structured result from update_drive_file."""

    file_id: str
    name: str
    web_view_link: str
    changes_applied: list[str] = field(default_factory=list)


@dataclass
class DriveShareableLinkResult:
    """Structured result from get_drive_shareable_link."""

    file_id: str
    name: str
    mime_type: str
    is_shared: bool
    web_view_link: Optional[str] = None
    web_content_link: Optional[str] = None
    permissions: list[DrivePermission] = field(default_factory=list)


@dataclass
class DriveShareResult:
    """Structured result from share_drive_file."""

    file_id: str
    file_name: str
    permission: DrivePermission
    web_view_link: str


@dataclass
class DriveBatchShareResultItem:
    """Result for a single recipient in batch share."""

    identifier: str
    success: bool
    permission: Optional[DrivePermission] = None
    error: Optional[str] = None


@dataclass
class DriveBatchShareResult:
    """Structured result from batch_share_drive_file."""

    file_id: str
    file_name: str
    success_count: int
    failure_count: int
    results: list[DriveBatchShareResultItem]
    web_view_link: str


@dataclass
class DrivePermissionUpdateResult:
    """Structured result from update_drive_permission."""

    file_id: str
    file_name: str
    permission: DrivePermission


@dataclass
class DrivePermissionRemoveResult:
    """Structured result from remove_drive_permission."""

    file_id: str
    file_name: str
    permission_id: str


@dataclass
class DriveCopyResult:
    """Structured result from copy_drive_file."""

    original_file_id: str
    original_name: str
    new_file_id: str
    new_name: str
    mime_type: str
    parent_folder_id: str
    web_view_link: str


@dataclass
class DriveOwnershipTransferResult:
    """Structured result from transfer_drive_ownership."""

    file_id: str
    file_name: str
    new_owner_email: str
    previous_owner_emails: list[str]
    moved_to_new_owners_root: bool = False


def _generate_schema(cls: type) -> dict[str, Any]:
    """Generate JSON schema for a dataclass."""
    return TypeAdapter(cls).json_schema()


# Pre-generated JSON schemas for use in @server.tool() decorators
DRIVE_SEARCH_RESULT_SCHEMA = _generate_schema(DriveSearchResult)
DRIVE_LIST_RESULT_SCHEMA = _generate_schema(DriveListResult)
DRIVE_FILE_CONTENT_SCHEMA = _generate_schema(DriveFileContent)
DRIVE_DOWNLOAD_RESULT_SCHEMA = _generate_schema(DriveDownloadResult)
DRIVE_CREATE_RESULT_SCHEMA = _generate_schema(DriveCreateResult)
DRIVE_IMPORT_RESULT_SCHEMA = _generate_schema(DriveImportResult)
DRIVE_PERMISSIONS_RESULT_SCHEMA = _generate_schema(DrivePermissionsResult)
DRIVE_PUBLIC_ACCESS_RESULT_SCHEMA = _generate_schema(DrivePublicAccessResult)
DRIVE_UPDATE_RESULT_SCHEMA = _generate_schema(DriveUpdateResult)
DRIVE_SHAREABLE_LINK_RESULT_SCHEMA = _generate_schema(DriveShareableLinkResult)
DRIVE_SHARE_RESULT_SCHEMA = _generate_schema(DriveShareResult)
DRIVE_BATCH_SHARE_RESULT_SCHEMA = _generate_schema(DriveBatchShareResult)
DRIVE_PERMISSION_UPDATE_RESULT_SCHEMA = _generate_schema(DrivePermissionUpdateResult)
DRIVE_PERMISSION_REMOVE_RESULT_SCHEMA = _generate_schema(DrivePermissionRemoveResult)
DRIVE_COPY_RESULT_SCHEMA = _generate_schema(DriveCopyResult)
DRIVE_OWNERSHIP_TRANSFER_RESULT_SCHEMA = _generate_schema(DriveOwnershipTransferResult)
