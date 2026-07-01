"""
Preference chat service — a Grok-powered conversational assistant that helps a
user describe the niche news they want to hear, then extracts those choices into
a structured object the news pipeline can consume.

The endpoint is stateless: the frontend sends the running conversation each turn
and we return the assistant's next reply plus the best-effort extracted
preferences. When the assistant has gathered enough, ``complete`` flips to true
and ``preferences`` is fully populated.
"""

import json
import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are the YourNews preference assistant. Your job is to have a short, \
friendly conversation that figures out exactly what news a user wants to hear in their \
personalised audio briefings.

Gather, conversationally and in as few turns as possible (ideally 2-4):
  1. The topics / niches they care about (e.g. "AI chips", "Premier League", "Indian startups").
  2. Any specific angle or keywords to emphasise (e.g. "funding rounds", "policy", "transfers").
  3. The region focus (Global, US, India, UK, Europe, etc.). If unclear, default to "Global".

Ask one natural question at a time. Acknowledge what they said. Do NOT ask for more than you \
need — once you can name concrete topics, finish.

CRITICAL OUTPUT FORMAT — you must respond with a SINGLE valid JSON object and NOTHING else \
(no markdown, no code fences, no text outside the JSON). The shape is exactly:
{
  "reply": "<the message to show the user>",
  "preferences": {
    "topics": ["<topic>", ...],
    "keywords": ["<keyword/angle>", ...],
    "region": "<Global|US|India|UK|Europe|...>",
    "summary": "<one short natural-language sentence describing what they want>"
  },
  "complete": <true|false>
}

Rules for the JSON:
  - Always include "reply". Keep replies warm and concise (1-3 sentences).
  - "preferences" should reflect your best understanding so far; use [] / "Global" / "" when unknown.
  - Set "complete": true ONLY when you have at least one concrete topic and have confirmed with \
the user. When complete, your "reply" should warmly confirm the saved preferences.
  - If the conversation is just starting (no user messages yet), greet the user and ask what \
topics they'd like briefings on. Keep "complete": false.
"""


def chat_preferences(messages: list[dict]) -> dict:
    """
    Advance the preference-gathering conversation by one assistant turn.

    Args:
        messages: prior conversation as [{"role": "user"|"assistant", "content": str}, ...].

    Returns:
        dict: {"reply": str, "preferences": dict | None, "complete": bool}
    """
    llm = get_llm()

    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in messages or []:
        role = (m.get("role") or "user").lower()
        content = m.get("content", "") or ""
        if role == "assistant":
            lc_messages.append(AIMessage(content=content))
        else:
            lc_messages.append(HumanMessage(content=content))

    # When there are no user messages yet, nudge the model to open the chat.
    if not any((m.get("role") or "user").lower() == "user" for m in (messages or [])):
        lc_messages.append(HumanMessage(content="(The user just opened the chat. Greet them and ask your first question.)"))

    response = llm.invoke(lc_messages)
    raw = response.content if isinstance(response.content, str) else _flatten(response.content)
    return _parse(raw)


# ── Internal helpers ─────────────────────────────────────────────

def _flatten(content) -> str:
    """Flatten a list-of-blocks message into plain text."""
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)


def _parse(raw: str) -> dict:
    """Tolerantly parse the model's JSON reply."""
    text = (raw or "").strip()
    # Strip accidental code fences.
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()

    data: dict = {}
    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except Exception:
                logger.warning("Could not parse preference chat JSON; returning raw text.")

    if not isinstance(data, dict) or "reply" not in data:
        # Fall back to treating the whole output as the visible reply.
        return {"reply": text or "Sorry, could you say that again?", "preferences": None, "complete": False}

    prefs = data.get("preferences")
    if isinstance(prefs, dict):
        prefs = {
            "topics": [t for t in (prefs.get("topics") or []) if t],
            "keywords": [k for k in (prefs.get("keywords") or []) if k],
            "region": prefs.get("region") or "Global",
            "summary": prefs.get("summary") or "",
        }
    else:
        prefs = None

    return {
        "reply": str(data.get("reply", "")).strip(),
        "preferences": prefs,
        "complete": bool(data.get("complete", False)),
    }
