"""
Google Slides MCP Tools

This module provides MCP tools for interacting with Google Slides API.
"""

import logging
import asyncio
from typing import List, Dict, Any

from fastmcp.tools.tool import ToolResult

from auth.service_decorator import require_google_service
from core.server import server
from core.structured_output import create_tool_result
from core.utils import handle_http_errors
from core.comments import create_comment_tools
from gslides.slides_models import (
    SlidesCreatePresentationResult,
    SlideInfo,
    SlidesGetPresentationResult,
    BatchUpdateReply,
    SlidesBatchUpdateResult,
    PageElementInfo,
    SlidesGetPageResult,
    SlidesGetPageThumbnailResult,
    SLIDES_CREATE_PRESENTATION_SCHEMA,
    SLIDES_GET_PRESENTATION_SCHEMA,
    SLIDES_BATCH_UPDATE_SCHEMA,
    SLIDES_GET_PAGE_SCHEMA,
    SLIDES_GET_PAGE_THUMBNAIL_SCHEMA,
)

logger = logging.getLogger(__name__)


@server.tool(output_schema=SLIDES_CREATE_PRESENTATION_SCHEMA)
@handle_http_errors("create_presentation", service_type="slides")
@require_google_service("slides", "slides")
async def create_presentation(
    service, title: str = "Untitled Presentation"
) -> ToolResult:
    """
    Create a new Google Slides presentation.

    Args:
        title (str): The title for the new presentation. Defaults to "Untitled Presentation".

    Returns:
        ToolResult: Details about the created presentation including ID and URL.
        Also includes structured_content for machine parsing.
    """
    logger.info(f"[create_presentation] Invoked. Title: '{title}'")

    body = {"title": title}

    result = await asyncio.to_thread(service.presentations().create(body=body).execute)

    presentation_id = result.get("presentationId")
    presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
    slide_count = len(result.get("slides", []))

    confirmation_message = f"""Presentation Created Successfully:
- Title: {title}
- Presentation ID: {presentation_id}
- URL: {presentation_url}
- Slides: {slide_count} slide(s) created"""

    structured_result = SlidesCreatePresentationResult(
        presentation_id=presentation_id,
        title=title,
        url=presentation_url,
        slide_count=slide_count,
    )

    logger.info("Presentation created successfully")
    return create_tool_result(text=confirmation_message, data=structured_result)


@server.tool(output_schema=SLIDES_GET_PRESENTATION_SCHEMA)
@handle_http_errors("get_presentation", is_read_only=True, service_type="slides")
@require_google_service("slides", "slides_read")
async def get_presentation(service, presentation_id: str) -> ToolResult:
    """
    Get details about a Google Slides presentation.

    Args:
        presentation_id (str): The ID of the presentation to retrieve.

    Returns:
        ToolResult: Details about the presentation including title, slides count, and metadata.
        Also includes structured_content for machine parsing.
    """
    logger.info(f"[get_presentation] Invoked. ID: '{presentation_id}'")

    result = await asyncio.to_thread(
        service.presentations().get(presentationId=presentation_id).execute
    )

    title = result.get("title", "Untitled")
    slides = result.get("slides", [])
    page_size = result.get("pageSize", {})

    slides_info = []
    structured_slides = []
    for i, slide in enumerate(slides, 1):
        slide_id = slide.get("objectId", "Unknown")
        page_elements = slide.get("pageElements", [])

        # Collect text from the slide whose JSON structure is very complicated
        # https://googleapis.github.io/google-api-python-client/docs/dyn/slides_v1.presentations.html#get
        slide_text = ""
        raw_slide_text = ""
        try:
            texts_from_elements = []
            for page_element in slide.get("pageElements", []):
                shape = page_element.get("shape", None)
                if shape and shape.get("text", None):
                    text = shape.get("text", None)
                    if text:
                        text_elements_in_shape = []
                        for text_element in text.get("textElements", []):
                            text_run = text_element.get("textRun", None)
                            if text_run:
                                content = text_run.get("content", None)
                                if content:
                                    start_index = text_element.get("startIndex", 0)
                                    text_elements_in_shape.append(
                                        (start_index, content)
                                    )

                        if text_elements_in_shape:
                            # Sort text elements within a single shape
                            text_elements_in_shape.sort(key=lambda item: item[0])
                            full_text_from_shape = "".join(
                                [item[1] for item in text_elements_in_shape]
                            )
                            texts_from_elements.append(full_text_from_shape)

            # cleanup text we collected
            slide_text = "\n".join(texts_from_elements)
            slide_text_rows = slide_text.split("\n")
            slide_text_rows = [row for row in slide_text_rows if len(row.strip()) > 0]
            raw_slide_text = "\n".join(slide_text_rows)
            if slide_text_rows:
                slide_text_rows = ["    > " + row for row in slide_text_rows]
                slide_text = "\n" + "\n".join(slide_text_rows)
            else:
                slide_text = ""
        except Exception as e:
            logger.warning(f"Failed to extract text from the slide {slide_id}: {e}")
            slide_text = f"<failed to extract text: {type(e)}, {e}>"
            raw_slide_text = slide_text

        slides_info.append(
            f"  Slide {i}: ID {slide_id}, {len(page_elements)} element(s), text: {slide_text if slide_text else 'empty'}"
        )
        structured_slides.append(
            SlideInfo(
                slide_number=i,
                slide_id=slide_id,
                element_count=len(page_elements),
                text_content=raw_slide_text,
            )
        )

    presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
    page_width = page_size.get("width", {}).get("magnitude")
    page_height = page_size.get("height", {}).get("magnitude")
    page_unit = page_size.get("width", {}).get("unit", "")

    confirmation_message = f"""Presentation Details:
- Title: {title}
- Presentation ID: {presentation_id}
- URL: {presentation_url}
- Total Slides: {len(slides)}
- Page Size: {page_width if page_width else "Unknown"} x {page_height if page_height else "Unknown"} {page_unit}

Slides Breakdown:
{chr(10).join(slides_info) if slides_info else "  No slides found"}"""

    structured_result = SlidesGetPresentationResult(
        presentation_id=presentation_id,
        title=title,
        url=presentation_url,
        total_slides=len(slides),
        page_width=page_width,
        page_height=page_height,
        page_unit=page_unit if page_unit else None,
        slides=structured_slides,
    )

    logger.info("Presentation retrieved successfully")
    return create_tool_result(text=confirmation_message, data=structured_result)


