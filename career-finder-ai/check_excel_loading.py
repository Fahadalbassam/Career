import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_PATH = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_PATH))

from app.recommender import get_candidates, recommend
from app.schemas import ParsedProfile


candidates = get_candidates()

print("Number of candidates loaded:", len(candidates))
print("First 3 candidates:")

for opp in candidates[:3]:
    print("-" * 50)
    print("Company:", opp.company)
    print("Title:", opp.title)
    print("City:", opp.city)
    print("Work mode:", opp.work_mode)
    print("Program type:", opp.program_type)
    print("Major fit:", opp.major_fit)
    print("Skills:", opp.skills_list)
    print("Source:", opp.source_url)


profile = ParsedProfile(
    major="CYS",
    city="Riyadh",
    interest="Cybersecurity",
    work_mode="Hybrid",
    program_type="Internship",
    skills=["linux", "network security"],
)

results = recommend(profile, top_n=5)

print("\nTop recommendations:")
for opp in results:
    print("-" * 50)
    print("Company:", opp.company)
    print("Title:", opp.title)
    print("Score:", opp.score)
    print("Reasons:", opp.why_recommended)
    print("Matched skills:", opp.skills_matched)