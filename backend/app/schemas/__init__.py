"""Meeting AI Schemas Package Exports"""
from app.schemas.common import ApiResponse, PaginatedData, PaginationParams, ErrorDetail
from app.schemas.auth import RegisterRequest, LoginRequest, RefreshTokenRequest, TokenData, AuthResponseData, UserRead, UserUpdate
from app.schemas.meeting import MeetingCreate, MeetingUpdate, MeetingRead, MeetingDetailRead, MeetingCounts, DashboardStats
from app.schemas.meeting_file import MeetingFileRead, UploadResponse
from app.schemas.speaker import SpeakerRead, SpeakerUpdate
from app.schemas.transcript import TranscriptSegmentRead, TranscriptResponse, SegmentMatch, TranscriptSearchResponse
from app.schemas.summary import MeetingSummaryRead, MeetingTopicRead, MeetingDecisionRead, MeetingQuestionRead, MeetingRiskRead
from app.schemas.action_item import ActionItemCreate, ActionItemUpdate, ActionItemRead
from app.schemas.processing_job import ProcessingJobRead, ProcessingStatusResponse
from app.schemas.search import SearchMeetingResult, SearchResponse
from app.schemas.ai_output import AIExtractedMeeting, AITopic, AIDecision, AIActionItem, AIQuestion, AIRisk

__all__ = [
    "ApiResponse",
    "PaginatedData",
    "PaginationParams",
    "ErrorDetail",
    "RegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "TokenData",
    "AuthResponseData",
    "UserRead",
    "UserUpdate",
    "MeetingCreate",
    "MeetingUpdate",
    "MeetingRead",
    "MeetingDetailRead",
    "MeetingCounts",
    "DashboardStats",
    "MeetingFileRead",
    "UploadResponse",
    "SpeakerRead",
    "SpeakerUpdate",
    "TranscriptSegmentRead",
    "TranscriptResponse",
    "SegmentMatch",
    "TranscriptSearchResponse",
    "MeetingSummaryRead",
    "MeetingTopicRead",
    "MeetingDecisionRead",
    "MeetingQuestionRead",
    "MeetingRiskRead",
    "ActionItemCreate",
    "ActionItemUpdate",
    "ActionItemRead",
    "ProcessingJobRead",
    "ProcessingStatusResponse",
    "SearchMeetingResult",
    "SearchResponse",
    "AIExtractedMeeting",
    "AITopic",
    "AIDecision",
    "AIActionItem",
    "AIQuestion",
    "AIRisk",
]
