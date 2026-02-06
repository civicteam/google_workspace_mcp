"""
Google Chat MCP Tools

This module provides MCP tools for interacting with Google Chat API.
"""

import logging
import asyncio
from typing import Optional

from googleapiclient.errors import HttpError
from fastmcp.tools.tool import ToolResult

# Auth & server utilities
from auth.service_decorator import require_google_service
from core.server import server
from core.utils import handle_http_errors
from core.structured_output import create_tool_result
from gchat.chat_models import (
    ChatSpace,
    ChatListSpacesResult,
    ChatMessage,
    ChatGetMessagesResult,
    ChatSendMessageResult,
    ChatSearchMessage,
    ChatSearchMessagesResult,
    CHAT_LIST_SPACES_RESULT_SCHEMA,
    CHAT_GET_MESSAGES_RESULT_SCHEMA,
    CHAT_SEND_MESSAGE_RESULT_SCHEMA,
    CHAT_SEARCH_MESSAGES_RESULT_SCHEMA,
)

logger = logging.getLogger(__name__)


@server.tool(output_schema=CHAT_LIST_SPACES_RESULT_SCHEMA)
@require_google_service("chat", "chat_read")
@handle_http_errors("list_spaces", service_type="chat")
async def list_spaces(
    service,
    page_size: int = 100,
    space_type: str = "all",  # "all", "room", "dm"
) -> ToolResult:
    """
    Lists Google Chat spaces (rooms and direct messages) accessible to the user.

    Returns:
        ToolResult: A formatted list of Google Chat spaces accessible to the user.
        Also includes structured_content for machine parsing.
    """
    logger.info(f"[list_spaces] Type={space_type}")

    # Build filter based on space_type
    filter_param = None
    if space_type == "room":
        filter_param = "spaceType = SPACE"
    elif space_type == "dm":
        filter_param = "spaceType = DIRECT_MESSAGE"

    request_params = {"pageSize": page_size}
    if filter_param:
        request_params["filter"] = filter_param

    response = await asyncio.to_thread(service.spaces().list(**request_params).execute)

    spaces = response.get("spaces", [])
    if not spaces:
        structured_result = ChatListSpacesResult(
            space_type_filter=space_type,
            total_found=0,
            spaces=[],
        )
        return create_tool_result(
            text=f"No Chat spaces found for type '{space_type}'.",
            data=structured_result,
        )

    output = [f"Found {len(spaces)} Chat spaces (type: {space_type}):"]
    space_list = []
    for space in spaces:
        space_name = space.get("displayName", "Unnamed Space")
        space_id = space.get("name", "")
        space_type_actual = space.get("spaceType", "UNKNOWN")
        output.append(f"- {space_name} (ID: {space_id}, Type: {space_type_actual})")
        space_list.append(
            ChatSpace(
                space_id=space_id,
                display_name=space_name,
                space_type=space_type_actual,
            )
        )

    structured_result = ChatListSpacesResult(
        space_type_filter=space_type,
        total_found=len(spaces),
        spaces=space_list,
    )

    return create_tool_result(text="\n".join(output), data=structured_result)


@server.tool(output_schema=CHAT_GET_MESSAGES_RESULT_SCHEMA)
@require_google_service("chat", "chat_read")
@handle_http_errors("get_messages", service_type="chat")
async def get_messages(
    service,
    space_id: str,
    page_size: int = 50,
    order_by: str = "createTime desc",
) -> ToolResult:
    """
    Retrieves messages from a Google Chat space.

    Returns:
        ToolResult: Formatted messages from the specified space.
        Also includes structured_content for machine parsing.
    """
    logger.info(f"[get_messages] Space ID: '{space_id}'")

    # Get space info first
    space_info = await asyncio.to_thread(service.spaces().get(name=space_id).execute)
    space_name = space_info.get("displayName", "Unknown Space")

    # Get messages
    response = await asyncio.to_thread(
        service.spaces()
        .messages()
        .list(parent=space_id, pageSize=page_size, orderBy=order_by)
        .execute
    )

    messages = response.get("messages", [])
    if not messages:
        structured_result = ChatGetMessagesResult(
            space_id=space_id,
            space_name=space_name,
            total_messages=0,
            messages=[],
        )
        return create_tool_result(
            text=f"No messages found in space '{space_name}' (ID: {space_id}).",
            data=structured_result,
        )

    output = [f"Messages from '{space_name}' (ID: {space_id}):\n"]
    message_list = []
    for msg in messages:
        sender = msg.get("sender", {}).get("displayName", "Unknown Sender")
        create_time = msg.get("createTime", "Unknown Time")
        text_content = msg.get("text", "No text content")
        msg_name = msg.get("name", "")

        output.append(f"[{create_time}] {sender}:")
        output.append(f"  {text_content}")
        output.append(f"  (Message ID: {msg_name})\n")

        message_list.append(
            ChatMessage(
                message_id=msg_name,
                sender=sender,
                create_time=create_time,
                text=text_content,
            )
        )

    structured_result = ChatGetMessagesResult(
        space_id=space_id,
        space_name=space_name,
        total_messages=len(messages),
        messages=message_list,
    )

    return create_tool_result(text="\n".join(output), data=structured_result)


