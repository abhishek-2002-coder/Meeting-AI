"""Structured AI Output Validation Schemas (Strict Pydantic Parsing)"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AITopic(BaseModel):
    title: str = Field(..., description="Concise title of the discussion topic")
    description: str = Field(..., description="Summary of what was discussed regarding this topic")

    model_config = ConfigDict(extra="ignore")


class AIDecision(BaseModel):
    decision: str = Field(..., description="Clear statement of the agreed decision")
    context: Optional[str] = Field(None, description="Context or rationale discussed")
    timestamp_seconds: Optional[float] = Field(None, description="Approximate start time in seconds where decided")

    model_config = ConfigDict(extra="ignore")


class AIActionItem(BaseModel):
    task: str = Field(..., description="Specific actionable task")
    assignee: Optional[str] = Field(None, description="Person assigned to the task (null if not explicitly mentioned)")
    due_date: Optional[str] = Field(None, description="ISO date or deadline string if mentioned, else null")
    priority: str = Field(default="MEDIUM", description="LOW | MEDIUM | HIGH | URGENT")
    timestamp_seconds: Optional[float] = Field(None, description="Timestamp in seconds where assigned")

    model_config = ConfigDict(extra="ignore")


class AIQuestion(BaseModel):
    question: str = Field(..., description="Unresolved question or open point")
    context: Optional[str] = Field(None, description="Context around the question")
    status: str = Field(default="UNRESOLVED")

    model_config = ConfigDict(extra="ignore")


class AIRisk(BaseModel):
    risk: str = Field(..., description="Potential obstacle or risk identified")
    impact: Optional[str] = Field(None, description="Potential impact on timeline or deliverables")

    model_config = ConfigDict(extra="ignore")


class AIExtractedMeeting(BaseModel):
    """Complete structured meeting intelligence payload returned from LLM"""
    executive_summary: str = Field(..., description="Short high-level executive summary grounded strictly in transcript")
    detailed_summary: str = Field(..., description="Comprehensive multi-paragraph meeting summary")
    topics: List[AITopic] = Field(default_factory=list)
    decisions: List[AIDecision] = Field(default_factory=list)
    action_items: List[AIActionItem] = Field(default_factory=list)
    questions: List[AIQuestion] = Field(default_factory=list)
    risks: List[AIRisk] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")
