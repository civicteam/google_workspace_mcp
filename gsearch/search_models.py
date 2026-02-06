"""
Google Custom Search Data Models for Structured Output

Dataclass models representing the structured data returned by Google Search tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import TypeAdapter


@dataclass
class SearchResultItem:
    """A single search result item."""

    position: int
    title: str
    link: str
    snippet: str
    content_type: Optional[str] = None
    published_date: Optional[str] = None


@dataclass
class SearchResult:
    """Structured result from search_custom."""

    query: str
    search_engine_id: str
    total_results: str
    search_time_seconds: float
    results_returned: int
    start_index: int
    items: list[SearchResultItem] = field(default_factory=list)
    next_page_start: Optional[int] = None


@dataclass
class SearchEngineFacet:
    """A search engine refinement/facet."""

    label: str
    anchor: str


@dataclass
class SearchEngineInfo:
    """Structured result from get_search_engine_info."""

    search_engine_id: str
    title: str
    total_indexed_results: Optional[str] = None
    facets: list[SearchEngineFacet] = field(default_factory=list)


def _generate_schema(cls: type) -> dict[str, Any]:
    """Generate JSON schema for a dataclass."""
    return TypeAdapter(cls).json_schema()


# Pre-generated JSON schemas for use in @server.tool() decorators
SEARCH_RESULT_SCHEMA = _generate_schema(SearchResult)
SEARCH_ENGINE_INFO_SCHEMA = _generate_schema(SearchEngineInfo)
