"""
Google Sheets Data Models for Structured Output

Dataclass models representing the structured data returned by Google Sheets tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass
from typing import Any

from pydantic import TypeAdapter


@dataclass
class SpreadsheetItem:
    """Summary of a spreadsheet from list results."""

    spreadsheet_id: str
    name: str
    modified_time: str
    web_link: str


@dataclass
class ListSpreadsheetsResult:
    """Structured result from list_spreadsheets."""

    total_found: int
    spreadsheets: list[SpreadsheetItem]


@dataclass
class SheetInfo:
    """Information about a single sheet within a spreadsheet."""

    sheet_id: int
    title: str
    row_count: int
    column_count: int
    conditional_format_count: int


@dataclass
class SpreadsheetInfoResult:
    """Structured result from get_spreadsheet_info."""

    spreadsheet_id: str
    title: str
    locale: str
    sheets: list[SheetInfo]


@dataclass
class ReadSheetValuesResult:
    """Structured result from read_sheet_values."""

    spreadsheet_id: str
    range_name: str
    row_count: int
    values: list[list[str]]
    has_errors: bool = False


@dataclass
class ModifySheetValuesResult:
    """Structured result from modify_sheet_values."""

    spreadsheet_id: str
    range_name: str
    operation: str
    updated_cells: int = 0
    updated_rows: int = 0
    updated_columns: int = 0
    has_errors: bool = False


@dataclass
class FormatSheetRangeResult:
    """Structured result from format_sheet_range."""

    spreadsheet_id: str
    range_name: str
    applied_formats: list[str]


@dataclass
class ConditionalFormatResult:
    """Structured result from add/update/delete conditional formatting."""

    spreadsheet_id: str
    sheet_name: str
    operation: str
    rule_index: int
    rule_type: str


@dataclass
class CreateSpreadsheetResult:
    """Structured result from create_spreadsheet."""

    spreadsheet_id: str
    title: str
    spreadsheet_url: str
    locale: str


@dataclass
class CreateSheetResult:
    """Structured result from create_sheet."""

    spreadsheet_id: str
    sheet_id: int
    sheet_name: str


def _generate_schema(cls: type) -> dict[str, Any]:
    """Generate JSON schema for a dataclass."""
    return TypeAdapter(cls).json_schema()


# Pre-generated JSON schemas for use in @server.tool() decorators
LIST_SPREADSHEETS_SCHEMA = _generate_schema(ListSpreadsheetsResult)
SPREADSHEET_INFO_SCHEMA = _generate_schema(SpreadsheetInfoResult)
READ_SHEET_VALUES_SCHEMA = _generate_schema(ReadSheetValuesResult)
MODIFY_SHEET_VALUES_SCHEMA = _generate_schema(ModifySheetValuesResult)
FORMAT_SHEET_RANGE_SCHEMA = _generate_schema(FormatSheetRangeResult)
CONDITIONAL_FORMAT_SCHEMA = _generate_schema(ConditionalFormatResult)
CREATE_SPREADSHEET_SCHEMA = _generate_schema(CreateSpreadsheetResult)
CREATE_SHEET_SCHEMA = _generate_schema(CreateSheetResult)
