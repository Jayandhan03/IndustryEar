"""
Scouts service.

Provides the deployed scouts shown on the dashboard, along with all of their
configurable traits (niche, personality, delivery platforms, schedule).

For now this returns richly-shaped DUMMY data so the frontend dashboard can be
built end-to-end. Each function is intentionally the single seam where real
persistence (MongoDB / per-user config) will be wired in later — the API routes
and response schemas never need to change.
"""

import logging

from app.models.schemas import (
    Scout,
    ScoutPersonality,
    ScoutPlatform,
    ScoutSchedule,
    ScoutStats,
)

logger = logging.getLogger(__name__)


# ── Dummy dataset ────────────────────────────────────────────────
# Keyed loosely on the marketing categories used across the app so the
# dashboard feels continuous with the landing page.

def _dummy_scouts() -> list[Scout]:
    return [
        Scout(
            id="finance-markets",
            name="Finance Scout",
            icon="💹",
            accent="#34d399",
            niche="Finance & Markets",
            description="Stocks, crypto, earnings and macro moves — the moment they break.",
            status="active",
            keywords=["S&P 500", "Fed rates", "earnings", "Bitcoin", "macro"],
            personality=ScoutPersonality(
                voice="Professional",
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                language="English",
                tone_summary="Crisp, analyst-style delivery with the numbers up front.",
            ),
            platforms=[
                ScoutPlatform(platform="telegram", connected=True, handle="@jayandhan"),
                ScoutPlatform(platform="whatsapp", connected=False, handle=None),
            ],
            schedule=ScoutSchedule(
                frequency="Twice daily",
                interval_minutes=720,
                times=["08:00", "18:00"],
                timezone="Asia/Kolkata",
                enabled=True,
                next_run_at="2026-07-01T18:00:00+05:30",
                last_sent_at="2026-07-01T08:00:00+05:30",
            ),
            stats=ScoutStats(briefings_sent=128, sources_tracked=42, last_briefing="4h ago"),
        ),
        Scout(
            id="jobs-careers",
            name="Careers Scout",
            icon="💼",
            accent="#4d7fff",
            niche="Jobs & Careers",
            description="Fresh roles, hiring trends and openings matched to your profile.",
            status="active",
            keywords=["AI engineer", "remote", "startups hiring", "referrals"],
            personality=ScoutPersonality(
                voice="Casual",
                voice_id="EXAVITQu4vr4xnSDxMaL",
                language="English",
                tone_summary="Friendly and encouraging, like a well-connected recruiter friend.",
            ),
            platforms=[
                ScoutPlatform(platform="telegram", connected=True, handle="@jayandhan"),
                ScoutPlatform(platform="whatsapp", connected=True, handle="+91 •••• ••1234"),
            ],
            schedule=ScoutSchedule(
                frequency="Daily",
                interval_minutes=1440,
                times=["09:00"],
                timezone="Asia/Kolkata",
                enabled=True,
                next_run_at="2026-07-02T09:00:00+05:30",
                last_sent_at="2026-07-01T09:00:00+05:30",
            ),
            stats=ScoutStats(briefings_sent=54, sources_tracked=18, last_briefing="7h ago"),
        ),
        Scout(
            id="law-policy",
            name="Policy Scout",
            icon="⚖️",
            accent="#8b5cf6",
            niche="Law & Policy",
            description="Regulations, rulings and legal shifts that actually affect you.",
            status="paused",
            keywords=["data privacy", "GDPR", "AI regulation", "tax law"],
            personality=ScoutPersonality(
                voice="Calm",
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                language="English",
                tone_summary="Measured and precise — no hype, just what changed and why it matters.",
            ),
            platforms=[
                ScoutPlatform(platform="telegram", connected=True, handle="@jayandhan"),
                ScoutPlatform(platform="whatsapp", connected=False, handle=None),
            ],
            schedule=ScoutSchedule(
                frequency="Weekly",
                interval_minutes=10080,
                times=["Mon 07:30"],
                timezone="Asia/Kolkata",
                enabled=False,
                next_run_at=None,
                last_sent_at="2026-06-23T07:30:00+05:30",
            ),
            stats=ScoutStats(briefings_sent=9, sources_tracked=11, last_briefing="8d ago"),
        ),
        Scout(
            id="tech-science",
            name="Tech Scout",
            icon="🧬",
            accent="#f472b6",
            niche="Tech & Science",
            description="Product launches, research breakthroughs and the next big thing.",
            status="active",
            keywords=["LLMs", "chip news", "space", "biotech", "open source"],
            personality=ScoutPersonality(
                voice="Energetic",
                voice_id="ErXwobaYiN019PkySvjV",
                language="English",
                tone_summary="Upbeat and curious, great for keeping up with fast-moving tech.",
            ),
            platforms=[
                ScoutPlatform(platform="telegram", connected=True, handle="@jayandhan"),
                ScoutPlatform(platform="whatsapp", connected=False, handle=None),
            ],
            schedule=ScoutSchedule(
                frequency="Real-time",
                interval_minutes=60,
                times=["As it happens"],
                timezone="Asia/Kolkata",
                enabled=True,
                next_run_at="2026-07-01T15:00:00+05:30",
                last_sent_at="2026-07-01T13:00:00+05:30",
            ),
            stats=ScoutStats(briefings_sent=340, sources_tracked=63, last_briefing="1h ago"),
        ),
    ]


# ── Public API (swap these bodies for real persistence later) ────

def list_scouts(email: str | None = None) -> list[Scout]:
    """Return all scouts deployed by a user. `email` is accepted now so the
    signature is stable once per-user persistence lands."""
    logger.debug("Listing scouts (email=%s) — returning dummy data", email)
    return _dummy_scouts()


def get_scout(scout_id: str, email: str | None = None) -> Scout | None:
    """Return a single scout by id, or None if it doesn't exist."""
    return next((s for s in list_scouts(email) if s.id == scout_id), None)
