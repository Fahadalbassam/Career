"""
role_families.py – Role-family taxonomy for CareerFinder.ai (Sprint-2).

Defines 14 role families, each with:
  - keywords          : tokens that signal relevance in profile text
  - foundational_skills : broad, weak role signal on their own
  - differentiating_skills : medium evidence — helps separate similar roles
  - signature_skills  : strong role signal (high confidence)
  - related_interests : canonical interest labels from taxonomy.INTEREST_ALIASES
  - related_majors    : major codes that often lead to this family
  - role_titles       : canonical role-title strings from parser/rubric
  - explanation       : one-sentence description shown to the student
  - suggested_questions: clarifying questions when this family is a candidate

Skill category weights used by role_inference.py:
  FOUNDATIONAL_WEIGHT  = 0.15   (e.g. SQL, Python, Git — common across many roles)
  DIFFERENTIATING_WEIGHT = 0.35 (e.g. React, Node, Power BI — narrows the field)
  SIGNATURE_WEIGHT     = 0.55   (e.g. SIEM, Airflow, Unity — strong role signal)

Pure data — no I/O, no external dependencies.  Safe to import anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Skill-weight constants (used by role_inference.py)
# ---------------------------------------------------------------------------

FOUNDATIONAL_WEIGHT: float = 0.15
DIFFERENTIATING_WEIGHT: float = 0.35
SIGNATURE_WEIGHT: float = 0.55

# Minimum confidence to include a family in the output list.
MIN_CONFIDENCE: float = 0.10

# Maximum families returned in a single inference result.
MAX_FAMILIES_RETURNED: int = 5


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class RoleFamilyDef:
    """Static definition of one role family."""

    keywords: List[str]
    foundational_skills: List[str]
    differentiating_skills: List[str]
    signature_skills: List[str]
    related_interests: List[str]
    related_majors: List[str]
    role_titles: List[str]
    explanation: str
    suggested_questions: List[str]


# ---------------------------------------------------------------------------
# 14 Role-family definitions
# ---------------------------------------------------------------------------

ROLE_FAMILIES: Dict[str, RoleFamilyDef] = {

    # ------------------------------------------------------------------ 1
    "Software Engineering": RoleFamilyDef(
        keywords=[
            "software engineer", "software engineering", "software development",
        ],
        foundational_skills=["python", "java", "c++", "c#", "git", "sql"],
        differentiating_skills=["typescript", "testing", "software testing", "qa"],
        signature_skills=["software engineer"],  # via role_titles match
        related_interests=["Software Development"],
        related_majors=["CS", "CIS", "CE"],
        role_titles=["Software Engineer"],
        explanation=(
            "Build, test, and maintain software systems — covers backend, "
            "frontend, mobile, and embedded domains."
        ),
        suggested_questions=[
            "Do you lean more toward backend systems, frontend interfaces, "
            "or are you comfortable working across both?",
            "Have you built any APIs, web apps, or mobile apps?",
        ],
    ),

    # ------------------------------------------------------------------ 2
    "Backend Engineering": RoleFamilyDef(
        keywords=[
            "backend", "back-end", "api development", "rest api",
            "backend developer", "server-side",
        ],
        foundational_skills=["python", "java", "sql", "git"],
        differentiating_skills=[
            "node", "django", "flask", "fastapi", "mongodb", "nosql",
        ],
        signature_skills=["backend"],  # via role_titles or skill overlap
        related_interests=["Software Development"],
        related_majors=["CS"],
        role_titles=["Backend Developer"],
        explanation=(
            "Design and build server-side logic, APIs, and databases that "
            "power applications."
        ),
        suggested_questions=[
            "What languages or frameworks have you used for backend work "
            "(e.g. Python/Django, Node.js, Java Spring)?",
            "Have you designed REST APIs or worked with databases like "
            "PostgreSQL or MongoDB?",
        ],
    ),

    # ------------------------------------------------------------------ 3
    "Frontend Engineering": RoleFamilyDef(
        keywords=[
            "frontend", "front-end", "ui development", "web ui",
            "frontend developer",
        ],
        foundational_skills=["javascript", "git"],
        differentiating_skills=["typescript", "react", "css"],
        signature_skills=["react"],  # react is a strong frontend indicator
        related_interests=["Software Development"],
        related_majors=["CS"],
        role_titles=["Frontend Developer"],
        explanation=(
            "Build the visual layer of applications — web pages, interfaces, "
            "and user interactions using JavaScript frameworks."
        ),
        suggested_questions=[
            "Which frameworks have you used for frontend (React, Vue, Angular, "
            "or just HTML/CSS)?",
            "Do you focus on UI design, accessibility, or performance?",
        ],
    ),

    # ------------------------------------------------------------------ 4
    "Full Stack Development": RoleFamilyDef(
        keywords=[
            "full stack", "fullstack", "full-stack",
        ],
        foundational_skills=["python", "javascript", "sql", "git"],
        differentiating_skills=[
            "react", "node", "typescript", "mongodb", "nosql",
        ],
        signature_skills=["react", "node"],  # both together = full stack
        related_interests=["Software Development"],
        related_majors=["CS"],
        role_titles=["Full Stack Developer"],
        explanation=(
            "Work across frontend and backend — building complete web features "
            "end-to-end, from the UI down to the API and database."
        ),
        suggested_questions=[
            "Do you prefer full-stack web roles or are you leaning toward "
            "specialising in one side (backend vs. frontend)?",
            "Have you deployed or hosted a project (e.g. on AWS, Vercel, Heroku)?",
        ],
    ),

    # ------------------------------------------------------------------ 5
    "Data Analysis": RoleFamilyDef(
        keywords=[
            "data analyst", "data analytics", "dashboard", "reporting",
            "business intelligence", "bi analyst",
        ],
        foundational_skills=["sql", "excel", "python"],
        differentiating_skills=["power bi", "tableau"],
        signature_skills=["power bi", "tableau"],  # either = strong signal
        related_interests=["Data Science", "Information Systems"],
        related_majors=["DS", "CIS", "FT"],
        role_titles=["Data Analyst"],
        explanation=(
            "Analyse datasets and build dashboards to help organisations "
            "understand trends, performance, and business questions."
        ),
        suggested_questions=[
            "Have you built dashboards or reports using Power BI, Tableau, "
            "or Excel?",
            "Is your focus more on business analytics/reporting, or are you "
            "moving toward predictive modelling?",
        ],
    ),

    # ------------------------------------------------------------------ 6
    "Data Engineering": RoleFamilyDef(
        keywords=[
            "data engineering", "data pipeline", "etl", "data warehouse",
            "data infrastructure",
        ],
        foundational_skills=["sql", "python"],
        differentiating_skills=["spark", "kafka"],
        signature_skills=["airflow", "spark", "kafka"],
        related_interests=["Data Engineering"],
        related_majors=["DE", "DS", "CS"],
        role_titles=["Data Engineer"],
        explanation=(
            "Build and maintain pipelines that move, transform, and store "
            "large volumes of data reliably."
        ),
        suggested_questions=[
            "Have you worked with pipeline tools like Apache Airflow, Spark, "
            "or Kafka?",
            "Do you focus more on ingestion/ETL, or on data warehousing and "
            "query optimisation?",
        ],
    ),

    # ------------------------------------------------------------------ 7
    "Data Science / Machine Learning": RoleFamilyDef(
        keywords=[
            "data science", "machine learning", "ml engineer", "model training",
            "deep learning", "nlp", "computer vision", "ai engineer",
        ],
        foundational_skills=["python", "sql"],
        differentiating_skills=["pandas", "numpy", "scikit-learn"],
        signature_skills=["tensorflow", "pytorch"],
        related_interests=[
            "Data Science", "Artificial Intelligence",
        ],
        related_majors=["DS", "AI", "CS"],
        role_titles=["Data Scientist", "Machine Learning Engineer", "AI Engineer"],
        explanation=(
            "Build predictive models, run experiments, and extract insights "
            "from data using ML/AI techniques."
        ),
        suggested_questions=[
            "Have you trained ML models (even for class projects)? "
            "Which libraries: scikit-learn, TensorFlow, PyTorch?",
            "Are you more interested in model research, or applying models to "
            "products and services?",
        ],
    ),

    # ------------------------------------------------------------------ 8
    "Cybersecurity Operations": RoleFamilyDef(
        keywords=[
            "soc analyst", "security operations", "soc monitoring",
            "incident response", "threat detection", "blue team",
        ],
        foundational_skills=["networking", "linux", "cybersecurity"],
        differentiating_skills=["soc", "vulnerability assessment"],
        signature_skills=["siem", "incident response"],
        related_interests=["Cybersecurity"],
        related_majors=["CYS", "CS", "CE"],
        role_titles=["SOC Analyst", "Cybersecurity Analyst", "Security Operations"],
        explanation=(
            "Monitor networks and systems for threats, respond to incidents, "
            "and operate security platforms like SIEMs."
        ),
        suggested_questions=[
            "Have you worked with a SIEM tool (Splunk, QRadar, Microsoft Sentinel)?",
            "Are you more interested in monitoring/detection (blue team) or "
            "testing/exploitation (red team)?",
        ],
    ),

    # ------------------------------------------------------------------ 9
    "Security Engineering": RoleFamilyDef(
        keywords=[
            "security engineer", "application security", "infrastructure security",
            "devsecops", "red team", "penetration testing",
        ],
        foundational_skills=["linux", "networking", "cybersecurity"],
        differentiating_skills=["network security"],
        signature_skills=["penetration testing"],
        related_interests=["Cybersecurity"],
        related_majors=["CYS", "CE", "CS"],
        role_titles=[
            "Security Engineering", "DevSecOps", "Network Security",
            "Penetration Testing",
        ],
        explanation=(
            "Design and harden security controls, conduct penetration tests, "
            "and integrate security into engineering pipelines."
        ),
        suggested_questions=[
            "Have you done any penetration testing or vulnerability research "
            "(even on labs like HackTheBox or TryHackMe)?",
            "Is your focus on network security, application security, or "
            "cloud/infrastructure hardening?",
        ],
    ),

    # ----------------------------------------------------------------- 10
    "Cloud / DevOps / Infrastructure": RoleFamilyDef(
        keywords=[
            "cloud engineer", "devops engineer", "platform engineering",
            "site reliability", "sre", "infrastructure engineer",
        ],
        foundational_skills=["linux", "git", "cloud", "aws", "azure", "gcp"],
        differentiating_skills=["cicd"],
        signature_skills=["docker", "kubernetes"],
        related_interests=["Cloud / DevOps"],
        related_majors=["CS", "CE"],
        role_titles=["Cloud Engineer", "DevOps Engineer"],
        explanation=(
            "Deploy, automate, and scale infrastructure — covering CI/CD, "
            "containerisation, cloud platforms, and reliability engineering."
        ),
        suggested_questions=[
            "Have you deployed anything on a cloud platform (AWS, Azure, GCP)?",
            "Do you use containers (Docker/Kubernetes) or automation tools "
            "(Terraform, Ansible)?",
        ],
    ),

    # ----------------------------------------------------------------- 11
    "QA / Testing": RoleFamilyDef(
        keywords=[
            "qa engineer", "quality assurance", "test engineer",
            "software testing", "test automation",
        ],
        foundational_skills=["python", "git"],
        differentiating_skills=["software testing", "qa"],
        signature_skills=["software testing", "qa"],
        related_interests=["QA/Testing"],
        related_majors=["CS", "CIS"],
        role_titles=["QA / Testing"],
        explanation=(
            "Ensure software quality through manual and automated testing — "
            "writing test cases, finding bugs, and maintaining CI pipelines."
        ),
        suggested_questions=[
            "Have you written automated tests (unit, integration, or end-to-end)?",
            "Which testing frameworks have you used (pytest, Selenium, "
            "Cypress, JUnit)?",
        ],
    ),

    # ----------------------------------------------------------------- 12
    "Business / Systems Analysis": RoleFamilyDef(
        keywords=[
            "business analyst", "systems analyst", "business analysis",
            "requirements gathering", "erp", "crm",
        ],
        foundational_skills=["sql", "excel"],
        differentiating_skills=["power bi"],
        signature_skills=[],  # no single-skill signal; role title is the signal
        related_interests=["Information Systems", "FinTech"],
        related_majors=["CIS", "FT", "DS"],
        role_titles=["Business Analyst", "Systems Analyst"],
        explanation=(
            "Bridge business needs and technical solutions — gather requirements, "
            "model processes, and translate them into actionable system specs."
        ),
        suggested_questions=[
            "Have you worked on requirements analysis, process mapping, "
            "or ERP/CRM systems?",
            "Do you lean toward data analysis (dashboards, reports) or "
            "process/systems design?",
        ],
    ),

    # ----------------------------------------------------------------- 13
    "Game Development": RoleFamilyDef(
        keywords=[
            "game developer", "game development", "game design",
            "game engine", "gameplay", "unity developer",
        ],
        foundational_skills=["python", "java", "c++"],
        differentiating_skills=["c#"],
        signature_skills=["unity", "unreal"],
        related_interests=["Game Development"],
        related_majors=["CS"],
        role_titles=["Game Developer"],
        explanation=(
            "Design and build interactive games using engines like Unity "
            "or Unreal, covering gameplay logic, graphics, and physics."
        ),
        suggested_questions=[
            "Have you built or shipped a game or game prototype "
            "(even a small personal project)?",
            "Which engine do you use — Unity (C#), Unreal (C++), "
            "or another framework?",
        ],
    ),

    # ----------------------------------------------------------------- 14
    "Product / Technical Coordination": RoleFamilyDef(
        keywords=[
            "product manager", "technical coordinator", "project coordinator",
            "product owner", "scrum master", "agile",
        ],
        foundational_skills=["sql", "excel", "git"],
        differentiating_skills=[],
        signature_skills=[],  # primarily role-title and interest driven
        related_interests=["Information Systems", "Software Development"],
        related_majors=["CIS", "CS", "FT"],
        role_titles=["Business Analyst", "Systems Analyst"],
        explanation=(
            "Coordinate between engineering and business — own product backlogs, "
            "write specs, and drive agile delivery."
        ),
        suggested_questions=[
            "Are you interested in managing products/projects, or do you "
            "prefer a hands-on technical role?",
            "Have you used agile methods (Scrum, Kanban) or project management "
            "tools (Jira, Trello)?",
        ],
    ),
}


# ---------------------------------------------------------------------------
# Transition path suggestions
# ---------------------------------------------------------------------------

# Maps (from_family, to_family) -> list of bridging paths
TRANSITION_PATHS: Dict[Tuple[str, str], List[str]] = {
    ("Game Development", "Cybersecurity Operations"): [
        "Application Security (combining coding skills with security awareness)",
        "Game Anti-cheat / Security Engineering",
        "General Security Fundamentals course (CompTIA Security+)",
    ],
    ("Game Development", "Security Engineering"): [
        "Application Security for Game Developers",
        "Penetration Testing / Red Team (leverages system-level C++ skills)",
        "Secure Coding Practices",
    ],
    ("Game Development", "Cloud / DevOps / Infrastructure"): [
        "Game Server Infrastructure / Backend DevOps",
        "Cloud Deployment for Game Services (AWS GameLift, Azure PlayFab)",
        "CI/CD for Game Build Pipelines",
    ],
    ("Game Development", "Backend Engineering"): [
        "Game Backend / LiveOps Services",
        "Multiplayer Networking & Server Architecture",
        "REST API Development (transferable from gameplay logic)",
    ],
    ("Software Engineering", "Data Science / Machine Learning"): [
        "ML Engineering / MLOps (leverages engineering skills)",
        "Data-Driven Feature Development",
        "Python + pandas + scikit-learn starter path",
    ],
    ("Software Engineering", "Cybersecurity Operations"): [
        "Application Security / Secure Development",
        "DevSecOps (integrating security into CI/CD)",
        "Security+/CEH certification path",
    ],
    ("Backend Engineering", "Data Engineering"): [
        "Backend Data Services / API + Pipeline Hybrid",
        "ETL with Python (transfers from backend scripting)",
        "SQL → Data Warehouse path",
    ],
    ("Data Analysis", "Data Science / Machine Learning"): [
        "Predictive Analytics / Forecasting",
        "Python + ML libraries (extends SQL + Excel skills)",
        "Business Intelligence → ML transition",
    ],
}


def get_transition_paths(from_family: str, to_family: str) -> List[str]:
    """Return suggested transition paths between two role families.

    Falls back to a generic message when no specific path is defined.
    """
    paths = TRANSITION_PATHS.get((from_family, to_family))
    if paths:
        return paths
    return [
        f"Start with core skills for {to_family}",
        f"Look for hybrid roles that blend {from_family} and {to_family}",
        f"Consider certifications or short courses in the target area",
    ]


# ---------------------------------------------------------------------------
# Discovery-mode trigger phrases
# ---------------------------------------------------------------------------

DISCOVERY_PHRASES: Tuple[str, ...] = (
    "i don't know",
    "i dont know",
    "idk",
    "not sure",
    "no idea",
    "i have no idea",
    "unsure",
    "haven't decided",
    "haven't decided yet",
    "undecided",
    "not decided",
    "don't know what i want",
    "dont know what i want",
    "i don't know what role",
    "i dont know what role",
    "exploring",
    "not sure what field",
    "help me decide",
    "can you help me choose",
)


def is_discovery_phrase(text: str) -> bool:
    """Return True when the normalised text contains a discovery trigger phrase."""
    norm = text.lower().strip()
    return any(phrase in norm for phrase in DISCOVERY_PHRASES)


# ---------------------------------------------------------------------------
# Guided-discovery question
# ---------------------------------------------------------------------------

DISCOVERY_QUESTION: str = (
    "I can help narrow it down. Which type of work sounds closer to you?\n"
    "  1. Analyst — investigate data, patterns, reports, business questions\n"
    "  2. Engineer/Developer — build systems, apps, APIs, tools\n"
    "  3. Security/Operations — monitor, protect, respond, harden systems\n"
    "  4. Infrastructure/Cloud — servers, deployment, networks, cloud\n"
    "  5. AI/Data Science — models, experiments, predictions"
)
