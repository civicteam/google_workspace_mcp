"""
Google Contacts Data Models for Structured Output

Dataclass models representing the structured data returned by Google Contacts tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from core.structured_output import generate_schema


@dataclass
class ContactOrganization:
    """Organization information for a contact."""

    name: Optional[str] = None
    title: Optional[str] = None


@dataclass
class ContactSummary:
    """Summary of a contact from list/search results."""

    contact_id: str
    name: Optional[str] = None
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    organization: Optional[ContactOrganization] = None


@dataclass
class ContactDetails:
    """Detailed contact information."""

    contact_id: str
    name: Optional[str] = None
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    organization: Optional[ContactOrganization] = None
    address: Optional[str] = None
    birthday: Optional[str] = None
    urls: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    sources: list[str] = field(default_factory=list)


@dataclass
class ListContactsResult:
    """Structured result from list_contacts."""


    total_count: int
    returned_count: int
    contacts: list[ContactSummary]
    next_page_token: Optional[str] = None


@dataclass
class GetContactResult:
    """Structured result from get_contact."""


    contact: ContactDetails


@dataclass
class SearchContactsResult:
    """Structured result from search_contacts."""


    query: str
    result_count: int
    contacts: list[ContactSummary]


@dataclass
class CreateContactResult:
    """Structured result from create_contact."""


    contact: ContactDetails


@dataclass
class UpdateContactResult:
    """Structured result from update_contact."""


    contact: ContactDetails


@dataclass
class DeleteContactResult:
    """Structured result from delete_contact."""


    contact_id: str
    deleted: bool


@dataclass
class ContactGroupSummary:
    """Summary of a contact group."""

    group_id: str
    name: str
    group_type: str
    member_count: int


@dataclass
class ListContactGroupsResult:
    """Structured result from list_contact_groups."""


    group_count: int
    groups: list[ContactGroupSummary]
    next_page_token: Optional[str] = None


@dataclass
class ContactGroupDetails:
    """Detailed contact group information."""

    group_id: str
    name: str
    group_type: str
    member_count: int
    member_ids: list[str] = field(default_factory=list)


@dataclass
class GetContactGroupResult:
    """Structured result from get_contact_group."""


    group: ContactGroupDetails


@dataclass
class BatchCreateContactsResult:
    """Structured result from batch_create_contacts."""


    created_count: int
    contacts: list[ContactSummary]


@dataclass
class BatchUpdateContactsResult:
    """Structured result from batch_update_contacts."""


    updated_count: int
    contacts: list[ContactSummary]


@dataclass
class BatchDeleteContactsResult:
    """Structured result from batch_delete_contacts."""


    deleted_count: int
    deleted: bool


@dataclass
class CreateContactGroupResult:
    """Structured result from create_contact_group."""


    group: ContactGroupSummary


@dataclass
class UpdateContactGroupResult:
    """Structured result from update_contact_group."""


    group_id: str
    name: str


@dataclass
class DeleteContactGroupResult:
    """Structured result from delete_contact_group."""


    group_id: str
    deleted: bool
    contacts_deleted: bool


@dataclass
class ModifyContactGroupMembersResult:
    """Structured result from modify_contact_group_members."""


    group_id: str
    added_count: int
    removed_count: int
    not_found_ids: list[str] = field(default_factory=list)
    cannot_remove_ids: list[str] = field(default_factory=list)


# Pre-generated JSON schemas for use in @server.tool() decorators
LIST_CONTACTS_RESULT_SCHEMA = generate_schema(ListContactsResult)
GET_CONTACT_RESULT_SCHEMA = generate_schema(GetContactResult)
SEARCH_CONTACTS_RESULT_SCHEMA = generate_schema(SearchContactsResult)
CREATE_CONTACT_RESULT_SCHEMA = generate_schema(CreateContactResult)
UPDATE_CONTACT_RESULT_SCHEMA = generate_schema(UpdateContactResult)
DELETE_CONTACT_RESULT_SCHEMA = generate_schema(DeleteContactResult)
LIST_CONTACT_GROUPS_RESULT_SCHEMA = generate_schema(ListContactGroupsResult)
GET_CONTACT_GROUP_RESULT_SCHEMA = generate_schema(GetContactGroupResult)
BATCH_CREATE_CONTACTS_RESULT_SCHEMA = generate_schema(BatchCreateContactsResult)
BATCH_UPDATE_CONTACTS_RESULT_SCHEMA = generate_schema(BatchUpdateContactsResult)
BATCH_DELETE_CONTACTS_RESULT_SCHEMA = generate_schema(BatchDeleteContactsResult)
CREATE_CONTACT_GROUP_RESULT_SCHEMA = generate_schema(CreateContactGroupResult)
UPDATE_CONTACT_GROUP_RESULT_SCHEMA = generate_schema(UpdateContactGroupResult)
DELETE_CONTACT_GROUP_RESULT_SCHEMA = generate_schema(DeleteContactGroupResult)
MODIFY_CONTACT_GROUP_MEMBERS_RESULT_SCHEMA = generate_schema(
    ModifyContactGroupMembersResult
)
