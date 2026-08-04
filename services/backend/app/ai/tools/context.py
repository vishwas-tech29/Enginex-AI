from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.user import User


@dataclass
class ToolContext:
    """Per-request execution context injected into every tool call.

    Kept separate from the LLM-facing input schema (the registry skips
    `ctx` when deriving tool schemas) so agents only see business
    parameters, never db/user plumbing.
    """

    db: Session
    user: User
