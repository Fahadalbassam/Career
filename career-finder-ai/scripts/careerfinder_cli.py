#!/usr/bin/env python3
"""
CareerFinder.ai terminal client — interactive chat against POST /recommend.

Uses only the Python standard library. No persistent storage.
Default output: compact profile + assistant reply + one-line recommendation rows.

ML-2B updates
=============

* Accidental-input guard. Empty input, single letters ("n", "y"), and
  ``/n`` style typos no longer call the backend.
* New commands: ``/undo`` (remove last user message, rerun if any remain)
  and ``/history`` (print numbered remembered user messages).
* Loading pattern. After a real message is accepted the CLI echoes the
  user input and prints "Analyzing profile" with a 3-step text spinner
  before calling ``POST /recommend``.
* Compact table now uses fixed-width columns (rank 4, score 6,
  company 28, program 32, city 14, mode 12, missing remaining) that
  collapse gracefully on narrow terminals.
* Score-change explanation. After each response the CLI compares the new
  top score / interest / skills / city / work mode / program type to the
  previous turn and prints a short "why did this change?" note.
* Assistant output uses ``=== Section ===`` headers (ANSI bold when the
  terminal supports it).
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any, Literal

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.assistant_reply import (  # noqa: E402
    build_assistant_reply as _build_assistant_reply,
    build_assistant_reply_parts,
    format_assistant_reply,
)

API_BASE = os.environ.get("CAREERFINDER_API_BASE", "http://127.0.0.1:8000").rstrip("/")

OutputMode = Literal["compact", "verbose", "split"]
SPLIT_MIN_COLUMNS = 120

# Compact table column budget (in characters).
COL_RANK = 4
COL_SCORE = 6
COL_COMPANY = 28
COL_PROGRAM = 32
COL_CITY = 14
COL_MODE = 12
COL_MISSING_MIN = 12

ACCIDENTAL_INPUT_MSG = (
    "That looks accidental. Type a full message, /help, /details 1, or /exit."
)

ASCII_LOGO = r"""
 _____                         ______ _           _                       _ 
