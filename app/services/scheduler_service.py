"""
Scheduler service — autonomous delivery of scheduled audio briefings.

A lightweight in-process loop (driven by APScheduler from main.py) periodically
asks: "which users are due for their next briefing?" For each, it rebuilds the
news query from their saved preferences, runs the existing fetch -> summarize ->
TTS pipeline, and sends the MP3 to their linked Telegram chat.

Preferences are written by the Next.js app; this module only reads them and
updates the scheduling bookkeeping fields (lastSentAt / nextRunAt / lastResult).
"""

import logging
from datetime import datetime, timedelta, timezone

from app.services.audio_service import generate_audio_stream
from app.services.db_service import get_chat_id_for_email, preferences_collection
from app.services.llm_service import summarize_news
from app.services.news_service import fetch_news
from app.services.telegram_service import send_audio_to_user

logger = logging.getLogger(__name__)

# Map the user-facing region to a RapidAPI country code.
REGION_TO_COUNTRY = {
    "global": "US",
    "us": "US",
    "usa": "US",
    "united states": "US",
    "india": "IN",
    "uk": "GB",
    "united kingdom": "GB",
    "gb": "GB",
    "europe": "GB",
    "canada": "CA",
    "australia": "AU",
}

DEFAULT_INTERVAL_MINUTES = 1440  # daily fallback


# ── Query building ───────────────────────────────────────────────

def _build_query(pref: dict) -> str:
    topics = pref.get("topics") or []
    keywords = pref.get("keywords") or []
    terms = [t for t in (list(topics) + list(keywords)) if t]
    if terms:
        return " ".join(terms)
    return (pref.get("summary") or "top news").strip()


def _topic_label(pref: dict) -> str:
    topics = pref.get("topics") or []
    if topics:
        return ", ".join(topics)
    return (pref.get("summary") or "Your News").strip()


def _country_for(pref: dict) -> str:
    return REGION_TO_COUNTRY.get(str(pref.get("region", "global")).lower(), "US")


# ── Delivery ─────────────────────────────────────────────────────

def deliver_for_user(pref: dict) -> dict:
    """
    Run the full pipeline for a single user's preferences and send the audio
    to their Telegram chat. Raises on hard failures so the caller can record it.
    """
    email = pref.get("email")
    if not email:
        return {"email": None, "delivered": False, "reason": "missing_email"}

    chat_id = get_chat_id_for_email(email)
    if not chat_id:
        logger.info("Skipping %s — no Telegram link.", email)
        return {"email": email, "delivered": False, "reason": "no_telegram_link"}

    query = _build_query(pref)
    label = _topic_label(pref)
    limit = int(pref.get("articleLimit") or 5)

    news_data = fetch_news(
        query=query,
        limit=limit,
        time_published="past_day",
        country=_country_for(pref),
    )
    articles = news_data.get("data", []) if news_data else []
    script = summarize_news(topic=label, articles=articles)

    audio_bytes = b"".join(generate_audio_stream(script))
    if not audio_bytes:
        raise ValueError("TTS produced no audio.")

    filename = (label.replace(" ", "_").replace(",", "")[:40] or "news") + "_briefing.mp3"
    caption = f"🎙 Your scheduled briefing: {label}"

    send_audio_to_user(
        chat_id=chat_id,
        audio_bytes=audio_bytes,
        filename=filename,
        caption=caption,
    )
    logger.info("Delivered scheduled briefing to %s (%d articles).", email, len(articles))
    return {"email": email, "delivered": True, "articles": len(articles)}


# ── Scheduling ───────────────────────────────────────────────────

def compute_next_run(interval_minutes: int, from_time: datetime | None = None) -> datetime:
    base = from_time or datetime.now(timezone.utc)
    minutes = max(1, int(interval_minutes or DEFAULT_INTERVAL_MINUTES))
    return base + timedelta(minutes=minutes)


def run_due_deliveries() -> dict:
    """
    Find every enabled preference whose next run is due (or never scheduled) and
    deliver it, then advance its nextRunAt. Designed to be called on a timer.
    """
    coll = preferences_collection()
    now = datetime.now(timezone.utc)

    due = list(
        coll.find(
            {
                "scheduleEnabled": True,
                "$or": [{"nextRunAt": {"$lte": now}}, {"nextRunAt": None}],
            }
        )
    )

    if due:
        logger.info("Scheduler tick: %d user(s) due.", len(due))

    results = []
    for pref in due:
        interval = pref.get("intervalMinutes") or DEFAULT_INTERVAL_MINUTES
        try:
            res = deliver_for_user(pref)
        except Exception as exc:  # noqa: BLE001 — record and keep going
            logger.error("Scheduled delivery failed for %s: %s", pref.get("email"), exc)
            res = {"email": pref.get("email"), "delivered": False, "reason": str(exc)}

        update = {
            "lastResult": res,
            "nextRunAt": compute_next_run(interval, now),
        }
        if res.get("delivered"):
            update["lastSentAt"] = now

        coll.update_one({"_id": pref["_id"]}, {"$set": update})
        results.append(res)

    return {"checked": len(due), "results": results}
