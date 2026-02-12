"""
Google Chat Data Models for Structured Output

Dataclass models representing the structured data returned by Google Chat tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass

from core.structured_output import generate_schema


@dataclass
class ChatSpace:
    """Metadata for a Google Chat space."""

    space_id: str
    display_name: str
    space_type: str


@dataclass
class ChatListSpacesResult:
    """Structured result from list_spaces."""

    space_type_filter: str
    total_found: int
    spaces: list[ChatSpace]


@dataclass
class ChatMessage:
    """Metadata for a Google Chat message."""

    message_id: str
    sender: str
    create_time: str
    text: str


@dataclass
class ChatGetMessagesResult:
    """Structured result from get_messages."""

    space_id: str
    space_name: str
    total_messages: int
    messages: list[ChatMessage]


@dataclass
class ChatSendMessageResult:
    """Structured result from send_message."""

    space_id: str
    message_id: str
    create_time: str


@dataclass
class ChatSearchMessage:
    """Message metadata from search results."""

    sender: str
    create_time: str
    text: str
    space_name: str


@dataclass
class ChatSearchMessagesResult:
    """Structured result from search_messages."""

    query: str
    context: str
    total_found: int
    messages: list[ChatSearchMessage]


# Pre-generated JSON schemas for use in @server.tool() decorators
CHAT_LIST_SPACES_RESULT_SCHEMA = generate_schema(ChatListSpacesResult)
CHAT_GET_MESSAGES_RESULT_SCHEMA = generate_schema(ChatGetMessagesResult)
CHAT_SEND_MESSAGE_RESULT_SCHEMA = generate_schema(ChatSendMessageResult)
CHAT_SEARCH_MESSAGES_RESULT_SCHEMA = generate_schema(ChatSearchMessagesResult)
