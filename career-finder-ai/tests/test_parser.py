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
    assert profile.university is None
    assert profile.city is None
    assert profile.preferred_locations == []
    assert profile.work_mode is None
    assert profile.program_type is None
    assert profile.skills == []
    assert profile.qualifications == []
    assert profile.preferred_roles == []
    assert profile.interview_preference is None


def test_parse_interest_derived_from_major():
    profile = parse_message("data science student in Riyadh")
    assert profile.interest == "Data Science"

def test_parse_cyber_security_with_space():
    profile = parse_message("I study cyber security")
    assert profile.major == "CYS"


def test_parse_co_op_with_dash():
    profile = parse_message("I am looking for a co-op")
    assert profile.program_type == "COOP"


def test_parse_co_op_with_space():
    profile = parse_message("I am looking for a co op")
    assert profile.program_type == "COOP"


def test_parse_work_from_home_as_remote():
    profile = parse_message("I prefer work from home")
    assert profile.work_mode == "Remote"


def test_parse_scikit_learn_skill_without_dash():
    profile = parse_message("I know scikit learn")
    assert "scikit-learn" in profile.skills


# ---------------------------------------------------------------------------
# University detection
# ---------------------------------------------------------------------------

def test_parse_university_iau_abbreviation():
    profile = parse_message("I am a CS student at IAU looking for COOP")
    assert profile.university == "IAU"


def test_parse_university_iau_full_name():
    profile = parse_message(
        "I study at Imam Abdulrahman Bin Faisal University in Dammam"
    )
    assert profile.university == "IAU"


def test_parse_university_kfupm():
    profile = parse_message("KFUPM student seeking internship")
    assert profile.university == "KFUPM"


def test_parse_university_ksu():
    profile = parse_message("King Saud University student in Riyadh")
    assert profile.university == "KSU"


def test_parse_university_kau():
    profile = parse_message("I attend King Abdulaziz University")
    assert profile.university == "KAU"


def test_parse_university_psu():
    profile = parse_message("Prince Sultan University graduate")
    assert profile.university == "PSU"


# ---------------------------------------------------------------------------
# Preferred locations
# ---------------------------------------------------------------------------

def test_parse_preferred_locations_or():
    profile = parse_message("Looking for COOP in Riyadh or Dammam")
    assert profile.city == "Riyadh"
    assert profile.preferred_locations == ["Riyadh", "Dammam"]


def test_parse_preferred_locations_and():
    profile = parse_message("Open to internships in Riyadh and Jeddah")
    assert profile.city == "Riyadh"
    assert profile.preferred_locations == ["Riyadh", "Jeddah"]


def test_parse_single_city_keeps_preferred_locations_empty():
    profile = parse_message("I want an internship in Riyadh")
    assert profile.city == "Riyadh"
    assert profile.preferred_locations == []


# ---------------------------------------------------------------------------
# Qualifications detection
# ---------------------------------------------------------------------------

def test_parse_qualification_aws():
    profile = parse_message("I have AWS and python skills")
    assert "AWS" in profile.qualifications
    assert "aws" not in profile.skills


def test_parse_qualification_ccna_and_security_plus():
    profile = parse_message("Certified in CCNA and Security+")
    assert "CCNA" in profile.qualifications
    assert "Security+" in profile.qualifications


def test_parse_qualification_gpa():
    profile = parse_message("My GPA is 4.2 and I know SQL")
    assert any(q.startswith("GPA 4.2") for q in profile.qualifications)


def test_parse_qualification_gpa_compact_form():
    profile = parse_message("GPA 4.5 student with python")
    assert "GPA 4.5" in profile.qualifications


# ---------------------------------------------------------------------------
# Preferred roles
# ---------------------------------------------------------------------------

def test_parse_preferred_role_software_engineer():
    profile = parse_message("I want a software engineering COOP")
    assert "Software Engineer" in profile.preferred_roles


def test_parse_preferred_role_data_scientist():
    profile = parse_message("Looking for data scientist internship")
    assert "Data Scientist" in profile.preferred_roles


def test_parse_preferred_role_soc_analyst():
    profile = parse_message("Interested in SOC analyst roles")
    assert "SOC Analyst" in profile.preferred_roles


# ---------------------------------------------------------------------------
# Interview preference
# ---------------------------------------------------------------------------

