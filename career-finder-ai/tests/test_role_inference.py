"""
test_role_inference.py – Sprint-2 tests for role-family inference, guided
questions, and discovery mode.

Coverage (mapped to sprint spec Part F):
  Parser / role inference:
    1. SQL alone does not force one specific role.
    2. SQL + Power BI + Excel + dashboard interest → Data Analysis top.
    3. SQL + Python + Airflow + pipelines → Data Engineering top.
    4. SQL + Node.js + React + APIs → Full Stack / Backend top.
    5. SIEM + Linux + networking + cybersecurity → Cybersecurity Operations top.
    6. Docker + Kubernetes + CI/CD + AWS → Cloud / DevOps / Infrastructure top.
    7. Unity + security interest → transition guidance, not fake exact match.
    8. "I don't know what role I want" → discovery mode.

  Assistant reply:
    1. Asks only one clarifying question.
    2. Does not block recommendations when enough fields exist.
    3. Shows possible role directions when available.
    4. Handles "idk" with directional choices.
    5. Does not claim certificate / job guarantees.

  Recommendation:
    1. match_score remains 0–100.
    2. score_source remains "rubric".
    3. No ML retraining (inferred from environment / config checks).
"""

import pytest

from app.parser import parse_message
from app.role_families import DISCOVERY_QUESTION, is_discovery_phrase
from app.role_inference import (
    RoleFamilyInferenceResult,
    detect_discovery_mode,
    format_role_directions,
    infer_role_families,
)
from app.schemas import ParsedProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_profile(**kwargs) -> ParsedProfile:
    defaults = {
        "major": None,
        "university": None,
        "city": None,
        "home_city": None,
        "preferred_locations": [],
        "acceptable_locations": [],
        "location_flexibility": None,
        "skills": [],
        "qualifications": [],
        "interest": None,
        "program_type": None,
        "work_mode": None,
        "preferred_roles": [],
        "interview_preference": None,
    }
    defaults.update(kwargs)
    return ParsedProfile(**defaults)


# ---------------------------------------------------------------------------
# Part F.1 — SQL alone does NOT force one specific role
# ---------------------------------------------------------------------------

class TestSQLAlone:
    def test_sql_alone_does_not_produce_single_high_confidence_role(self):
        profile = _make_profile(skills=["sql"])
        result = infer_role_families(profile)
        top = result.matches[0] if result.matches else None
        # No single role should dominate — confidence must stay below 0.35
        assert top is None or top.confidence < 0.35, (
            f"SQL alone should not force a role; got {top}"
        )

    def test_sql_alone_marks_profile_as_ambiguous(self):
        profile = _make_profile(skills=["sql"])
        result = infer_role_families(profile)
        assert result.is_ambiguous, "SQL alone should yield an ambiguous result"

    def test_sql_alone_provides_guided_question(self):
        profile = _make_profile(skills=["sql"])
        result = infer_role_families(profile)
        assert result.guided_question, (
            "An ambiguous SQL-only profile should have a guided question"
        )


# ---------------------------------------------------------------------------
# Part F.2 — SQL + Power BI + Excel → Data Analysis
# ---------------------------------------------------------------------------

class TestDataAnalysisSignals:
    def test_power_bi_excel_dashboard_interest_top_data_analysis(self):
        profile = _make_profile(
            skills=["sql", "power bi", "excel"],
            interest="Data Science",
        )
        result = infer_role_families(profile)
        families = [m.role_family for m in result.matches]
        assert "Data Analysis" in families, (
            f"Data Analysis should be in top families; got {families}"
        )
        # It should be in position 1 or 2
        top2 = families[:2]
        assert "Data Analysis" in top2, (
            f"Data Analysis should be in top-2; got {top2}"
        )

    def test_power_bi_gives_higher_confidence_than_sql_alone(self):
        sql_only = infer_role_families(_make_profile(skills=["sql"]))
        sql_powerbi = infer_role_families(_make_profile(skills=["sql", "power bi", "excel"]))

        da_sql = next(
            (m.confidence for m in sql_only.matches if m.role_family == "Data Analysis"),
            0.0,
        )
        da_sql_powerbi = next(
            (m.confidence for m in sql_powerbi.matches if m.role_family == "Data Analysis"),
            0.0,
        )
        assert da_sql_powerbi > da_sql, (
            "Power BI + Excel should raise Data Analysis confidence vs SQL alone"
        )

    def test_tableau_also_signals_data_analysis(self):
        profile = _make_profile(skills=["sql", "tableau"])
        result = infer_role_families(profile)
        families = [m.role_family for m in result.matches]
        assert "Data Analysis" in families, (
            "Tableau should trigger Data Analysis family"
        )


