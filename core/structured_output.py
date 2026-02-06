"""
Structured Output Utilities for Google Workspace MCP Tools

This module provides helper functions for creating tool results that include
both human-readable text content and machine-parseable structured data.
"""

from dataclasses import asdict, is_dataclass
from typing import Any

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent


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
        structured_content=structured,
    )
