"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None

project_type = postgresql.ENUM("cad", "pcb", "mixed", "robotics", name="project_type")
project_status = postgresql.ENUM("active", "archived", name="project_status")
subscription_tier = postgresql.ENUM("free", "pro", "enterprise", name="subscription_tier")
subscription_status = postgresql.ENUM(
    "active", "cancelled", "past_due", name="subscription_status"
)
ai_role = postgresql.ENUM("user", "assistant", "system", name="ai_role")
audit_action = postgresql.ENUM(
    "login", "create", "update", "delete", "export", "share", name="audit_action"
)


def upgrade() -> None:
    bind = op.get_bind()
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    for enum in (project_type, project_status, subscription_tier, subscription_status, ai_role, audit_action):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("avatar", sa.Text(), nullable=True),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subscription_tier", subscription_tier, nullable=False, server_default="free"),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("members", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", project_type, nullable=False, server_default="mixed"),
        sa.Column("status", project_status, nullable=False, server_default="active"),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("folders.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("folder_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("folders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("file_key", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "cad_objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("object_type", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cad_objects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "pcb_boards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("width_mm", sa.Float(), nullable=False, server_default="0"),
        sa.Column("height_mm", sa.Float(), nullable=False, server_default="0"),
        sa.Column("layers_count", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "pcb_components",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("board_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pcb_boards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference_designator", sa.Text(), nullable=False),
        sa.Column("footprint_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("library_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("position_x", sa.Float(), nullable=False, server_default="0"),
        sa.Column("position_y", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rotation_degrees", sa.Float(), nullable=False, server_default="0"),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "layers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("layer_type", sa.Text(), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("color", sa.Text(), nullable=False, server_default="#000000"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "ai_chats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "ai_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_chats.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", ai_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("model_used", sa.Text(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "ai_agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("tools", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("memory_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "agent_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_chats.id", ondelete="CASCADE"), nullable=True),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tier", subscription_tier, nullable=False, server_default="free"),
        sa.Column("status", subscription_status, nullable=False, server_default="active"),
        sa.Column("stripe_subscription_id", sa.Text(), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("ended_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("encrypted_key", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("operation", sa.Text(), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_index("idx_files_project_id", "files", ["project_id"])
    op.create_index("idx_projects_organization_id", "projects", ["organization_id"])
    op.create_index("idx_cad_objects_file_id", "cad_objects", ["file_id"])
    op.create_index("idx_ai_messages_chat_id", "ai_messages", ["chat_id"])
    op.create_index("idx_agent_memory_agent_id", "agent_memory", ["agent_id"])
    op.create_index("idx_usage_logs_org_date", "usage_logs", ["organization_id", "created_at"])
    op.create_index("idx_audit_logs_user_created", "audit_logs", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("usage_logs")
    op.drop_table("api_keys")
    op.drop_table("subscriptions")
    op.drop_table("agent_memory")
    op.drop_table("ai_agents")
    op.drop_table("ai_messages")
    op.drop_table("ai_chats")
    op.drop_table("layers")
    op.drop_table("pcb_components")
    op.drop_table("pcb_boards")
    op.drop_table("cad_objects")
    op.drop_table("files")
    op.drop_table("folders")
    op.drop_table("projects")
    op.drop_table("teams")
    op.drop_table("organizations")
    op.drop_table("users")

    bind = op.get_bind()
    for enum in (audit_action, ai_role, subscription_status, subscription_tier, project_status, project_type):
        enum.drop(bind, checkfirst=True)