@server.tool(output_schema=SLIDES_BATCH_UPDATE_SCHEMA)
@handle_http_errors("batch_update_presentation", service_type="slides")
@require_google_service("slides", "slides")
async def batch_update_presentation(
    service,
    presentation_id: str,
    requests: List[Dict[str, Any]],
) -> ToolResult:
    """
    Apply batch updates to a Google Slides presentation.

    Args:
        presentation_id (str): The ID of the presentation to update.
        requests (List[Dict[str, Any]]): List of update requests to apply.

    Returns:
        ToolResult: Details about the batch update operation results.
        Also includes structured_content for machine parsing.
    """
    logger.info(
        f"[batch_update_presentation] Invoked. ID: '{presentation_id}', Requests: {len(requests)}"
    )

    body = {"requests": requests}

    result = await asyncio.to_thread(
        service.presentations()
        .batchUpdate(presentationId=presentation_id, body=body)
        .execute
    )

    replies = result.get("replies", [])
    presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"

    confirmation_message = f"""Batch Update Completed:
- Presentation ID: {presentation_id}
- URL: {presentation_url}
- Requests Applied: {len(requests)}
- Replies Received: {len(replies)}"""

    structured_replies = []
    if replies:
        confirmation_message += "\n\nUpdate Results:"
        for i, reply in enumerate(replies, 1):
            if "createSlide" in reply:
                slide_id = reply["createSlide"].get("objectId", "Unknown")
                confirmation_message += (
                    f"\n  Request {i}: Created slide with ID {slide_id}"
                )
                structured_replies.append(
                    BatchUpdateReply(
                        request_number=i,
                        operation_type="createSlide",
                        object_id=slide_id,
                    )
                )
            elif "createShape" in reply:
                shape_id = reply["createShape"].get("objectId", "Unknown")
                confirmation_message += (
                    f"\n  Request {i}: Created shape with ID {shape_id}"
                )
                structured_replies.append(
                    BatchUpdateReply(
                        request_number=i,
                        operation_type="createShape",
                        object_id=shape_id,
                    )
                )
            else:
                confirmation_message += f"\n  Request {i}: Operation completed"
                structured_replies.append(
                    BatchUpdateReply(
                        request_number=i,
                        operation_type="other",
                        object_id=None,
                    )
                )

    structured_result = SlidesBatchUpdateResult(
        presentation_id=presentation_id,
        url=presentation_url,
        requests_applied=len(requests),
        replies_received=len(replies),
        replies=structured_replies,
    )

    logger.info("Batch update completed successfully")
    return create_tool_result(text=confirmation_message, data=structured_result)