@server.tool(output_schema=CHAT_SEND_MESSAGE_RESULT_SCHEMA)
@require_google_service("chat", "chat_write")
@handle_http_errors("send_message", service_type="chat")
async def send_message(
    service,
    space_id: str,
    message_text: str,
    thread_key: Optional[str] = None,
) -> ToolResult:
    """
    Sends a message to a Google Chat space.

    Returns:
        ToolResult: Confirmation message with sent message details.
        Also includes structured_content for machine parsing.
    """
    logger.info(f"[send_message] Space: '{space_id}'")

    message_body = {"text": message_text}

    # Add thread key if provided (for threaded replies)
    request_params = {"parent": space_id, "body": message_body}
    if thread_key:
        request_params["threadKey"] = thread_key

    message = await asyncio.to_thread(
        service.spaces().messages().create(**request_params).execute
    )

    message_name = message.get("name", "")
    create_time = message.get("createTime", "")

    msg = f"Message sent to space '{space_id}'. Message ID: {message_name}, Time: {create_time}"
    logger.info(f"Successfully sent message to space '{space_id}'")

    structured_result = ChatSendMessageResult(
        space_id=space_id,
        message_id=message_name,
        create_time=create_time,
    )

    return create_tool_result(text=msg, data=structured_result)


@server.tool(output_schema=CHAT_SEARCH_MESSAGES_RESULT_SCHEMA)
@require_google_service("chat", "chat_read")
@handle_http_errors("search_messages", service_type="chat")
async def search_messages(
    service,
    query: str,
    space_id: Optional[str] = None,
    page_size: int = 25,
) -> ToolResult:
    """
    Searches for messages in Google Chat spaces by text content.

    Returns:
        ToolResult: A formatted list of messages matching the search query.
        Also includes structured_content for machine parsing.
    """
    logger.info(f"[search_messages] Query='{query}'")

    # If specific space provided, search within that space
    if space_id:
        response = await asyncio.to_thread(
            service.spaces()
            .messages()
            .list(parent=space_id, pageSize=page_size, filter=f'text:"{query}"')
            .execute
        )
        messages = response.get("messages", [])
        context = f"space '{space_id}'"
    else:
        # Search across all accessible spaces (this may require iterating through spaces)
        # For simplicity, we'll search the user's spaces first
        spaces_response = await asyncio.to_thread(
            service.spaces().list(pageSize=100).execute
        )
        spaces = spaces_response.get("spaces", [])

        messages = []
        for space in spaces[:10]:  # Limit to first 10 spaces to avoid timeout
            try:
                space_messages = await asyncio.to_thread(
                    service.spaces()
                    .messages()
                    .list(
                        parent=space.get("name"), pageSize=5, filter=f'text:"{query}"'
                    )
                    .execute
                )
                space_msgs = space_messages.get("messages", [])
                for msg in space_msgs:
                    msg["_space_name"] = space.get("displayName", "Unknown")
                messages.extend(space_msgs)
            except HttpError:
                continue  # Skip spaces we can't access
        context = "all accessible spaces"

    if not messages:
        structured_result = ChatSearchMessagesResult(
            query=query,
            context=context,
            total_found=0,
            messages=[],
        )
        return create_tool_result(
            text=f"No messages found matching '{query}' in {context}.",
            data=structured_result,
        )

    output = [f"Found {len(messages)} messages matching '{query}' in {context}:"]
    message_list = []
    for msg in messages:
        sender = msg.get("sender", {}).get("displayName", "Unknown Sender")
        create_time = msg.get("createTime", "Unknown Time")
        text_content = msg.get("text", "No text content")
        space_name = msg.get("_space_name", "Unknown Space")

        # Truncate long messages for text output
        display_text = text_content
        if len(display_text) > 100:
            display_text = display_text[:100] + "..."

        output.append(f"- [{create_time}] {sender} in '{space_name}': {display_text}")

        message_list.append(
            ChatSearchMessage(
                sender=sender,
                create_time=create_time,
                text=text_content,  # Full text in structured output
                space_name=space_name,
            )
        )

    structured_result = ChatSearchMessagesResult(
        query=query,
        context=context,
        total_found=len(messages),
        messages=message_list,
    )

    return create_tool_result(text="\n".join(output), data=structured_result)
