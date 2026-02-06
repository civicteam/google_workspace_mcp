"""
Google Calendar Data Models for Structured Output

Dataclass models representing the structured data returned by Google Calendar tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import TypeAdapter


@dataclass
class CalendarInfo:
    """Information about a single calendar."""

    calendar_id: str
    summary: str
    is_primary: bool


@dataclass
class CalendarListResult:
    """Structured result from list_calendars."""

    total_count: int
    calendars: list[CalendarInfo]


@dataclass
class EventAttendee:
    """Information about an event attendee."""

    email: str
    response_status: str
    is_organizer: bool = False
    is_optional: bool = False


@dataclass
class EventAttachment:
    """Information about an event attachment."""

    title: str
    file_url: str
    file_id: str
    mime_type: str


@dataclass
class CalendarEvent:
    """Information about a single calendar event."""

    event_id: str
    summary: str
    start: str
    end: str
    html_link: str
    description: Optional[str] = None
    location: Optional[str] = None
    color_id: Optional[str] = None
    attendees: list[EventAttendee] = field(default_factory=list)
    attachments: list[EventAttachment] = field(default_factory=list)


@dataclass
class GetEventsResult:
    """Structured result from get_events."""

    calendar_id: str
    total_count: int
    events: list[CalendarEvent]


@dataclass
class CreateEventResult:
    """Structured result from create_event."""

    event_id: str
    summary: str
    html_link: str
    google_meet_link: Optional[str] = None


@dataclass
class ModifyEventResult:
    """Structured result from modify_event."""

    event_id: str
    summary: str
    html_link: str
    google_meet_link: Optional[str] = None
    google_meet_removed: bool = False


@dataclass
class DeleteEventResult:
    """Structured result from delete_event."""

    event_id: str
    calendar_id: str


@dataclass
class BusyPeriod:
    """A busy time period."""

    start: str
    end: str


@dataclass
class CalendarFreeBusy:
    """Free/busy information for a single calendar."""

    calendar_id: str
    busy_periods: list[BusyPeriod]
    errors: list[str] = field(default_factory=list)


@dataclass
class FreeBusyResult:
    """Structured result from query_freebusy."""

    user_email: str
    time_min: str
    time_max: str
    calendars: list[CalendarFreeBusy]


def _generate_schema(cls: type) -> dict[str, Any]:
    """Generate JSON schema for a dataclass."""
    return TypeAdapter(cls).json_schema()


# Pre-generated JSON schemas for use in @server.tool() decorators
CALENDAR_LIST_RESULT_SCHEMA = _generate_schema(CalendarListResult)
GET_EVENTS_RESULT_SCHEMA = _generate_schema(GetEventsResult)
CREATE_EVENT_RESULT_SCHEMA = _generate_schema(CreateEventResult)
MODIFY_EVENT_RESULT_SCHEMA = _generate_schema(ModifyEventResult)
DELETE_EVENT_RESULT_SCHEMA = _generate_schema(DeleteEventResult)
FREEBUSY_RESULT_SCHEMA = _generate_schema(FreeBusyResult)
