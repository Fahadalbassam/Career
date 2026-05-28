import type { Recommendation, StudentProfile } from "@/lib/types"

const NS = "Not stated"

function isNS(value: string | undefined | null): boolean {
  return !value || value.trim() === "" || value === NS
}

function profileGaps(profile: StudentProfile): string[] {
  const gaps: string[] = []
  if (!profile.preferredRoles?.length) gaps.push("preferred role")
  if (isNS(profile.workMode)) gaps.push("work mode")
  if (!profile.interviewPreference?.trim()) gaps.push("interview preference")
  return gaps
}

function missingSkillsFromRecommendation(
  rec: Recommendation | undefined,
): string[] {
  if (!rec?.missingSkills?.length) return []
  const out: string[] = []
  for (const item of rec.missingSkills) {
    if (item?.trim() && !isNS(item) && !out.includes(item.trim())) {
      out.push(item.trim())
    }
    if (out.length >= 4) break
  }
  return out
}

function nextActionForSkillGaps(skillGaps: string[]): string {
  if (skillGaps.length > 0) {
    return `Review the top match details and strengthen skills like ${skillGaps.slice(0, 4).join(", ")} to improve the match.`
  }
  return "Review the top match details to confirm missing skills and opportunity requirements."
}

function suggestSkillGaps(profile: StudentProfile): string[] {
  const have = new Set(
    profile.skills
      .filter((s) => !isNS(s))
      .map((s) => s.trim().toLowerCase()),
  )
  const interest = (profile.interest || "").toLowerCase()

  const candidates: [string, string][] =
    interest.includes("cyber") || interest.includes("security")
      ? [
          ["linux", "Linux"],
          ["networking", "networking"],
          ["siem", "SIEM"],
          ["cybersecurity", "security fundamentals"],
        ]
      : interest.includes("data")
        ? [
            ["python", "Python"],
            ["sql", "SQL"],
            ["pandas", "pandas"],
            ["machine learning", "machine learning"],
          ]
        : interest.includes("cloud") || interest.includes("devops")
          ? [
              ["linux", "Linux"],
              ["docker", "Docker"],
              ["kubernetes", "Kubernetes"],
              ["aws", "cloud (AWS/Azure)"],
            ]
          : [
              ["python", "Python"],
              ["sql", "SQL"],
              ["git", "Git"],
              ["linux", "Linux"],
            ]

  const suggestions: string[] = []
  for (const [token, label] of candidates) {
    if (!have.has(token) && !suggestions.includes(label)) {
      suggestions.push(label)
    }
    if (suggestions.length >= 4) break
  }
  return suggestions
}

export function buildAssistantReply({
  profile,
  recommendations,
  backendSucceeded,
  softSkillsOnly,
}: {
  profile: StudentProfile | undefined
  recommendations: Recommendation[]
  backendSucceeded: boolean
  softSkillsOnly: boolean
}): string {
  if (!backendSucceeded || !profile) {
    return "I'm scanning Saudi COOP and internship options. Add your major, city, and technical skills to get a personalised ranking."
  }

  if (isNS(profile.major)) {
    return "I still need your major to rank opportunities correctly. Are you CS, AI, CYS, CIS, DS, DE, CE, or FinTech?"
  }

  const hasNoTechSkills =
    profile.skills.length === 0 ||
    (profile.skills.length === 1 && profile.skills[0] === NS)

  if (hasNoTechSkills) {
    return "Tell me a few technical skills you have used, such as Python, SQL, Linux, networking, React, Docker, cloud, cybersecurity, or machine learning."
  }

  if (softSkillsOnly) {
    return "Leadership and organisation help, but for computing COOP ranking I also need technical skills. Do you have skills like Python, SQL, Linux, networking, React, cloud, cybersecurity, or machine learning?"
  }

  if (
    isNS(profile.city) &&
    (!profile.preferredLocations || profile.preferredLocations.length === 0)
  ) {
    return "Which city or preferred location should I prioritise? For example Riyadh, Jeddah, Dammam, Khobar, Dhahran, remote, or multiple."
  }

  if (isNS(profile.programType)) {
    return "Are you looking for COOP, internship, Tamheer, or general training?"
  }

  if (isNS(profile.workMode)) {
    return "Do you prefer remote, hybrid, or on-site opportunities?"
  }

  const topRec = recommendations[0]
  const topScore = topRec?.scorePercent ?? 0
  const topMatch =
    topRec != null
      ? `${topRec.companyName} — ${topRec.programName}, ${topScore}%`
      : ""

  const gaps = profileGaps(profile)
  const skillGaps =
    missingSkillsFromRecommendation(topRec) || suggestSkillGaps(profile)

  if (recommendations.length > 0 && topScore >= 80 && gaps.length === 0) {
    return [
      "Strong match found.",
      topMatch ? `Top match: ${topMatch}` : "",
      `Next best action: ${nextActionForSkillGaps(skillGaps)}`,
    ]
      .filter(Boolean)
      .join(" ")
  }

  if (recommendations.length > 0 && topScore >= 70) {
    if (gaps.length > 0) {
      return [
        "Good matches found — a few details would sharpen the ranking.",
        topMatch ? `Top match: ${topMatch}.` : "",
        `Next best action: Tell me your ${gaps.join(", ")}.`,
      ]
        .filter(Boolean)
        .join(" ")
    }
    return [
      "Strong match found.",
      topMatch ? `Top match: ${topMatch}.` : "",
      `Next best action: ${nextActionForSkillGaps(skillGaps)} I've updated the shelf cards with the best options.`,
    ]
      .filter(Boolean)
      .join(" ")
  }

  if (recommendations.length > 0) {
    const nextAction =
      gaps.length > 0
        ? `Tell me your ${gaps.join(", ")}.`
        : "Tell me your city, program type, and 2–3 skills so I can rank opportunities more accurately."
    return `Early matches found — your profile can be sharper. ${nextAction}`
  }

  return "I'm scanning Saudi COOP and internship options. Share your major, city, skills, or preferred work mode to get a personalised ranking."
}
