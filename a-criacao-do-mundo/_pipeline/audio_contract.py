"""Canonical audio prompts and cache inputs shared by generation and validation."""

from __future__ import annotations


VOICE_TEST_TEXT = (
    "Oi! Que bom ter você aqui. Hoje a gente vai embarcar numa aventura cheia "
    "de coragem, esperança e fé. O barco já está no porto, e o coração bate forte."
)

TTS_JOB_TYPE = "eleven_multilingual_v2"
NARRATION_TTS_MODEL = "eleven_v3"
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
    text: str,
    voice_id: str,
    provider: str = TTS_PROVIDER,
    *,
    direction: str = "",
    model: str = TTS_JOB_TYPE,
) -> dict[str, str]:
    values = {
        "model": provider,
        "voice_id": voice_id,
        "voice_type": "elevenlabs",
        "prompt": text,
        "tts_model": model,
    }
    if model == NARRATION_TTS_MODEL:
        values.update(
            {
                "direction": direction,
                "stability": "0.50",
                "similarity_boost": "0.78",
                "speed": "0.90",
                "post_atempo": "0.95",
            }
        )
    return values


def narration_direction(scene_id: str, act: str, voice: str) -> str:
    special = {
        "04": "[powerful] [with awe]",
        "05": "[excited] [filled with wonder]",
        "12": "[powerful] [building excitement]",
        "15": "[delighted] [animated storytelling]",
        "21": "[joyful] [playfully]",
        "22": "[joyful] [filled with wonder]",
        "23": "[joyful] [filled with wonder]",
        "25": "[joyful] [filled with wonder]",
        "29": "[tender] [with awe]",
        "30": "[amazed] [joyfully]",
        "31": "[warmly] [reassuring]",
        "32": "[tender] [softly]",
        "33": "[tender] [softly]",
        "34": "[tender] [softly]",
        "35": "[overjoyed] [warmly]",
        "36": "[brightly] [hopeful]",
        "38": "[peaceful] [reverent]",
        "39": "[warmly] [reassuring]",
        "40": "[warmly] [reassuring]",
    }
    if scene_id in special:
        return special[scene_id]
    if voice == "deus":
        return "[warmly] [with quiet authority]"
    return {
        "gancho": "[hushed] [mysterious storytelling]",
        "vazio": "[hushed] [mysterious storytelling]",
        "luz": "[with awe] [animated storytelling]",
        "ceu": "[with awe] [animated storytelling]",
        "astros": "[with awe] [animated storytelling]",
        "terra": "[warmly] [filled with wonder]",
        "vida": "[joyful] [animated storytelling]",
        "humanidade": "[tender] [warm storytelling]",
        "descanso": "[peaceful] [softly]",
        "aplicacao": "[warmly] [reassuring]",
    }.get(act, "[warmly] [animated storytelling]")


def narration_tts_values(
    scene_id: str,
    act: str,
    voice: str,
    text: str,
    voice_id: str,
    provider: str = TTS_PROVIDER,
) -> dict[str, str]:
    return tts_values(
        text,
        voice_id,
        provider,
        direction=narration_direction(scene_id, act, voice),
        model=NARRATION_TTS_MODEL,
    )


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
