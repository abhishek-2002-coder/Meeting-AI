"""Initial schema for Meeting AI

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. Meetings
    op.create_table(
        'meetings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='UPLOADED'),
        sa.Column('language', sa.String(length=20), nullable=False, server_default='en'),
        sa.Column('duration_seconds', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_meetings_user_id', 'meetings', ['user_id'])
    op.create_index('ix_meetings_status', 'meetings', ['status'])
    op.create_index('ix_meetings_title', 'meetings', ['title'])

    # 3. Meeting Files
    op.create_table(
        'meeting_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('meeting_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_meeting_files_meeting_id', 'meeting_files', ['meeting_id'], unique=True)

    # 4. Meeting Speakers
    op.create_table(
        'meeting_speakers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('meeting_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('speaker_label', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_meeting_speakers_meeting_id', 'meeting_speakers', ['meeting_id'])

    # 5. Transcript Segments
    op.create_table(
        'transcript_segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('meeting_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('speaker_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meeting_speakers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_transcript_segments_meeting_id', 'transcript_segments', ['meeting_id'])
    op.create_index('ix_transcript_segments_start', 'transcript_segments', ['meeting_id', 'start_time'])

    # 6. Meeting Summaries
    op.create_table(
        'meeting_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('meeting_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('short_summary', sa.Text(), nullable=False),
        sa.Column('detailed_summary', sa.Text(), nullable=False),
        sa.Column('model_provider', sa.String(length=100), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_meeting_summaries_meeting_id', 'meeting_summaries', ['meeting_id'], unique=True)

    # 7. Meeting Topics
    op.create_table(
        'meeting_topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('meeting_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_meeting_topics_meeting_id', 'meeting_topics', ['meeting_id'])

    # 8. Meeting Decisions
    op.create_table(
        'meeting_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('meeting_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_segment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transcript_segments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decision', sa.Text(), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('timestamp_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_meeting_decisions_meeting_id', 'meeting_decisions', ['meeting_id'])

    # 9. Action Items
    op.create_table(
        'action_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('meeting_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_segment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transcript_segments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('task', sa.Text(), nullable=False),
        sa.Column('assignee', sa.String(length=255), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'),
        sa.Column('timestamp_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_action_items_meeting_id', 'action_items', ['meeting_id'])
    op.create_index('ix_action_items_status', 'action_items', ['status'])

    # 10. Meeting Questions
    op.create_table(
        'meeting_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('meeting_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='UNRESOLVED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_meeting_questions_meeting_id', 'meeting_questions', ['meeting_id'])

    # 11. Meeting Risks
    op.create_table(
        'meeting_risks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('meeting_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('risk', sa.Text(), nullable=False),
        sa.Column('impact', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_meeting_risks_meeting_id', 'meeting_risks', ['meeting_id'])

    # 12. Processing Jobs
    op.create_table(
        'processing_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('meeting_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_processing_jobs_meeting_id', 'processing_jobs', ['meeting_id'])

    # 13. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('processing_jobs')
    op.drop_table('meeting_risks')
    op.drop_table('meeting_questions')
    op.drop_table('action_items')
    op.drop_table('meeting_decisions')
    op.drop_table('meeting_topics')
    op.drop_table('meeting_summaries')
    op.drop_table('transcript_segments')
    op.drop_table('meeting_speakers')
    op.drop_table('meeting_files')
    op.drop_table('meetings')
    op.drop_table('users')