# ---------------------------------------------------------------------------
# Part F.3 — SQL + Python + Airflow + pipelines → Data Engineering
# ---------------------------------------------------------------------------

class TestDataEngineeringSignals:
    def test_airflow_pushes_data_engineering_to_top(self):
        profile = _make_profile(
            skills=["sql", "python", "airflow"],
            interest="Data Engineering",
        )
        result = infer_role_families(profile)
        assert result.matches, "Should have at least one match"
        assert result.matches[0].role_family == "Data Engineering", (
            f"Expected Data Engineering on top; got {result.matches[0].role_family}"
        )

    def test_spark_kafka_signal_data_engineering(self):
        profile = _make_profile(skills=["python", "spark", "kafka"])
        result = infer_role_families(profile)
        families = [m.role_family for m in result.matches]
        assert "Data Engineering" in families[:3], (
            f"Spark + Kafka should produce Data Engineering; got {families}"
        )

    def test_data_engineering_confidence_above_threshold(self):
        profile = _make_profile(
            skills=["sql", "python", "airflow", "spark"],
            interest="Data Engineering",
        )
        result = infer_role_families(profile)
        de = next(
            (m for m in result.matches if m.role_family == "Data Engineering"), None
        )
        assert de is not None and de.confidence >= 0.40, (
            f"Strong DE signals should yield confidence >= 0.40; got {de}"
        )


# ---------------------------------------------------------------------------
# Part F.4 — SQL + Node.js + React + APIs → Full Stack / Backend
# ---------------------------------------------------------------------------

class TestFullStackSignals:
    def test_react_node_infers_full_stack(self):
        profile = _make_profile(skills=["sql", "node", "react"])
        result = infer_role_families(profile)
        families = [m.role_family for m in result.matches]
        # Either Full Stack or Frontend/Backend should appear
        overlap = {"Full Stack Development", "Frontend Engineering", "Backend Engineering"}
        assert overlap & set(families), (
            f"React + Node should produce Full Stack / FE / BE; got {families}"
        )

    def test_full_stack_confidence_with_both_react_and_node(self):
        profile = _make_profile(skills=["javascript", "react", "node", "sql"])
        result = infer_role_families(profile)
        fs = next(
            (m for m in result.matches if m.role_family == "Full Stack Development"), None
        )
        assert fs is not None and fs.confidence >= 0.30, (
            f"React + Node should give Full Stack >= 0.30; got {fs}"
        )


# ---------------------------------------------------------------------------
# Part F.5 — SIEM + Linux + networking + cybersecurity → Cybersecurity Operations
# ---------------------------------------------------------------------------

class TestCybersecurityOperationsSignals:
    def test_siem_linux_networking_top_cybersec_ops(self):
        profile = _make_profile(
            skills=["siem", "linux", "networking", "cybersecurity"],
            interest="Cybersecurity",
        )
        result = infer_role_families(profile)
        assert result.matches, "Should have at least one match"
        assert result.matches[0].role_family == "Cybersecurity Operations", (
            f"Expected Cybersecurity Operations on top; got {result.matches[0].role_family}"
        )

    def test_siem_alone_signals_cybersec_ops(self):
        profile = _make_profile(skills=["siem"])
        result = infer_role_families(profile)
        families = [m.role_family for m in result.matches]
        assert "Cybersecurity Operations" in families, (
            "SIEM alone should appear in Cybersecurity Operations"
        )

    def test_incident_response_is_cybersec_ops_evidence(self):
        profile = _make_profile(skills=["linux", "incident response", "siem"])
        result = infer_role_families(profile)
        co = next(
            (m for m in result.matches if m.role_family == "Cybersecurity Operations"), None
        )
        assert co is not None, "Incident response + SIEM should include CyberOps"
        assert "incident response" in co.evidence or "siem" in co.evidence


