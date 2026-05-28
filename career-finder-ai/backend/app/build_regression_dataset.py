"""
build_regression_dataset.py – Supervised regression training pairs.

Pairs deterministic synthetic student profiles with loaded opportunities and
assigns a rubric-based target_score in [0, 100].

Run from the backend directory:
    python -m app.build_regression_dataset

Output:
    data/processed/student_opportunity_regression_dataset.csv
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import pandas as pd

from app.opportunity_enrichment import enrich_opportunity_signals
from app.recommender import (
    OPPORTUNITIES_XLSX_PATH,
    get_candidates,
    load_opportunities_from_xlsx,
)
from app.rubric import (
    TARGET_WEIGHTS,
    compute_city_match_score,
    compute_interview_score,
    compute_major_fit_score,
    compute_program_type_score,
    compute_role_interest_score,
    compute_skill_match_score,
    compute_target_score,
    compute_verification_score,
    compute_work_mode_score,
    infer_interview_required,
    infer_role_cluster,
    infer_verified_opportunity,
    score_profile_opportunity_pair,
)
from app.schemas import Opportunity, ParsedProfile

# Re-exported for backwards compatibility with existing test imports.
__all__ = [
    "CSV_COLUMNS",
    "TARGET_WEIGHTS",
    "build_regression_dataset",
    "build_regression_rows",
    "build_synthetic_profiles",
    "compute_city_match_score",
    "compute_interview_score",
    "compute_major_fit_score",
    "compute_program_type_score",
    "compute_role_interest_score",
    "compute_skill_match_score",
    "compute_target_score",
    "compute_verification_score",
    "compute_work_mode_score",
    "infer_interview_required",
    "infer_role_cluster",
    "infer_verified_opportunity",
    "score_profile_opportunity_pair",
]

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "student_opportunity_regression_dataset.csv"
OPPORTUNITIES_ENRICHED_CSV_PATH = PROCESSED_DIR / "Opportunities_Enriched.csv"

CSV_COLUMNS: List[str] = [
    "profile_id",
    "chat_message",
    "major",
    "university",
    "city",
    "preferred_locations",
    "skills",
    "qualifications",
    "interest",
    "program_type",
    "work_mode",
    "preferred_roles",
    "interview_preference",
    "opportunity_id",
    "company_name",
    "program_name",
    "opportunity_city",
    "opportunity_program_type",
    "opportunity_work_mode",
    "opportunity_skills",
    "opportunity_requirements",
    "opportunity_role_cluster",
    "interview_required",
    "source_url",
    "verified_opportunity",
    # ML-2C: enriched opportunity signal columns
    "opportunity_inferred_role_cluster",
    "opportunity_inferred_interests",
    "opportunity_inferred_skills",
    "opportunity_required_skills",
    "opportunity_preferred_skills",
    "major_fit_score",
    "skill_match_score",
    "role_interest_score",
    "city_match_score",
    "program_type_score",
    "work_mode_score",
    "verification_score",
    "interview_score",
    "target_score",
]


# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------

def _join_list(values: Sequence[str]) -> str:
    return "; ".join(values)


def _join_any(values: object) -> str:
    """Join a list or return a string as-is."""
    if isinstance(values, list):
        return "; ".join(str(v) for v in values if v)
    return str(values) if values else ""


# ---------------------------------------------------------------------------
# Enriched CSV loader  (ML-2C)
# ---------------------------------------------------------------------------

def load_opportunities_from_enriched_csv(
    csv_path: Path = OPPORTUNITIES_ENRICHED_CSV_PATH,
) -> List[Opportunity]:
    """Load opportunities from Opportunities_Enriched.csv.

    Returns an empty list when the file does not exist.  The caller is
    responsible for falling back to the xlsx when this returns empty.
    """
    if not csv_path.exists():
        return []

    df = pd.read_csv(csv_path)
    opportunities: List[Opportunity] = []

    for index, row_data in df.iterrows():
        row = row_data.where(pd.notna(row_data), other=None).to_dict()

        def _get(keys: List[str], default: str = "") -> str:
            for k in keys:
                v = row.get(k)
                if v is not None and str(v).strip() and str(v).lower() not in {"nan", "none"}:
                    return str(v).strip()
            return default

        def _split(raw: str) -> List[str]:
            if not raw or str(raw).lower() in {"nan", "none"}:
                return []
            raw = raw.replace(";", ",")
            return [x.strip() for x in raw.split(",") if x.strip()]

        opp_id_raw = _get(["id", "opportunity_id"], default=str(index + 1))
        try:
            opp_id = int(float(opp_id_raw))
        except (ValueError, TypeError):
            opp_id = index + 1

        opportunities.append(
            Opportunity(
                id=opp_id,
                company=_get(["company", "company_name"], default="Unknown Company"),
                title=_get(["title", "program_name"], default="Untitled"),
                city=_get(["city"], default="Not stated"),
                work_mode=_get(["work_mode"], default="Not stated"),
                program_type=_get(["program_type"], default="Not stated"),
                major_fit=_split(_get(["major_fit", "degree_tags"], default="")),
                requirements=_get(["requirements"], default=""),
                skills_list=_split(_get(["skills_list", "technical_skills"], default="")),
                source_url=_get(["source_url", "application_url"], default=""),
            )
        )

    return opportunities


# ---------------------------------------------------------------------------
# Synthetic profiles (deterministic, >= 40)
# ---------------------------------------------------------------------------

def _profile(
    profile_id: str,
    chat_message: str,
    *,
    major: Optional[str] = None,
    university: Optional[str] = None,
    city: Optional[str] = None,
    preferred_locations: Optional[List[str]] = None,
    skills: Optional[List[str]] = None,
    qualifications: Optional[List[str]] = None,
    interest: Optional[str] = None,
    program_type: Optional[str] = None,
    work_mode: Optional[str] = None,
    preferred_roles: Optional[List[str]] = None,
    interview_preference: Optional[str] = None,
) -> Tuple[str, str, ParsedProfile]:
    return (
        profile_id,
        chat_message,
        ParsedProfile(
            major=major,
            university=university,
            city=city,
            preferred_locations=preferred_locations or [],
            skills=skills or [],
            qualifications=qualifications or [],
            interest=interest,
            program_type=program_type,
            work_mode=work_mode,
            preferred_roles=preferred_roles or [],
            interview_preference=interview_preference,
        ),
    )


def build_synthetic_profiles() -> List[Tuple[str, str, ParsedProfile]]:
    """Return at least 40 deterministic synthetic student profiles."""
    profiles = [
        _profile(
            "cs-backend-riyadh-coop",
            "CS student at KSU in Riyadh seeking on-site COOP in backend development with Python and SQL.",
            major="CS",
            university="KSU",
            city="Riyadh",
            skills=["python", "sql", "git"],
            interest="Software Development",
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Backend Developer"],
        ),
        _profile(
            "cs-frontend-jeddah-intern",
            "Computer science student in Jeddah looking for a hybrid frontend developer internship with React and JavaScript.",
            major="CS",
            city="Jeddah",
            skills=["javascript", "react", "typescript"],
            interest="Software Development",
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Frontend Developer"],
        ),
        _profile(
            "cs-fullstack-remote",
            "I am a CS student who wants a remote full stack developer COOP using Python, Docker, and REST APIs.",
            major="CS",
            city="Riyadh",
            skills=["python", "docker", "javascript"],
            program_type="COOP",
            work_mode="Remote",
            preferred_roles=["Full Stack Developer"],
        ),
        _profile(
            "cs-software-eng-dammam",
            "Software engineering student in Dammam looking for software engineering COOP on-site.",
            major="CS",
            city="Dammam",
            skills=["java", "python", "git"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Software Engineer"],
        ),
        _profile(
            "cs-iau-backend",
            "CS student at IAU with Python and SQL seeking backend developer internship in Riyadh or Dammam.",
            major="CS",
            university="IAU",
            city="Riyadh",
            preferred_locations=["Riyadh", "Dammam"],
            skills=["python", "sql"],
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Backend Developer"],
        ),
        _profile(
            "cys-soc-riyadh",
            "Cybersecurity student at KFUPM in Dhahran targeting SOC analyst COOP with Linux and network security.",
            major="CYS",
            university="KFUPM",
            city="Dhahran",
            skills=["linux", "network security"],
            interest="Cybersecurity",
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["SOC Analyst"],
        ),
        _profile(
            "cys-analyst-jeddah",
            "Cyber security student in Jeddah seeking cybersecurity analyst internship with Security+ and CCNA.",
            major="CYS",
            city="Jeddah",
            skills=["linux"],
            qualifications=["Security+", "CCNA"],
            interest="Cybersecurity",
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Cybersecurity Analyst"],
        ),
        _profile(
            "cys-network-dammam",
            "CYS student in Dammam or Khobar looking for network security COOP without interview.",
            major="CYS",
            city="Dammam",
            preferred_locations=["Dammam", "Khobar"],
            skills=["network security", "linux"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Network Engineer"],
            interview_preference="No interview preferred",
        ),
        _profile(
            "cys-remote-intern",
            "Cybersecurity student seeking remote internship in incident response and SOC monitoring.",
            major="CYS",
            skills=["linux", "python"],
            interest="Cybersecurity",
            program_type="Internship",
            work_mode="Remote",
            preferred_roles=["SOC Analyst"],
        ),
        _profile(
            "cys-ceh-riyadh",
            "Information security student in Riyadh with CEH and CompTIA pursuing cybersecurity COOP.",
            major="CYS",
            city="Riyadh",
            qualifications=["CEH", "CompTIA"],
            skills=["linux"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Cybersecurity Analyst"],
        ),
        _profile(
            "ai-ml-riyadh",
            "AI student at KSU in Riyadh seeking machine learning engineer internship with Python and TensorFlow.",
            major="AI",
            university="KSU",
            city="Riyadh",
            skills=["python", "tensorflow", "pytorch"],
            interest="Artificial Intelligence",
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Machine Learning Engineer"],
        ),
        _profile(
            "ai-engineer-remote",
            "Artificial intelligence student looking for remote AI engineer COOP with NLP experience.",
            major="AI",
            skills=["python", "machine learning"],
            program_type="COOP",
            work_mode="Remote",
            preferred_roles=["AI Engineer"],
        ),
        _profile(
            "ai-ds-cross",
            "ML student in Dhahran open to data science and AI engineering roles with scikit-learn.",
            major="AI",
            city="Dhahran",
            skills=["python", "scikit-learn", "sql"],
            interest="Artificial Intelligence",
            program_type="COOP/Internship",
            work_mode="On-site",
            preferred_roles=["Machine Learning Engineer", "Data Scientist"],
        ),
        _profile(
            "ds-analyst-riyadh",
            "Data science student in Riyadh seeking data analyst internship with SQL, Python, and Power BI.",
            major="DS",
            city="Riyadh",
            skills=["python", "sql", "pandas"],
            qualifications=["Power BI"],
            interest="Data Science",
            program_type="Internship",
            work_mode="On-site",
            preferred_roles=["Data Analyst"],
        ),
        _profile(
            "ds-scientist-jeddah",
            "Data science student at KAU in Jeddah looking for data scientist COOP with statistics and Python.",
            major="DS",
            university="KAU",
            city="Jeddah",
            skills=["python", "sql", "numpy"],
            interest="Data Science",
            program_type="COOP",
            work_mode="Hybrid",
            preferred_roles=["Data Scientist"],
        ),
        _profile(
            "ds-remote-coop",
            "DS student seeking remote COOP in machine learning and data analysis.",
            major="DS",
            skills=["python", "pandas", "scikit-learn"],
            program_type="COOP",
            work_mode="Remote",
            preferred_roles=["Data Scientist"],
        ),
        _profile(
            "ds-gpa-ielts",
            "Data science student with GPA 4.5 and IELTS looking for internship in Riyadh.",
            major="DS",
            city="Riyadh",
            qualifications=["GPA 4.5", "IELTS"],
            skills=["sql", "python"],
            program_type="Internship",
            work_mode="On-site",
            preferred_roles=["Data Analyst"],
        ),
        _profile(
            "de-pipelines-riyadh",
            "Data engineering student in Riyadh seeking COOP in ETL, data pipelines, and SQL.",
            major="DE",
            city="Riyadh",
            skills=["python", "sql", "spark"],
            interest="Data Engineering",
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Data Engineering"],
        ),
        _profile(
            "de-cloud-dammam",
            "Data engineer student in Dammam targeting cloud and big data training with AWS.",
            major="DE",
            city="Dammam",
            skills=["python", "sql"],
            qualifications=["AWS"],
            program_type="Training",
            work_mode="Hybrid",
            preferred_roles=["Cloud Engineer", "Data Engineering"],
        ),
        _profile(
            "de-etl-remote",
            "DE student looking for remote data engineering internship focused on ETL pipelines.",
            major="DE",
            skills=["python", "sql", "kafka"],
            program_type="Internship",
            work_mode="Remote",
            preferred_roles=["Data Engineering"],
        ),
        _profile(
            "cis-business-riyadh",
            "CIS student at PSU seeking business analyst COOP in Riyadh with SQL and Excel.",
            major="CIS",
            university="PSU",
            city="Riyadh",
            skills=["sql", "excel"],
            interest="Information Systems",
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Business Analyst"],
        ),
        _profile(
            "cis-systems-jeddah",
            "Computer information systems student in Jeddah looking for systems analyst internship.",
            major="CIS",
            city="Jeddah",
            skills=["sql"],
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Systems Analyst"],
        ),
        _profile(
            "ce-network-dhahran",
            "Computer engineering student at KFUPM in Dhahran seeking network engineer COOP.",
            major="CE",
            university="KFUPM",
            city="Dhahran",
            skills=["linux", "c++"],
            interest="Computer Engineering",
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Network Engineer"],
        ),
        _profile(
            "ce-embedded-khobar",
            "CE student in Khobar interested in embedded systems and infrastructure engineering internship.",
            major="CE",
            city="Khobar",
            skills=["c++", "linux"],
            program_type="Internship",
            work_mode="On-site",
            preferred_roles=["Embedded Systems"],
        ),
        _profile(
            "ft-banking-riyadh",
            "Fintech student in Riyadh seeking internship in banking technology and product analytics.",
            major="FT",
            city="Riyadh",
            skills=["sql", "python"],
            interest="FinTech",
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Business Analyst"],
        ),
        _profile(
            "ft-finance-remote",
            "FinTech student looking for remote COOP in finance technology and dashboards.",
            major="FT",
            skills=["sql", "excel"],
            program_type="COOP",
            work_mode="Remote",
            preferred_roles=["FinTech"],
        ),
        _profile(
            "riyadh-only-cs",
            "CS student based in Riyadh seeking any on-site software engineering opportunity.",
            major="CS",
            city="Riyadh",
            skills=["python"],
            program_type="COOP/Internship",
            work_mode="On-site",
            preferred_roles=["Software Engineer"],
        ),
        _profile(
            "jeddah-ds",
            "Data science student in Jeddah open to internship or COOP in analytics.",
            major="DS",
            city="Jeddah",
            skills=["python", "sql"],
            program_type="COOP/Internship",
            work_mode="Hybrid",
        ),
        _profile(
            "eastern-province-cys",
            "Cybersecurity student in Dammam open to Khobar and Dhahran SOC roles.",
            major="CYS",
            city="Dammam",
            preferred_locations=["Dammam", "Khobar", "Dhahran"],
            skills=["linux"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["SOC Analyst"],
        ),
        _profile(
            "saudi-arabia-flex",
            "AI student open to opportunities across Saudi Arabia with remote hybrid flexibility.",
            major="AI",
            city="Riyadh",
            preferred_locations=["Saudi Arabia"],
            skills=["python"],
            program_type="Internship",
            work_mode="Hybrid",
        ),
        _profile(
            "remote-only-de",
            "Data engineering student seeking fully remote training anywhere in Saudi Arabia.",
            major="DE",
            city="Remote",
            preferred_locations=["Remote", "Saudi Arabia"],
            skills=["python", "sql"],
            program_type="Training",
            work_mode="Remote",
        ),
        _profile(
            "coop-explicit-cs",
            "Computer science student looking specifically for a COOP program in Riyadh.",
            major="CS",
            city="Riyadh",
            skills=["java"],
            program_type="COOP",
            work_mode="On-site",
        ),
        _profile(
            "internship-explicit-ai",
            "AI student looking specifically for an internship in machine learning.",
            major="AI",
            city="Riyadh",
            skills=["python"],
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Machine Learning Engineer"],
        ),
        _profile(
            "coop-internship-flex",
            "CS student open to COOP or Internship in software engineering across Riyadh and Jeddah.",
            major="CS",
            city="Riyadh",
            preferred_locations=["Riyadh", "Jeddah"],
            skills=["python", "git"],
            program_type="COOP/Internship",
            work_mode="Hybrid",
            preferred_roles=["Software Engineer"],
        ),
        _profile(
            "tamheer-cis",
            "CIS student seeking Tamheer program in Riyadh for business and systems analysis.",
            major="CIS",
            city="Riyadh",
            skills=["sql"],
            program_type="Tamheer",
            work_mode="On-site",
            preferred_roles=["Business Analyst", "Systems Analyst"],
        ),
        _profile(
            "training-de",
            "Data engineering student applying for training program with ETL and Python.",
            major="DE",
            city="Riyadh",
            skills=["python", "sql"],
            program_type="Training",
            work_mode="On-site",
            preferred_roles=["Data Engineering"],
        ),
        _profile(
            "in-person-cs",
            "CS student who prefers in person work in Jeddah for software engineering COOP.",
            major="CS",
            city="Jeddah",
            skills=["python"],
            program_type="COOP",
            work_mode="In person",
            preferred_roles=["Software Engineer"],
        ),
        _profile(
            "hybrid-ds-riyadh",
            "Data science student in Riyadh seeking hybrid data analyst COOP.",
            major="DS",
            city="Riyadh",
            skills=["python", "sql"],
            program_type="COOP",
            work_mode="Hybrid",
            preferred_roles=["Data Analyst"],
        ),
        _profile(
            "no-interview-cs",
            "CS student in Riyadh wants software engineering COOP without interview or direct acceptance.",
            major="CS",
            city="Riyadh",
            skills=["python"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Software Engineer"],
            interview_preference="No interview preferred",
        ),
        _profile(
            "no-interview-ft",
            "Fintech student seeking internship with no interview required in Riyadh.",
            major="FT",
            city="Riyadh",
            skills=["sql"],
            program_type="Internship",
            interview_preference="No interview preferred",
        ),
        _profile(
            "interview-okay-ai",
            "AI student in Jeddah; interview is okay for machine learning internship roles.",
            major="AI",
            city="Jeddah",
            skills=["python"],
            program_type="Internship",
            preferred_roles=["Machine Learning Engineer"],
            interview_preference="Interview okay",
        ),
        _profile(
            "interview-okay-cys",
            "Cybersecurity student in Riyadh; I can do interviews for SOC analyst COOP.",
            major="CYS",
            city="Riyadh",
            skills=["linux"],
            program_type="COOP",
            preferred_roles=["SOC Analyst"],
            interview_preference="Interview okay",
        ),
        _profile(
            "qual-aws-azure",
            "CS student with AWS and Azure certifications seeking cloud engineer internship.",
            major="CS",
            city="Riyadh",
            skills=["python", "linux"],
            qualifications=["AWS", "Azure"],
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Cloud Engineer"],
        ),
        _profile(
            "qual-security-certs",
            "CYS student with CCNA, Security+, and CEH seeking cybersecurity COOP in Dammam.",
            major="CYS",
            city="Dammam",
            qualifications=["CCNA", "Security+", "CEH"],
            skills=["linux"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Cybersecurity Analyst"],
        ),
        _profile(
            "qual-powerbi-gpa",
            "Data science student with Power BI and GPA 4.5 seeking analyst internship in Riyadh.",
            major="DS",
            city="Riyadh",
            qualifications=["Power BI", "GPA 4.5"],
            skills=["sql", "python"],
            program_type="Internship",
            preferred_roles=["Data Analyst"],
        ),
        _profile(
            "qual-ielts-intern",
            "Business-oriented CIS student with IELTS 6.5 seeking internship in Jeddah.",
            major="CIS",
            city="Jeddah",
            qualifications=["IELTS"],
            skills=["excel", "sql"],
            program_type="Internship",
            work_mode="On-site",
            preferred_roles=["Business Analyst"],
        ),
        _profile(
            "devops-cs-cloud",
            "CS student targeting DevOps engineer COOP with Docker, Linux, and AWS in Riyadh.",
            major="CS",
            city="Riyadh",
            skills=["docker", "linux", "python"],
            qualifications=["AWS"],
            program_type="COOP",
            work_mode="Hybrid",
            preferred_roles=["DevOps Engineer", "Cloud Engineer"],
        ),
        _profile(
            "open-major-broad",
            "Computing student in Riyadh with Python and SQL open to software or data roles.",
            major="CS",
            city="Riyadh",
            skills=["python", "sql"],
            program_type="COOP/Internship",
            work_mode="Hybrid",
            preferred_roles=["Software Engineer", "Data Analyst"],
        ),
    ]

    if len(profiles) < 40:
        raise ValueError(f"Expected at least 40 synthetic profiles, found {len(profiles)}")

    return profiles


# ---------------------------------------------------------------------------
# Dataset assembly
# ---------------------------------------------------------------------------

def build_regression_rows(
    profiles: Sequence[Tuple[str, str, ParsedProfile]],
    opportunities: Sequence[Opportunity],
) -> List[dict]:
    """Build one CSV row dict per (profile, opportunity) pair."""
    rows: List[dict] = []

    for profile_id, chat_message, profile in profiles:
        for opportunity in opportunities:
            scores = score_profile_opportunity_pair(profile, opportunity)
            role_cluster = infer_role_cluster(opportunity)
            interview_required = infer_interview_required(opportunity)
            verified = infer_verified_opportunity(opportunity)

            # ML-2C: enrich opportunity signals for dataset metadata
            signals = enrich_opportunity_signals(opportunity)

            rows.append(
                {
                    "profile_id": profile_id,
                    "chat_message": chat_message,
                    "major": profile.major,
                    "university": profile.university,
                    "city": profile.city,
                    "preferred_locations": _join_list(profile.preferred_locations),
                    "skills": _join_list(profile.skills),
                    "qualifications": _join_list(profile.qualifications),
                    "interest": profile.interest,
                    "program_type": profile.program_type,
                    "work_mode": profile.work_mode,
                    "preferred_roles": _join_list(profile.preferred_roles),
                    "interview_preference": profile.interview_preference,
                    "opportunity_id": opportunity.id,
                    "company_name": opportunity.company,
                    "program_name": opportunity.title,
                    "opportunity_city": opportunity.city,
                    "opportunity_program_type": opportunity.program_type,
                    "opportunity_work_mode": opportunity.work_mode,
                    "opportunity_skills": _join_list(opportunity.skills_list),
                    "opportunity_requirements": opportunity.requirements,
                    "opportunity_role_cluster": role_cluster,
                    "interview_required": interview_required,
                    "source_url": opportunity.source_url,
                    "verified_opportunity": verified,
                    # ML-2C enriched columns
                    "opportunity_inferred_role_cluster": signals.get("role_cluster") or "",
                    "opportunity_inferred_interests": _join_any(
                        signals.get("inferred_interests", [])
                    ),
                    "opportunity_inferred_skills": _join_any(
                        signals.get("inferred_skills", [])
                    ),
                    "opportunity_required_skills": _join_any(
                        signals.get("required_skills", [])
                    ),
                    "opportunity_preferred_skills": _join_any(
                        signals.get("preferred_skills", [])
                    ),
                    **scores,
                }
            )

    return rows


def build_regression_dataset(
    profiles: Optional[Sequence[Tuple[str, str, ParsedProfile]]] = None,
    opportunities: Optional[Sequence[Opportunity]] = None,
) -> pd.DataFrame:
    """Build the full regression dataset dataframe."""
    profile_list = list(profiles or build_synthetic_profiles())
    opportunity_list = list(opportunities or get_candidates())
    rows = build_regression_rows(profile_list, opportunity_list)
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def main() -> None:
    """Generate and save the regression training dataset."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    profiles = build_synthetic_profiles()

    # ML-2C: prefer enriched CSV; fall back to xlsx; fall back to placeholders
    enriched_loaded = load_opportunities_from_enriched_csv()
    if enriched_loaded:
        opportunities = enriched_loaded
        print(
            f"[build_regression_dataset] Loaded {len(opportunities)} opportunities "
            f"from {OPPORTUNITIES_ENRICHED_CSV_PATH} (enriched)"
        )
    else:
        xlsx_loaded = load_opportunities_from_xlsx()
        opportunities = xlsx_loaded if xlsx_loaded else get_candidates()
        if xlsx_loaded:
            print(
                f"[build_regression_dataset] Loaded {len(opportunities)} opportunities "
                f"from {OPPORTUNITIES_XLSX_PATH}"
            )
        else:
            print(
                "[build_regression_dataset] WARNING: Enriched CSV and Excel both "
                f"missing or empty — using placeholder opportunities ({len(opportunities)} rows)."
            )

    df = build_regression_dataset(profiles, opportunities)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"[build_regression_dataset] Synthetic profiles: {len(profiles)}")
    print(f"[build_regression_dataset] Opportunities: {len(opportunities)}")
    print(f"[build_regression_dataset] Generated rows: {len(df)}")
    print(f"[build_regression_dataset] Saved to {OUTPUT_FILE}")
    print(
        "[build_regression_dataset] target_score = 100 * ("
        "0.35*major_fit + 0.20*skill_match + 0.15*role_interest + "
        "0.10*city_match + 0.10*program_type + 0.05*work_mode + "
        "0.03*verification + 0.02*interview)"
    )


if __name__ == "__main__":
    main()
