"""
Google Apps Script Data Models for Structured Output

Dataclass models representing the structured data returned by Apps Script tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from core.structured_output import generate_schema


@dataclass
class ScriptProjectSummary:
    """Summary of a script project from list results."""

    script_id: str
    title: str
    created_time: str
    modified_time: str


@dataclass
class ListScriptProjectsResult:
    """Structured result from list_script_projects."""

    total_found: int
    projects: list[ScriptProjectSummary]
    next_page_token: Optional[str] = None


@dataclass
class ScriptFile:
    """A file within a script project."""

    name: str
    file_type: str
    source_preview: Optional[str] = None


@dataclass
class GetScriptProjectResult:
    """Structured result from get_script_project."""

    script_id: str
    title: str
    creator: str
    created_time: str
    modified_time: str
    files: list[ScriptFile]


@dataclass
class GetScriptContentResult:
    """Structured result from get_script_content."""

    script_id: str
    file_name: str
    file_type: str
    source: str
    found: bool = True


@dataclass
class CreateScriptProjectResult:
    """Structured result from create_script_project."""

    script_id: str
    title: str
    edit_url: str


@dataclass
class UpdatedFile:
    """A file that was updated in a script project."""

    name: str
    file_type: str


@dataclass
class UpdateScriptContentResult:
    """Structured result from update_script_content."""

    script_id: str
    files_updated: int
    files: list[UpdatedFile]


@dataclass
class RunScriptFunctionResult:
    """Structured result from run_script_function."""

    function_name: str
    success: bool
    result: Optional[Any] = None
    error_message: Optional[str] = None


@dataclass
class CreateDeploymentResult:
    """Structured result from create_deployment."""

    script_id: str
    deployment_id: str
    version_number: int
    description: str


@dataclass
class DeploymentSummary:
    """Summary of a deployment from list results."""

    deployment_id: str
    description: str
    update_time: str


@dataclass
class ListDeploymentsResult:
    """Structured result from list_deployments."""

    script_id: str
    total_found: int
    deployments: list[DeploymentSummary]


@dataclass
class UpdateDeploymentResult:
    """Structured result from update_deployment."""

    script_id: str
    deployment_id: str
    description: str


@dataclass
class DeleteDeploymentResult:
    """Structured result from delete_deployment."""

    script_id: str
    deployment_id: str
    deleted: bool = True


@dataclass
class ProcessSummary:
    """Summary of a script execution process."""

    function_name: str
    process_status: str
    start_time: str
    duration: str


@dataclass
class ListScriptProcessesResult:
    """Structured result from list_script_processes."""

    total_found: int
    script_id: Optional[str] = None
    processes: list[ProcessSummary] = field(default_factory=list)


@dataclass
class DeleteScriptProjectResult:
    """Structured result from delete_script_project."""

    script_id: str
    deleted: bool = True


@dataclass
class VersionSummary:
    """Summary of a script version."""

    version_number: int
    description: str
    create_time: str


@dataclass
class ListVersionsResult:
    """Structured result from list_versions."""

    script_id: str
    total_found: int
    versions: list[VersionSummary]


@dataclass
class CreateVersionResult:
    """Structured result from create_version."""

    script_id: str
    version_number: int
    description: str
    create_time: str


@dataclass
class GetVersionResult:
    """Structured result from get_version."""

    script_id: str
    version_number: int
    description: str
    create_time: str


@dataclass
class MetricDataPoint:
    """A single metric data point."""

    start_time: str
    end_time: str
    value: str


@dataclass
class GetScriptMetricsResult:
    """Structured result from get_script_metrics."""

    script_id: str
    granularity: str
    active_users: list[MetricDataPoint] = field(default_factory=list)
    total_executions: list[MetricDataPoint] = field(default_factory=list)
    failed_executions: list[MetricDataPoint] = field(default_factory=list)


@dataclass
class GenerateTriggerCodeResult:
    """Structured result from generate_trigger_code."""

    trigger_type: str
    function_name: str
    schedule: str
    code: str
    is_simple_trigger: bool


# Pre-generated JSON schemas for use in @server.tool() decorators
LIST_SCRIPT_PROJECTS_SCHEMA = generate_schema(ListScriptProjectsResult)
GET_SCRIPT_PROJECT_SCHEMA = generate_schema(GetScriptProjectResult)
GET_SCRIPT_CONTENT_SCHEMA = generate_schema(GetScriptContentResult)
CREATE_SCRIPT_PROJECT_SCHEMA = generate_schema(CreateScriptProjectResult)
UPDATE_SCRIPT_CONTENT_SCHEMA = generate_schema(UpdateScriptContentResult)
RUN_SCRIPT_FUNCTION_SCHEMA = generate_schema(RunScriptFunctionResult)
CREATE_DEPLOYMENT_SCHEMA = generate_schema(CreateDeploymentResult)
LIST_DEPLOYMENTS_SCHEMA = generate_schema(ListDeploymentsResult)
UPDATE_DEPLOYMENT_SCHEMA = generate_schema(UpdateDeploymentResult)
DELETE_DEPLOYMENT_SCHEMA = generate_schema(DeleteDeploymentResult)
LIST_SCRIPT_PROCESSES_SCHEMA = generate_schema(ListScriptProcessesResult)
DELETE_SCRIPT_PROJECT_SCHEMA = generate_schema(DeleteScriptProjectResult)
LIST_VERSIONS_SCHEMA = generate_schema(ListVersionsResult)
CREATE_VERSION_SCHEMA = generate_schema(CreateVersionResult)
GET_VERSION_SCHEMA = generate_schema(GetVersionResult)
GET_SCRIPT_METRICS_SCHEMA = generate_schema(GetScriptMetricsResult)
GENERATE_TRIGGER_CODE_SCHEMA = generate_schema(GenerateTriggerCodeResult)