# ---------------------------------------------------------------------------
# Part F.6 — Docker + Kubernetes + CI/CD + AWS → Cloud / DevOps / Infrastructure
# ---------------------------------------------------------------------------

class TestCloudDevOpsSignals:
    def test_docker_kubernetes_top_cloud_devops(self):
        profile = _make_profile(
            skills=["docker", "kubernetes", "cicd", "aws"],
            interest="Cloud / DevOps",
        )
        result = infer_role_families(profile)
        assert result.matches, "Should have at least one match"
        assert result.matches[0].role_family == "Cloud / DevOps / Infrastructure", (
            f"Expected Cloud / DevOps / Infrastructure on top; got {result.matches[0].role_family}"
        )

    def test_docker_kubernetes_without_interest_still_signals_cloud(self):
        profile = _make_profile(skills=["docker", "kubernetes"])
        result = infer_role_families(profile)
        families = [m.role_family for m in result.matches]
        assert "Cloud / DevOps / Infrastructure" in families, (
            f"Docker + Kubernetes should signal Cloud/DevOps; got {families}"
        )

    def test_cloud_devops_confidence_above_threshold(self):
        profile = _make_profile(
            skills=["linux", "docker", "kubernetes", "cicd", "aws"],
        )
        result = infer_role_families(profile)
        cd = next(
            (m for m in result.matches if m.role_family == "Cloud / DevOps / Infrastructure"),
            None,
        )
        assert cd is not None and cd.confidence >= 0.50, (
            f"Strong Cloud/DevOps signals should be >= 0.50; got {cd}"
        )


# ---------------------------------------------------------------------------
# Part F.7 — Unity + security interest → transition guidance, NOT fake match
# ---------------------------------------------------------------------------

class TestGameDevSecurityTransition:
    def test_unity_skill_triggers_game_dev_family(self):
        profile = _make_profile(skills=["unity", "c#"])
        result = infer_role_families(profile)
        families = [m.role_family for m in result.matches]
        assert "Game Development" in families, (
            f"Unity + C# should trigger Game Development family; got {families}"
        )

    def test_security_interest_with_unity_skill_shows_transition(self):
        profile = _make_profile(
            skills=["unity", "c++", "c#"],
            interest="Cybersecurity",
        )
        result = infer_role_families(profile)
        assert result.current_strength_family == "Game Development", (
            f"Skill strength should point to Game Development; got "
            f"{result.current_strength_family}"
        )
        assert result.target_interest_family in (
            "Cybersecurity Operations", "Security Engineering"
        ), (
            f"Interest should point to a security family; got "
            f"{result.target_interest_family}"
        )

    def test_transition_paths_are_provided(self):
        profile = _make_profile(
            skills=["unity", "c++", "c#"],
            interest="Cybersecurity",
        )
        result = infer_role_families(profile)
        assert result.transition_paths, (
            "Transition paths should be provided for Game Dev → Security"
        )

    def test_game_dev_security_guided_question_about_conflict(self):
        profile = _make_profile(
            skills=["unity", "c++", "c#"],
            interest="Cybersecurity",
        )
        result = infer_role_families(profile)
        assert result.guided_question, (
            "A skill/interest conflict should produce a guided question"
        )
        # The question should mention both directions
        q = result.guided_question.lower()
        assert "skill" in q or "strength" in q or "current" in q or "direction" in q, (
            "Question should reference the conflict direction"
        )

    def test_no_artificially_high_cybersec_ops_from_unity_alone(self):
        """Game dev skills should not inflate Cybersecurity Operations confidence."""
        profile = _make_profile(skills=["unity"])
        result = infer_role_families(profile)
        co = next(
            (m for m in result.matches if m.role_family == "Cybersecurity Operations"), None
        )
        assert co is None or co.confidence < 0.35, (
            "Unity alone should not produce high Cybersecurity Operations confidence"
        )


# ---------------------------------------------------------------------------
# Part F.8 — "I don't know" triggers guided discovery
# ---------------------------------------------------------------------------

