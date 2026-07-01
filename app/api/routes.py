"""
Unified API routes — single file defining all endpoints.
All routes are prefixed with /api/v1 via the main router.
"""

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    AudioRequest,
    DeliverNowRequest,
    HealthResponse,
    NewsRequest,
    NewsResponse,
    PreferenceChatRequest,
    PreferenceChatResponse,
    ScoutResponse,
    ScoutsResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.audio_service import generate_audio_stream
from app.services.llm_service import run_agent, summarize_news
from app.services.news_service import fetch_news
from app.services.preferences_chat_service import chat_preferences
from app.services.scheduler_service import deliver_for_user, run_due_deliveries
from app.services.scouts_service import get_scout, list_scouts
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


# ── Scouts (dashboard) ───────────────────────────────────────────

@router.get(
    "/scouts",
    response_model=ScoutsResponse,
    tags=["Scouts"],
    summary="List the scouts a user has deployed, with all their traits",
)
async def get_scouts(email: str | None = None):
    """
    Return every deployed scout and its configuration (niche, personality,
    delivery platforms, schedule). Currently backed by dummy data; `email`
    will scope results to the signed-in user once persistence is wired in.
    """
    try:
        scouts = list_scouts(email=email)
        return ScoutsResponse(success=True, scouts=scouts)
    except Exception as e:
        logger.error("GET /scouts error: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to list scouts: {e}")


@router.get(
    "/scouts/{scout_id}",
    response_model=ScoutResponse,
    tags=["Scouts"],
    summary="Fetch a single scout by id",
)
async def get_scout_by_id(scout_id: str, email: str | None = None):
    try:
        scout = get_scout(scout_id, email=email)
        if scout is None:
            raise HTTPException(status_code=404, detail="Scout not found.")
        return ScoutResponse(success=True, scout=scout)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("GET /scouts/%s error: %s", scout_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch scout: {e}")


# ── Preferences (conversational setup) ───────────────────────────

@router.post(
    "/preferences/chat",
    response_model=PreferenceChatResponse,
    tags=["Preferences"],
    summary="Grok-powered chat that gathers a user's news preferences",
)
async def preferences_chat(data: PreferenceChatRequest):
    try:
        messages = [m.model_dump() for m in data.messages]
        result = chat_preferences(messages)
        return PreferenceChatResponse(success=True, **result)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error("POST /preferences/chat error: %s", e)
        raise HTTPException(status_code=500, detail=f"Preference chat failed: {e}")


# ── Scheduler ────────────────────────────────────────────────────

@router.post(
    "/scheduler/deliver-now",
    tags=["Scheduler"],
    summary="Immediately generate and send one briefing for a user",
)
async def scheduler_deliver_now(data: DeliverNowRequest):
    """
    Send a single briefing right now using the user's saved preferences.
    Backs the 'Send me one now' button in the app.
    """
    from app.services.db_service import preferences_collection

    pref = preferences_collection().find_one({"email": data.email.lower()})
    if not pref:
        raise HTTPException(status_code=404, detail="No saved preferences for this user.")

    try:
        result = deliver_for_user(pref)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error("POST /scheduler/deliver-now error: %s", e)
        raise HTTPException(status_code=500, detail=f"Delivery failed: {e}")

    if not result.get("delivered"):
        reason = result.get("reason", "unknown")
        if reason == "no_telegram_link":
            raise HTTPException(status_code=409, detail="Telegram is not linked for this user.")
        raise HTTPException(status_code=500, detail=f"Delivery failed: {reason}")

    return result


@router.post(
    "/scheduler/run-due",
    tags=["Scheduler"],
    summary="Manually trigger the due-delivery sweep (testing / external cron)",
)
async def scheduler_run_due():
    try:
        return run_due_deliveries()
    except Exception as e:
        logger.error("POST /scheduler/run-due error: %s", e)
        raise HTTPException(status_code=500, detail=f"Scheduler run failed: {e}")
