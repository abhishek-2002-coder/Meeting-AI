"""Pluggable AI Providers Factory"""
from app.core.config import settings
from app.providers.base import LLMProvider, SpeechToTextProvider
from app.providers.llm.mock_llm_provider import MockLLMProvider
from app.providers.llm.openai_provider import OpenAILLMProvider
from app.providers.stt.mock_stt_provider import MockSTTProvider
from app.providers.stt.whisper_provider import WhisperSTTProvider


def get_stt_provider() -> SpeechToTextProvider:
    """Factory function returning the configured Speech-to-Text provider"""
    provider_type = settings.STT_PROVIDER.lower().strip()
    if provider_type == "openai" and settings.OPENAI_API_KEY:
        return WhisperSTTProvider()
    return MockSTTProvider()


def get_llm_provider() -> LLMProvider:
    """Factory function returning the configured LLM intelligence provider"""
    provider_type = settings.LLM_PROVIDER.lower().strip()
    if provider_type == "openai" and settings.OPENAI_API_KEY:
        return OpenAILLMProvider()
    return MockLLMProvider()


__all__ = [
    "SpeechToTextProvider",
    "LLMProvider",
    "MockSTTProvider",
    "WhisperSTTProvider",
    "MockLLMProvider",
    "OpenAILLMProvider",
    "get_stt_provider",
    "get_llm_provider",
]
