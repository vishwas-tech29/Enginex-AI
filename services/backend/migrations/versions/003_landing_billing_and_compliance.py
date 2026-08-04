"""landing page signup attribution, age verification, Stripe billing fields, analytics events

Revision ID: 003
Revises: 002
Create Date: 2026-08-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside the transaction Alembic
    # normally wraps a migration in (Postgres forbids using a new enum
    # value in the same transaction that added it) — run these in their
    # own autocommit block.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE subscription_tier ADD VALUE IF NOT EXISTS 'hobbyist'")
        op.execute("ALTER TYPE subscription_tier ADD VALUE IF NOT EXISTS 'professional'")
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'age_verification'")

    op.add_column("users", sa.Column("created_from", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("referral_source", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("company", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("trial_ends", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column(
        "users",
        sa.Column("age_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("users", sa.Column("age_verified_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("users", sa.Column("birth_year", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("age_verification_country", sa.String(length=2), nullable=True))

    op.add_column(
        "organizations",
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True, unique=True),
    )

    op.add_column("subscriptions", sa.Column("billing_cycle", sa.String(length=20), nullable=True))
    op.add_column(
        "subscriptions", sa.Column("current_period_end", sa.TIMESTAMP(timezone=True), nullable=True)
    )

    op.create_table(
        "analytics_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("event_name", sa.Text(), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_analytics_events_name_created", "analytics_events", ["event_name", "created_at"])
    op.create_index("idx_analytics_events_user", "analytics_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_analytics_events_user", table_name="analytics_events")
    op.drop_index("idx_analytics_events_name_created", table_name="analytics_events")
    op.drop_table("analytics_events")

    op.drop_column("subscriptions", "current_period_end")
    op.drop_column("subscriptions", "billing_cycle")

    op.drop_column("organizations", "stripe_customer_id")

    op.drop_column("users", "age_verification_country")
    op.drop_column("users", "birth_year")
    op.drop_column("users", "age_verified_at")
    op.drop_column("users", "age_verified")
    op.drop_column("users", "trial_ends")
    op.drop_column("users", "company")
    op.drop_column("users", "referral_source")
    op.drop_column("users", "created_from")

    # Postgres has no ALTER TYPE ... DROP VALUE — reverting the enum
    # additions requires rebuilding the type, which isn't done here since
    # this app's tests run against SQLite and never execute this migration
    # live; a real rollback would need a documented manual enum rebuild.
