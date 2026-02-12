"""
Structured Output Utilities for Google Workspace MCP Tools

This module provides helper functions for creating tool results that include
both human-readable text content and machine-parseable structured data.
"""

from dataclasses import asdict, is_dataclass
from typing import Any

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from pydantic import TypeAdapter


def _coerce_none(obj: Any) -> Any:
    """Recursively remove None values from dicts and lists.

    MCP output schema validation does not support JSON Schema ``anyOf``,
    so ``Optional`` fields that are ``None`` fail validation.  Removing
    them from the output is safe because every ``Optional`` field already
    has a default and is not listed in the schema's ``required`` array.
    """
    if isinstance(obj, dict):
        return {k: _coerce_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_coerce_none(item) for item in obj]
    return obj


def _strip_any_of(schema: Any) -> Any:
    """Recursively replace ``anyOf`` nullable patterns with the non-null type.

    Pydantic generates ``{"anyOf": [{"type": "string"}, {"type": "null"}]}``
    for ``Optional[str]``, but MCP schema validation does not support
    ``anyOf``.  This collapses such patterns to ``{"type": "string"}``,
    preserving all sibling keys (``default``, ``title``, etc.).
    """
    if isinstance(schema, list):
        return [_strip_any_of(item) for item in schema]
    if not isinstance(schema, dict):
        return schema

    # Recurse into all dict values first
    result = {k: _strip_any_of(v) for k, v in schema.items()}

    # Collapse anyOf nullable patterns
    if "anyOf" in result:
        any_of = result["anyOf"]
        non_null = [opt for opt in any_of if opt != {"type": "null"}]
        if len(non_null) == 1:
            # Replace the anyOf with the single non-null option, keep siblings
            collapsed = {k: v for k, v in result.items() if k != "anyOf"}
            collapsed.update(non_null[0])
            return collapsed

    return result


def _inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Inline all ``$ref`` references and remove ``$defs``.

    MCP schema validation does not support ``$ref`` / ``$defs``.
    Pydantic generates these for nested dataclasses. This function
    resolves every ``$ref`` by substituting the referenced definition
    inline, then drops the top-level ``$defs`` block.
    """
    defs = schema.get("$defs", {})
    if not defs:
        return schema

    def _resolve(node: Any) -> Any:
        if isinstance(node, list):
            return [_resolve(item) for item in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            ref_path = node["$ref"]  # e.g. "#/$defs/CalendarInfo"
            def_name = ref_path.rsplit("/", 1)[-1]
            if def_name in defs:
                # Merge any sibling keys (e.g. title) with the resolved def
                resolved = {k: v for k, v in node.items() if k != "$ref"}
                resolved.update(_resolve(defs[def_name]))
                return resolved
        return {k: _resolve(v) for k, v in node.items()}

    result = _resolve(schema)
    result.pop("$defs", None)
    return result


def generate_schema(cls: type) -> dict[str, Any]:
    """Generate an MCP-compatible JSON schema for a dataclass.

    Uses Pydantic's ``TypeAdapter`` then:
    1. Inlines ``$ref`` / ``$defs`` (not supported by MCP)
    2. Strips ``anyOf`` nullable patterns (not supported by MCP)
    """
    raw = TypeAdapter(cls).json_schema()
    return _strip_any_of(_inline_refs(raw))


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
        structured_content=_coerce_none(structured),
    )
