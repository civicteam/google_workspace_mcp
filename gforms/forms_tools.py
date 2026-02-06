"""
Google Forms MCP Tools

This module provides MCP tools for interacting with Google Forms API.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any

from fastmcp.tools.tool import ToolResult

from auth.service_decorator import require_google_service
from core.server import server
from core.structured_output import create_tool_result
from core.utils import handle_http_errors
from gforms.forms_models import (
    FormsCreateResult,
    FormsGetResult,
    FormsQuestionSummary,
    FormsPublishSettingsResult,
    FormsResponseResult,
    FormsAnswerDetail,
    FormsListResponsesResult,
    FormsResponseSummary,
    FormsBatchUpdateResult,
    FormsBatchUpdateReply,
    FORMS_CREATE_RESULT_SCHEMA,
    FORMS_GET_RESULT_SCHEMA,
    FORMS_PUBLISH_SETTINGS_RESULT_SCHEMA,
    FORMS_RESPONSE_RESULT_SCHEMA,
    FORMS_LIST_RESPONSES_RESULT_SCHEMA,
    FORMS_BATCH_UPDATE_RESULT_SCHEMA,
)

logger = logging.getLogger(__name__)


@server.tool(output_schema=FORMS_CREATE_RESULT_SCHEMA)
@handle_http_errors("create_form", service_type="forms")
@require_google_service("forms", "forms")
async def create_form(
    service,
    title: str,
    description: Optional[str] = None,
    document_title: Optional[str] = None,
) -> ToolResult:
    """
    Create a new form using the title given in the provided form message in the request.

    Args:
        title (str): The title of the form.
        description (Optional[str]): The description of the form.
        document_title (Optional[str]): The document title (shown in browser tab).

    Returns:
        ToolResult: Confirmation message with form ID and edit URL.
        Also includes structured_content for machine parsing.
    """
    logger.info(f"[create_form] Invoked. Title: {title}")

    form_body: Dict[str, Any] = {"info": {"title": title}}

    if description:
        form_body["info"]["description"] = description

    if document_title:
        form_body["info"]["document_title"] = document_title

    created_form = await asyncio.to_thread(
        service.forms().create(body=form_body).execute
    )

    form_id = created_form.get("formId")
    form_title = created_form.get("info", {}).get("title", title)
    edit_url = f"https://docs.google.com/forms/d/{form_id}/edit"
    responder_url = created_form.get(
        "responderUri", f"https://docs.google.com/forms/d/{form_id}/viewform"
    )

    confirmation_message = f"Successfully created form '{form_title}'. Form ID: {form_id}. Edit URL: {edit_url}. Responder URL: {responder_url}"
    logger.info(f"Form created successfully. ID: {form_id}")

    structured_result = FormsCreateResult(
        form_id=form_id,
        title=form_title,
        edit_url=edit_url,
        responder_url=responder_url,
    )

    return create_tool_result(text=confirmation_message, data=structured_result)


@server.tool(output_schema=FORMS_GET_RESULT_SCHEMA)
@handle_http_errors("get_form", is_read_only=True, service_type="forms")
@require_google_service("forms", "forms")
async def get_form(service, form_id: str) -> ToolResult:
    """
    Get a form.

    Args:
        form_id (str): The ID of the form to retrieve.

    Returns:
        ToolResult: Form details including title, description, questions, and URLs.
        Also includes structured_content for machine parsing.
    """
    logger.info(f"[get_form] Invoked. Form ID: {form_id}")

    form = await asyncio.to_thread(service.forms().get(formId=form_id).execute)

    form_info = form.get("info", {})
    title = form_info.get("title", "No Title")
    description = form_info.get("description", "No Description")
    document_title = form_info.get("documentTitle", title)

    edit_url = f"https://docs.google.com/forms/d/{form_id}/edit"
    responder_url = form.get(
        "responderUri", f"https://docs.google.com/forms/d/{form_id}/viewform"
    )

    items = form.get("items", [])
    questions_summary = []
    structured_questions = []
    for i, item in enumerate(items, 1):
        item_title = item.get("title", f"Question {i}")
        is_required = (
            item.get("questionItem", {}).get("question", {}).get("required", False)
        )
        required_text = " (Required)" if is_required else ""
        questions_summary.append(f"  {i}. {item_title}{required_text}")
        structured_questions.append(
            FormsQuestionSummary(index=i, title=item_title, required=is_required)
        )

    questions_text = (
        "\n".join(questions_summary) if questions_summary else "  No questions found"
    )

    result = f"""Form Details:
