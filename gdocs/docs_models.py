"""
Google Docs Data Models for Structured Output

Dataclass models representing the structured data returned by Google Docs tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import TypeAdapter


@dataclass
class DocsSearchResultItem:
    """Summary of a Google Doc from search results."""

    doc_id: str
    name: str
    modified_time: Optional[str] = None
    web_link: Optional[str] = None


@dataclass
class DocsSearchResult:
    """Structured result from search_docs."""

    query: str
    total_found: int
    documents: list[DocsSearchResultItem]


@dataclass
class DocsContent:
    """Structured result from get_doc_content."""

    document_id: str
    name: str
    mime_type: str
    web_link: str
    content: str


@dataclass
class DocsListResult:
    """Structured result from list_docs_in_folder."""

    folder_id: str
    total_found: int
    documents: list[DocsSearchResultItem]


@dataclass
class DocsCreateResult:
    """Structured result from create_doc."""

    document_id: str
    title: str
    web_link: str


@dataclass
class DocsModifyTextResult:
    """Structured result from modify_doc_text."""

    document_id: str
    operations: list[str]
    text_length: Optional[int] = None
    web_link: str = ""


@dataclass
class DocsFindReplaceResult:
    """Structured result from find_and_replace_doc."""

    document_id: str
    find_text: str
    replace_text: str
    occurrences_changed: int
    web_link: str


@dataclass
class DocsInsertElementResult:
    """Structured result from insert_doc_elements."""

    document_id: str
    element_type: str
    description: str
    index: int
    web_link: str


@dataclass
class DocsInsertImageResult:
    """Structured result from insert_doc_image."""

    document_id: str
    source_description: str
    index: int
    size_info: str
    web_link: str


@dataclass
class DocsHeaderFooterResult:
    """Structured result from update_doc_headers_footers."""

    document_id: str
    section_type: str
    header_footer_type: str
    message: str
    web_link: str


@dataclass
class DocsBatchUpdateResult:
    """Structured result from batch_update_doc."""

    document_id: str
    operations_count: int
    replies_count: int
    message: str
    web_link: str


@dataclass
class DocsElementSummary:
    """Summary of a document element."""

    element_type: str
    start_index: int
    end_index: int
    rows: Optional[int] = None
    columns: Optional[int] = None
    cell_count: Optional[int] = None
    text_preview: Optional[str] = None


@dataclass
class DocsTablePosition:
    """Table position information."""

    start: int
    end: int


@dataclass
class DocsTableDimensions:
    """Table dimensions."""

    rows: int
    columns: int


@dataclass
class DocsTableSummary:
    """Summary of a table in the document."""

    index: int
    position: DocsTablePosition
    dimensions: DocsTableDimensions
    preview: list[list[str]] = field(default_factory=list)


@dataclass
class DocsStructureStatistics:
    """Document structure statistics."""

    elements: int
    tables: int
    paragraphs: int
    has_headers: bool
    has_footers: bool


@dataclass
class DocsStructureResult:
    """Structured result from inspect_doc_structure."""

    document_id: str
    title: Optional[str] = None
    total_length: Optional[int] = None
    total_elements: Optional[int] = None
    statistics: Optional[DocsStructureStatistics] = None
    elements: list[DocsElementSummary] = field(default_factory=list)
    tables: list[DocsTableSummary] = field(default_factory=list)
    table_details: list[dict[str, Any]] = field(default_factory=list)
    web_link: str = ""


@dataclass
class DocsCreateTableResult:
    """Structured result from create_table_with_data."""

    document_id: str
    rows: int
    columns: int
    index: int
    message: str
    web_link: str
    success: bool


@dataclass
class DocsCellDebugInfo:
    """Debug information for a single table cell."""

    position: str
    range: str
    insertion_index: str
    current_content: str
    content_elements_count: int


@dataclass
class DocsTableDebugResult:
    """Structured result from debug_table_structure."""

    document_id: str
    table_index: int
    dimensions: str
    table_range: str
    cells: list[list[DocsCellDebugInfo]]
    web_link: str


@dataclass
class DocsExportPdfResult:
    """Structured result from export_doc_to_pdf."""

    original_document_id: str
    original_name: str
    pdf_file_id: str
    pdf_filename: str
    pdf_size_bytes: int
    folder_id: Optional[str] = None
    pdf_web_link: str = ""
    original_web_link: str = ""


@dataclass
class DocsParagraphStyleResult:
    """Structured result from update_paragraph_style."""

    document_id: str
    start_index: int
    end_index: int
    applied_styles: list[str]
    web_link: str


def _generate_schema(cls: type) -> dict[str, Any]:
    """Generate JSON schema for a dataclass."""
    return TypeAdapter(cls).json_schema()


# Pre-generated JSON schemas for use in @server.tool() decorators
DOCS_SEARCH_RESULT_SCHEMA = _generate_schema(DocsSearchResult)
DOCS_CONTENT_SCHEMA = _generate_schema(DocsContent)
DOCS_LIST_RESULT_SCHEMA = _generate_schema(DocsListResult)
DOCS_CREATE_RESULT_SCHEMA = _generate_schema(DocsCreateResult)
DOCS_MODIFY_TEXT_RESULT_SCHEMA = _generate_schema(DocsModifyTextResult)
DOCS_FIND_REPLACE_RESULT_SCHEMA = _generate_schema(DocsFindReplaceResult)
DOCS_INSERT_ELEMENT_RESULT_SCHEMA = _generate_schema(DocsInsertElementResult)
DOCS_INSERT_IMAGE_RESULT_SCHEMA = _generate_schema(DocsInsertImageResult)
DOCS_HEADER_FOOTER_RESULT_SCHEMA = _generate_schema(DocsHeaderFooterResult)
DOCS_BATCH_UPDATE_RESULT_SCHEMA = _generate_schema(DocsBatchUpdateResult)
DOCS_STRUCTURE_RESULT_SCHEMA = _generate_schema(DocsStructureResult)
DOCS_CREATE_TABLE_RESULT_SCHEMA = _generate_schema(DocsCreateTableResult)
DOCS_TABLE_DEBUG_RESULT_SCHEMA = _generate_schema(DocsTableDebugResult)
DOCS_EXPORT_PDF_RESULT_SCHEMA = _generate_schema(DocsExportPdfResult)
DOCS_PARAGRAPH_STYLE_RESULT_SCHEMA = _generate_schema(DocsParagraphStyleResult)