def test_parse_interview_preference_no_interview():
    profile = parse_message("I prefer COOP without interview")
    assert profile.interview_preference == "No interview preferred"


def test_parse_interview_preference_no_interview_direct_acceptance():
    profile = parse_message("Looking for direct acceptance opportunities")
    assert profile.interview_preference == "No interview preferred"


def test_parse_interview_preference_okay():
    profile = parse_message("Interview is okay for me")
    assert profile.interview_preference == "Interview okay"


def test_parse_interview_preference_not_mentioned():
    profile = parse_message("remote internship in Riyadh")
    assert profile.interview_preference is None


# ---------------------------------------------------------------------------
# Combined extended profile
# ---------------------------------------------------------------------------

def test_parse_combined_extended_profile():
    profile = parse_message(
        "I am a CS student at IAU with Python, SQL, AWS and GPA 4.5. "
        "I want a remote COOP in Riyadh or Dammam for software engineering "
        "without interview."
    )
    assert profile.major == "CS"
    assert profile.university == "IAU"
    assert "python" in profile.skills
    assert "sql" in profile.skills
    assert "AWS" in profile.qualifications
    assert "GPA 4.5" in profile.qualifications
    assert profile.work_mode == "Remote"
    assert profile.program_type == "COOP"
    assert profile.city == "Riyadh"
    assert profile.preferred_locations == ["Riyadh", "Dammam"]
    assert "Software Engineer" in profile.preferred_roles
    assert profile.interview_preference == "No interview preferred"


# ---------------------------------------------------------------------------
# ML-2A: taxonomy-backed parser improvements
# ---------------------------------------------------------------------------

# City aliases ---------------------------------------------------------------

def test_parse_alkhobar_normalises_to_khobar():
    profile = parse_message("I live in alkhobar and study CS")
    assert profile.city == "Khobar"


def test_parse_al_khobar_with_space_normalises_to_khobar():
    profile = parse_message("CS student based in al khobar")
    assert profile.city == "Khobar"


def test_parse_al_khobar_with_hyphen_normalises_to_khobar():
    profile = parse_message("Looking for COOP in al-khobar")
    assert profile.city == "Khobar"


def test_parse_jedda_normalises_to_jeddah():
    profile = parse_message("DS student in jedda")
    assert profile.city == "Jeddah"


def test_parse_ad_dammam_normalises_to_dammam():
    profile = parse_message("CS student in ad dammam looking for COOP")
    assert profile.city == "Dammam"


def test_parse_remote_alone_is_not_picked_as_city():
    """Work-mode word 'remote' must not poison primary-city detection."""
    profile = parse_message("I prefer remote work")
    assert profile.city is None
    assert profile.work_mode == "Remote"


# Interest detection ---------------------------------------------------------

def test_parse_security_focused_maps_to_cybersecurity():
    profile = parse_message("Looking for security focused opportunities")
    assert profile.interest == "Cybersecurity"


def test_parse_cyber_security_phrase_maps_to_cybersecurity_interest():
    profile = parse_message("I want cyber security roles")
    assert profile.interest == "Cybersecurity"


def test_parse_cs_student_with_security_focus_overrides_default_interest():
    """Explicit interest from text must override the CS major default."""
    profile = parse_message(
        "I am a CS student looking for security focused opportunities"
    )
    assert profile.major == "CS"
    assert profile.interest == "Cybersecurity"


def test_parse_cs_student_in_alkhobar_with_security_focus():
    profile = parse_message(
        "I am a CS student in alkhobar looking for security focused opportunities"
    )
    assert profile.major == "CS"
    assert profile.city == "Khobar"
    assert profile.interest == "Cybersecurity"
    # Cluster fallback should seed preferred_roles when no explicit role is named.
    assert "Cybersecurity" in profile.preferred_roles
    assert "SOC Analyst" in profile.preferred_roles
    assert "Network Security" in profile.preferred_roles
    assert "Penetration Testing" in profile.preferred_roles


def test_parse_dev_ops_maps_to_cloud_devops_interest():
    profile = parse_message("I want cloud infrastructure or dev ops")
    assert profile.interest == "Cloud / DevOps"


def test_parse_cloud_infrastructure_maps_to_cloud_devops_interest():
    profile = parse_message("Looking for cloud infrastructure roles")
    assert profile.interest == "Cloud / DevOps"


# Skill aliases --------------------------------------------------------------

