"""
test_parser.py – Unit tests for the rule-based message parser.
"""

import pytest
from app.parser import parse_message


# ---------------------------------------------------------------------------
# Major detection
# ---------------------------------------------------------------------------

def test_parse_cs_major():
    profile = parse_message("I am a computer science student looking for an internship")
    assert profile.major == "CS"


def test_parse_ai_major():
    profile = parse_message("I study artificial intelligence and want a COOP")
    assert profile.major == "AI"


def test_parse_cys_major():
    profile = parse_message("I am a cybersecurity student in Riyadh")
    assert profile.major == "CYS"


def test_parse_ds_major():
    profile = parse_message("I am a data science student seeking remote work")
    assert profile.major == "DS"


def test_parse_de_major():
    profile = parse_message("data engineering student looking for on-site opportunities")
    assert profile.major == "DE"


def test_parse_ce_major():
    profile = parse_message("computer engineering student in Jeddah")
    assert profile.major == "CE"


def test_parse_ft_major():
    profile = parse_message("I am interested in fintech internships")
    assert profile.major == "FT"


def test_parse_cis_major():
    profile = parse_message("computer information systems student")
    assert profile.major == "CIS"


# ---------------------------------------------------------------------------
# City detection
# ---------------------------------------------------------------------------

def test_parse_riyadh_city():
    profile = parse_message("I want an internship in Riyadh")
    assert profile.city == "Riyadh"


def test_parse_dammam_city():
    profile = parse_message("cybersecurity student in dammam looking for remote COOP")
    assert profile.city == "Dammam"


def test_parse_jeddah_city():
    profile = parse_message("AI student in Jeddah")
    assert profile.city == "Jeddah"


# ---------------------------------------------------------------------------
# Work mode detection
# ---------------------------------------------------------------------------

def test_parse_remote_work_mode():
    profile = parse_message("I prefer remote work")
    assert profile.work_mode == "Remote"


def test_parse_onsite_work_mode():
    profile = parse_message("I want an on-site position")
    assert profile.work_mode == "On-site"


def test_parse_hybrid_work_mode():
    profile = parse_message("looking for a hybrid role")
    assert profile.work_mode == "Hybrid"


# ---------------------------------------------------------------------------
# Program type detection
# ---------------------------------------------------------------------------

def test_parse_coop_program_type():
    profile = parse_message("looking for a COOP position")
    assert profile.program_type == "COOP"


def test_parse_internship_program_type():
    profile = parse_message("I am looking for an internship")
    assert profile.program_type == "Internship"


# ---------------------------------------------------------------------------
# Skills detection
# ---------------------------------------------------------------------------

def test_parse_python_skill():
    profile = parse_message("I know python and sql")
    assert "python" in profile.skills
    assert "sql" in profile.skills


def test_parse_multiple_skills():
    profile = parse_message("I have experience with python, pandas, and scikit-learn")
    assert "python" in profile.skills
    assert "pandas" in profile.skills
    assert "scikit-learn" in profile.skills


# ---------------------------------------------------------------------------
# Combined scenarios
# ---------------------------------------------------------------------------

def test_parse_full_message():
    profile = parse_message(
        "I am a cybersecurity student in Dammam looking for remote COOP"
    )
    assert profile.major == "CYS"
    assert profile.city == "Dammam"
    assert profile.work_mode == "Remote"
    assert profile.program_type == "COOP"


def test_parse_empty_fields_when_unknown():
    profile = parse_message("I want a job")
    assert profile.major is None
    assert profile.city is None
    assert profile.work_mode is None
    assert profile.program_type is None
    assert profile.skills == []


def test_parse_interest_derived_from_major():
    profile = parse_message("data science student in Riyadh")
    assert profile.interest == "Data Science"
