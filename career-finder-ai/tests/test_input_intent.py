"""Tests for HOTFIX-4.1 greeting/noise guards and recommendation gating."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from app.input_intent import (
    build_greeting_reply,
    is_greeting_only,
    should_recommend,
)
from app.parser import parse_message
from app.recommender import recommend_from_message

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _REPO_ROOT / "scripts" / "careerfinder_cli.py"

FULL_DEMO_MESSAGE = (
    "I am a CS student in Khobar looking for cybersecurity COOP. "
    "I know SQL, MongoDB, Linux, networking, and SIEM. "
    "I prefer on-site and I want an interview. "
    "I want to work in Security Operations."
)


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("careerfinder_cli_intent", _CLI_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["careerfinder_cli_intent"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cli():
    return _load_cli_module()


@pytest.mark.parametrize(
    "message",
    ["hey", "ehy", "hi", "salam", "السلام عليكم"],
)
def test_greeting_detected_as_small_talk(message: str):
    profile = parse_message(message)
    assert is_greeting_only(message, profile)


def test_greeting_reply_does_not_mention_recommendations_ranking():
    reply = build_greeting_reply("hey")
    assert "major" in reply.lower()
    assert "coop" in reply.lower() or "internship" in reply.lower()


def test_salam_reply_is_islamic_greeting():
    reply = build_greeting_reply("salam alaikum")
    assert "Wa alaikum assalam" in reply


@pytest.mark.parametrize(
    "message",
    ["hey", "ehy", "asdf", "ok"],
)
def test_should_not_recommend_greeting_or_noise(message: str):
    profile = parse_message(message)
    assert not should_recommend(message, profile)


def test_discovery_phrase_guidance_without_recommendations():
    message = "I don't know what role I want"
    profile = parse_message(message)
    assert not should_recommend(message, profile)
    response = recommend_from_message(message)
    assert response.recommendations == []


def test_i_know_sql_guidance_without_recommendations():
    message = "I know SQL"
    profile = parse_message(message)
    assert not should_recommend(message, profile)
    response = recommend_from_message(message)
    assert response.recommendations == []


def test_full_demo_still_recommends():
    profile = parse_message(FULL_DEMO_MESSAGE)
    assert should_recommend(FULL_DEMO_MESSAGE, profile)
    response = recommend_from_message(FULL_DEMO_MESSAGE)
    assert response.recommendations
    assert all(r.score_source == "rubric" for r in response.recommendations[:3])
    assert response.recommendations[0].match_score >= 70


def test_terminal_header_shows_ascii_logo(cli, capsys):
    cli.print_logo()
    out = capsys.readouterr().out
    assert "Saudi COOP" in out
    assert "|  ___(_)_ __" in out or "____" in out


def test_backend_unavailable_message_includes_uvicorn_command(cli):
    assert "uvicorn app.main:app" in cli.BACKEND_UNAVAILABLE_MSG
    assert "--app-dir backend" in cli.BACKEND_UNAVAILABLE_MSG


def test_cli_skip_recommend_does_not_call_post(monkeypatch, cli):
    called: list[str] = []

    def fake_post(_message: str) -> dict:
        called.append(_message)
        return {"profile": {}, "recommendations": [], "total_candidates": 0}

    monkeypatch.setattr(cli, "post_recommend", fake_post)
    profile, recs, _score = cli._send_and_render(
        ["hey"],
        "compact",
        None,
        None,
    )
    assert called == []
    assert recs == []
    assert profile is not None
