"""
Google Slides Data Models for Structured Output

Dataclass models representing the structured data returned by Google Slides tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import TypeAdapter


@dataclass
class SlidesCreatePresentationResult:
    """Structured result from create_presentation."""

    presentation_id: str
    title: str
    url: str
    slide_count: int


@dataclass
class SlideInfo:
    """Information about a single slide in a presentation."""

    slide_number: int
    slide_id: str
    element_count: int
    text_content: str


@dataclass
class SlidesGetPresentationResult:
    """Structured result from get_presentation."""

    presentation_id: str
    title: str
    url: str
    total_slides: int
    page_width: Optional[float] = None
    page_height: Optional[float] = None
    page_unit: Optional[str] = None
    slides: list[SlideInfo] = field(default_factory=list)


@dataclass
class BatchUpdateReply:
    """Result of a single request in a batch update."""

    request_number: int
    operation_type: str
    object_id: Optional[str] = None


@dataclass
class SlidesBatchUpdateResult:
    """Structured result from batch_update_presentation."""

    presentation_id: str
    url: str
    requests_applied: int
    replies_received: int
    replies: list[BatchUpdateReply] = field(default_factory=list)


@dataclass
class PageElementInfo:
    """Information about a page element."""

    element_id: str
    element_type: str
    details: Optional[str] = None


@dataclass
class SlidesGetPageResult:
    """Structured result from get_page."""

    presentation_id: str
    page_id: str
    page_type: str
    total_elements: int
    elements: list[PageElementInfo] = field(default_factory=list)


@dataclass
class SlidesGetPageThumbnailResult:
    """Structured result from get_page_thumbnail."""

    presentation_id: str
    page_id: str
    thumbnail_size: str
    thumbnail_url: str


def _generate_schema(cls: type) -> dict[str, Any]:
    """Generate JSON schema for a dataclass."""
    return TypeAdapter(cls).json_schema()


# Pre-generated JSON schemas for use in @server.tool() decorators
SLIDES_CREATE_PRESENTATION_SCHEMA = _generate_schema(SlidesCreatePresentationResult)
SLIDES_GET_PRESENTATION_SCHEMA = _generate_schema(SlidesGetPresentationResult)
SLIDES_BATCH_UPDATE_SCHEMA = _generate_schema(SlidesBatchUpdateResult)
SLIDES_GET_PAGE_SCHEMA = _generate_schema(SlidesGetPageResult)
SLIDES_GET_PAGE_THUMBNAIL_SCHEMA = _generate_schema(SlidesGetPageThumbnailResult)
