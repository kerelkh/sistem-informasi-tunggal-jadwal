"""store times as UTC instants

Meeting times used to be naive WIB wall-clock values; audit timestamps were naive
UTC. Everything becomes TIMESTAMPTZ, converting each column from the zone it was
actually written in. Adds meeting.timezone (the organizer's zone) and
notification.event_at.

Revision ID: 7c1d2e3f4a5b
Revises: 2f6e9fdb2e0f
Create Date: 2026-09-27 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7c1d2e3f4a5b'
down_revision: Union[str, Sequence[str], None] = '2f6e9fdb2e0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Every existing meeting was entered on the WIB clock.
LEGACY_MEETING_ZONE = 'Asia/Jakarta'

MEETING_TIMES = ('scheduled_start', 'scheduled_end', 'actual_start', 'actual_end')
UTC_STAMPS = (
    ('user', 'created_at'),
    ('unit', 'created_at'),
    ('meeting', 'created_at'),
    ('meeting', 'updated_at'),
    ('meetingparticipant', 'invited_at'),
    ('meetingparticipant', 'responded_at'),
    ('notification', 'created_at'),
)


def _retype(table: str, column: str, source_zone: str) -> None:
    op.execute(
        f'ALTER TABLE "{table}" ALTER COLUMN {column} TYPE TIMESTAMP WITH TIME ZONE '
        f"USING {column} AT TIME ZONE '{source_zone}'"
    )


def _untype(table: str, column: str, target_zone: str) -> None:
    op.execute(
        f'ALTER TABLE "{table}" ALTER COLUMN {column} TYPE TIMESTAMP WITHOUT TIME ZONE '
        f"USING {column} AT TIME ZONE '{target_zone}'"
    )


def upgrade() -> None:
    for column in MEETING_TIMES:
        _retype('meeting', column, LEGACY_MEETING_ZONE)
    for table, column in UTC_STAMPS:
        _retype(table, column, 'UTC')

    op.add_column(
        'meeting',
        sa.Column('timezone', sa.String(), nullable=False, server_default=LEGACY_MEETING_ZONE),
    )
    # The default only existed to fill old rows; new ones always get it from the app.
    op.alter_column('meeting', 'timezone', server_default=None)
    op.add_column('notification', sa.Column('event_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('notification', 'event_at')
    op.drop_column('meeting', 'timezone')
    for table, column in UTC_STAMPS:
        _untype(table, column, 'UTC')
    for column in MEETING_TIMES:
        _untype('meeting', column, LEGACY_MEETING_ZONE)