def test_parse_pen_testing_alias_maps_to_penetration_testing_skill():
    profile = parse_message("I know Linux and pen testing")
    assert "penetration testing" in profile.skills


def test_parse_k8s_alias_maps_to_kubernetes_skill():
    profile = parse_message("Experience with k8s and docker")
    assert "kubernetes" in profile.skills


def test_parse_dev_ops_alias_maps_to_devops_skill():
    profile = parse_message("I have dev ops experience")
    assert "devops" in profile.skills


def test_parse_infosec_alias_maps_to_cybersecurity_skill():
    profile = parse_message("Strong infosec background and Linux skills")
    assert "cybersecurity" in profile.skills
    assert "linux" in profile.skills


def test_parse_cicd_alias_maps_to_cicd_skill():
    profile = parse_message("I have CI CD pipeline experience")
    assert "cicd" in profile.skills


def test_parse_security_related_skills_persist_as_skills():
    profile = parse_message(
        "I know Linux, networking, Docker, and penetration testing"
    )
    for expected in ("linux", "networking", "docker", "penetration testing"):
        assert expected in profile.skills


# Preferred-roles cluster seeding -------------------------------------------

def test_parse_explicit_role_keeps_priority_over_interest_cluster():
    """Existing role detection (SOC Analyst) should not be replaced by cluster seeding."""
    profile = parse_message("Interested in SOC analyst roles")
    assert "SOC Analyst" in profile.preferred_roles


def test_parse_devops_interest_seeds_cloud_devops_cluster_roles():
    profile = parse_message("I want cloud infrastructure or dev ops")
    assert profile.interest == "Cloud / DevOps"
    # No explicit "DevOps Engineer" / "Cloud Engineer" phrase in input,
    # so cluster fallback should fire.
    assert "Cloud / DevOps" in profile.preferred_roles


# ---------------------------------------------------------------------------
# ML-2B parser regression tests
# ---------------------------------------------------------------------------


def test_parse_ml2b_security_focused_still_maps_to_cybersecurity():
    profile = parse_message("I want security focused opportunities")
    assert profile.interest == "Cybersecurity"


def test_parse_ml2b_alkhobar_still_normalises_to_khobar():
    profile = parse_message("I am a CS student in alkhobar")
    assert profile.city == "Khobar"


def test_parse_ml2b_i_want_role_in_devops_maps_to_cloud_devops():
    profile = parse_message("I want role in DevOps")
    assert profile.interest == "Cloud / DevOps"
    assert "devops" in profile.skills
    assert "Cloud / DevOps" in profile.preferred_roles


# ---------------------------------------------------------------------------
# FINAL-POLISH-1: MongoDB, interview preference, security roles
# ---------------------------------------------------------------------------

def test_parse_mongodb_skill_from_sql_and_mongodb():
    profile = parse_message("I know SQL and MongoDB")
    assert "sql" in profile.skills
    assert "mongodb" in profile.skills


def test_parse_interview_in_person_sets_preference_and_work_mode():
    profile = parse_message("i want an interview, in person")
    assert profile.interview_preference == "Interview preferred"
    assert profile.work_mode == "On-site"


def test_parse_no_interview_preference():
    profile = parse_message("I prefer no interview")
    assert profile.interview_preference == "No interview preferred"


def test_parse_security_developer_operator_preferred_role():
    profile = parse_message("I'd like to work as a Security Developer Operator")
    assert any(
        role in profile.preferred_roles
        for role in ("Security Operations", "DevSecOps", "Security Engineering")
    )


def test_parse_multiturn_final_polish_conversation():
    combined = "\n".join(
        [
            "IM a CS student, im in IAU university , im interested in Security infrastructure, and know a bit about SQL and Mongodb",
            "alkhobar",
            "COOP and general training",
            "hybrid and onsite",
            "i want an interview, in person",
            "I'd like to work as a Security Developer Operator",
        ]
    )
    profile = parse_message(combined)
    assert profile.major == "CS"
    assert profile.university == "IAU"
    assert profile.city == "Khobar"
    assert profile.interest == "Cybersecurity"
    assert profile.program_type == "COOP"
    assert profile.work_mode == "On-site"
    assert "sql" in profile.skills
    assert "mongodb" in profile.skills
    assert profile.interview_preference == "Interview preferred"
    assert "Security Operations" in profile.preferred_roles