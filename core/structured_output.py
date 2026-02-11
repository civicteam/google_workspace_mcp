"""
Structured Output Utilities for Google Workspace MCP Tools

This module provides helper functions for creating tool results that include
both human-readable text content and machine-parseable structured data.
"""

from dataclasses import asdict, is_dataclass
from typing import Any

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent


def _strip_none(obj: Any) -> Any:
    """Recursively strip None values from dicts and lists.

    MCP output schema validation does not support JSON Schema ``anyOf``,
    so ``Optional`` fields that are ``None`` fail validation.  Removing
    them from the output is safe because every ``Optional`` field already
    has a default and is not listed in the schema's ``required`` array.
    """
    if isinstance(obj, dict):
        return {k: _strip_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_none(item) for item in obj]
    return obj


def create_tool_result(
    text: str,
    data: dict[str, Any] | Any,
) -> ToolResult:
    """
    Create a ToolResult with both text content and structured data.

    Args:
        text: Human-readable text output for LLM consumption
        data: Structured data (dict or dataclass) for machine parsing

    Returns:
        ToolResult with both content and structured_content populated
    """
    structured = asdict(data) if is_dataclass(data) else data
    return ToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=_strip_none(structured),
    )
