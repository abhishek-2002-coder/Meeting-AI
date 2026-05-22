"""Mock LLM Provider for Local Development & Offline Testing"""
from typing import Optional
from app.providers.base import LLMProvider
from app.schemas.ai_output import (
    AIActionItem,
    AIDecision,
    AIExtractedMeeting,
    AIQuestion,
    AIRisk,
    AITopic,
)


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider generating structured meeting insights grounded in standard meeting patterns.
    """
    async def analyze_transcript(
        self,
        meeting_title: str,
        structured_transcript: str,
        meeting_description: Optional[str] = None,
    ) -> AIExtractedMeeting:
        return AIExtractedMeeting(
            executive_summary=(
                "The engineering team met to review backend API development progress, discuss production "
                "container deployment challenges, and finalize the Friday delivery deadline. The team agreed "
                "to standardize on Docker for production and assigned specific deliverables."
            ),
            detailed_summary=(
                "### Meeting Overview\n"
                "The team conducted their weekly engineering synchronization to evaluate project milestones.\n\n"
                "### Key Discussion Points\n"
                "- **Backend APIs**: Core database models and user authentication are in place. The meeting processing pipeline is currently underway.\n"
                "- **Production Deployment**: Previous container startup issues prompted a review of staging and production environments. Standardizing on Docker Compose was confirmed.\n"
                "- **Infrastructure & Access**: DevOps credentials for cloud hosting are required to avoid deployment timeline risks."
            ),
            topics=[
                AITopic(
                    title="Backend Development Progress",
                    description="Review of database schema, user authentication APIs, and pipeline implementation.",
                ),
                AITopic(
                    title="Production Deployment Architecture",
                    description="Discussion regarding container startup issues and adoption of Docker Compose.",
                ),
                AITopic(
                    title="Timeline & Deliverables",
                    description="Agreement on the Friday delivery deadline for the authentication and worker modules.",
                ),
            ],
            decisions=[
                AIDecision(
                    decision="Production deployment will use Docker.",
                    context="Docker Compose was selected to eliminate container startup discrepancies across environments.",
                    timestamp_seconds=62.0,
                ),
                AIDecision(
                    decision="Authentication API and processing worker must be completed by Friday.",
                    context="Agreed timeline to keep overall engineering milestones on schedule.",
                    timestamp_seconds=23.0,
                ),
            ],
            action_items=[
                AIActionItem(
                    task="Complete authentication API and background worker with tests",
                    assignee="Abhishek",
                    due_date="2026-10-10",
                    priority="HIGH",
                    timestamp_seconds=35.2,
                ),
                AIActionItem(
                    task="Prepare deployment server and Docker configuration",
                    assignee="Rahul",
                    due_date="2026-10-09",
                    priority="HIGH",
                    timestamp_seconds=76.0,
                ),
            ],
            questions=[
                AIQuestion(
                    question="Which cloud provider will host the production PostgreSQL database?",
                    context="DevOps credentials and server access are pending.",
                    status="UNRESOLVED",
                )
            ],
            risks=[
                AIRisk(
                    risk="Production deployment may be delayed if server access is not granted by DevOps.",
                    impact="Potential slip in end-of-week release timeline.",
                )
            ],
        )