@server.tool(output_schema=SLIDES_GET_PAGE_SCHEMA)
@handle_http_errors("get_page", is_read_only=True, service_type="slides")
@require_google_service("slides", "slides_read")
async def get_page(service, presentation_id: str, page_object_id: str) -> ToolResult:
    """
    Get details about a specific page (slide) in a presentation.

    Args:
        presentation_id (str): The ID of the presentation.
        page_object_id (str): The object ID of the page/slide to retrieve.

    Returns:
        ToolResult: Details about the specific page including elements and layout.
        Also includes structured_content for machine parsing.
    """
    logger.info(
        f"[get_page] Invoked. Presentation: '{presentation_id}', Page: '{page_object_id}'"
    )

    result = await asyncio.to_thread(
        service.presentations()
        .pages()
        .get(presentationId=presentation_id, pageObjectId=page_object_id)
        .execute
    )

    page_type = result.get("pageType", "Unknown")
    page_elements = result.get("pageElements", [])

    elements_info = []
    structured_elements = []
    for element in page_elements:
        element_id = element.get("objectId", "Unknown")
        if "shape" in element:
            shape_type = element["shape"].get("shapeType", "Unknown")
            elements_info.append(f"  Shape: ID {element_id}, Type: {shape_type}")
            structured_elements.append(
                PageElementInfo(
                    element_id=element_id,
                    element_type="Shape",
                    details=shape_type,
                )
            )
        elif "table" in element:
            table = element["table"]
            rows = table.get("rows", 0)
            cols = table.get("columns", 0)
            elements_info.append(f"  Table: ID {element_id}, Size: {rows}x{cols}")
            structured_elements.append(
                PageElementInfo(
                    element_id=element_id,
                    element_type="Table",
                    details=f"{rows}x{cols}",
                )
            )
        elif "line" in element:
            line_type = element["line"].get("lineType", "Unknown")
            elements_info.append(f"  Line: ID {element_id}, Type: {line_type}")
            structured_elements.append(
                PageElementInfo(
                    element_id=element_id,
                    element_type="Line",
                    details=line_type,
                )
            )
        else:
            elements_info.append(f"  Element: ID {element_id}, Type: Unknown")
            structured_elements.append(
                PageElementInfo(
                    element_id=element_id,
                    element_type="Unknown",
                    details=None,
                )
            )

    confirmation_message = f"""Page Details:
- Presentation ID: {presentation_id}
- Page ID: {page_object_id}
- Page Type: {page_type}
- Total Elements: {len(page_elements)}

Page Elements:
{chr(10).join(elements_info) if elements_info else "  No elements found"}"""

    structured_result = SlidesGetPageResult(
        presentation_id=presentation_id,
        page_id=page_object_id,
        page_type=page_type,
        total_elements=len(page_elements),
        elements=structured_elements,
    )

    logger.info("Page retrieved successfully")
    return create_tool_result(text=confirmation_message, data=structured_result)


@server.tool(output_schema=SLIDES_GET_PAGE_THUMBNAIL_SCHEMA)
@handle_http_errors("get_page_thumbnail", is_read_only=True, service_type="slides")
@require_google_service("slides", "slides_read")
async def get_page_thumbnail(
    service,
    presentation_id: str,
    page_object_id: str,
    thumbnail_size: str = "MEDIUM",
) -> ToolResult:
    """
    Generate a thumbnail URL for a specific page (slide) in a presentation.

    Args:
        presentation_id (str): The ID of the presentation.
        page_object_id (str): The object ID of the page/slide.
        thumbnail_size (str): Size of thumbnail ("LARGE", "MEDIUM", "SMALL"). Defaults to "MEDIUM".

    Returns:
        ToolResult: URL to the generated thumbnail image.
        Also includes structured_content for machine parsing.
    """
    logger.info(
        f"[get_page_thumbnail] Invoked. Presentation: '{presentation_id}', Page: '{page_object_id}', Size: '{thumbnail_size}'"
    )

    result = await asyncio.to_thread(
        service.presentations()
        .pages()
        .getThumbnail(
            presentationId=presentation_id,
            pageObjectId=page_object_id,
            thumbnailProperties_thumbnailSize=thumbnail_size,
            thumbnailProperties_mimeType="PNG",
        )
        .execute
    )

    thumbnail_url = result.get("contentUrl", "")

    confirmation_message = f"""Thumbnail Generated:
- Presentation ID: {presentation_id}
- Page ID: {page_object_id}
- Thumbnail Size: {thumbnail_size}
- Thumbnail URL: {thumbnail_url}

You can view or download the thumbnail using the provided URL."""

    structured_result = SlidesGetPageThumbnailResult(
        presentation_id=presentation_id,
        page_id=page_object_id,
        thumbnail_size=thumbnail_size,
        thumbnail_url=thumbnail_url,
    )

    logger.info("Thumbnail generated successfully")
    return create_tool_result(text=confirmation_message, data=structured_result)


# Create comment management tools for slides
_comment_tools = create_comment_tools("presentation", "presentation_id")
read_presentation_comments = _comment_tools["read_comments"]
create_presentation_comment = _comment_tools["create_comment"]
reply_to_presentation_comment = _comment_tools["reply_to_comment"]
resolve_presentation_comment = _comment_tools["resolve_comment"]

# Aliases for backwards compatibility and intuitive naming
read_slide_comments = read_presentation_comments
create_slide_comment = create_presentation_comment
reply_to_slide_comment = reply_to_presentation_comment
resolve_slide_comment = resolve_presentation_comment
