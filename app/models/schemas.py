"""
Pydantic request / response schemas for all API endpoints.
"""

from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────

class NewsRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Search topic")


class SummarizeRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Search topic")
    limit: int = Field(default=5, ge=1, le=20, description="Number of articles to fetch")
    time_published: str = Field(
        default="anytime",
        description="Time filter: anytime | past_hour | past_day | past_week",
    )


class AudioRequest(SummarizeRequest):
    voice_id: str = Field(
        default="JBFqnCBsd6RMkjVDRZzb",
        description="ElevenLabs voice ID (default: George — news anchor)",
    )
    model_id: str = Field(
        default="eleven_multilingual_v2",
        description="ElevenLabs TTS model ID",
    )


# ── Response Schemas ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str


class NewsResponse(BaseModel):
    success: bool
    news: str | None = None
    error: str | None = None


class SummarizeResponse(BaseModel):
    success: bool
    topic: str | None = None
    article_count: int | None = None
    summary: str | None = None
    error: str | None = None