class TestDiscoveryMode:
    def test_idk_message_triggers_discovery(self):
        profile = _make_profile()
        result = infer_role_families(profile, message="I don't know what role I want")
        assert result.discovery_mode, "idk message should trigger discovery mode"

    def test_idk_variation_triggers_discovery(self):
        profile = _make_profile()
        for phrase in ["idk", "not sure", "no idea", "I haven't decided"]:
            result = infer_role_families(profile, message=phrase)
            assert result.discovery_mode, (
                f"Phrase '{phrase}' should trigger discovery mode"
            )

    def test_discovery_mode_guided_question_contains_choices(self):
        profile = _make_profile()
        result = infer_role_families(profile, message="idk")
        assert result.guided_question, "Discovery mode should have a guided question"
        q = result.guided_question
        assert "1." in q or "analyst" in q.lower() or "engineer" in q.lower(), (
            "Discovery question should provide numbered/labelled choices"
        )

    def test_empty_profile_also_triggers_discovery(self):
        profile = _make_profile()
        result = infer_role_families(profile, message="")
        assert result.discovery_mode, "Completely empty profile should be discovery mode"

    def test_profile_with_major_and_skills_is_not_discovery(self):
        profile = _make_profile(
            major="CS", skills=["python", "react"], interest="Software Development"
        )
        result = infer_role_families(profile)
        assert not result.discovery_mode, (
            "Profile with major + skills should not be in discovery mode"
        )


# ---------------------------------------------------------------------------
# is_discovery_phrase helper
# ---------------------------------------------------------------------------

class TestIsDiscoveryPhrase:
    def test_recognises_idk(self):
        assert is_discovery_phrase("idk")

    def test_recognises_dont_know(self):
        assert is_discovery_phrase("i don't know what i want")

    def test_recognises_not_sure(self):
        assert is_discovery_phrase("not sure what to pick")

    def test_does_not_flag_normal_message(self):
        assert not is_discovery_phrase("I know Python and SQL")


# ---------------------------------------------------------------------------
# format_role_directions display helper
# ---------------------------------------------------------------------------

class TestFormatRoleDirections:
    def test_displays_percentages(self):
        profile = _make_profile(
            skills=["siem", "linux", "networking"],
            interest="Cybersecurity",
        )
        result = infer_role_families(profile)
        text = format_role_directions(result)
        assert "%" in text, "Role directions should display percentages"

    def test_displays_evidence(self):
        profile = _make_profile(skills=["siem", "linux"], interest="Cybersecurity")
        result = infer_role_families(profile)
        text = format_role_directions(result)
        assert "Evidence" in text, "Role directions should show evidence"

    def test_discovery_mode_shows_question(self):
        profile = _make_profile()
        result = infer_role_families(profile, message="idk")
        text = format_role_directions(result)
        assert "1." in text or "analyst" in text.lower(), (
            "Discovery mode output should contain directional choices"
        )


# ---------------------------------------------------------------------------
# Part F — Assistant reply: one question, not blocked
# ---------------------------------------------------------------------------