/  __ \                        |  ___(_)         | |                     (_)
| /  \/ __ _ _ __ ___  ___ _ __| |_   _ _ __   __| | ___ _ __        __ _ _ 
| |    / _` | '__/ _ \/ _ \ '__|  _| | | '_ \ / _` |/ _ \ '__|      / _` | |
| \__/\ (_| | | |  __/  __/ |  | |   | | | | | (_| |  __/ |     _  | (_| | |
 \____/\__,_|_|  \___|\___|_|  \_|   |_|_| |_|\__,_|\___|_|    (_)  \__,_|_|
""".strip(
    "\n"
)

PLAIN_LOGO = "CareerFinder.ai"

HELP_TEXT = """
Commands:
  /help              Show this help
  /profile           Full parsed profile (all fields)
  /top               Compact top 5 (default)
  /top N             Compact top N
  /details N         Full details for recommendation rank N
  /open N            Open rank N source URL in your browser
  /links             All ranked source URLs (raw)
  /history           Show remembered user messages
  /undo              Remove last user message and rerun (if any remain)
  /metrics           Fair + rubric-assisted model metrics (from ML reports)
  /model             Live ML shadow status (ranking stays rubric-based)
  /shadow            Rubric vs ML comparison summary
  /ml                Short combined ML status + key metrics
  /compact           Default compact output
  /verbose           Verbose multi-line recommendation output
  /split             Side-by-side layout when terminal >= 120 cols
  /clear             Clear conversation and screen
  /login             Login placeholder (stub)
  /guest             Continue as guest
  /exit              Quit

Type a natural-language message to update your profile and get recommendations.
Messages accumulate across turns (same as the web chat).
Use /details N or /open N to inspect a specific match.
""".strip()

COMMANDS_TIP = (
    "Commands: /details 1 | /open 1 | /links | /undo | /history | /help"
)

NO_RECS_MSG = "No recommendations yet. Send your profile first."

METRICS_MISSING_MSG = (
    "Metrics file not found. Run ML-3/ML-4/ML-5 scripts first."
)

RUBRIC_ASSISTED_LEAKAGE_WARNING = (
    "Rubric-assisted metrics are a leakage demo and should not be reported "
    "as honest model performance."
)

SHADOW_RECOMMENDATION = (
    "keep rubric primary, use ML as shadow score"
)

ML_SCORE_SOURCE = "fair_gradient_boosting"
MODEL_ARTIFACT_REL = "models/fair_gradient_boosting_model.joblib"


def repo_root() -> Path:
    """Career-finder-ai repo root (parent of ``scripts/``)."""
    return Path(__file__).resolve().parents[1]


def is_ml_shadow_enabled() -> bool:
    return os.environ.get("CAREERFINDER_ENABLE_ML_SCORE", "").strip().lower() == "true"


def _metrics_file_missing(path: Path) -> list[str]:
    return [
        METRICS_MISSING_MSG,
        f"Expected file: {path}",
        "",
    ]


def _read_metrics_csv(path: Path) -> list[dict[str, str]] | None:
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except (OSError, csv.Error):
        return None


def _best_row_by_mae(rows: list[dict[str, str]], track: str) -> dict[str, str] | None:
    candidates = [r for r in rows if (r.get("track") or "").strip() == track]
    if not candidates:
        return None
    return min(candidates, key=lambda r: float(r.get("mae") or "inf"))


def _fmt_float(value: str | float | None, digits: int = 3) -> str:
    if value is None or value == "":
        return "—"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_pct_fraction(value: str | float | None) -> str:
    if value is None or value == "":
        return "—"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _split_description(row: dict[str, str]) -> str:
    train_rows = row.get("train_rows", "?")
    test_rows = row.get("test_rows", "?")
    train_profiles = row.get("train_profiles", "?")
    test_profiles = row.get("test_profiles", "?")
    return (
        f"GroupShuffleSplit by profile_id - "
        f"{train_rows} train / {test_rows} test rows "
        f"({train_profiles} train / {test_profiles} test profiles)"
    )


def _metrics_block_lines(label: str, row: dict[str, str], *, warning: str = "") -> list[str]:
    leakage = row.get("leakage_safe", "")
    leakage_text = "true" if str(leakage).lower() in ("true", "1", "yes") else str(leakage)
    lines = [
        _section_header(label),
        f"  Best model:        {row.get('model', '?')}",
        f"  MAE:               {_fmt_float(row.get('mae'))}",
        f"  RMSE:              {_fmt_float(row.get('rmse'))}",
        f"  R²:                {_fmt_float(row.get('r2'))}",
        f"  Precision@1:       {_fmt_pct_fraction(row.get('precision_at_1'))}",
        f"  Precision@3:       {_fmt_pct_fraction(row.get('precision_at_3'))}",
        f"  Precision@5:       {_fmt_pct_fraction(row.get('precision_at_5'))}",
        f"  Train rows:        {row.get('train_rows', '?')}",
        f"  Test rows:         {row.get('test_rows', '?')}",
        f"  Train/test split:  {_split_description(row)}",
        f"  Leakage-safe:      {leakage_text}",
        "",
    ]
    if warning:
        lines.insert(1, f"  WARNING: {warning}")
        lines.insert(2, "")
    return lines


def build_metrics_lines() -> list[str]:
    """Return lines for ``/metrics`` (fair + rubric-assisted sections)."""
    fair_path = repo_root() / "data/processed/fair_regression_model_metrics.csv"
    rubric_path = (
        repo_root() / "data/processed/rubric_assisted_regression_model_metrics.csv"
    )

    fair_rows = _read_metrics_csv(fair_path)
    if fair_rows is None:
        return _metrics_file_missing(fair_path)

    fair_best = _best_row_by_mae(fair_rows, "fair")
    if fair_best is None:
        return [
            METRICS_MISSING_MSG,
            f"Expected fair model rows in: {fair_path}",
            "",
        ]

    lines = _metrics_block_lines("Fair model metrics (leakage-safe)", fair_best)

    rubric_rows = _read_metrics_csv(rubric_path)
    if rubric_rows is None:
        lines.extend(_metrics_file_missing(rubric_path))
        return lines

    rubric_best = _best_row_by_mae(rubric_rows, "rubric_assisted")
    if rubric_best is None:
        lines.extend(
            [
                METRICS_MISSING_MSG,
                f"Expected rubric-assisted rows in: {rubric_path}",
                "",
            ]
        )
        return lines

    lines.extend(
        _metrics_block_lines(
            "Rubric-assisted model metrics (leakage demo)",
            rubric_best,
            warning=RUBRIC_ASSISTED_LEAKAGE_WARNING,
        )
    )
    return lines


def build_model_status_lines() -> list[str]:
    """Return lines for ``/model``."""
    artifact_path = repo_root() / MODEL_ARTIFACT_REL
    enabled = is_ml_shadow_enabled()
    artifact_exists = artifact_path.is_file()

    lines = [
        _section_header("ML system status"),
        "  Live ranking:        rubric match_score",
        f"  ML shadow score:     {'enabled' if enabled else 'disabled'}",
        f"  Model artifact:      {MODEL_ARTIFACT_REL}"
        + (" (found)" if artifact_exists else " (not found)"),
        "  Score source:        rubric",
        f"  ML score source:     {ML_SCORE_SOURCE}",
        "  Ranking changed by ML: No",
        "",
    ]
    if enabled:
        lines.append(
            "  ML shadow scoring is enabled. /recommend may return ml_score, "
            "but sorting still uses match_score."
        )
    else:
        lines.append(
            "  ML shadow scoring is disabled. Set CAREERFINDER_ENABLE_ML_SCORE=true "
            "to include ml_score."
        )
    lines.append("")
    return lines


def _read_json_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def build_shadow_lines() -> list[str]:
    """Return lines for ``/shadow``."""
    summary_path = repo_root() / "data/processed/rubric_vs_ml_summary.json"
    summary = _read_json_file(summary_path)
    if summary is None:
        return _metrics_file_missing(summary_path)

    return [
        _section_header("Rubric vs ML shadow comparison"),
        f"  Rows compared:              {summary.get('rows_compared', '?')}",
        f"  Profiles compared:          {summary.get('profiles_compared', '?')}",
        f"  Mean absolute difference:   {_fmt_float(summary.get('mean_absolute_difference'))}",
        f"  Median absolute difference: {_fmt_float(summary.get('median_absolute_difference'))}",
        f"  Max difference:             {_fmt_float(summary.get('max_absolute_difference'))}",
        f"  Pearson correlation:        {_fmt_float(summary.get('pearson_correlation'))}",
        f"  Spearman correlation:       {_fmt_float(summary.get('spearman_correlation'))}",
        f"  Average top-5 overlap:      {_fmt_float(summary.get('average_overlap_at_5'))}",
        f"  Recommendation:             {SHADOW_RECOMMENDATION}",
        "",
    ]


def build_ml_summary_lines() -> list[str]:
    """Return lines for ``/ml`` (status + best fair model + shadow note)."""
    lines = build_model_status_lines()

    fair_path = repo_root() / "data/processed/fair_regression_model_metrics.csv"
    fair_rows = _read_metrics_csv(fair_path)
    if fair_rows is None:
        lines.extend(_metrics_file_missing(fair_path))
        return lines

    fair_best = _best_row_by_mae(fair_rows, "fair")
    if fair_best is None:
        lines.extend(
            [
                METRICS_MISSING_MSG,
                f"Expected fair model rows in: {fair_path}",
                "",
            ]
        )
        return lines

    lines.extend(
        [
            _section_header("Best fair model (quick)"),
            f"  Model:  {fair_best.get('model', '?')}",
            f"  MAE:    {_fmt_float(fair_best.get('mae'))}",
            f"  R²:     {_fmt_float(fair_best.get('r2'))}",
            f"  Recommendation: {SHADOW_RECOMMENDATION}",
            "",
        ]
    )
    return lines


def print_metrics() -> None:
    for line in build_metrics_lines():
        _safe_print(line)


def print_model_status() -> None:
    for line in build_model_status_lines():
        _safe_print(line)


def print_shadow() -> None:
    for line in build_shadow_lines():
        _safe_print(line)


def print_ml_summary() -> None:
    for line in build_ml_summary_lines():
        _safe_print(line)


# ---------------------------------------------------------------------------
# Output helpers (ANSI bold + safe printing)
# ---------------------------------------------------------------------------

def _ansi_supported() -> bool:
    """Best-effort check for ANSI support in the current terminal."""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    if sys.platform == "win32":
        # Windows 10+ terminal and Windows Terminal handle ANSI; the CLI
        # is launched via PowerShell which enables VT processing in
        # modern Windows builds. Older consoles still tolerate "===" so
        # the headers remain readable even without bold.
        return os.environ.get("WT_SESSION") is not None or os.environ.get(
            "TERM_PROGRAM"
        ) is not None
    return True


_ANSI = _ansi_supported()
_BOLD = "\033[1m" if _ANSI else ""
_RESET = "\033[0m" if _ANSI else ""


def _safe_print(text: str = "") -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(
            text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
                sys.stdout.encoding or "utf-8", errors="replace"
            )
        )


def _section_header(label: str) -> str:
    """Build a ``=== Label ===`` section header (bold when ANSI is safe)."""
    return f"{_BOLD}=== {label} ==={_RESET}"


def terminal_width(default: int = 100) -> int:
    try:
        return shutil.get_terminal_size(fallback=(default, 24)).columns
    except OSError:
        return default


def truncate(text: str, width: int) -> str:
    if width <= 0:
        return ""
    text = " ".join(str(text).split())
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    if width == 2:
        return text[:2]
    return text[: width - 1] + "…"


def clear_screen() -> None:
    if sys.platform == "win32":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="")


def print_logo() -> None:
    try:
        _safe_print(ASCII_LOGO)
    except Exception:
        _safe_print(PLAIN_LOGO)
    _safe_print()
    _safe_print("Saudi COOP & internship recommender for computing students")
    _safe_print()


def is_missing(value: str | None) -> bool:
    if value is None:
        return True
    stripped = value.strip()
    return stripped == "" or stripped.lower() == "not stated"


def _fmt_list(items: list[str] | None, empty: str = "(none)") -> str:
    if not items:
        return empty
    return ", ".join(items)


# ---------------------------------------------------------------------------
# Input guard (Part A)
# ---------------------------------------------------------------------------

_ACCIDENTAL_SLASH_LETTERS = {"/n", "/y", "/n.", "/y."}


def is_accidental_input(line: str) -> bool:
    """Return True for input that should never be sent to /recommend.

    Treated as accidental:

    * Empty / whitespace-only.
    * A single alphabetical letter (e.g. ``"n"``, ``"y"``, ``"Y"``).
    * ``"/n"`` / ``"/y"`` style typos that look like a command but are
      not one of our real commands.

    Multi-letter input ("hi", "ok"), and known commands ("/exit",
    "/history", ...) are NOT accidental — they are handled by their own
    branches in :func:`main`.
    """
    stripped = line.strip()
    if not stripped:
        return True
    lowered = stripped.lower()
    if len(stripped) == 1 and stripped.isalpha():
        return True
    if lowered in _ACCIDENTAL_SLASH_LETTERS:
        return True
    return False


# ---------------------------------------------------------------------------
# Loading pattern (Part B)
# ---------------------------------------------------------------------------

def echo_user_input(line: str) -> None:
    """Print the user's accepted message so it remains visible after Enter."""
    _safe_print(f"\n{_BOLD}> {_RESET}{line}" if _ANSI else f"\n> {line}")


def show_loading_pattern(label: str = "Analyzing profile") -> None:
    """Print a small 3-step text loading pattern over ~1 second.

    Falls back to a single line on non-TTY targets so the CLI behaves the
    same when output is piped or captured by a test harness.
    """
    if not sys.stdout.isatty():
        _safe_print(f"{label}...")
        return

    for dots in (".", "..", "..."):
        # Use \r so the line rewrites in place.
        sys.stdout.write(f"\r{label}{dots}   ")
        sys.stdout.flush()
        time.sleep(0.35)

    sys.stdout.write("\r" + " " * (len(label) + 10) + "\r")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Assistant reply (delegates to app.assistant_reply)
# ---------------------------------------------------------------------------

def build_assistant_reply(
    profile: dict[str, Any], recommendations: list[dict[str, Any]]
) -> str:
    return _build_assistant_reply(profile, recommendations)


def format_assistant_block(
    profile: dict[str, Any], recommendations: list[dict[str, Any]]
) -> str:
    """Format assistant output with optional Top match / Next action lines."""
    parts = build_assistant_reply_parts(profile, recommendations)
    return format_assistant_reply(parts)


# ---------------------------------------------------------------------------
# Score-change explanation (Part G)
# ---------------------------------------------------------------------------

def diff_skills(prev: list[str] | None, curr: list[str] | None) -> list[str]:
    prev_set = {s.lower() for s in (prev or [])}
    return [s for s in (curr or []) if s.lower() not in prev_set]


def build_score_change_notes(
    prev_profile: dict[str, Any] | None,
    prev_top_score: int | None,
    new_profile: dict[str, Any],
    new_top_score: int | None,
) -> list[str]:
    """Return short human-readable notes describing what changed.

    The notes are deliberately brief — at most one line per change type.
    """
    notes: list[str] = []

    # Top-score drop of 5+ points (logical interpretation: profile got more
    # specific, narrowing the pool).
    if (
        prev_top_score is not None
        and new_top_score is not None
        and prev_top_score - new_top_score >= 5
    ):
        notes.append(
            "Note: Your top score dropped because the new details made the search more specific."
        )

    if not prev_profile:
        return notes

    # Interest change.
    prev_interest = (prev_profile.get("interest") or "").strip()
    new_interest = (new_profile.get("interest") or "").strip()
    if prev_interest and new_interest and prev_interest.lower() != new_interest.lower():
        notes.append(
            f"Interest changed from {prev_interest} to {new_interest}, so results were reranked."
        )

    # Newly added skills.
    added_skills = diff_skills(prev_profile.get("skills"), new_profile.get("skills"))
    if added_skills:
        notes.append(f"New skills added: {', '.join(added_skills)}.")

    # City change.
    prev_city = (prev_profile.get("city") or "").strip()
    new_city = (new_profile.get("city") or "").strip()
    if prev_city and new_city and prev_city.lower() != new_city.lower():
        notes.append(f"City changed from {prev_city} to {new_city}.")

    # Work mode change.
    prev_mode = (prev_profile.get("work_mode") or "").strip()
    new_mode = (new_profile.get("work_mode") or "").strip()
    if prev_mode and new_mode and prev_mode.lower() != new_mode.lower():
        notes.append(f"Work mode changed from {prev_mode} to {new_mode}.")

    # Program type change.
    prev_prog = (prev_profile.get("program_type") or "").strip()
    new_prog = (new_profile.get("program_type") or "").strip()
    if prev_prog and new_prog and prev_prog.lower() != new_prog.lower():
        notes.append(f"Program type changed from {prev_prog} to {new_prog}.")

    return notes


# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

def post_recommend(message: str) -> dict[str, Any]:
    url = f"{API_BASE}/recommend"
    payload = json.dumps({"message": message}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"POST /recommend failed ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot reach backend at {API_BASE}. "
            "Start it with: cd backend && python -m uvicorn app.main:app "
            "--reload --host 127.0.0.1 --port 8000"
        ) from exc


def find_recommendation_by_rank(
    recommendations: list[dict[str, Any]], rank: int
) -> dict[str, Any] | None:
    for rec in recommendations:
        if rec.get("rank") == rank:
            return rec
    if 1 <= rank <= len(recommendations):
        return recommendations[rank - 1]
    return None


# ---------------------------------------------------------------------------
# Profile / details / links rendering
# ---------------------------------------------------------------------------

def _profile_field_lines(profile: dict[str, Any], compact: bool) -> list[str]:
    lines: list[str] = []

    def add(label: str, value: str | None) -> None:
        if not is_missing(value):
            lines.append(f"  {label}: {value}")

    add("Major", profile.get("major"))
    add("University", profile.get("university"))
    add("City", profile.get("city"))
    add("Interest", profile.get("interest"))
    add("Program type", profile.get("program_type"))
    add("Work mode", profile.get("work_mode"))

    skills = profile.get("skills") or []
    if skills:
        lines.append(f"  Skills: {_fmt_list(skills)}")

    roles = profile.get("preferred_roles") or []
    if roles:
        lines.append(f"  Preferred roles: {_fmt_list(roles)}")
    interview = profile.get("interview_preference")
    if not is_missing(interview):
        lines.append(f"  Interview pref.: {interview}")

    if not compact:
        preferred = profile.get("preferred_locations") or []
        if preferred:
            lines.append(f"  Preferred locations: {_fmt_list(preferred)}")
        quals = profile.get("qualifications") or []
        if quals:
            lines.append(f"  Qualifications: {_fmt_list(quals)}")
    if not lines and compact:
        lines.append("  (no fields parsed yet)")
    return lines


def format_profile_block(profile: dict[str, Any], compact: bool = True) -> str:
    header = _section_header("Profile") if compact else _section_header("Profile (full)")
    lines = [header, *_profile_field_lines(profile, compact=compact), ""]
    return "\n".join(lines)


def print_profile_full(profile: dict[str, Any]) -> None:
    _safe_print()
    _safe_print(format_profile_block(profile, compact=False))
    _safe_print()


def _compact_missing_summary(rec: dict[str, Any], max_width: int) -> str:
    missing = rec.get("missing_skills") or []
    if not missing:
        return ""
    summary = ", ".join(missing[:3])
    if len(missing) > 3:
        summary += f" +{len(missing) - 3} more"
    return "missing: " + truncate(summary, max(8, max_width - 10))


# ---------------------------------------------------------------------------
# Compact table (Part C)
# ---------------------------------------------------------------------------

def _compact_column_widths(width: int) -> dict[str, int]:
    """Return per-column widths that fit within ``width`` characters.

    Targets the fixed budget specified for ML-2B::

        Rank: 4 | Score: 6 | Company: 28 | Program: 32 |
        City: 14 | Mode: 12 | Missing: remaining

    On narrow terminals (<100 cols) the company and program columns shrink
    proportionally so the row still fits. The missing column always keeps
    at least ``COL_MISSING_MIN`` characters.
    """
    rank, score = COL_RANK, COL_SCORE
    company, program = COL_COMPANY, COL_PROGRAM
    city, mode = COL_CITY, COL_MODE

    # Two spaces of padding between each pair of columns -> 6 separators.
    separators = 2 * 6
    minimum_missing = COL_MISSING_MIN

    fixed = rank + score + city + mode + separators + minimum_missing
    remaining = width - fixed

    if remaining < company + program:
        # Not enough room — shrink company and program proportionally.
        shrinkable = max(20, remaining)
        ratio = company / (company + program) if (company + program) else 0.5
        company = max(12, int(shrinkable * ratio))
        program = max(12, shrinkable - company)

    used = rank + score + company + program + city + mode + separators
    missing = max(minimum_missing, width - used)

    return {
        "rank": rank,
        "score": score,
        "company": company,
        "program": program,
        "city": city,
        "mode": mode,
        "missing": missing,
    }


def format_compact_header(widths: dict[str, int]) -> str:
    parts = [
        f"{'Rank':<{widths['rank']}}",
        f"{'Score':<{widths['score']}}",
        f"{'Company':<{widths['company']}}",
        f"{'Program':<{widths['program']}}",
        f"{'City':<{widths['city']}}",
        f"{'Mode':<{widths['mode']}}",
        f"{'Missing':<{widths['missing']}}",
    ]
    line = "  ".join(parts)
    return f"{_BOLD}{line}{_RESET}" if _ANSI else line


def format_compact_recommendation_row(rec: dict[str, Any], widths: dict[str, int]) -> str:
    rank = rec.get("rank", "?")
    score = rec.get("match_score", 0)
    company = rec.get("company", "?") or "—"
    program = rec.get("title", "?") or "—"
    city = rec.get("city", "") or "—"
    mode = rec.get("work_mode", "") or "—"

    rank_cell = f"#{rank}"
    score_cell = f"{score}%"

    missing_part = _compact_missing_summary(rec, widths["missing"])

    parts = [
        f"{truncate(rank_cell, widths['rank']):<{widths['rank']}}",
        f"{truncate(score_cell, widths['score']):<{widths['score']}}",
        f"{truncate(company, widths['company']):<{widths['company']}}",
        f"{truncate(program, widths['program']):<{widths['program']}}",
        f"{truncate(city, widths['city']):<{widths['city']}}",
        f"{truncate(mode, widths['mode']):<{widths['mode']}}",
        truncate(missing_part, widths["missing"]),
    ]
    return "  ".join(parts).rstrip()


def format_compact_recommendations_table(
    recommendations: list[dict[str, Any]], limit: int, width: int | None = None
) -> str:
    if not recommendations:
        return "No recommendations returned."

    w = width or terminal_width()
    widths = _compact_column_widths(w)

    lines = [
        _section_header(f"Top {min(limit, len(recommendations))} (compact)"),
        format_compact_header(widths),
    ]
    for rec in recommendations[:limit]:
        lines.append(format_compact_recommendation_row(rec, widths))
    lines.append("")
    lines.append(COMMANDS_TIP)
    return "\n".join(lines)


def print_recommendations_verbose(
    recommendations: list[dict[str, Any]], limit: int = 5
) -> None:
    if not recommendations:
        _safe_print("No recommendations returned.\n")
        return

    _safe_print(f"\n{_section_header(f'Top {min(limit, len(recommendations))} recommendations (verbose)')}")
    for rec in recommendations[:limit]:
        rank = rec.get("rank", "?")
        company = rec.get("company", "?")
        title = rec.get("title", "?")
        match_score = rec.get("match_score", 0)
        role_cluster = rec.get("role_cluster", "")
        city = rec.get("city", "")
        work_mode = rec.get("work_mode", "")
        program_type = rec.get("program_type", "")
        interview = rec.get("interview_required", "Not stated")
        matched = _fmt_list(rec.get("skills_matched"))
        missing = _fmt_list(rec.get("missing_skills"))
        why = rec.get("why_recommended") or []
        why_text = " • ".join(why) if why else "(none)"
        source = rec.get("source_url") or ""

        ml_score = rec.get("ml_score")
        ml_score_source = rec.get("ml_score_source") or ""
        score_source = rec.get("score_source", "rubric")

        _safe_print(f"\n  #{rank}  {company} — {title}")
        _safe_print(f"       Match score:     {match_score}%")
        _safe_print(f"       Score source:    {score_source}")
        if ml_score is not None:
            ml_label = f"({ml_score_source})" if ml_score_source else ""
            _safe_print(f"       ML score:        {ml_score}% {ml_label}".rstrip())
        _safe_print(f"       Role cluster:    {role_cluster or '(none)'}")
        _safe_print(f"       City:            {city}")
        _safe_print(f"       Work mode:       {work_mode}")
        _safe_print(f"       Program type:    {program_type}")
        _safe_print(f"       Interview:       {interview}")
        _safe_print(f"       Matched skills:  {matched}")
        _safe_print(f"       Missing skills:  {missing}")
        _safe_print(f"       Why recommended: {why_text}")
        if source:
            _safe_print(f"       Source:          {source}")
    _safe_print("\n--------------------------------\n")


_SCORE_BREAKDOWN_LABELS: dict[str, str] = {
    "major_fit_score": "Major fit",
    "city_match_score": "Location fit",
    "program_type_score": "Program fit",
    "work_mode_score": "Work mode fit",
    "role_interest_score": "Role/interest fit",
    "skill_match_score": "Skill fit",
    "verification_score": "Source confidence",
    "interview_score": "Interview fit",
}


def _format_score_breakdown(breakdown: dict[str, Any] | None) -> str:
    if not breakdown:
        return ""
    parts: list[str] = []
    for key, label in _SCORE_BREAKDOWN_LABELS.items():
        raw = breakdown.get(key)
        if raw is None:
            continue
        try:
            pct = int(round(float(raw) * 100))
        except (TypeError, ValueError):
            continue
        parts.append(f"{label} {pct}%")
    return " | ".join(parts)


def print_recommendation_details(rec: dict[str, Any]) -> None:
    rank = rec.get("rank", "?")
    _safe_print(f"\n{_section_header(f'Details #{rank}')}")
    _safe_print(f"  Company:           {rec.get('company', '?')}")
    _safe_print(f"  Title:             {rec.get('title', '?')}")
    _safe_print(f"  Match score:       {rec.get('match_score', 0)}%")
    _safe_print(f"  Score source:      {rec.get('score_source', 'rubric')}")
    breakdown_line = _format_score_breakdown(rec.get("score_breakdown"))
    if breakdown_line:
        _safe_print(f"  Score breakdown:   {breakdown_line}")
    ml_score = rec.get("ml_score")
    ml_source = rec.get("ml_score_source") or ""
    if ml_score is not None:
        ml_label = f"({ml_source})" if ml_source else ""
        _safe_print(f"  ML score:          {ml_score}% {ml_label}".rstrip())
    else:
        _safe_print("  ML score:          not available")
    _safe_print(f"  Role cluster:      {rec.get('role_cluster') or '(none)'}")
    _safe_print(f"  City:              {rec.get('city', '')}")
    _safe_print(f"  Work mode:         {rec.get('work_mode', '')}")
    _safe_print(f"  Program type:      {rec.get('program_type', '')}")
    _safe_print(f"  Interview:         {rec.get('interview_required', 'Not stated')}")
    _safe_print(f"  Matched skills:    {_fmt_list(rec.get('skills_matched'))}")
    _safe_print(f"  Missing skills:    {_fmt_list(rec.get('missing_skills'))}")
    why = rec.get("why_recommended") or []
    why_text = " • ".join(why) if why else "(none)"
    _safe_print(f"  Why recommended:   {why_text}")
    source = (rec.get("source_url") or "").strip()
    if source:
        _safe_print(f"  Source URL:        {source}")
    else:
        _safe_print("  Source URL:        (none)")
    _safe_print()


def print_links(recommendations: list[dict[str, Any]]) -> None:
    _safe_print(f"\n{_section_header('Ranked links')}")
    for rec in recommendations:
        rank = rec.get("rank", "?")
        company = rec.get("company", "?")
        url = (rec.get("source_url") or "").strip()
        if url:
            _safe_print(f"#{rank} {company} — {url}")
        else:
            _safe_print(f"#{rank} {company} — (no URL)")
    _safe_print()


def open_recommendation_url(rec: dict[str, Any]) -> None:
    rank = rec.get("rank", "?")
    url = (rec.get("source_url") or "").strip()
    if not url:
        _safe_print(f"No source URL for recommendation #{rank}.\n")
        return
    _safe_print(f"Opening #{rank}: {url}")
    if not webbrowser.open(url, new=2):
        _safe_print("Could not open browser. Copy the URL from /details or /links.\n")
    else:
        _safe_print()


# ---------------------------------------------------------------------------
# Split layout
# ---------------------------------------------------------------------------

def _wrap_text_block(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        while len(paragraph) > width:
            split_at = paragraph.rfind(" ", 0, width)
            if split_at <= 0:
                split_at = width
            lines.append(paragraph[:split_at].rstrip())
            paragraph = paragraph[split_at:].lstrip()
        if paragraph:
            lines.append(paragraph)
    return lines or [""]


def print_turn_result_split(
    profile: dict[str, Any],
    reply: str,
    recommendations: list[dict[str, Any]],
    total: int,
    limit: int = 5,
) -> None:
    width = terminal_width()
    left_width = max(40, (width - 4) // 2)
    right_width = max(40, width - left_width - 4)

    left_text = (
        format_profile_block(profile, compact=True)
        + f"\n{_section_header('Assistant')}\n  "
        + reply
        + f"\n\nScanned {total} opportunities."
    )
    right_text = format_compact_recommendations_table(
        recommendations, limit, width=right_width
    )

    left_lines = _wrap_text_block(left_text, left_width)
    right_lines = _wrap_text_block(right_text, right_width)
    max_lines = max(len(left_lines), len(right_lines))

    _safe_print()
    for i in range(max_lines):
        left = left_lines[i] if i < len(left_lines) else ""
        right = right_lines[i] if i < len(right_lines) else ""
        _safe_print(f"{left:<{left_width}}  |  {right}")
    _safe_print()


def print_turn_result(
    profile: dict[str, Any],
    reply: str,
    recommendations: list[dict[str, Any]],
    total: int,
    mode: OutputMode,
    limit: int = 5,
    notes: list[str] | None = None,
) -> None:
    width = terminal_width()

    if mode == "split" and width < SPLIT_MIN_COLUMNS:
        _safe_print(
            "Terminal is too narrow for split mode; using compact view.\n"
        )
        mode = "compact"

    if mode == "split" and width >= SPLIT_MIN_COLUMNS:
        print_turn_result_split(profile, reply, recommendations, total, limit=limit)
        if notes:
            for note in notes:
                _safe_print(note)
            _safe_print()
        return

    _safe_print()
    _safe_print(format_profile_block(profile, compact=True))
    _safe_print(_section_header("Assistant"))
    for reply_line in reply.split("\n"):
        _safe_print(f"  {reply_line}")
    _safe_print()
    _safe_print(f"Scanned {total} opportunities.")

    if mode == "verbose":
        print_recommendations_verbose(recommendations, limit=limit)
    else:
        _safe_print()
        _safe_print(
            format_compact_recommendations_table(recommendations, limit, width=width)
        )
        _safe_print()

    if notes:
        for note in notes:
            _safe_print(note)
        _safe_print()


# ---------------------------------------------------------------------------
# Startup auth (placeholder)
# ---------------------------------------------------------------------------

def prompt_startup_auth() -> tuple[str, str | None]:
    _safe_print("Welcome to CareerFinder.ai terminal chat.")
    _safe_print(f"Backend: {API_BASE}")
    _safe_print()
    _safe_print("[1] Continue as guest")
    _safe_print("[2] Login placeholder")
    _safe_print()

    while True:
        choice = input("Choose 1 or 2: ").strip()
        if choice in ("1", "guest", ""):
            _safe_print("\nContinuing as guest. No login required.\n")
            return "guest", None
        if choice in ("2", "login"):
            email = input("Email: ").strip()
            _safe_print()
            _safe_print(
                "Note: Login is currently a stub. No real auth or database persistence is used."
            )
            _safe_print("Your session continues in this terminal only.\n")
            return "login", email or None
        _safe_print("Please enter 1 or 2.")


def run_login_placeholder() -> str | None:
    email = input("Email: ").strip()
    _safe_print(
        "Note: Login is currently a stub. No real auth or database persistence is used.\n"
    )
    return email or None


def parse_top_limit(parts: list[str], default: int = 5) -> int | None:
    if len(parts) == 1:
        return default
    if len(parts) == 2 and parts[1].isdigit():
        return max(1, int(parts[1]))
    return None


def parse_rank_command(parts: list[str]) -> int | None:
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    return None


# ---------------------------------------------------------------------------
# Send/rerun helper (used by normal turns and /undo)
# ---------------------------------------------------------------------------

def _send_and_render(
    user_messages: list[str],
    output_mode: OutputMode,
    prev_profile: dict[str, Any] | None,
    prev_top_score: int | None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], int | None]:
    """Send the accumulated user messages and render the response.

    Returns ``(new_profile, new_recommendations, new_top_score)``. Returns
    ``(prev_profile, [], prev_top_score)`` on failure so the caller can keep
    showing the previous successful state.
    """
    combined = "\n".join(user_messages)
    _safe_print(f"Calling POST {API_BASE}/recommend ...")
    try:
        response = post_recommend(combined)
    except RuntimeError as exc:
        _safe_print(f"\nError: {exc}\n")
        return prev_profile, [], prev_top_score

    new_profile: dict[str, Any] = response.get("profile") or {}
    new_recommendations: list[dict[str, Any]] = response.get("recommendations") or []
    total = response.get("total_candidates", 0)
    reply = format_assistant_block(new_profile, new_recommendations)

    new_top_score: int | None = (
        int(new_recommendations[0].get("match_score", 0))
        if new_recommendations
        else None
    )

    notes = build_score_change_notes(
        prev_profile, prev_top_score, new_profile, new_top_score
    )

    print_turn_result(
        new_profile,
        reply,
        new_recommendations,
        total,
        mode=output_mode,
        limit=5,
        notes=notes,
    )

    return new_profile, new_recommendations, new_top_score


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> int:
    print_logo()
    session_mode, login_email = prompt_startup_auth()

    user_messages: list[str] = []
    latest_profile: dict[str, Any] | None = None
    latest_recommendations: list[dict[str, Any]] = []
    prev_top_score: int | None = None
    output_mode: OutputMode = "compact"

    _safe_print("Type your profile in natural language, or /help for commands.")
    _safe_print("Default view: compact. Use /verbose for full cards.\n")

    while True:
        try:
            line = input("You> ")
        except (EOFError, KeyboardInterrupt):
            _safe_print("\nGoodbye.")
            return 0

        # Strip but keep original for echo.
        stripped = line.strip()

        # Part A: accidental-input guard. Empty, single-letter, or "/n"
        # style typos should never call /recommend.
        if is_accidental_input(stripped):
            _safe_print(ACCIDENTAL_INPUT_MSG)
            continue

        lower = stripped.lower()
        parts = lower.split()

        if lower in ("/exit", "/quit", "exit", "quit"):
            _safe_print("Goodbye.")
            return 0

        if lower == "/help":
            _safe_print(HELP_TEXT)
            continue

        if lower == "/metrics":
            print_metrics()
            continue

        if lower in ("/model",):
            print_model_status()
            continue

        if lower == "/shadow":
            print_shadow()
            continue

        if lower == "/ml":
            print_ml_summary()
            continue

        if lower == "/compact":
            output_mode = "compact"
            _safe_print("Output mode: compact (default).\n")
            continue

        if lower == "/verbose":
            output_mode = "verbose"
            _safe_print("Output mode: verbose.\n")
            continue

        if lower == "/split":
            output_mode = "split"
            if terminal_width() < SPLIT_MIN_COLUMNS:
                _safe_print(
                    "Output mode: split (will fall back to compact if terminal < 120 cols).\n"
                )
            else:
                _safe_print("Output mode: split.\n")
            continue

        if lower == "/clear":
            user_messages.clear()
            latest_profile = None
            latest_recommendations = []
            prev_top_score = None
            clear_screen()
            print_logo()
            _safe_print("Conversation cleared.\n")
            continue

        if lower == "/guest":
            session_mode = "guest"
            login_email = None
            _safe_print("Now continuing as guest.\n")
            continue

        if lower == "/login":
            session_mode = "login"
            login_email = run_login_placeholder()
            continue

        if lower == "/profile":
            if latest_profile:
                print_profile_full(latest_profile)
            else:
                _safe_print("No profile yet. Send a message first.\n")
            continue

        # Part A: /history — show numbered remembered user messages.
        if lower == "/history":
            if not user_messages:
                _safe_print("No remembered messages yet.\n")
            else:
                _safe_print(f"\n{_section_header('History')}")
                for index, message in enumerate(user_messages, start=1):
                    _safe_print(f"  {index}. {message}")
                _safe_print()
            continue

        # Part A: /undo — remove last user message and rerun.
        if lower == "/undo":
            if not user_messages:
                _safe_print("Nothing to undo.\n")
                continue
            removed = user_messages.pop()
            _safe_print(f"Removed last message: {removed}")
            if not user_messages:
                latest_profile = None
                latest_recommendations = []
                prev_top_score = None
                _safe_print("No remaining messages. Profile and recommendations cleared.\n")
                continue
            _safe_print()
            new_profile, new_recommendations, new_top_score = _send_and_render(
                user_messages,
                output_mode,
                latest_profile,
                prev_top_score,
            )
            if new_profile is not None:
                latest_profile = new_profile
            latest_recommendations = new_recommendations
            prev_top_score = new_top_score
            continue

        if parts and parts[0] == "/top":
            limit = parse_top_limit(parts)
            if limit is None:
                _safe_print("Usage: /top or /top N\n")
                continue
            if not latest_recommendations:
                _safe_print(NO_RECS_MSG + "\n")
                continue
            if output_mode == "verbose":
                print_recommendations_verbose(latest_recommendations, limit=limit)
            else:
                _safe_print()
                _safe_print(
                    format_compact_recommendations_table(
                        latest_recommendations, limit, width=terminal_width()
                    )
                )
                _safe_print()
            continue

        if parts and parts[0] == "/details":
            rank = parse_rank_command(parts)
            if rank is None:
                _safe_print("Usage: /details N  (e.g. /details 1)\n")
                continue
            if not latest_recommendations:
                _safe_print(NO_RECS_MSG + "\n")
                continue
            rec = find_recommendation_by_rank(latest_recommendations, rank)
            if rec is None:
                _safe_print(f"No recommendation at rank #{rank}.\n")
                continue
            print_recommendation_details(rec)
            continue

        if parts and parts[0] == "/open":
            rank = parse_rank_command(parts)
            if rank is None:
                _safe_print("Usage: /open N  (e.g. /open 1)\n")
                continue
            if not latest_recommendations:
                _safe_print(NO_RECS_MSG + "\n")
                continue
            rec = find_recommendation_by_rank(latest_recommendations, rank)
            if rec is None:
                _safe_print(f"No recommendation at rank #{rank}.\n")
                continue
            open_recommendation_url(rec)
            continue

        if lower == "/links":
            if not latest_recommendations:
                _safe_print(NO_RECS_MSG + "\n")
                continue
            print_links(latest_recommendations)
            continue

        if stripped.startswith("/"):
            _safe_print(f"Unknown command: {stripped}. Type /help for options.\n")
            continue

        # ----- Normal user message -----
        user_messages.append(stripped)

        # Part B: echo + loading pattern + POST line.
        echo_user_input(stripped)
        show_loading_pattern("Analyzing profile")

        new_profile, new_recommendations, new_top_score = _send_and_render(
            user_messages,
            output_mode,
            latest_profile,
            prev_top_score,
        )

        # If the network call failed we keep the previous profile/recs
        # visible and pop the failing message so /history stays clean.
        if not new_recommendations and new_profile is latest_profile:
            user_messages.pop()
            continue

        latest_profile = new_profile
        latest_recommendations = new_recommendations
        prev_top_score = new_top_score

        if session_mode == "login" and login_email:
            _safe_print(f"(Session: login stub for {login_email})\n")


if __name__ == "__main__":
    sys.exit(main())
