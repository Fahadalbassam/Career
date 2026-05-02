import type { Recommendation, RecommendRequest, StudentProfile } from "@/lib/types"

export const mockStudentProfile: StudentProfile = {
  major: "Computer Science",
  city: "Riyadh",
  interest: "Backend systems and applied ML pipelines",
  workMode: "Hybrid",
  programType: "COOP",
  skills: ["Python", "SQL", "Docker", "REST APIs", "Git"],
}

export const mockRecommendations: Recommendation[] = [
  {
    rank: 1,
    companyName: "Nejumi Tech",
    programName: "Software Engineering COOP — Platform Team",
    city: "Riyadh",
    programType: "COOP",
    workMode: "Hybrid",
    fitLevel: "Strong fit",
    scorePercent: 92,
    matchedSkills: ["Python", "REST APIs", "Docker", "Git"],
    whyRecommended:
      "Heavy backend ownership with Python services and containerized deployments matches your stack and hybrid preference in Riyadh.",
    sourceUrl: "https://example.com/opportunities/nejumi-platform-coop",
    sourceLabel: "View posting",
  },
  {
    rank: 2,
    companyName: "Green Falcon Analytics",
    programName: "Data Engineering Internship",
    city: "Riyadh",
    programType: "Internship",
    workMode: "On-site",
    fitLevel: "Strong fit",
    scorePercent: 88,
    matchedSkills: ["Python", "SQL", "Git"],
    whyRecommended:
      "Pipeline work emphasizes SQL and Python ETL stages aligned with your interest in backend data flows.",
    sourceUrl: "https://example.com/opportunities/green-falcon-de-intern",
    sourceLabel: "View posting",
  },
  {
    rank: 3,
    companyName: "Red Sands Cloud",
    programName: "Cloud Infrastructure COOP",
    city: "Dhahran",
    programType: "COOP",
    workMode: "Hybrid",
    fitLevel: "Good fit",
    scorePercent: 81,
    matchedSkills: ["Docker", "Git", "Python"],
    whyRecommended:
      "Kubernetes-focused rotation rewards Docker literacy; location differs but hybrid COOP fits program type.",
    sourceUrl: "https://example.com/opportunities/red-sands-cloud-coop",
    sourceLabel: "Company careers page",
  },
  {
    rank: 4,
    companyName: "Hayat Innovation Lab",
    programName: "Applied ML Engineering Intern",
    city: "Jeddah",
    programType: "Internship",
    workMode: "Remote-first",
    fitLevel: "Good fit",
    scorePercent: 76,
    matchedSkills: ["Python", "REST APIs"],
    whyRecommended:
      "Matches your ML interest via model serving and API integrations even though city preference is weaker.",
    sourceUrl: "https://example.com/opportunities/hayat-ml-intern",
    sourceLabel: "View posting",
  },
  {
    rank: 5,
    companyName: "Bayan Financial Systems",
    programName: "Junior Backend Developer COOP",
    city: "Riyadh",
    programType: "COOP",
    workMode: "On-site",
    fitLevel: "Moderate fit",
    scorePercent: 71,
    matchedSkills: ["SQL", "REST APIs", "Git"],
    whyRecommended:
      "Core banking APIs align with REST and SQL strengths; fully on-site is a partial mismatch with hybrid preference.",
    sourceUrl: "https://example.com/opportunities/bayan-backend-coop",
    sourceLabel: "Apply portal",
  },
]

/** Example body matching {@link RecommendRequest} for future API wiring. */
export const mockRecommendRequest: RecommendRequest = {
  profile: mockStudentProfile,
  studentQuery:
    "Looking for a hybrid COOP in Riyadh doing backend or ML infra with Python.",
}
