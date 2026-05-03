import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_PATH = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_PATH))

import app.recommender as recommender_module
from app.recommender import get_candidates, load_opportunities_from_xlsx


print("Project root:", PROJECT_ROOT)
print("Backend path:", BACKEND_PATH)
print("Expected Excel path:", recommender_module.OPPORTUNITIES_XLSX_PATH)
print("Excel file exists:", recommender_module.OPPORTUNITIES_XLSX_PATH.exists())

print("\nTrying to load Excel directly...")
xlsx_candidates = load_opportunities_from_xlsx()
print("Excel candidates loaded directly:", len(xlsx_candidates))

if xlsx_candidates:
    print("\nFirst 3 Excel candidates:")
    for opp in xlsx_candidates[:3]:
        print("-" * 50)
        print("Company:", opp.company)
        print("Title:", opp.title)
        print("City:", opp.city)
        print("Work mode:", opp.work_mode)
        print("Program type:", opp.program_type)
        print("Major fit:", opp.major_fit)
        print("Skills:", opp.skills_list)
        print("Source:", opp.source_url)

print("\nTrying get_candidates()...")
candidates = get_candidates()
print("Candidates from get_candidates():", len(candidates))

print("\nFirst 3 get_candidates() results:")
for opp in candidates[:3]:
    print("-" * 50)
    print("Company:", opp.company)
    print("Title:", opp.title)