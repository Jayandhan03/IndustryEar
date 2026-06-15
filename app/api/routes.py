"""
Unified API routes — single file defining all endpoints.
All routes are prefixed with /api/v1 via the main router.
"""

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    AudioRequest,
    HealthResponse,
    NewsRequest,
    NewsResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.audio_service import generate_audio_stream
from app.services.llm_service import run_agent, summarize_news
from app.services.news_service import fetch_news
from app.services.telegram_service import send_audio_to_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Health ───────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Service health check",
)
async def health_check():
    return HealthResponse(status="ok", version="1.0.0")


# ── News ─────────────────────────────────────────────────────────

@router.post(
    "/news/generate",
    response_model=NewsResponse,
    tags=["News"],
    summary="Generate AI-researched news summary for a topic",
)
async def generate_news(data: NewsRequest):
    try:
        result = run_agent(topic=data.topic)
        return NewsResponse(success=True, news=result)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error("POST /news/generate error: %s", e)
        raise HTTPException(status_code=500, detail=f"News generation failed: {e}")


@router.post(
    "/news/summarize",
    response_model=SummarizeResponse,
    tags=["News"],
    summary="Fetch articles and return a broadcast-style summary",
)
async def summarize_news_endpoint(data: SummarizeRequest):
    try:
        news_data = fetch_news(
            query=data.topic,
            limit=data.limit,
            time_published=data.time_published,
        )
        articles = news_data.get("data", []) if news_data else []
        summary = summarize_news(topic=data.topic, articles=articles)
        return SummarizeResponse(
            success=True,
            topic=data.topic,
            article_count=len(articles),
            summary=summary,
        )
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error("POST /news/summarize error: %s", e)
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {e}")


# ── Audio ────────────────────────────────────────────────────────

@router.post(
    "/audio/news",
    tags=["Audio"],
    summary="Full pipeline: fetch → summarize → TTS → stream MP3",
)
async def news_audio_endpoint(data: AudioRequest):
    try:
        news_data = fetch_news(
            query=data.topic,
            limit=data.limit,
            time_published=data.time_published,
        )
        articles = news_data.get("data", []) if news_data else []
    except Exception as e:
        logger.error("POST /audio/news fetch error: %s", e)
        raise HTTPException(status_code=502, detail=f"News fetch failed: {e}")

    try:
        script = summarize_news(topic=data.topic, articles=articles)
    except Exception as e:
        logger.error("POST /audio/news summarize error: %s", e)
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {e}")

    try:
        audio_stream = generate_audio_stream(
            script=script,
            voice_id=data.voice_id,
            model_id=data.model_id,
        )
        filename = data.topic.replace(" ", "_")[:40] + "_news.mp3"
        return StreamingResponse(
            audio_stream,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Topic": data.topic,
                "X-Article-Count": str(len(articles)),
            },
        )
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error("POST /audio/news TTS error: %s", e)
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")


# ── Telegram ─────────────────────────────────────────────────────

@router.post(
    "/telegram/send-audio",
    tags=["Telegram"],
    summary="Send an audio file to a Telegram user by chat_id",
)
async def telegram_send_audio(
    audio: UploadFile = File(..., description="MP3 audio file"),
    chat_id: str = Form(..., description="Telegram chat ID (captured when the user links the bot)"),
    topic: str = Form(default="News Briefing", description="Topic for the caption"),
):
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=422, detail="Empty audio file.")

        filename = audio.filename or f"{topic.replace(' ', '_')[:40]}_news.mp3"
        caption = f"🎙 Your audio briefing: {topic}"

        result = send_audio_to_user(
            chat_id=chat_id,
            audio_bytes=audio_bytes,
            filename=filename,
            caption=caption,
        )
        return result

    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error("POST /telegram/send-audio error: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to send audio: {e}")
