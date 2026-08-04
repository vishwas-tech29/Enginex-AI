import uuid

from app.ai.tools.context import ToolContext
from app.ai.tools.registry import tool_registry
from app.api.v1.folders.schemas import CreateFolderRequest
from app.api.v1.folders.service import FolderService
from app.api.v1.projects.service import ProjectService

ROLES = ["planning", "manufacturing", "documentation", "design_review"]


async def list_project_files(ctx: ToolContext, project_id: str) -> dict:
    """List all files in a project."""
    from app.api.v1.files.service import FileService

    files = FileService(ctx.db).list_for_project(uuid.UUID(project_id), ctx.user)
    return {"files": [{"id": str(f.id), "name": f.name, "type": f.type} for f in files]}


async def create_folder(ctx: ToolContext, project_id: str, name: str) -> dict:
    """Create a folder inside a project to organize files."""
    folder = FolderService(ctx.db).create(
        uuid.UUID(project_id), CreateFolderRequest(name=name), ctx.user
    )
    return {"folder_id": str(folder.id), "name": folder.name}


async def get_project_summary(ctx: ToolContext, project_id: str) -> dict:
    """Get a project's name, type, status, and description."""
    project = ProjectService(ctx.db).get(uuid.UUID(project_id), ctx.user)
    return {
        "id": str(project.id),
        "name": project.name,
        "type": project.type,
        "status": project.status,
        "description": project.description,
    }


def register() -> None:
    tool_registry.register("list_project_files", list_project_files.__doc__, list_project_files, ROLES)
    tool_registry.register("create_folder", create_folder.__doc__, create_folder, ROLES)
    tool_registry.register("get_project_summary", get_project_summary.__doc__, get_project_summary, ROLES)
