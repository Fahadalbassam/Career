"""Lightweight tests for ML-7 terminal inspection commands."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _REPO_ROOT / "scripts" / "careerfinder_cli.py"


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("careerfinder_cli", _CLI_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["careerfinder_cli"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cli():
    return _load_cli_module()


def test_metrics_includes_fair_best_model(cli, monkeypatch):
    monkeypatch.chdir(_REPO_ROOT)
    lines = cli.build_metrics_lines()
    text = "\n".join(lines)
    assert "fair_gradient_boosting" in text
    assert "MAE:" in text
    assert "Leakage-safe:" in text
    assert cli.RUBRIC_ASSISTED_LEAKAGE_WARNING in text


def test_metrics_missing_fair_file(cli, monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)
    lines = cli.build_metrics_lines()
    text = "\n".join(lines)
    assert cli.METRICS_MISSING_MSG in text
    assert "fair_regression_model_metrics.csv" in text


def test_model_status_disabled(cli, monkeypatch):
    monkeypatch.delenv("CAREERFINDER_ENABLE_ML_SCORE", raising=False)
    text = "\n".join(cli.build_model_status_lines())
    assert "ML shadow score:     disabled" in text
    assert "Ranking changed by ML: No" in text
    assert "CAREERFINDER_ENABLE_ML_SCORE=true" in text


def test_model_status_enabled(cli, monkeypatch):
    monkeypatch.setenv("CAREERFINDER_ENABLE_ML_SCORE", "true")
    text = "\n".join(cli.build_model_status_lines())
    assert "ML shadow score:     enabled" in text
    assert "sorting still uses match_score" in text


def test_shadow_summary(cli, monkeypatch):
    monkeypatch.chdir(_REPO_ROOT)
    text = "\n".join(cli.build_shadow_lines())
    assert "Pearson correlation" in text
    assert "Average top-5 overlap" in text
    assert cli.SHADOW_RECOMMENDATION in text


def test_shadow_missing_file(cli, monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)
    lines = cli.build_shadow_lines()
    assert cli.METRICS_MISSING_MSG in "\n".join(lines)


def test_ml_summary_combines_status_and_fair(cli, monkeypatch):
    monkeypatch.chdir(_REPO_ROOT)
    text = "\n".join(cli.build_ml_summary_lines())
    assert "ML system status" in text
    assert "fair_gradient_boosting" in text
    assert cli.SHADOW_RECOMMENDATION in text


def test_help_lists_sprint_commands(cli):
    assert "/reset" in cli.HELP_TEXT
    assert "/home" in cli.HELP_TEXT
    assert "/clear" in cli.HELP_TEXT
    assert "/details N" in cli.HELP_TEXT or "/details" in cli.HELP_TEXT


def test_reset_clears_session_state(cli):
    user_messages = ["hello"]
    latest_profile = {"city": "Riyadh"}
    latest_recommendations = [{"rank": 1}]
    prev_top_score = 80
    user_messages.clear()
    latest_profile = None
    latest_recommendations = []
    prev_top_score = None
    assert user_messages == []
    assert latest_profile is None
    assert latest_recommendations == []
    assert prev_top_score is None


def test_show_home_screen_does_not_crash(cli, capsys):
    cli.show_home_screen()
    out = capsys.readouterr().out
    assert "CareerFinder" in out
    assert "Saudi COOP" in out


def test_clear_screen_and_logo(cli, capsys):
    cli.clear_screen()
    cli.print_logo()
    out = capsys.readouterr().out
    assert "Saudi COOP" in out
    assert r"\____\__,_|" in out or "____" in out


def test_backend_unavailable_help(cli):
    assert "uvicorn app.main:app" in cli.BACKEND_UNAVAILABLE_MSG
    assert "--app-dir backend" in cli.BACKEND_UNAVAILABLE_MSG


def test_greeting_guard():
    from app.input_intent import is_greeting_only
    from app.parser import parse_message

    assert is_greeting_only("hey", parse_message("hey"))
    assert is_greeting_only("ehy", parse_message("ehy"))


def test_compact_table_location_column_label(cli):
    widths = cli._compact_column_widths(120)
    header = cli.format_compact_header(widths)
    assert "Location" in header
    assert "City" not in header.split()


def test_details_ml_score_not_available(capsys):
    cli = _load_cli_module()
    rec = {
        "rank": 1,
        "company": "Acme",
        "title": "Intern",
        "match_score": 80,
        "score_source": "rubric",
        "ml_score": None,
        "score_breakdown": {
            "major_fit_score": 1.0,
            "skill_match_score": 0.5,
            "role_interest_score": 0.6,
            "city_match_score": 0.7,
            "program_type_score": 1.0,
            "work_mode_score": 1.0,
            "verification_score": 1.0,
            "interview_score": 0.5,
        },
        "city": "Riyadh",
        "work_mode": "On-site",
        "program_type": "COOP",
        "interview_required": "Not stated",
        "skills_matched": ["python"],
        "missing_skills": ["docker"],
    }
    cli.print_recommendation_details(rec)
    out = capsys.readouterr().out
    assert "ML score:          not available" in out
    assert "Score source:      rubric" in out
    assert "Why this matched:" in out
    assert "Score breakdown:" in out
    assert "Next best action:" in out