- Title: "{title}"
- Description: "{description}"
- Document Title: "{document_title}"
- Form ID: {form_id}
- Edit URL: {edit_url}
- Responder URL: {responder_url}
- Questions ({len(items)} total):
{questions_text}"""

    logger.info(f"Successfully retrieved form. ID: {form_id}")

    structured_result = FormsGetResult(
        form_id=form_id,
        title=title,
        description=description,
        document_title=document_title,
        edit_url=edit_url,
        responder_url=responder_url,
        questions=structured_questions,
    )

    return create_tool_result(text=result, data=structured_result)


@server.tool(output_schema=FORMS_PUBLISH_SETTINGS_RESULT_SCHEMA)
@handle_http_errors("set_publish_settings", service_type="forms")
@require_google_service("forms", "forms")
async def set_publish_settings(
    service,
    form_id: str,
    publish_as_template: bool = False,
    require_authentication: bool = False,
) -> ToolResult:
    """
    Updates the publish settings of a form.

    Args:
        form_id (str): The ID of the form to update publish settings for.
        publish_as_template (bool): Whether to publish as a template. Defaults to False.
        require_authentication (bool): Whether to require authentication to view/submit. Defaults to False.

    Returns:
        ToolResult: Confirmation message of the successful publish settings update.
        Also includes structured_content for machine parsing.
    """
    logger.info(f"[set_publish_settings] Invoked. Form ID: {form_id}")

    settings_body = {
        "publishAsTemplate": publish_as_template,
        "requireAuthentication": require_authentication,
    }

    await asyncio.to_thread(
        service.forms().setPublishSettings(formId=form_id, body=settings_body).execute
    )

    confirmation_message = f"Successfully updated publish settings for form {form_id}. Publish as template: {publish_as_template}, Require authentication: {require_authentication}"
    logger.info(f"Publish settings updated successfully. Form ID: {form_id}")

    structured_result = FormsPublishSettingsResult(
        form_id=form_id,
        publish_as_template=publish_as_template,
        require_authentication=require_authentication,
    )

    return create_tool_result(text=confirmation_message, data=structured_result)


@server.tool(output_schema=FORMS_RESPONSE_RESULT_SCHEMA)
@handle_http_errors("get_form_response", is_read_only=True, service_type="forms")
@require_google_service("forms", "forms")
async def get_form_response(service, form_id: str, response_id: str) -> ToolResult:
    """
    Get one response from the form.

    Args:
        form_id (str): The ID of the form.
        response_id (str): The ID of the response to retrieve.

    Returns:
        ToolResult: Response details including answers and metadata.
        Also includes structured_content for machine parsing.
    """
    logger.info(
        f"[get_form_response] Invoked. Form ID: {form_id}, Response ID: {response_id}"
    )

    response = await asyncio.to_thread(
        service.forms().responses().get(formId=form_id, responseId=response_id).execute
    )

    result_response_id = response.get("responseId", "Unknown")
    create_time = response.get("createTime", "Unknown")
    last_submitted_time = response.get("lastSubmittedTime", "Unknown")

    answers = response.get("answers", {})
    answer_details = []
    structured_answers = []
    for question_id, answer_data in answers.items():
        question_response = answer_data.get("textAnswers", {}).get("answers", [])
        if question_response:
            answer_text = ", ".join([ans.get("value", "") for ans in question_response])
            answer_details.append(f"  Question ID {question_id}: {answer_text}")
        else:
            answer_text = "No answer provided"
            answer_details.append(f"  Question ID {question_id}: No answer provided")
        structured_answers.append(
            FormsAnswerDetail(question_id=question_id, answer_text=answer_text)
        )

    answers_text = "\n".join(answer_details) if answer_details else "  No answers found"

    result = f"""Form Response Details:
- Form ID: {form_id}
- Response ID: {result_response_id}
- Created: {create_time}
- Last Submitted: {last_submitted_time}
- Answers:
{answers_text}"""

    logger.info(f"Successfully retrieved response. Response ID: {result_response_id}")

    structured_result = FormsResponseResult(
        form_id=form_id,
        response_id=result_response_id,
        create_time=create_time,
        last_submitted_time=last_submitted_time,
        answers=structured_answers,
    )

    return create_tool_result(text=result, data=structured_result)


@server.tool(output_schema=FORMS_LIST_RESPONSES_RESULT_SCHEMA)
@handle_http_errors("list_form_responses", is_read_only=True, service_type="forms")
@require_google_service("forms", "forms")
async def list_form_responses(
    service,
    form_id: str,
    page_size: int = 10,
    page_token: Optional[str] = None,
) -> ToolResult:
    """
    List a form's responses.

    Args:
        form_id (str): The ID of the form.
        page_size (int): Maximum number of responses to return. Defaults to 10.
        page_token (Optional[str]): Token for retrieving next page of results.

    Returns:
        ToolResult: List of responses with basic details and pagination info.
        Also includes structured_content for machine parsing.
    """
    logger.info(f"[list_form_responses] Invoked. Form ID: {form_id}")

    params = {"formId": form_id, "pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token

    responses_result = await asyncio.to_thread(
        service.forms().responses().list(**params).execute
    )

    responses = responses_result.get("responses", [])
    next_page_token = responses_result.get("nextPageToken")

    if not responses:
        structured_result = FormsListResponsesResult(
            form_id=form_id,
            total_returned=0,
            responses=[],
            next_page_token=None,
        )
        return create_tool_result(
            text=f"No responses found for form {form_id}.",
            data=structured_result,
        )

    response_details = []
    structured_responses = []
    for i, response in enumerate(responses, 1):
        response_id = response.get("responseId", "Unknown")
        create_time = response.get("createTime", "Unknown")
        last_submitted_time = response.get("lastSubmittedTime", "Unknown")

        answers_count = len(response.get("answers", {}))
        response_details.append(
            f"  {i}. Response ID: {response_id} | Created: {create_time} | Last Submitted: {last_submitted_time} | Answers: {answers_count}"
        )
        structured_responses.append(
            FormsResponseSummary(
                response_id=response_id,
                create_time=create_time,
                last_submitted_time=last_submitted_time,
                answer_count=answers_count,
            )
        )

    pagination_info = (
        f"\nNext page token: {next_page_token}"
        if next_page_token
        else "\nNo more pages."
    )

    result = f"""Form Responses:
