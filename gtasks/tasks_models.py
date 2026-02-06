"""
Google Tasks Data Models for Structured Output

Dataclass models representing the structured data returned by Google Tasks tools.
These models provide machine-parseable JSON alongside the human-readable text output.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import TypeAdapter


@dataclass
class TaskListSummary:
    """Summary of a task list."""

    id: str
    title: str
    updated: Optional[str] = None
    self_link: Optional[str] = None


@dataclass
class ListTaskListsResult:
    """Structured result from list_task_lists."""

    task_lists: list[TaskListSummary]
    total_count: int
    next_page_token: Optional[str] = None


@dataclass
class GetTaskListResult:
    """Structured result from get_task_list."""

    id: str
    title: str
    updated: Optional[str] = None
    self_link: Optional[str] = None


@dataclass
class CreateTaskListResult:
    """Structured result from create_task_list."""

    id: str
    title: str
    updated: Optional[str] = None
    self_link: Optional[str] = None


@dataclass
class UpdateTaskListResult:
    """Structured result from update_task_list."""

    id: str
    title: str
    updated: Optional[str] = None


@dataclass
class DeleteTaskListResult:
    """Structured result from delete_task_list."""

    task_list_id: str
    deleted: bool


@dataclass
class TaskSummary:
    """Summary of a task."""

    id: str
    title: Optional[str] = None
    status: Optional[str] = None
    due: Optional[str] = None
    notes: Optional[str] = None
    updated: Optional[str] = None
    completed: Optional[str] = None
    parent: Optional[str] = None
    position: Optional[str] = None
    self_link: Optional[str] = None
    web_view_link: Optional[str] = None
    subtasks: list["TaskSummary"] = field(default_factory=list)


@dataclass
class ListTasksResult:
    """Structured result from list_tasks."""

    task_list_id: str
    tasks: list[TaskSummary]
    total_count: int
    next_page_token: Optional[str] = None


@dataclass
class GetTaskResult:
    """Structured result from get_task."""

    id: str
    title: str
    status: Optional[str] = None
    updated: Optional[str] = None
    due: Optional[str] = None
    completed: Optional[str] = None
    notes: Optional[str] = None
    parent: Optional[str] = None
    position: Optional[str] = None
    self_link: Optional[str] = None
    web_view_link: Optional[str] = None


@dataclass
class CreateTaskResult:
    """Structured result from create_task."""

    id: str
    title: str
    status: Optional[str] = None
    updated: Optional[str] = None
    due: Optional[str] = None
    notes: Optional[str] = None
    web_view_link: Optional[str] = None


@dataclass
class UpdateTaskResult:
    """Structured result from update_task."""

    id: str
    title: str
    status: Optional[str] = None
    updated: Optional[str] = None
    due: Optional[str] = None
    notes: Optional[str] = None
    completed: Optional[str] = None


@dataclass
class DeleteTaskResult:
    """Structured result from delete_task."""

    task_list_id: str
    task_id: str
    deleted: bool


@dataclass
class MoveTaskResult:
    """Structured result from move_task."""

    id: str
    title: str
    status: Optional[str] = None
    updated: Optional[str] = None
    parent: Optional[str] = None
    position: Optional[str] = None
    destination_task_list: Optional[str] = None


@dataclass
class ClearCompletedTasksResult:
    """Structured result from clear_completed_tasks."""

    task_list_id: str
    cleared: bool


def _generate_schema(cls: type) -> dict[str, Any]:
    """Generate JSON schema for a dataclass."""
    return TypeAdapter(cls).json_schema()


# Pre-generated JSON schemas for use in @server.tool() decorators
TASKS_LIST_TASK_LISTS_SCHEMA = _generate_schema(ListTaskListsResult)
TASKS_GET_TASK_LIST_SCHEMA = _generate_schema(GetTaskListResult)
TASKS_CREATE_TASK_LIST_SCHEMA = _generate_schema(CreateTaskListResult)
TASKS_UPDATE_TASK_LIST_SCHEMA = _generate_schema(UpdateTaskListResult)
TASKS_DELETE_TASK_LIST_SCHEMA = _generate_schema(DeleteTaskListResult)
TASKS_LIST_TASKS_SCHEMA = _generate_schema(ListTasksResult)
TASKS_GET_TASK_SCHEMA = _generate_schema(GetTaskResult)
TASKS_CREATE_TASK_SCHEMA = _generate_schema(CreateTaskResult)
TASKS_UPDATE_TASK_SCHEMA = _generate_schema(UpdateTaskResult)
TASKS_DELETE_TASK_SCHEMA = _generate_schema(DeleteTaskResult)
TASKS_MOVE_TASK_SCHEMA = _generate_schema(MoveTaskResult)
TASKS_CLEAR_COMPLETED_SCHEMA = _generate_schema(ClearCompletedTasksResult)
