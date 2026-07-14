"""Canonical audio prompts and cache inputs shared by generation and validation."""

from __future__ import annotations


VOICE_TEST_TEXT = (
    "Oi! Que bom ter você aqui. Hoje a gente vai embarcar numa aventura cheia "
    "de coragem, esperança e fé. O barco já está no porto, e o coração bate forte."
)

TTS_JOB_TYPE = "eleven_multilingual_v2"
TTS_PROVIDER = "elevenlabs"
SFX_JOB_TYPE = "sound_generation"
MUSIC_JOB_TYPE = "music"

SFX_SUFFIX = (
    "Cinematic layered sound design for a premium family animated film. "
    "No dialogue, no voices, no narration, no music."
)

MUSIC_SUFFIX = (
    "Instrumental cinematic score for a premium family animated film. "
    "No vocals, no speech, clean ending."
)


def tts_values(
    text: str, voice_id: str, provider: str = TTS_PROVIDER
) -> dict[str, str]:
    return {
        "model": provider,
        "voice_id": voice_id,
        "voice_type": "elevenlabs",
        "prompt": text,
        "tts_model": TTS_JOB_TYPE,
    }


def effective_sfx_prompt(prompt: str) -> str:
    return f"{prompt.strip()}. {SFX_SUFFIX}"


def sfx_values(prompt: str, duration: float) -> dict[str, str]:
    return {
        "duration": f"{duration:.2f}",
        "prompt": effective_sfx_prompt(prompt),
    }


def effective_music_prompt(prompt: str) -> str:
    return f"{prompt.strip()}. {MUSIC_SUFFIX}"


def music_values(prompt: str, duration: float) -> dict[str, str]:
    return {
        "duration": f"{duration:.2f}",
        "prompt": effective_music_prompt(prompt),
    }