- Form ID: {form_id}
- Total responses returned: {len(responses)}
- Responses:
{chr(10).join(response_details)}{pagination_info}"""

    logger.info(
        f"Successfully retrieved {len(responses)} responses. Form ID: {form_id}"
    )

    structured_result = FormsListResponsesResult(
        form_id=form_id,
        total_returned=len(responses),
        responses=structured_responses,
        next_page_token=next_page_token,
    )

    return create_tool_result(text=result, data=structured_result)


# Internal implementation function for testing
async def _batch_update_form_impl(
    service: Any,
    form_id: str,
    requests: List[Dict[str, Any]],
) -> tuple[str, FormsBatchUpdateResult]:
    """Internal implementation for batch_update_form.

    Applies batch updates to a Google Form using the Forms API batchUpdate method.

    Args:
        service: Google Forms API service client.
        form_id: The ID of the form to update.
        requests: List of update request dictionaries.

    Returns:
        Tuple of (formatted string with batch update results, structured result).
    """
    body = {"requests": requests}

    result = await asyncio.to_thread(
        service.forms().batchUpdate(formId=form_id, body=body).execute
    )

    replies = result.get("replies", [])
    edit_url = f"https://docs.google.com/forms/d/{form_id}/edit"

    confirmation_message = f"""Batch Update Completed:
- Form ID: {form_id}
- URL: {edit_url}
- Requests Applied: {len(requests)}
- Replies Received: {len(replies)}"""

    structured_replies = []
    if replies:
        confirmation_message += "\n\nUpdate Results:"
        for i, reply in enumerate(replies, 1):
            if "createItem" in reply:
                item_id = reply["createItem"].get("itemId", "Unknown")
                question_ids = reply["createItem"].get("questionId", [])
                question_info = (
                    f" (Question IDs: {', '.join(question_ids)})"
                    if question_ids
                    else ""
                )
                confirmation_message += (
                    f"\n  Request {i}: Created item {item_id}{question_info}"
                )
                structured_replies.append(
                    FormsBatchUpdateReply(
                        request_index=i,
                        operation="createItem",
                        item_id=item_id,
                        question_ids=question_ids if question_ids else [],
                    )
                )
            else:
                confirmation_message += f"\n  Request {i}: Operation completed"
                structured_replies.append(
                    FormsBatchUpdateReply(
                        request_index=i,
                        operation="completed",
                    )
                )

    structured_result = FormsBatchUpdateResult(
        form_id=form_id,
        edit_url=edit_url,
        requests_applied=len(requests),
        replies_received=len(replies),
        replies=structured_replies,
    )

    return confirmation_message, structured_result


@server.tool(output_schema=FORMS_BATCH_UPDATE_RESULT_SCHEMA)
@handle_http_errors("batch_update_form", service_type="forms")
@require_google_service("forms", "forms")
async def batch_update_form(
    service,
    user_google_email: str,
    form_id: str,
    requests: List[Dict[str, Any]],
) -> ToolResult:
    """
    Apply batch updates to a Google Form.

    Supports adding, updating, and deleting form items, as well as updating
    form metadata and settings. This is the primary method for modifying form
    content after creation.

    Args:
        user_google_email (str): The user's Google email address. Required.
        form_id (str): The ID of the form to update.
        requests (List[Dict[str, Any]]): List of update requests to apply.
            Supported request types:
            - createItem: Add a new question or content item
            - updateItem: Modify an existing item
            - deleteItem: Remove an item
            - moveItem: Reorder an item
            - updateFormInfo: Update form title/description
            - updateSettings: Modify form settings (e.g., quiz mode)

    Returns:
        ToolResult: Details about the batch update operation results.
        Also includes structured_content for machine parsing.
    """
    logger.info(
        f"[batch_update_form] Invoked. Email: '{user_google_email}', "
        f"Form ID: '{form_id}', Requests: {len(requests)}"
    )

    text_result, structured_result = await _batch_update_form_impl(
        service, form_id, requests
    )

    logger.info(f"Batch update completed successfully for {user_google_email}")
    return create_tool_result(text=text_result, data=structured_result)
