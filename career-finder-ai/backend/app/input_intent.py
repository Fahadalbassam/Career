"""
input_intent.py – Greeting/noise guards and recommendation-worthiness checks.

Used by the terminal CLI and ``recommend_from_message`` so casual greetings,
typos, and empty profiles do not trigger weak Top-5 rankings.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from app.role_families import is_discovery_phrase
from app.role_inference import detect_discovery_mode, infer_role_families
from app.schemas import ParsedProfile

# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

_PUNCT_RE = re.compile(r"[^\w\s\u0600-\u06FF]+", re.UNICODE)


def normalize_intent_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    if not text:
        return ""
    folded = unicodedata.normalize("NFKC", text).strip().lower()
    folded = _PUNCT_RE.sub(" ", folded)
    return " ".join(folded.split())


# ---------------------------------------------------------------------------
# Greeting detection
# ---------------------------------------------------------------------------

_GREETING_TOKENS = frozenset(
    {
        "hi",
        "hey",
        "hello",
        "heyy",
        "hii",
        "ehy",
        "hola",
        "salam",
        "مرحبا",
        "هلا",
    }
)

_GREETING_PHRASES = (
    "good morning",
    "good evening",
    "salam alaikum",
    "assalamu alaikum",
    "assalamualaikum",
    "السلام عليكم",
)


def is_greeting_only(message: str, profile: Optional[ParsedProfile] = None) -> bool:
    """True when the message is only a greeting with no career signal."""
    if profile is not None and has_profile_signal(profile):
        return False

    norm = normalize_intent_text(message)
    if not norm:
        return False

    for phrase in _GREETING_PHRASES:
        if norm == phrase or norm.startswith(phrase + " "):
            return True

    tokens = norm.split()
    if len(tokens) == 1 and tokens[0] in _GREETING_TOKENS:
        return True

    # Allow short multi-token greetings without career words.
    if len(tokens) <= 4 and all(t in _GREETING_TOKENS or t in {"alaikum", "assalamu"} for t in tokens):
        joined = " ".join(tokens)
        if any(phrase in joined for phrase in ("salam", "assalam", "alaikum")):
            return True

    return False


# ---------------------------------------------------------------------------
# Noise / low-signal replies
# ---------------------------------------------------------------------------

_NOISE_TOKENS = frozenset({"ok", "yes", "no", "asdf", "test", "lol", "hmm", "hm"})


def is_noise_only(message: str, profile: ParsedProfile) -> bool:
    """Random or one-word replies with nothing parsed."""
    if has_profile_signal(profile):
        return False
    norm = normalize_intent_text(message)
    if not norm:
        return True
    tokens = norm.split()
    if len(tokens) == 1 and tokens[0] in _NOISE_TOKENS:
        return True
    if len(tokens) == 1 and len(tokens[0]) <= 4 and tokens[0].isalpha():
        return tokens[0] not in _GREETING_TOKENS
    return False


# ---------------------------------------------------------------------------
# Profile signals
# ---------------------------------------------------------------------------


def _is_present(value: str | None) -> bool:
    if value is None:
        return False
    stripped = str(value).strip()
    return stripped != "" and stripped.lower() != "not stated"


def has_location_signal(profile: ParsedProfile) -> bool:
    return (
        _is_present(profile.city)
        or _is_present(profile.home_city)
        or bool(profile.preferred_locations)
        or bool(profile.acceptable_locations)
    )


def has_anchor_signal(profile: ParsedProfile) -> bool:
    """Strong signals that anchor a useful ranking."""
    return (
        _is_present(profile.major)
        or has_location_signal(profile)
        or _is_present(profile.interest)
        or bool(profile.preferred_roles)
    )


def has_profile_signal(profile: ParsedProfile) -> bool:
    """Any parsed field that could matter for matching or guidance."""
    return (
        has_anchor_signal(profile)
        or bool(profile.skills)
        or _is_present(profile.program_type)
        or _is_present(profile.work_mode)
        or _is_present(profile.interview_preference)
        or bool(profile.qualifications)
    )


def is_role_guidance_only(message: str, profile: ParsedProfile) -> bool:
    """Skills-only or ambiguous role hints without enough context to rank."""
    if is_discovery_phrase(message):
        return True
    if detect_discovery_mode(message, profile):
        return True

    if has_anchor_signal(profile):
        return False

    if not profile.skills:
        return False

    try:
        result = infer_role_families(profile, message=message)
    except Exception:  # noqa: BLE001
        return True

    if result.discovery_mode or result.is_ambiguous:
        return True

    # Single-skill statements like "I know SQL".
    if len(profile.skills) <= 2 and not _is_present(profile.program_type):
        return True

    return False


def should_recommend(message: str, profile: ParsedProfile) -> bool:
    """Return True when the message warrants ranked recommendations."""
    if is_greeting_only(message, profile):
        return False
    if is_noise_only(message, profile):
        return False
    if is_role_guidance_only(message, profile):
        return False
    if not has_profile_signal(profile):
        return False
    if not has_anchor_signal(profile):
        secondary = sum(
            1
            for flag in (
                bool(profile.skills),
                _is_present(profile.program_type),
                _is_present(profile.work_mode),
                _is_present(profile.interview_preference),
            )
            if flag
        )
        return secondary >= 2
    return True


# ---------------------------------------------------------------------------
# User-facing copy
# ---------------------------------------------------------------------------

_DEFAULT_PROMPT = (
    "Hi! Tell me your major, city, skills, and whether you want COOP or internship, "
    "and I'll recommend suitable Saudi opportunities."
)

_SALAM_REPLY = (
    "Wa alaikum assalam! Tell me your major, city, skills, and preferred role "
    "so I can recommend suitable opportunities."
)

_INSUFFICIENT_PROFILE_MSG = (
    "I could not extract enough career information yet. Please tell me your major, "
    "city, skills, and whether you want COOP or internship."
)


def build_greeting_reply(message: str) -> str:
    norm = normalize_intent_text(message)
    if any(
        token in norm
        for token in ("salam", "assalam", "alaikum", "السلام", "عليكم")
    ):
        return _SALAM_REPLY
    return _DEFAULT_PROMPT


def build_insufficient_profile_reply() -> str:
    return _INSUFFICIENT_PROFILE_MSG


def build_guidance_reply(message: str, profile: ParsedProfile) -> str:
    """Reply for guidance-only turns (discovery, ambiguous role, noise)."""
    if is_greeting_only(message, profile):
        return build_greeting_reply(message)
    if is_noise_only(message, profile):
        return build_insufficient_profile_reply()

    if is_discovery_phrase(message) or detect_discovery_mode(message, profile):
        try:
            result = infer_role_families(profile, message=message)
            if result.guided_question:
                return result.guided_question
        except Exception:  # noqa: BLE001
            pass
        from app.role_families import DISCOVERY_QUESTION

        return DISCOVERY_QUESTION

    try:
        result = infer_role_families(profile, message=message)
        if result.guided_question:
            return result.guided_question
        from app.role_inference import format_role_directions

        directions = format_role_directions(result)
        if directions:
            return directions
    except Exception:  # noqa: BLE001
        pass

    return build_insufficient_profile_reply()
