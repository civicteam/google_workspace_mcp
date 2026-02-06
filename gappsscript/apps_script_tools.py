"""
Google Apps Script MCP Tools

This module provides MCP tools for interacting with Google Apps Script API.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional

from fastmcp.tools.tool import ToolResult

from auth.service_decorator import require_google_service
from core.server import server
from core.structured_output import create_tool_result
from core.utils import handle_http_errors
from gappsscript.apps_script_models import (
    ScriptProjectSummary,
    ListScriptProjectsResult,
    ScriptFile,
    GetScriptProjectResult,
    GetScriptContentResult,
    CreateScriptProjectResult,
    UpdatedFile,
    UpdateScriptContentResult,
    RunScriptFunctionResult,
    CreateDeploymentResult,
    DeploymentSummary,
    ListDeploymentsResult,
    UpdateDeploymentResult,
    DeleteDeploymentResult,
    ProcessSummary,
    ListScriptProcessesResult,
    DeleteScriptProjectResult,
    VersionSummary,
    ListVersionsResult,
    CreateVersionResult,
    GetVersionResult,
    MetricDataPoint,
    GetScriptMetricsResult,
    GenerateTriggerCodeResult,
    LIST_SCRIPT_PROJECTS_SCHEMA,
    GET_SCRIPT_PROJECT_SCHEMA,
    GET_SCRIPT_CONTENT_SCHEMA,
    CREATE_SCRIPT_PROJECT_SCHEMA,
    UPDATE_SCRIPT_CONTENT_SCHEMA,
    RUN_SCRIPT_FUNCTION_SCHEMA,
    CREATE_DEPLOYMENT_SCHEMA,
    LIST_DEPLOYMENTS_SCHEMA,
    UPDATE_DEPLOYMENT_SCHEMA,
    DELETE_DEPLOYMENT_SCHEMA,
    LIST_SCRIPT_PROCESSES_SCHEMA,
    DELETE_SCRIPT_PROJECT_SCHEMA,
    LIST_VERSIONS_SCHEMA,
    CREATE_VERSION_SCHEMA,
    GET_VERSION_SCHEMA,
    GET_SCRIPT_METRICS_SCHEMA,
    GENERATE_TRIGGER_CODE_SCHEMA,
)

logger = logging.getLogger(__name__)


# Internal implementation functions for testing
async def _list_script_projects_impl(
    service: Any,
    user_google_email: str,
    page_size: int = 50,
    page_token: Optional[str] = None,
) -> tuple[str, ListScriptProjectsResult]:
    """Internal implementation for list_script_projects.

    Uses Drive API to find Apps Script files since the Script API
    does not have a projects.list method.
    """
    logger.info(
        f"[list_script_projects] Email: {user_google_email}, PageSize: {page_size}"
    )

    # Search for Apps Script files using Drive API
    query = "mimeType='application/vnd.google-apps.script' and trashed=false"
    request_params = {
        "q": query,
        "pageSize": page_size,
        "fields": "nextPageToken, files(id, name, createdTime, modifiedTime)",
        "orderBy": "modifiedTime desc",
    }
    if page_token:
        request_params["pageToken"] = page_token

    response = await asyncio.to_thread(service.files().list(**request_params).execute)

    files = response.get("files", [])
    next_page_token = response.get("nextPageToken")

    if not files:
        structured = ListScriptProjectsResult(
            total_found=0, projects=[], next_page_token=next_page_token
        )
        return "No Apps Script projects found.", structured

    output = [f"Found {len(files)} Apps Script projects:"]
    project_summaries = []
    for file in files:
        title = file.get("name", "Untitled")
        script_id = file.get("id", "Unknown ID")
        create_time = file.get("createdTime", "Unknown")
        update_time = file.get("modifiedTime", "Unknown")

        output.append(
            f"- {title} (ID: {script_id}) Created: {create_time} Modified: {update_time}"
        )
        project_summaries.append(
            ScriptProjectSummary(
                script_id=script_id,
                title=title,
                created_time=create_time,
                modified_time=update_time,
            )
        )

    if next_page_token:
        output.append(f"\nNext page token: {next_page_token}")

    logger.info(
        f"[list_script_projects] Found {len(files)} projects for {user_google_email}"
    )

    structured = ListScriptProjectsResult(
        total_found=len(project_summaries),
        projects=project_summaries,
        next_page_token=next_page_token,
    )
    return "\n".join(output), structured


@server.tool(output_schema=LIST_SCRIPT_PROJECTS_SCHEMA)
@handle_http_errors("list_script_projects", is_read_only=True, service_type="drive")
@require_google_service("drive", "drive_read")
async def list_script_projects(
    service: Any,
    user_google_email: str,
    page_size: int = 50,
    page_token: Optional[str] = None,
) -> ToolResult:
    """
    Lists Google Apps Script projects accessible to the user.

    Uses Drive API to find Apps Script files.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        page_size: Number of results per page (default: 50)
        page_token: Token for pagination (optional)

    Returns:
        ToolResult: Formatted list of script projects with structured data
    """
    text, structured = await _list_script_projects_impl(
        service, user_google_email, page_size, page_token
    )
    return create_tool_result(text=text, data=structured)


async def _get_script_project_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
) -> tuple[str, GetScriptProjectResult]:
    """Internal implementation for get_script_project."""
    logger.info(f"[get_script_project] Email: {user_google_email}, ID: {script_id}")

    project = await asyncio.to_thread(
        service.projects().get(scriptId=script_id).execute
    )

    title = project.get("title", "Untitled")
    project_script_id = project.get("scriptId", "Unknown")
    creator = project.get("creator", {}).get("email", "Unknown")
    create_time = project.get("createTime", "Unknown")
    update_time = project.get("updateTime", "Unknown")

    output = [
        f"Project: {title} (ID: {project_script_id})",
        f"Creator: {creator}",
        f"Created: {create_time}",
        f"Modified: {update_time}",
        "",
        "Files:",
    ]

    files = project.get("files", [])
    script_files = []
    for i, file in enumerate(files, 1):
        file_name = file.get("name", "Untitled")
        file_type = file.get("type", "Unknown")
        source = file.get("source", "")

        output.append(f"{i}. {file_name} ({file_type})")
        source_preview = None
        if source:
            source_preview = source[:200] + ("..." if len(source) > 200 else "")
            output.append(f"   {source_preview}")
            output.append("")

        script_files.append(
            ScriptFile(
                name=file_name, file_type=file_type, source_preview=source_preview
            )
        )

    logger.info(f"[get_script_project] Retrieved project {script_id}")

    structured = GetScriptProjectResult(
        script_id=project_script_id,
        title=title,
        creator=creator,
        created_time=create_time,
        modified_time=update_time,
        files=script_files,
    )
    return "\n".join(output), structured


@server.tool(output_schema=GET_SCRIPT_PROJECT_SCHEMA)
@handle_http_errors("get_script_project", is_read_only=True, service_type="script")
@require_google_service("script", "script_readonly")
async def get_script_project(
    service: Any,
    user_google_email: str,
    script_id: str,
) -> ToolResult:
    """
    Retrieves complete project details including all source files.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID

    Returns:
        ToolResult: Formatted project details with all file contents and structured data
    """
    text, structured = await _get_script_project_impl(
        service, user_google_email, script_id
    )
    return create_tool_result(text=text, data=structured)


async def _get_script_content_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
    file_name: str,
) -> tuple[str, GetScriptContentResult]:
    """Internal implementation for get_script_content."""
    logger.info(
        f"[get_script_content] Email: {user_google_email}, ID: {script_id}, File: {file_name}"
    )

    project = await asyncio.to_thread(
        service.projects().get(scriptId=script_id).execute
    )

    files = project.get("files", [])
    target_file = None

    for file in files:
        if file.get("name") == file_name:
            target_file = file
            break

    if not target_file:
        text = f"File '{file_name}' not found in project {script_id}"
        structured = GetScriptContentResult(
            script_id=script_id,
            file_name=file_name,
            file_type="Unknown",
            source="",
            found=False,
        )
        return text, structured

    source = target_file.get("source", "")
    file_type = target_file.get("type", "Unknown")

    output = [f"File: {file_name} ({file_type})", "", source]

    logger.info(f"[get_script_content] Retrieved file {file_name} from {script_id}")

    structured = GetScriptContentResult(
        script_id=script_id,
        file_name=file_name,
        file_type=file_type,
        source=source,
        found=True,
    )
    return "\n".join(output), structured


@server.tool(output_schema=GET_SCRIPT_CONTENT_SCHEMA)
@handle_http_errors("get_script_content", is_read_only=True, service_type="script")
@require_google_service("script", "script_readonly")
async def get_script_content(
    service: Any,
    user_google_email: str,
    script_id: str,
    file_name: str,
) -> ToolResult:
    """
    Retrieves content of a specific file within a project.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID
        file_name: Name of the file to retrieve

    Returns:
        ToolResult: File content with structured data
    """
    text, structured = await _get_script_content_impl(
        service, user_google_email, script_id, file_name
    )
    return create_tool_result(text=text, data=structured)


async def _create_script_project_impl(
    service: Any,
    user_google_email: str,
    title: str,
    parent_id: Optional[str] = None,
) -> tuple[str, CreateScriptProjectResult]:
    """Internal implementation for create_script_project."""
    logger.info(f"[create_script_project] Email: {user_google_email}, Title: {title}")

    request_body = {"title": title}

    if parent_id:
        request_body["parentId"] = parent_id

    project = await asyncio.to_thread(
        service.projects().create(body=request_body).execute
    )

    script_id = project.get("scriptId", "Unknown")
    edit_url = f"https://script.google.com/d/{script_id}/edit"

    output = [
        f"Created Apps Script project: {title}",
        f"Script ID: {script_id}",
        f"Edit URL: {edit_url}",
    ]

    logger.info(f"[create_script_project] Created project {script_id}")

    structured = CreateScriptProjectResult(
        script_id=script_id,
        title=title,
        edit_url=edit_url,
    )
    return "\n".join(output), structured


@server.tool(output_schema=CREATE_SCRIPT_PROJECT_SCHEMA)
@handle_http_errors("create_script_project", service_type="script")
@require_google_service("script", "script_projects")
async def create_script_project(
    service: Any,
    user_google_email: str,
    title: str,
    parent_id: Optional[str] = None,
) -> ToolResult:
    """
    Creates a new Apps Script project.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        title: Project title
        parent_id: Optional Drive folder ID or bound container ID

    Returns:
        ToolResult: Formatted string with new project details and structured data
    """
    text, structured = await _create_script_project_impl(
        service, user_google_email, title, parent_id
    )
    return create_tool_result(text=text, data=structured)


async def _update_script_content_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
    files: List[Dict[str, str]],
) -> tuple[str, UpdateScriptContentResult]:
    """Internal implementation for update_script_content."""
    logger.info(
        f"[update_script_content] Email: {user_google_email}, ID: {script_id}, Files: {len(files)}"
    )

    request_body = {"files": files}

    updated_content = await asyncio.to_thread(
        service.projects().updateContent(scriptId=script_id, body=request_body).execute
    )

    output = [f"Updated script project: {script_id}", "", "Modified files:"]

    updated_files = []
    for file in updated_content.get("files", []):
        file_name = file.get("name", "Untitled")
        file_type = file.get("type", "Unknown")
        output.append(f"- {file_name} ({file_type})")
        updated_files.append(UpdatedFile(name=file_name, file_type=file_type))

    logger.info(f"[update_script_content] Updated {len(files)} files in {script_id}")

    structured = UpdateScriptContentResult(
        script_id=script_id,
        files_updated=len(updated_files),
        files=updated_files,
    )
    return "\n".join(output), structured


@server.tool(output_schema=UPDATE_SCRIPT_CONTENT_SCHEMA)
@handle_http_errors("update_script_content", service_type="script")
@require_google_service("script", "script_projects")
async def update_script_content(
    service: Any,
    user_google_email: str,
    script_id: str,
    files: List[Dict[str, str]],
) -> ToolResult:
    """
    Updates or creates files in a script project.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID
        files: List of file objects with name, type, and source

    Returns:
        ToolResult: Formatted string confirming update with file list and structured data
    """
    text, structured = await _update_script_content_impl(
        service, user_google_email, script_id, files
    )
    return create_tool_result(text=text, data=structured)


async def _run_script_function_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
    function_name: str,
    parameters: Optional[List[Any]] = None,
    dev_mode: bool = False,
) -> tuple[str, RunScriptFunctionResult]:
    """Internal implementation for run_script_function."""
    logger.info(
        f"[run_script_function] Email: {user_google_email}, ID: {script_id}, Function: {function_name}"
    )

    request_body = {"function": function_name, "devMode": dev_mode}

    if parameters:
        request_body["parameters"] = parameters

    try:
        response = await asyncio.to_thread(
            service.scripts().run(scriptId=script_id, body=request_body).execute
        )

        if "error" in response:
            error_details = response["error"]
            error_message = error_details.get("message", "Unknown error")
            text = (
                f"Execution failed\nFunction: {function_name}\nError: {error_message}"
            )
            structured = RunScriptFunctionResult(
                function_name=function_name,
                success=False,
                error_message=error_message,
            )
            return text, structured

        result = response.get("response", {}).get("result")
        output = [
            "Execution successful",
            f"Function: {function_name}",
            f"Result: {result}",
        ]

        logger.info(f"[run_script_function] Successfully executed {function_name}")

        structured = RunScriptFunctionResult(
            function_name=function_name,
            success=True,
            result=result,
        )
        return "\n".join(output), structured

    except Exception as e:
        logger.error(f"[run_script_function] Execution error: {str(e)}")
        text = f"Execution failed\nFunction: {function_name}\nError: {str(e)}"
        structured = RunScriptFunctionResult(
            function_name=function_name,
            success=False,
            error_message=str(e),
        )
        return text, structured


@server.tool(output_schema=RUN_SCRIPT_FUNCTION_SCHEMA)
@handle_http_errors("run_script_function", service_type="script")
@require_google_service("script", "script_projects")
async def run_script_function(
    service: Any,
    user_google_email: str,
    script_id: str,
    function_name: str,
    parameters: Optional[List[Any]] = None,
    dev_mode: bool = False,
) -> ToolResult:
    """
    Executes a function in a deployed script.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID
        function_name: Name of function to execute
        parameters: Optional list of parameters to pass
        dev_mode: Whether to run latest code vs deployed version

    Returns:
        ToolResult: Formatted string with execution result or error and structured data
    """
    text, structured = await _run_script_function_impl(
        service, user_google_email, script_id, function_name, parameters, dev_mode
    )
    return create_tool_result(text=text, data=structured)


async def _create_deployment_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
    description: str,
    version_description: Optional[str] = None,
) -> tuple[str, CreateDeploymentResult]:
    """Internal implementation for create_deployment.

    Creates a new version first, then creates a deployment using that version.
    """
    logger.info(
        f"[create_deployment] Email: {user_google_email}, ID: {script_id}, Desc: {description}"
    )

    # First, create a new version
    version_body = {"description": version_description or description}
    version = await asyncio.to_thread(
        service.projects()
        .versions()
        .create(scriptId=script_id, body=version_body)
        .execute
    )
    version_number = version.get("versionNumber")
    logger.info(f"[create_deployment] Created version {version_number}")

    # Now create the deployment with the version number
    deployment_body = {
        "versionNumber": version_number,
        "description": description,
    }

    deployment = await asyncio.to_thread(
        service.projects()
        .deployments()
        .create(scriptId=script_id, body=deployment_body)
        .execute
    )

    deployment_id = deployment.get("deploymentId", "Unknown")

    output = [
        f"Created deployment for script: {script_id}",
        f"Deployment ID: {deployment_id}",
        f"Version: {version_number}",
        f"Description: {description}",
    ]

    logger.info(f"[create_deployment] Created deployment {deployment_id}")

    structured = CreateDeploymentResult(
        script_id=script_id,
        deployment_id=deployment_id,
        version_number=version_number,
        description=description,
    )
    return "\n".join(output), structured


@server.tool(output_schema=CREATE_DEPLOYMENT_SCHEMA)
@handle_http_errors("create_deployment", service_type="script")
@require_google_service("script", "script_deployments")
async def create_deployment(
    service: Any,
    user_google_email: str,
    script_id: str,
    description: str,
    version_description: Optional[str] = None,
) -> ToolResult:
    """
    Creates a new deployment of the script.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID
        description: Deployment description
        version_description: Optional version description

    Returns:
        ToolResult: Formatted string with deployment details and structured data
    """
    text, structured = await _create_deployment_impl(
        service, user_google_email, script_id, description, version_description
    )
    return create_tool_result(text=text, data=structured)


async def _list_deployments_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
) -> tuple[str, ListDeploymentsResult]:
    """Internal implementation for list_deployments."""
    logger.info(f"[list_deployments] Email: {user_google_email}, ID: {script_id}")

    response = await asyncio.to_thread(
        service.projects().deployments().list(scriptId=script_id).execute
    )

    deployments = response.get("deployments", [])

    if not deployments:
        structured = ListDeploymentsResult(
            script_id=script_id, total_found=0, deployments=[]
        )
        return f"No deployments found for script: {script_id}", structured

    output = [f"Deployments for script: {script_id}", ""]

    deployment_summaries = []
    for i, deployment in enumerate(deployments, 1):
        deployment_id = deployment.get("deploymentId", "Unknown")
        description = deployment.get("description", "No description")
        update_time = deployment.get("updateTime", "Unknown")

        output.append(f"{i}. {description} ({deployment_id})")
        output.append(f"   Updated: {update_time}")
        output.append("")

        deployment_summaries.append(
            DeploymentSummary(
                deployment_id=deployment_id,
                description=description,
                update_time=update_time,
            )
        )

    logger.info(f"[list_deployments] Found {len(deployments)} deployments")

    structured = ListDeploymentsResult(
        script_id=script_id,
        total_found=len(deployment_summaries),
        deployments=deployment_summaries,
    )
    return "\n".join(output), structured


@server.tool(output_schema=LIST_DEPLOYMENTS_SCHEMA)
@handle_http_errors("list_deployments", is_read_only=True, service_type="script")
@require_google_service("script", "script_deployments_readonly")
async def list_deployments(
    service: Any,
    user_google_email: str,
    script_id: str,
) -> ToolResult:
    """
    Lists all deployments for a script project.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID

    Returns:
        ToolResult: Formatted string with deployment list and structured data
    """
    text, structured = await _list_deployments_impl(
        service, user_google_email, script_id
    )
    return create_tool_result(text=text, data=structured)


async def _update_deployment_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
    deployment_id: str,
    description: Optional[str] = None,
) -> tuple[str, UpdateDeploymentResult]:
    """Internal implementation for update_deployment."""
    logger.info(
        f"[update_deployment] Email: {user_google_email}, Script: {script_id}, Deployment: {deployment_id}"
    )

    request_body = {}
    if description:
        request_body["description"] = description

    deployment = await asyncio.to_thread(
        service.projects()
        .deployments()
        .update(scriptId=script_id, deploymentId=deployment_id, body=request_body)
        .execute
    )

    final_description = deployment.get("description", "No description")

    output = [
        f"Updated deployment: {deployment_id}",
        f"Script: {script_id}",
        f"Description: {final_description}",
    ]

    logger.info(f"[update_deployment] Updated deployment {deployment_id}")

    structured = UpdateDeploymentResult(
        script_id=script_id,
        deployment_id=deployment_id,
        description=final_description,
    )
    return "\n".join(output), structured


@server.tool(output_schema=UPDATE_DEPLOYMENT_SCHEMA)
@handle_http_errors("update_deployment", service_type="script")
@require_google_service("script", "script_deployments")
async def update_deployment(
    service: Any,
    user_google_email: str,
    script_id: str,
    deployment_id: str,
    description: Optional[str] = None,
) -> ToolResult:
    """
    Updates an existing deployment configuration.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID
        deployment_id: The deployment ID to update
        description: Optional new description

    Returns:
        ToolResult: Formatted string confirming update with structured data
    """
    text, structured = await _update_deployment_impl(
        service, user_google_email, script_id, deployment_id, description
    )
    return create_tool_result(text=text, data=structured)


async def _delete_deployment_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
    deployment_id: str,
) -> tuple[str, DeleteDeploymentResult]:
    """Internal implementation for delete_deployment."""
    logger.info(
        f"[delete_deployment] Email: {user_google_email}, Script: {script_id}, Deployment: {deployment_id}"
    )

    await asyncio.to_thread(
        service.projects()
        .deployments()
        .delete(scriptId=script_id, deploymentId=deployment_id)
        .execute
    )

    output = f"Deleted deployment: {deployment_id} from script: {script_id}"

    logger.info(f"[delete_deployment] Deleted deployment {deployment_id}")

    structured = DeleteDeploymentResult(
        script_id=script_id,
        deployment_id=deployment_id,
        deleted=True,
    )
    return output, structured


@server.tool(output_schema=DELETE_DEPLOYMENT_SCHEMA)
@handle_http_errors("delete_deployment", service_type="script")
@require_google_service("script", "script_deployments")
async def delete_deployment(
    service: Any,
    user_google_email: str,
    script_id: str,
    deployment_id: str,
) -> ToolResult:
    """
    Deletes a deployment.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID
        deployment_id: The deployment ID to delete

    Returns:
        ToolResult: Confirmation message with structured data
    """
    text, structured = await _delete_deployment_impl(
        service, user_google_email, script_id, deployment_id
    )
    return create_tool_result(text=text, data=structured)


async def _list_script_processes_impl(
    service: Any,
    user_google_email: str,
    page_size: int = 50,
    script_id: Optional[str] = None,
) -> tuple[str, ListScriptProcessesResult]:
    """Internal implementation for list_script_processes."""
    logger.info(
        f"[list_script_processes] Email: {user_google_email}, PageSize: {page_size}"
    )

    request_params = {"pageSize": page_size}
    if script_id:
        request_params["scriptId"] = script_id

    response = await asyncio.to_thread(
        service.processes().list(**request_params).execute
    )

    processes = response.get("processes", [])

    if not processes:
        structured = ListScriptProcessesResult(
            total_found=0, script_id=script_id, processes=[]
        )
        return "No recent script executions found.", structured

    output = ["Recent script executions:", ""]

    process_summaries = []
    for i, process in enumerate(processes, 1):
        function_name = process.get("functionName", "Unknown")
        process_status = process.get("processStatus", "Unknown")
        start_time = process.get("startTime", "Unknown")
        duration = process.get("duration", "Unknown")

        output.append(f"{i}. {function_name}")
        output.append(f"   Status: {process_status}")
        output.append(f"   Started: {start_time}")
        output.append(f"   Duration: {duration}")
        output.append("")

        process_summaries.append(
            ProcessSummary(
                function_name=function_name,
                process_status=process_status,
                start_time=start_time,
                duration=duration,
            )
        )

    logger.info(f"[list_script_processes] Found {len(processes)} processes")

    structured = ListScriptProcessesResult(
        total_found=len(process_summaries),
        script_id=script_id,
        processes=process_summaries,
    )
    return "\n".join(output), structured


@server.tool(output_schema=LIST_SCRIPT_PROCESSES_SCHEMA)
@handle_http_errors("list_script_processes", is_read_only=True, service_type="script")
@require_google_service("script", "script_readonly")
async def list_script_processes(
    service: Any,
    user_google_email: str,
    page_size: int = 50,
    script_id: Optional[str] = None,
) -> ToolResult:
    """
    Lists recent execution processes for user's scripts.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        page_size: Number of results (default: 50)
        script_id: Optional filter by script ID

    Returns:
        ToolResult: Formatted string with process list and structured data
    """
    text, structured = await _list_script_processes_impl(
        service, user_google_email, page_size, script_id
    )
    return create_tool_result(text=text, data=structured)


# ============================================================================
# Delete Script Project
# ============================================================================


async def _delete_script_project_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
) -> tuple[str, DeleteScriptProjectResult]:
    """Internal implementation for delete_script_project."""
    logger.info(
        f"[delete_script_project] Email: {user_google_email}, ScriptID: {script_id}"
    )

    # Apps Script projects are stored as Drive files
    await asyncio.to_thread(service.files().delete(fileId=script_id).execute)

    logger.info(f"[delete_script_project] Deleted script {script_id}")

    structured = DeleteScriptProjectResult(script_id=script_id, deleted=True)
    return f"Deleted Apps Script project: {script_id}", structured


@server.tool(output_schema=DELETE_SCRIPT_PROJECT_SCHEMA)
@handle_http_errors("delete_script_project", is_read_only=False, service_type="drive")
@require_google_service("drive", "drive_full")
async def delete_script_project(
    service: Any,
    user_google_email: str,
    script_id: str,
) -> ToolResult:
    """
    Deletes an Apps Script project.

    This permanently deletes the script project. The action cannot be undone.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID to delete

    Returns:
        ToolResult: Confirmation message with structured data
    """
    text, structured = await _delete_script_project_impl(
        service, user_google_email, script_id
    )
    return create_tool_result(text=text, data=structured)


# ============================================================================
# Version Management
# ============================================================================


async def _list_versions_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
) -> tuple[str, ListVersionsResult]:
    """Internal implementation for list_versions."""
    logger.info(f"[list_versions] Email: {user_google_email}, ScriptID: {script_id}")

    response = await asyncio.to_thread(
        service.projects().versions().list(scriptId=script_id).execute
    )

    versions = response.get("versions", [])

    if not versions:
        structured = ListVersionsResult(script_id=script_id, total_found=0, versions=[])
        return f"No versions found for script: {script_id}", structured

    output = [f"Versions for script: {script_id}", ""]

    version_summaries = []
    for version in versions:
        version_number = version.get("versionNumber", "Unknown")
        description = version.get("description", "No description")
        create_time = version.get("createTime", "Unknown")

        output.append(f"Version {version_number}: {description}")
        output.append(f"   Created: {create_time}")
        output.append("")

        version_summaries.append(
            VersionSummary(
                version_number=version_number,
                description=description,
                create_time=create_time,
            )
        )

    logger.info(f"[list_versions] Found {len(versions)} versions")

    structured = ListVersionsResult(
        script_id=script_id,
        total_found=len(version_summaries),
        versions=version_summaries,
    )
    return "\n".join(output), structured


@server.tool(output_schema=LIST_VERSIONS_SCHEMA)
@handle_http_errors("list_versions", is_read_only=True, service_type="script")
@require_google_service("script", "script_readonly")
async def list_versions(
    service: Any,
    user_google_email: str,
    script_id: str,
) -> ToolResult:
    """
    Lists all versions of a script project.

    Versions are immutable snapshots of your script code.
    They are created when you deploy or explicitly create a version.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID

    Returns:
        ToolResult: Formatted string with version list and structured data
    """
    text, structured = await _list_versions_impl(service, user_google_email, script_id)
    return create_tool_result(text=text, data=structured)


async def _create_version_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
    description: Optional[str] = None,
) -> tuple[str, CreateVersionResult]:
    """Internal implementation for create_version."""
    logger.info(f"[create_version] Email: {user_google_email}, ScriptID: {script_id}")

    request_body = {}
    if description:
        request_body["description"] = description

    version = await asyncio.to_thread(
        service.projects()
        .versions()
        .create(scriptId=script_id, body=request_body)
        .execute
    )

    version_number = version.get("versionNumber", "Unknown")
    create_time = version.get("createTime", "Unknown")
    final_description = description or "No description"

    output = [
        f"Created version {version_number} for script: {script_id}",
        f"Description: {final_description}",
        f"Created: {create_time}",
    ]

    logger.info(f"[create_version] Created version {version_number}")

    structured = CreateVersionResult(
        script_id=script_id,
        version_number=version_number,
        description=final_description,
        create_time=create_time,
    )
    return "\n".join(output), structured


@server.tool(output_schema=CREATE_VERSION_SCHEMA)
@handle_http_errors("create_version", is_read_only=False, service_type="script")
@require_google_service("script", "script_full")
async def create_version(
    service: Any,
    user_google_email: str,
    script_id: str,
    description: Optional[str] = None,
) -> ToolResult:
    """
    Creates a new immutable version of a script project.

    Versions capture a snapshot of the current script code.
    Once created, versions cannot be modified.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID
        description: Optional description for this version

    Returns:
        ToolResult: Formatted string with new version details and structured data
    """
    text, structured = await _create_version_impl(
        service, user_google_email, script_id, description
    )
    return create_tool_result(text=text, data=structured)


async def _get_version_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
    version_number: int,
) -> tuple[str, GetVersionResult]:
    """Internal implementation for get_version."""
    logger.info(
        f"[get_version] Email: {user_google_email}, ScriptID: {script_id}, Version: {version_number}"
    )

    version = await asyncio.to_thread(
        service.projects()
        .versions()
        .get(scriptId=script_id, versionNumber=version_number)
        .execute
    )

    ver_num = version.get("versionNumber", "Unknown")
    description = version.get("description", "No description")
    create_time = version.get("createTime", "Unknown")

    output = [
        f"Version {ver_num} of script: {script_id}",
        f"Description: {description}",
        f"Created: {create_time}",
    ]

    logger.info(f"[get_version] Retrieved version {ver_num}")

    structured = GetVersionResult(
        script_id=script_id,
        version_number=ver_num,
        description=description,
        create_time=create_time,
    )
    return "\n".join(output), structured


@server.tool(output_schema=GET_VERSION_SCHEMA)
@handle_http_errors("get_version", is_read_only=True, service_type="script")
@require_google_service("script", "script_readonly")
async def get_version(
    service: Any,
    user_google_email: str,
    script_id: str,
    version_number: int,
) -> ToolResult:
    """
    Gets details of a specific version.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID
        version_number: The version number to retrieve (1, 2, 3, etc.)

    Returns:
        ToolResult: Formatted string with version details and structured data
    """
    text, structured = await _get_version_impl(
        service, user_google_email, script_id, version_number
    )
    return create_tool_result(text=text, data=structured)


# ============================================================================
# Metrics
# ============================================================================


async def _get_script_metrics_impl(
    service: Any,
    user_google_email: str,
    script_id: str,
    metrics_granularity: str = "DAILY",
) -> tuple[str, GetScriptMetricsResult]:
    """Internal implementation for get_script_metrics."""
    logger.info(
        f"[get_script_metrics] Email: {user_google_email}, ScriptID: {script_id}, Granularity: {metrics_granularity}"
    )

    request_params = {
        "scriptId": script_id,
        "metricsGranularity": metrics_granularity,
    }

    response = await asyncio.to_thread(
        service.projects().getMetrics(**request_params).execute
    )

    output = [
        f"Metrics for script: {script_id}",
        f"Granularity: {metrics_granularity}",
        "",
    ]

    # Active users
    active_users = response.get("activeUsers", [])
    active_users_data = []
    if active_users:
        output.append("Active Users:")
        for metric in active_users:
            start_time = metric.get("startTime", "Unknown")
            end_time = metric.get("endTime", "Unknown")
            value = metric.get("value", "0")
            output.append(f"  {start_time} to {end_time}: {value} users")
            active_users_data.append(
                MetricDataPoint(start_time=start_time, end_time=end_time, value=value)
            )
        output.append("")

    # Total executions
    total_executions = response.get("totalExecutions", [])
    total_executions_data = []
    if total_executions:
        output.append("Total Executions:")
        for metric in total_executions:
            start_time = metric.get("startTime", "Unknown")
            end_time = metric.get("endTime", "Unknown")
            value = metric.get("value", "0")
            output.append(f"  {start_time} to {end_time}: {value} executions")
            total_executions_data.append(
                MetricDataPoint(start_time=start_time, end_time=end_time, value=value)
            )
        output.append("")

    # Failed executions
    failed_executions = response.get("failedExecutions", [])
    failed_executions_data = []
    if failed_executions:
        output.append("Failed Executions:")
        for metric in failed_executions:
            start_time = metric.get("startTime", "Unknown")
            end_time = metric.get("endTime", "Unknown")
            value = metric.get("value", "0")
            output.append(f"  {start_time} to {end_time}: {value} failures")
            failed_executions_data.append(
                MetricDataPoint(start_time=start_time, end_time=end_time, value=value)
            )
        output.append("")

    if not active_users and not total_executions and not failed_executions:
        output.append("No metrics data available for this script.")

    logger.info(f"[get_script_metrics] Retrieved metrics for {script_id}")

    structured = GetScriptMetricsResult(
        script_id=script_id,
        granularity=metrics_granularity,
        active_users=active_users_data,
        total_executions=total_executions_data,
        failed_executions=failed_executions_data,
    )
    return "\n".join(output), structured


@server.tool(output_schema=GET_SCRIPT_METRICS_SCHEMA)
@handle_http_errors("get_script_metrics", is_read_only=True, service_type="script")
@require_google_service("script", "script_readonly")
async def get_script_metrics(
    service: Any,
    user_google_email: str,
    script_id: str,
    metrics_granularity: str = "DAILY",
) -> ToolResult:
    """
    Gets execution metrics for a script project.

    Returns analytics data including active users, total executions,
    and failed executions over time.

    Args:
        service: Injected Google API service client
        user_google_email: User's email address
        script_id: The script project ID
        metrics_granularity: Granularity of metrics - "DAILY" or "WEEKLY"

    Returns:
        ToolResult: Formatted string with metrics data and structured data
    """
    text, structured = await _get_script_metrics_impl(
        service, user_google_email, script_id, metrics_granularity
    )
    return create_tool_result(text=text, data=structured)


# ============================================================================
# Trigger Code Generation
# ============================================================================


def _generate_trigger_code_impl(
    trigger_type: str,
    function_name: str,
    schedule: str = "",
) -> tuple[str, GenerateTriggerCodeResult]:
    """Internal implementation for generate_trigger_code."""
    code_lines = []
    is_simple_trigger = False

    if trigger_type == "on_open":
        is_simple_trigger = True
        code_lines = [
            "// Simple trigger - just rename your function to 'onOpen'",
            "// This runs automatically when the document is opened",
            "function onOpen(e) {",
            f"  {function_name}();",
            "}",
        ]
    elif trigger_type == "on_edit":
        is_simple_trigger = True
        code_lines = [
            "// Simple trigger - just rename your function to 'onEdit'",
            "// This runs automatically when a user edits the spreadsheet",
            "function onEdit(e) {",
            f"  {function_name}();",
            "}",
        ]
    elif trigger_type == "time_minutes":
        interval = schedule or "5"
        code_lines = [
            "// Run this function ONCE to install the trigger",
            f"function createTimeTrigger_{function_name}() {{",
            "  // Delete existing triggers for this function first",
            "  const triggers = ScriptApp.getProjectTriggers();",
            "  triggers.forEach(trigger => {",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            "      ScriptApp.deleteTrigger(trigger);",
            "    }",
            "  });",
            "",
            f"  // Create new trigger - runs every {interval} minutes",
            f"  ScriptApp.newTrigger('{function_name}')",
            "    .timeBased()",
            f"    .everyMinutes({interval})",
            "    .create();",
            "",
            f"  Logger.log('Trigger created: {function_name} will run every {interval} minutes');",
            "}",
        ]
    elif trigger_type == "time_hours":
        interval = schedule or "1"
        code_lines = [
            "// Run this function ONCE to install the trigger",
            f"function createTimeTrigger_{function_name}() {{",
            "  // Delete existing triggers for this function first",
            "  const triggers = ScriptApp.getProjectTriggers();",
            "  triggers.forEach(trigger => {",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            "      ScriptApp.deleteTrigger(trigger);",
            "    }",
            "  });",
            "",
            f"  // Create new trigger - runs every {interval} hour(s)",
            f"  ScriptApp.newTrigger('{function_name}')",
            "    .timeBased()",
            f"    .everyHours({interval})",
            "    .create();",
            "",
            f"  Logger.log('Trigger created: {function_name} will run every {interval} hour(s)');",
            "}",
        ]
    elif trigger_type == "time_daily":
        hour = schedule or "9"
        code_lines = [
            "// Run this function ONCE to install the trigger",
            f"function createDailyTrigger_{function_name}() {{",
            "  // Delete existing triggers for this function first",
            "  const triggers = ScriptApp.getProjectTriggers();",
            "  triggers.forEach(trigger => {",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            "      ScriptApp.deleteTrigger(trigger);",
            "    }",
            "  });",
            "",
            f"  // Create new trigger - runs daily at {hour}:00",
            f"  ScriptApp.newTrigger('{function_name}')",
            "    .timeBased()",
            f"    .atHour({hour})",
            "    .everyDays(1)",
            "    .create();",
            "",
            f"  Logger.log('Trigger created: {function_name} will run daily at {hour}:00');",
            "}",
        ]
    elif trigger_type == "time_weekly":
        day = schedule.upper() if schedule else "MONDAY"
        code_lines = [
            "// Run this function ONCE to install the trigger",
            f"function createWeeklyTrigger_{function_name}() {{",
            "  // Delete existing triggers for this function first",
            "  const triggers = ScriptApp.getProjectTriggers();",
            "  triggers.forEach(trigger => {",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            "      ScriptApp.deleteTrigger(trigger);",
            "    }",
            "  });",
            "",
            f"  // Create new trigger - runs weekly on {day}",
            f"  ScriptApp.newTrigger('{function_name}')",
            "    .timeBased()",
            f"    .onWeekDay(ScriptApp.WeekDay.{day})",
            "    .atHour(9)",
            "    .create();",
            "",
            f"  Logger.log('Trigger created: {function_name} will run every {day} at 9:00');",
            "}",
        ]
    elif trigger_type == "on_form_submit":
        code_lines = [
            "// Run this function ONCE to install the trigger",
            "// This must be run from a script BOUND to the Google Form",
            f"function createFormSubmitTrigger_{function_name}() {{",
            "  // Delete existing triggers for this function first",
            "  const triggers = ScriptApp.getProjectTriggers();",
            "  triggers.forEach(trigger => {",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            "      ScriptApp.deleteTrigger(trigger);",
            "    }",
            "  });",
            "",
            "  // Create new trigger - runs when form is submitted",
            f"  ScriptApp.newTrigger('{function_name}')",
            "    .forForm(FormApp.getActiveForm())",
            "    .onFormSubmit()",
            "    .create();",
            "",
            f"  Logger.log('Trigger created: {function_name} will run on form submit');",
            "}",
        ]
    elif trigger_type == "on_change":
        code_lines = [
            "// Run this function ONCE to install the trigger",
            "// This must be run from a script BOUND to a Google Sheet",
            f"function createChangeTrigger_{function_name}() {{",
            "  // Delete existing triggers for this function first",
            "  const triggers = ScriptApp.getProjectTriggers();",
            "  triggers.forEach(trigger => {",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            "      ScriptApp.deleteTrigger(trigger);",
            "    }",
            "  });",
            "",
            "  // Create new trigger - runs when spreadsheet changes",
            f"  ScriptApp.newTrigger('{function_name}')",
            "    .forSpreadsheet(SpreadsheetApp.getActive())",
            "    .onChange()",
            "    .create();",
            "",
            f"  Logger.log('Trigger created: {function_name} will run on spreadsheet change');",
            "}",
        ]
    else:
        error_text = (
            f"Unknown trigger type: {trigger_type}\n\n"
            "Valid types: time_minutes, time_hours, time_daily, time_weekly, "
            "on_open, on_edit, on_form_submit, on_change"
        )
        structured = GenerateTriggerCodeResult(
            trigger_type=trigger_type,
            function_name=function_name,
            schedule=schedule,
            code="",
            is_simple_trigger=False,
        )
        return error_text, structured

    code = "\n".join(code_lines)

    instructions = []
    if trigger_type.startswith("on_"):
        if trigger_type in ("on_open", "on_edit"):
            instructions = [
                "SIMPLE TRIGGER",
                "=" * 50,
                "",
                "Add this code to your script. Simple triggers run automatically",
                "when the event occurs - no setup function needed.",
                "",
                "Note: Simple triggers have limitations:",
                "- Cannot access services that require authorization",
                "- Cannot run longer than 30 seconds",
                "- Cannot make external HTTP requests",
                "",
                "For more capabilities, use an installable trigger instead.",
                "",
                "CODE TO ADD:",
                "-" * 50,
            ]
        else:
            instructions = [
                "INSTALLABLE TRIGGER",
                "=" * 50,
                "",
                "1. Add this code to your script",
                f"2. Run the setup function once: createFormSubmitTrigger_{function_name}() or similar",
                "3. The trigger will then run automatically",
                "",
                "CODE TO ADD:",
                "-" * 50,
            ]
    else:
        instructions = [
            "INSTALLABLE TRIGGER",
            "=" * 50,
            "",
            "1. Add this code to your script using update_script_content",
            "2. Run the setup function ONCE (manually in Apps Script editor or via run_script_function)",
            "3. The trigger will then run automatically on schedule",
            "",
            "To check installed triggers: Apps Script editor > Triggers (clock icon)",
            "",
            "CODE TO ADD:",
            "-" * 50,
        ]

    text = "\n".join(instructions) + "\n\n" + code
    structured = GenerateTriggerCodeResult(
        trigger_type=trigger_type,
        function_name=function_name,
        schedule=schedule,
        code=code,
        is_simple_trigger=is_simple_trigger,
    )
    return text, structured


@server.tool(output_schema=GENERATE_TRIGGER_CODE_SCHEMA)
async def generate_trigger_code(
    trigger_type: str,
    function_name: str,
    schedule: str = "",
) -> ToolResult:
    """
    Generates Apps Script code for creating triggers.

    The Apps Script API cannot create triggers directly - they must be created
    from within Apps Script itself. This tool generates the code you need.

    Args:
        trigger_type: Type of trigger. One of:
                      - "time_minutes" (run every N minutes: 1, 5, 10, 15, 30)
                      - "time_hours" (run every N hours: 1, 2, 4, 6, 8, 12)
                      - "time_daily" (run daily at a specific hour: 0-23)
                      - "time_weekly" (run weekly on a specific day)
                      - "on_open" (simple trigger - runs when document opens)
                      - "on_edit" (simple trigger - runs when user edits)
                      - "on_form_submit" (runs when form is submitted)
                      - "on_change" (runs when content changes)

        function_name: The function to run when trigger fires (e.g., "sendDailyReport")

        schedule: Schedule details (depends on trigger_type):
                  - For time_minutes: "1", "5", "10", "15", or "30"
                  - For time_hours: "1", "2", "4", "6", "8", or "12"
                  - For time_daily: hour as "0"-"23" (e.g., "9" for 9am)
                  - For time_weekly: "MONDAY", "TUESDAY", etc.
                  - For simple triggers (on_open, on_edit): not needed

    Returns:
        ToolResult: Apps Script code to create the trigger with structured data
    """
    text, structured = _generate_trigger_code_impl(
        trigger_type, function_name, schedule
    )
    return create_tool_result(text=text, data=structured)
