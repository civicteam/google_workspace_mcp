"""
Gmail Data Models for Structured Output

Dataclass models representing the structured data returned by Gmail tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import TypeAdapter


@dataclass
class GmailMessageSummary:
    """Summary of a Gmail message from search results."""

    message_id: str
    thread_id: str
    web_link: str
    thread_link: str


@dataclass
class GmailSearchResult:
    """Structured result from search_gmail_messages."""

    query: str
    total_found: int
    messages: list[GmailMessageSummary]
    next_page_token: Optional[str] = None


@dataclass
class GmailAttachment:
    """Metadata for an email attachment."""

    filename: str
    mime_type: str
    size_bytes: int
    attachment_id: str


@dataclass
class GmailMessageContent:
    """Structured result from get_gmail_message_content."""

    message_id: str
    subject: str
    sender: str
    date: str
    to: Optional[str] = None
    cc: Optional[str] = None
    rfc822_message_id: Optional[str] = None
    body: str = ""
    attachments: list[GmailAttachment] = field(default_factory=list)


@dataclass
class GmailSendResult:
    """Structured result from send_gmail_message."""

    message_id: str
    thread_id: Optional[str] = None
    attachment_count: int = 0


def _generate_schema(cls: type) -> dict[str, Any]:
    """Generate JSON schema for a dataclass."""
    return TypeAdapter(cls).json_schema()


# Pre-generated JSON schemas for use in @server.tool() decorators
GMAIL_SEARCH_RESULT_SCHEMA = _generate_schema(GmailSearchResult)
GMAIL_MESSAGE_CONTENT_SCHEMA = _generate_schema(GmailMessageContent)
GMAIL_SEND_RESULT_SCHEMA = _generate_schema(GmailSendResult)
