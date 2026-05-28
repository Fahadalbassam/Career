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


def test_details_ml_score_not_available(capsys):
    cli = _load_cli_module()
    rec = {
        "rank": 1,
        "company": "Acme",
        "title": "Intern",
        "match_score": 80,
        "score_source": "rubric",
        "ml_score": None,
    }
    cli.print_recommendation_details(rec)
    out = capsys.readouterr().out
    assert "ML score:          not available" in out
    assert "Score source:      rubric" in out
