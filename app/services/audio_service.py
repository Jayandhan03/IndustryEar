"""
Text-to-Speech service — Google TTS (gTTS).
"""

import io
import logging

from gtts import gTTS

logger = logging.getLogger(__name__)


def generate_audio_stream(
    script: str,
    voice_id: str | None = None,
    model_id: str | None = None,
    chunk_size: int = 4096,
):
    """
    Convert text to an MP3 audio stream using Google TTS.

    Args:
        script: The text to synthesize.
        voice_id: Accepted for API compatibility (unused by gTTS).
        model_id: Accepted for API compatibility (unused by gTTS).
        chunk_size: Bytes per yielded chunk.

    Yields:
        bytes: Chunks of MP3 audio data.

    Raises:
        ValueError: If the script is empty or whitespace-only.
    """
    if not script or not script.strip():
        raise ValueError("Script text is empty — cannot generate audio.")

    logger.info("Generating TTS audio via gTTS (%d chars)", len(script))

    tts = gTTS(text=script, lang="en")

    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)

    while True:
        chunk = buffer.read(chunk_size)
        if not chunk:
            break
        yield chunk
