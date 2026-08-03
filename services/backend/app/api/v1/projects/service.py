import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.projects.schemas import (
    CreateProjectRequest,
    InviteProjectRequest,
    ShareProjectRequest,
    UpdateProjectRequest,
)
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.project import Project
from app.models.user import User

ROLE_OWNER = "owner"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"
_ROLE_RANK = {ROLE_VIEWER: 0, ROLE_EDITOR: 1, ROLE_OWNER: 2}


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def get_role(self, project: Project, user: User) -> str | None:
        if project.owner_id == user.id:
            return ROLE_OWNER
        for member in project.members:
            if member.get("user_id") == str(user.id):
                return member.get("role", ROLE_VIEWER)
        return None

    def require_access(self, project: Project, user: User, min_role: str = ROLE_VIEWER) -> str:
        role = self.get_role(project, user)
        if role is None or _ROLE_RANK[role] < _ROLE_RANK[min_role]:
            raise ForbiddenError("Insufficient permissions on this project")
        return role

    def list_for_user(self, user: User) -> list[Project]:
        all_projects = self.db.query(Project).order_by(Project.created_at.desc()).all()
        return [p for p in all_projects if self.get_role(p, user) is not None]

    def get(self, project_id: uuid.UUID, user: User) -> Project:
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        self.require_access(project, user, ROLE_VIEWER)
        return project

    def create(self, payload: CreateProjectRequest, user: User) -> Project:
        project = Project(
            organization_id=payload.organization_id,
            team_id=payload.team_id,
            name=payload.name,
            description=payload.description,
            owner_id=user.id,
            type=payload.type,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update(self, project_id: uuid.UUID, payload: UpdateProjectRequest, user: User) -> Project:
        project = self.get(project_id, user)
        self.require_access(project, user, ROLE_EDITOR)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id: uuid.UUID, user: User) -> None:
        project = self.get(project_id, user)
        self.require_access(project, user, ROLE_OWNER)
        self.db.delete(project)
        self.db.commit()

    def list_members(self, project_id: uuid.UUID, user: User) -> list[dict]:
        project = self.get(project_id, user)
        members = [{"user_id": str(project.owner_id), "role": ROLE_OWNER}]
        members.extend(project.members)
        return self._hydrate_members(members)

    def share(self, project_id: uuid.UUID, payload: ShareProjectRequest, user: User) -> list[dict]:
        project = self.get(project_id, user)
        self.require_access(project, user, ROLE_OWNER)

        target = self.db.get(User, payload.user_id)
        if not target:
            raise NotFoundError("User", payload.user_id)

        members = [m for m in project.members if m.get("user_id") != str(payload.user_id)]
        members.append({"user_id": str(payload.user_id), "role": payload.role})
        project.members = members
        self.db.commit()
        self.db.refresh(project)
        return self.list_members(project_id, user)

    def invite(self, project_id: uuid.UUID, payload: InviteProjectRequest, user: User) -> list[dict]:
        project = self.get(project_id, user)
        self.require_access(project, user, ROLE_OWNER)

        target = self.db.query(User).filter(User.email == payload.email).first()
        if not target:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "No user found with that email. Email invitations for "
                "users without an account aren't implemented yet — ask "
                "them to register first.",
            )
        return self.share(project_id, ShareProjectRequest(user_id=target.id, role=payload.role), user)

    def _hydrate_members(self, members: list[dict]) -> list[dict]:
        user_ids = [uuid.UUID(m["user_id"]) for m in members]
        users_by_id = {str(u.id): u for u in self.db.query(User).filter(User.id.in_(user_ids)).all()}
        hydrated = []
        for member in members:
            target = users_by_id.get(member["user_id"])
            if not target:
                continue
            hydrated.append(
                {
                    "user_id": member["user_id"],
                    "email": target.email,
                    "name": target.name,
                    "role": member["role"],
                }
            )
        return hydrated
