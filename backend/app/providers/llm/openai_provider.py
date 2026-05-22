"""OpenAI LLM Meeting Intelligence Provider with Strict Pydantic Validation"""
import json
from typing import Optional
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import HealthSetuException
from app.providers.base import LLMProvider
from app.schemas.ai_output import AIExtractedMeeting

PROMPT_SYSTEM_DIRECTIVE = """You are an expert executive meeting assistant.
Your job is to analyze the provided meeting transcript and return a strictly structured JSON summary.

CRITICAL RULES:
1. Ground every claim STRICTLY in the transcript. Do NOT hallucinate names, dates, or decisions.
2. Only extract explicit decisions where consensus or direction was reached (distinguish suggestions from decisions).
3. Extract specific action items with assignees (use null if unassigned) and deadlines (use null if not specified).
4. Identify unresolved questions and genuine risks discussed during the meeting.
5. Return valid JSON matching the required schema.

JSON SCHEMA REQUIREMENT:
{
  "executive_summary": "Short 2-3 sentence overview",
  "detailed_summary": "Structured multi-paragraph detailed summary in markdown",
  "topics": [{"title": "Topic name", "description": "What was discussed"}],
  "decisions": [{"decision": "Agreed decision", "context": "Rationale", "timestamp_seconds": 0.0}],
  "action_items": [{"task": "Task description", "assignee": "Person or null", "due_date": "YYYY-MM-DD or null", "priority": "LOW|MEDIUM|HIGH|URGENT", "timestamp_seconds": 0.0}],
  "questions": [{"question": "Unresolved question", "context": "Context", "status": "UNRESOLVED"}],
  "risks": [{"risk": "Risk description", "impact": "Impact description"}]
}
"""


class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = settings.OPENAI_MODEL):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        if not self.api_key:
            raise HealthSetuException(
                message="OpenAI API key is missing. Please set OPENAI_API_KEY in environment.",
                code="AI_PROVIDER_ERROR",
                status_code=500,
            )
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def analyze_transcript(
        self,
        meeting_title: str,
        structured_transcript: str,
        meeting_description: Optional[str] = None,
    ) -> AIExtractedMeeting:
        user_prompt = f"""MEETING TITLE: {meeting_title}
DESCRIPTION: {meeting_description or 'None'}

TRANSCRIPT:
{structured_transcript}

Please produce the structured meeting intelligence JSON."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PROMPT_SYSTEM_DIRECTIVE},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            raw_content = response.choices[0].message.content or "{}"
            parsed_json = json.loads(raw_content)

            # Strict Pydantic validation
            validated_output = AIExtractedMeeting.model_validate(parsed_json)
            return validated_output

        except Exception as e:
            raise HealthSetuException(
                message=f"OpenAI LLM meeting analysis failed: {str(e)}",
                code="LLM_ANALYSIS_ERROR",
                status_code=502,
            )
