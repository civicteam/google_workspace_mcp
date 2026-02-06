"""
Google Forms Data Models for Structured Output

Dataclass models representing the structured data returned by Google Forms tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import TypeAdapter


@dataclass
class FormsCreateResult:
    """Structured result from create_form."""

    form_id: str
    title: str
    edit_url: str
    responder_url: str


@dataclass
class FormsQuestionSummary:
    """Summary of a form question/item."""

    index: int
    title: str
    required: bool


@dataclass
class FormsGetResult:
    """Structured result from get_form."""

    form_id: str
    title: str
    description: str
    document_title: str
    edit_url: str
    responder_url: str
    questions: list[FormsQuestionSummary]


@dataclass
class FormsPublishSettingsResult:
    """Structured result from set_publish_settings."""

    form_id: str
    publish_as_template: bool
    require_authentication: bool


@dataclass
class FormsAnswerDetail:
    """Detail of an answer to a form question."""

    question_id: str
    answer_text: str


@dataclass
class FormsResponseResult:
    """Structured result from get_form_response."""

    form_id: str
    response_id: str
    create_time: str
    last_submitted_time: str
    answers: list[FormsAnswerDetail]


@dataclass
class FormsResponseSummary:
    """Summary of a form response from list results."""

    response_id: str
    create_time: str
    last_submitted_time: str
    answer_count: int


@dataclass
class FormsListResponsesResult:
    """Structured result from list_form_responses."""

    form_id: str
    total_returned: int
    responses: list[FormsResponseSummary]
    next_page_token: Optional[str] = None


@dataclass
class FormsBatchUpdateReply:
    """Reply from a single batch update request."""

    request_index: int
    operation: str
    item_id: Optional[str] = None
    question_ids: list[str] = field(default_factory=list)


@dataclass
class FormsBatchUpdateResult:
    """Structured result from batch_update_form."""

    form_id: str
    edit_url: str
    requests_applied: int
    replies_received: int
    replies: list[FormsBatchUpdateReply]


def _generate_schema(cls: type) -> dict[str, Any]:
    """Generate JSON schema for a dataclass."""
    return TypeAdapter(cls).json_schema()


# Pre-generated JSON schemas for use in @server.tool() decorators
FORMS_CREATE_RESULT_SCHEMA = _generate_schema(FormsCreateResult)
FORMS_GET_RESULT_SCHEMA = _generate_schema(FormsGetResult)
FORMS_PUBLISH_SETTINGS_RESULT_SCHEMA = _generate_schema(FormsPublishSettingsResult)
FORMS_RESPONSE_RESULT_SCHEMA = _generate_schema(FormsResponseResult)
FORMS_LIST_RESPONSES_RESULT_SCHEMA = _generate_schema(FormsListResponsesResult)
FORMS_BATCH_UPDATE_RESULT_SCHEMA = _generate_schema(FormsBatchUpdateResult)