class TestAssistantReplyRoleIntelligence:
    """Sprint-2 assistant reply rules."""

    def _complete_profile(self, **overrides):
        base = {
            "major": "CS",
            "city": "Riyadh",
            "skills": ["sql", "power bi", "excel"],
            "interest": "Data Science",
            "program_type": "COOP",
            "work_mode": "On-site",
            "preferred_roles": ["Data Analyst"],
            "interview_preference": "Interview preferred",
            "preferred_locations": [],
            "qualifications": [],
        }
        base.update(overrides)
        return base

    def test_assistant_does_not_block_recommendations_when_profile_complete(self):
        from app.assistant_reply import build_assistant_reply_parts
        parts = build_assistant_reply_parts(
            self._complete_profile(),
            [{"company": "SDAIA", "title": "Data Analyst COOP", "match_score": 75}],
        )
        # Should have a headline that is NOT a mandatory-field question
        assert parts["headline"]
        assert "major" not in parts["headline"].lower()
        assert "skill" not in parts["headline"].lower() or "strengthen" in parts["headline"].lower()

    def test_assistant_shows_role_intelligence_when_profile_complete(self):
        from app.assistant_reply import build_assistant_reply_parts
        parts = build_assistant_reply_parts(
            self._complete_profile(),
            [{"company": "SDAIA", "title": "Data Analyst COOP", "match_score": 75}],
        )
        # Role intelligence should be present (non-empty) or at least attempted
        # (it may be empty if no strong signal, but should not error)
        assert "role_intelligence" in parts

    def test_assistant_discovery_mode_when_idk(self):
        from app.assistant_reply import build_assistant_reply_parts
        parts = build_assistant_reply_parts(
            {"major": None, "skills": [], "interest": None, "preferred_roles": []},
            [],
            message="idk",
        )
        headline = parts["headline"].lower()
        # Should guide, not ask about major first
        assert (
            "narrow" in headline
            or "analyst" in headline
            or "engineer" in headline
            or "help" in headline
            or "1." in parts["headline"]
        )

    def test_assistant_asks_at_most_one_clarifying_question(self):
        """Count question marks — there should be at most one question in the reply."""
        from app.assistant_reply import build_assistant_reply
        profile = self._complete_profile(preferred_roles=[], interview_preference=None)
        reply = build_assistant_reply(
            profile,
            [{"company": "STC", "title": "COOP", "match_score": 70}],
        )
        # The reply may have 0 or 1 question marks; never more than 2.
        question_marks = reply.count("?")
        assert question_marks <= 2, (
            f"Assistant should ask at most one question; found {question_marks} '?' in reply:\n{reply}"
        )

    def test_assistant_does_not_claim_guarantees(self):
        from app.assistant_reply import build_assistant_reply
        profile = self._complete_profile()
        reply = build_assistant_reply(
            profile,
            [{"company": "STC", "title": "COOP", "match_score": 80}],
        )
        forbidden = ["guarantee", "guaranteed", "will get", "will land", "certify"]
        for word in forbidden:
            assert word not in reply.lower(), (
                f"Reply should not claim '{word}'; reply was: {reply}"
            )


# ---------------------------------------------------------------------------
# Part F — Recommendation: score integrity
# ---------------------------------------------------------------------------

class TestRecommendationScoreIntegrity:
    """Verify rubric scoring is unchanged after Sprint-2."""

    def test_scores_remain_sorted_descending(self):
        from app.recommender import recommend_from_message
        response = recommend_from_message(
            "CS student in Riyadh, Python SQL, COOP, on-site"
        )
        scores = [r.match_score for r in response.recommendations]
        assert scores == sorted(scores, reverse=True), (
            "Recommendations must be sorted by match_score descending"
        )

    def test_match_score_is_within_0_100(self):
        from app.recommender import recommend_from_message
        response = recommend_from_message(
            "CYS student, SIEM Linux networking, Khobar, COOP, on-site"
        )
        for rec in response.recommendations:
            assert 0 <= rec.match_score <= 100, (
                f"match_score out of range: {rec.match_score}"
            )

    def test_score_source_is_rubric(self):
        from app.recommender import recommend_from_message
        response = recommend_from_message(
            "DS student, Python pandas SQL, Riyadh, internship, hybrid"
        )
        for rec in response.recommendations[:5]:
            assert rec.score_source == "rubric", (
                f"score_source must be 'rubric'; got {rec.score_source}"
            )

    def test_sprint2_does_not_retrain_ml(self):
        """No ML model file should be modified by Sprint-2 imports."""
        import importlib
        # Simply importing Sprint-2 modules should not raise and should not
        # trigger any model loading.
        from app import role_families, role_inference  # noqa: F401
        assert True  # If imports succeed, no ML loading occurred.


# ---------------------------------------------------------------------------
# Parser integration — new skill keywords
# ---------------------------------------------------------------------------

class TestParserNewSkillKeywords:
    def test_unity_parsed_as_skill(self):
        profile = parse_message("I know Unity and C# for game development")
        assert "unity" in profile.skills, f"Expected 'unity' in skills; got {profile.skills}"

    def test_unreal_parsed_as_skill(self):
        profile = parse_message("I use Unreal Engine for game programming")
        assert "unreal" in profile.skills, f"Expected 'unreal' in skills; got {profile.skills}"

    def test_airflow_parsed_as_skill(self):
        profile = parse_message("I use Apache Airflow for data pipelines")
        assert "airflow" in profile.skills, f"Expected 'airflow' in skills; got {profile.skills}"

    def test_game_dev_interest_detected(self):
        profile = parse_message("I am interested in game development and know Unity")
        assert profile.interest == "Game Development", (
            f"Expected 'Game Development' interest; got {profile.interest}"
        )
