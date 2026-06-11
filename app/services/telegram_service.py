"""
Telegram Bot service — handles /start linking, connection status,
and sending audio files to connected users.

Uses Telegram Bot API long-polling (getUpdates) in a background thread.
Token-to-chat mapping is stored in-memory (dict). Sufficient for
development and small-scale production; swap for DB/Redis in production.
"""

import io
import logging
import threading
import time
from typing import TypedDict

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── Types ────────────────────────────────────────────────────────

class TelegramConnection(TypedDict):
    chat_id: int
    username: str | None
    first_name: str | None


# ── In-memory store: user_token → TelegramConnection ────────────

_connections: dict[str, TelegramConnection] = {}
_lock = threading.Lock()


# ── Public API ───────────────────────────────────────────────────

def get_connection(token: str) -> TelegramConnection | None:
    """Return the Telegram connection for a user token, or None."""
    with _lock:
        return _connections.get(token)


def send_audio_to_user(
    token: str,
    audio_bytes: bytes,
    filename: str = "news_audio.mp3",
    caption: str | None = None,
) -> dict:
    """
    Send an audio file to the Telegram user linked to `token`.

    Args:
        token: The user_token (e.g. tg_abc123) that was linked via /start.
        audio_bytes: Raw MP3 bytes.
        filename: Filename for the audio attachment.
        caption: Optional text caption sent with the audio.

    Returns:
        dict with success status and details.

    Raises:
        ValueError: If the token is not connected or bot token is missing.
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not configured.")

    conn = get_connection(token)
    if conn is None:
        raise ValueError(f"No Telegram account linked for token '{token}'.")

    chat_id = conn["chat_id"]
    url = f"https://api.telegram.org/bot{bot_token}/sendAudio"

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    data: dict = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption
    files = {"audio": (filename, audio_file, "audio/mpeg")}

    logger.info("Sending audio to chat_id=%s (token=%s, %d bytes)", chat_id, token, len(audio_bytes))

    resp = requests.post(url, data=data, files=files, timeout=30)

    if not resp.ok:
        error_detail = resp.text
        logger.error("Telegram sendAudio failed: %s %s", resp.status_code, error_detail)
        raise ValueError(f"Telegram API error ({resp.status_code}): {error_detail}")

    result = resp.json()
    logger.info("Audio sent successfully to chat_id=%s", chat_id)
    return {"success": True, "message_id": result.get("result", {}).get("message_id")}


# ── Bot Polling (background thread) ─────────────────────────────

_polling_thread: threading.Thread | None = None
_stop_event = threading.Event()


def start_polling() -> None:
    """Start the Telegram bot polling loop in a background daemon thread."""
    global _polling_thread

    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram bot polling disabled.")
        return

    if _polling_thread is not None and _polling_thread.is_alive():
        logger.info("Telegram polling already running.")
        return

    _stop_event.clear()
    _polling_thread = threading.Thread(target=_poll_loop, args=(bot_token,), daemon=True)
    _polling_thread.start()
    logger.info("✅ Telegram bot polling started (background thread).")


def stop_polling() -> None:
    """Signal the polling thread to stop."""
    _stop_event.set()
    logger.info("Telegram bot polling stop requested.")


def _poll_loop(bot_token: str) -> None:
    """
    Long-polling loop that listens for /start commands.
    When a user sends `/start <token>`, we store the mapping
    token → chat_id and reply with a confirmation message.
    """
    base_url = f"https://api.telegram.org/bot{bot_token}"
    offset = 0

    logger.info("Telegram polling loop started. Listening for /start commands...")

    while not _stop_event.is_set():
        try:
            resp = requests.get(
                f"{base_url}/getUpdates",
                params={"offset": offset, "timeout": 25},
                timeout=30,
            )

            if not resp.ok:
                logger.error("getUpdates failed: %s %s", resp.status_code, resp.text[:200])
                time.sleep(5)
                continue

            data = resp.json()
            updates = data.get("result", [])

            for update in updates:
                offset = update["update_id"] + 1
                _handle_update(update, base_url)

        except requests.exceptions.Timeout:
            # Normal for long-polling — just retry
            continue
        except requests.exceptions.ConnectionError as e:
            logger.error("Telegram connection error: %s", e)
            time.sleep(10)
        except Exception as e:
            logger.error("Unexpected error in polling loop: %s", e, exc_info=True)
            time.sleep(5)

    logger.info("Telegram polling loop stopped.")


def _handle_update(update: dict, base_url: str) -> None:
    """Process a single Telegram update. We only care about /start commands."""
    message = update.get("message")
    if not message:
        return

    text = message.get("text", "").strip()
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    from_user = message.get("from", {})
    username = from_user.get("username")
    first_name = from_user.get("first_name")

    if not text.startswith("/start"):
        return

    # Extract the token from "/start tg_abc123"
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        # Just "/start" with no token — send a welcome message
        _send_message(
            base_url,
            chat_id,
            "👋 Welcome to YourNews!\n\n"
            "To connect your account, please use the 'Connect Telegram' button "
            "on the YourNews website. It will open this bot with a special link.\n\n"
            "Once connected, you'll receive your AI audio news briefings right here! 🎧",
        )
        return

    token = parts[1].strip()
    logger.info(
        "Received /start with token=%s from chat_id=%s (username=%s, name=%s)",
        token, chat_id, username, first_name,
    )

    # Store the mapping
    with _lock:
        _connections[token] = TelegramConnection(
            chat_id=chat_id,
            username=username,
            first_name=first_name,
        )

    logger.info("✅ Linked token=%s → chat_id=%s", token, chat_id)

    # Send confirmation to the user
    display_name = first_name or username or "there"
    _send_message(
        base_url,
        chat_id,
        f"✅ Connected successfully, {display_name}!\n\n"
        "Your Telegram is now linked to YourNews. "
        "When you generate an audio briefing on the website, you can send it "
        "directly here with one click.\n\n"
        "🎧 Enjoy your personalized audio news!",
    )


def _send_message(base_url: str, chat_id: int, text: str) -> None:
    """Send a text message to a Telegram chat."""
    try:
        requests.post(
            f"{base_url}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception as e:
        logger.error("Failed to send message to chat_id=%s: %s", chat_id, e)
