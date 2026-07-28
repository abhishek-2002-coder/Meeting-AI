# Meeting AI — AI-Powered Meeting Intelligence Platform MVP

Meeting AI is a production-quality meeting intelligence platform that transcribes recordings, segments speakers, and uses structured LLM intelligence to generate executive summaries, key discussion topics, explicit decisions, action items with assignees & due dates, questions, and risks.

---

## 🏗 Pipeline Architecture

```text
Meeting Recording (MP3 / WAV / M4A / MP4 / WEBM)
       ↓
Audio Storage & Duration Validation
       ↓
Speech-to-Text (Pluggable Provider: OpenAI Whisper / Local)
       ↓
Speaker Diarization & Segmentation
       ↓
Structured Synchronized Transcript
       ↓
Chunking Engine (for long transcripts)
       ↓
Structured LLM Intelligence (OpenAI / Anthropic / Local)
 ┌───────────────┬────────────────┬──────────────┐
 ▼               ▼                ▼              ▼
Executive       Key             Action         Decisions
Summary         Topics          Items          & Risks
```

---

## 🚀 Quick Start with Docker

```bash
# 1. Clone or enter directory
cd MeetingAI

# 2. Copy environment variables
cp backend/.env.example backend/.env

# 3. Start PostgreSQL, Redis, and Backend
docker-compose up -d --build
```

- **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **API Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 🛠 Local Development Setup

### Backend (Python 3.11+)
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

---

## 🔒 Key Features
- **Pluggable AI Providers**: Interface-driven design for Speech-to-Text (`SpeechToTextProvider`) and LLMs (`LLMProvider`).
- **Structured Pydantic Validation**: AI outputs are validated against strict Pydantic models before persistence.
- **Asynchronous Pipeline**: Upload -> Background Multi-stage Job Execution (`AUDIO_PROCESSING`, `TRANSCRIPTION`, `DIARIZATION`, `SUMMARY`, `ACTION_EXTRACTION`).
- **Full-Text Search**: Search across meeting titles, summaries, topics, and timestamped transcripts.
- **Synchronized Transcript & Audio Player**: Byte-range stream support and segment timestamp seeking.
