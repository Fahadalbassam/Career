import type {
  OpportunityApi,
  ParsedProfileApi,
  ScoreBreakdownApi,
} from "@/lib/api-types"
import type {
  CareerFitMemory,
  Recommendation,
  StudentProfile,
} from "@/lib/types"

const NOT_STATED = "Not stated"

function fallbackText(value: string | null | undefined): string {
  if (value == null || value.trim() === "") return NOT_STATED
  return value.trim()
}

function fitLevelFromScore(matchScore: number): string {
  if (matchScore >= 85) return "Strong fit"
  if (matchScore >= 70) return "Good fit"
  if (matchScore >= 50) return "Moderate fit"
  return "Growth fit"
}

function toScoreBreakdown(
  breakdown: ScoreBreakdownApi,
): Record<string, number> {
  return {
    majorFitScore: breakdown.major_fit_score,
    skillMatchScore: breakdown.skill_match_score,
    roleInterestScore: breakdown.role_interest_score,
    cityMatchScore: breakdown.city_match_score,
    programTypeScore: breakdown.program_type_score,
    workModeScore: breakdown.work_mode_score,
    verificationScore: breakdown.verification_score,
    interviewScore: breakdown.interview_score,
  }
}

export function toStudentProfile(profile: ParsedProfileApi): StudentProfile {
  return {
    major: fallbackText(profile.major),
    city: fallbackText(profile.city),
    interest: fallbackText(profile.interest),
    workMode: fallbackText(profile.work_mode),
    programType: fallbackText(profile.program_type),
    skills: profile.skills?.length ? profile.skills : [NOT_STATED],
    university: profile.university?.trim() || undefined,
    preferredLocations: profile.preferred_locations?.length
      ? profile.preferred_locations
      : undefined,
    qualifications: profile.qualifications?.length
      ? profile.qualifications
      : undefined,
    preferredRoles: profile.preferred_roles?.length
      ? profile.preferred_roles
      : undefined,
    interviewPreference: profile.interview_preference?.trim() || undefined,
  }
}

export function toRecommendation(opportunity: OpportunityApi): Recommendation {
  const whyRecommended = opportunity.why_recommended?.length
    ? opportunity.why_recommended.join(" • ")
    : NOT_STATED

  const matchedSkills = opportunity.skills_matched?.length
    ? opportunity.skills_matched
    : []

  const matchScore = opportunity.match_score ?? 0

  return {
    rank: opportunity.rank,
    companyName: fallbackText(opportunity.company),
    programName: fallbackText(opportunity.title),
    city: fallbackText(opportunity.city),
    programType: fallbackText(opportunity.program_type),
    workMode: fallbackText(opportunity.work_mode),
    fitLevel: fitLevelFromScore(matchScore),
    scorePercent: matchScore,
    matchedSkills,
    whyRecommended,
    sourceUrl: opportunity.source_url?.trim() || "",
    sourceLabel: "View posting",
    roleCluster: opportunity.role_cluster?.trim() || undefined,
    interviewRequired: opportunity.interview_required?.trim() || undefined,
    missingSkills: opportunity.missing_skills?.length
      ? opportunity.missing_skills
      : undefined,
    scoreBreakdown: opportunity.score_breakdown
      ? toScoreBreakdown(opportunity.score_breakdown)
      : undefined,
  }
}

export function toRecommendations(
  opportunities: OpportunityApi[],
): Recommendation[] {
  return opportunities.map(toRecommendation)
}

const SHELF_TITLE_MAX_LEN = 52

function shelfCardTitle(company: string, program: string): string {
  const companyTrim = company === NOT_STATED ? "" : company
  const programTrim = program === NOT_STATED ? "" : program
  if (companyTrim && programTrim) {
    const combined = `${companyTrim} — ${programTrim}`
    if (combined.length <= SHELF_TITLE_MAX_LEN) return combined
    const budget = SHELF_TITLE_MAX_LEN - 3 - companyTrim.length
    if (budget >= 12) return `${companyTrim} — ${programTrim.slice(0, budget)}…`
    return programTrim.length <= SHELF_TITLE_MAX_LEN
      ? programTrim
      : `${programTrim.slice(0, SHELF_TITLE_MAX_LEN - 1)}…`
  }
  return programTrim || companyTrim || "Opportunity"
}

function truncateReason(text: string, max = 140): string {
  if (text.length <= max) return text
  return `${text.slice(0, max - 1)}…`
}

export function toCareerFitMemory(recommendation: Recommendation): CareerFitMemory {
  const why = recommendation.whyRecommended
  const tagsFromSkills = recommendation.matchedSkills.slice(0, 3)
  const fallbackTags = [
    recommendation.roleCluster,
    recommendation.programType,
  ].filter((t): t is string => Boolean(t?.trim()))
  const tags = tagsFromSkills.length ? tagsFromSkills : fallbackTags.slice(0, 3)

  const stableKey = `${recommendation.rank}-${recommendation.companyName}-${recommendation.programName}`
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")

  return {
    id: `backend-shelf-${stableKey}`,
    title: shelfCardTitle(recommendation.companyName, recommendation.programName),
    matchConfidence: recommendation.scorePercent,
    tags,
    shortReason: truncateReason(why),
    detailText: why,
    roleCluster: recommendation.roleCluster,
    city: recommendation.city !== NOT_STATED ? recommendation.city : undefined,
    workMode:
      recommendation.workMode !== NOT_STATED ? recommendation.workMode : undefined,
    programType:
      recommendation.programType !== NOT_STATED
        ? recommendation.programType
        : undefined,
    interviewRequired: recommendation.interviewRequired,
    missingSkills: recommendation.missingSkills,
    sourceUrl: recommendation.sourceUrl?.trim() || undefined,
    rank: recommendation.rank,
    source: "backend" as const,
  }
}

// ---------------------------------------------------------------------------
// Multi-turn profile merging
// ---------------------------------------------------------------------------

function isUseful(val: string | undefined | null): boolean {
  return !!val && val.trim() !== "" && val.trim() !== NOT_STATED
}

function unionList(
  a: string[] | undefined,
  b: string[] | undefined,
): string[] | undefined {
  const aArr = (a ?? []).filter(isUseful)
  const bArr = (b ?? []).filter(isUseful)
  if (aArr.length === 0 && bArr.length === 0) return undefined
  const seen = new Set<string>()
  const result: string[] = []
  for (const v of [...aArr, ...bArr]) {
    const key = v.toLowerCase()
    if (!seen.has(key)) {
      seen.add(key)
      result.push(v)
    }
  }
  return result.length > 0 ? result : undefined
}

/**
 * Merge an incoming StudentProfile (latest backend parse) into the current
 * accumulated profile from previous turns.
 *
 * Rules:
 * - Scalar fields: latest non-empty incoming value wins; if incoming is
 *   empty/NS, keep the current value.
 * - List fields: union and deduplicate, case-insensitively.
 * - Skills: same union logic; always falls back to [NOT_STATED] when both
 *   are empty so downstream checks stay consistent.
 */
export function mergeStudentProfiles(
  current: StudentProfile | null,
  incoming: StudentProfile,
): StudentProfile {
  if (!current) return incoming

  const mergedSkills = (() => {
    const a = current.skills.filter(isUseful)
    const b = incoming.skills.filter(isUseful)
    const combined = [...a]
    for (const v of b) {
      if (!combined.some((u) => u.toLowerCase() === v.toLowerCase())) {
        combined.push(v)
      }
    }
    return combined.length > 0 ? combined : [NOT_STATED]
  })()

  const pick = (cur: string, inc: string): string =>
    isUseful(inc) ? inc : isUseful(cur) ? cur : inc

  return {
    major: pick(current.major, incoming.major),
    city: pick(current.city, incoming.city),
    interest: pick(current.interest, incoming.interest),
    workMode: pick(current.workMode, incoming.workMode),
    programType: pick(current.programType, incoming.programType),
    skills: mergedSkills,
    university: incoming.university ?? current.university,
    preferredLocations: unionList(
      current.preferredLocations,
      incoming.preferredLocations,
    ),
    qualifications: unionList(current.qualifications, incoming.qualifications),
    preferredRoles: unionList(current.preferredRoles, incoming.preferredRoles),
    interviewPreference:
      incoming.interviewPreference ?? current.interviewPreference,
  }
}

// ---------------------------------------------------------------------------
// Profile completeness helpers
// ---------------------------------------------------------------------------

function countProfileFieldsFilled(profile: StudentProfile): number {
  let n = 0
  if (profile.major && profile.major !== NOT_STATED) n += 1
  if (profile.city && profile.city !== NOT_STATED) n += 1
  if (profile.interest && profile.interest !== NOT_STATED) n += 1
  if (profile.programType && profile.programType !== NOT_STATED) n += 1
  if (profile.workMode && profile.workMode !== NOT_STATED) n += 1
  if (
    profile.skills.length > 0 &&
    !(profile.skills.length === 1 && profile.skills[0] === NOT_STATED)
  ) {
    n += 1
  }
  if (profile.interviewPreference?.trim()) n += 1
  if (profile.preferredRoles?.length) n += 1
  return n
}

/** How many real shelf cards to show based on profile completeness. */
export function shelfRevealCount(profile: StudentProfile): number {
  const filled = countProfileFieldsFilled(profile)
  if (filled === 0) return 0
  if (filled <= 2) return 1
  if (filled === 3) return 3
  if (filled === 4) return 4
  return 6
}

function pickLeftShelf(
  sorted: Recommendation[],
  max = 3,
): Recommendation[] {
  const strong = sorted.filter((r) => r.scorePercent >= 70)
  const pool = strong.length > 0 ? strong : sorted
  const picked: Recommendation[] = []
  const clusters = new Set<string>()

  for (const rec of pool) {
    if (picked.length >= max) break
    const cluster = rec.roleCluster?.toLowerCase() ?? ""
    if (
      cluster &&
      clusters.has(cluster) &&
      pool.some(
        (other) =>
          !picked.includes(other) &&
          (other.roleCluster?.toLowerCase() ?? "") !== cluster,
      )
    ) {
      continue
    }
    picked.push(rec)
    if (cluster) clusters.add(cluster)
  }

  if (picked.length < max) {
    for (const rec of pool) {
      if (picked.length >= max) break
      if (!picked.includes(rec)) picked.push(rec)
    }
  }

  return picked.slice(0, max)
}

function growthScore(rec: Recommendation): number {
  const missing = rec.missingSkills?.length ?? 0
  if (missing >= 1 && missing <= 3) return 10 - missing
  return 0
}

function pickRightShelf(
  sorted: Recommendation[],
  left: Recommendation[],
  max = 3,
): Recommendation[] {
  const used = new Set(left)
  const leftClusters = new Set(
    left.map((r) => r.roleCluster?.toLowerCase()).filter(Boolean) as string[],
  )
  const remaining = sorted.filter((r) => !used.has(r))

  const altCluster = remaining.filter((r) => {
    const c = r.roleCluster?.toLowerCase()
    return c && !leftClusters.has(c)
  })
  const growth = remaining.filter((r) => growthScore(r) > 0)
  const pool = [...altCluster, ...growth, ...remaining]

  const picked: Recommendation[] = []
  const seen = new Set<Recommendation>()

  for (const rec of pool) {
    if (picked.length >= max) break
    if (seen.has(rec)) continue
    seen.add(rec)
    picked.push(rec)
  }

  return picked.slice(0, max)
}

/** Interleave left/right picks as L1, R1, L2, R2, L3, R3 (oldest-first global order). */
function interleaveShelfMemories(
  left: CareerFitMemory[],
  right: CareerFitMemory[],
): CareerFitMemory[] {
  const out: CareerFitMemory[] = []
  const depth = Math.max(left.length, right.length)
  for (let i = 0; i < depth; i += 1) {
    const l = left[i]
    const r = right[i]
    if (l) out.push(l)
    if (r) out.push(r)
  }
  return out
}

/**
 * Build up to six shelf memories from backend recommendations.
 * Always reveals at least one card when the backend returned results, regardless of
 * how sparse the parsed profile is, so a real response never falls back to demo tiles.
 */
export function buildShelfMemoriesFromRecommendations(
  recommendations: Recommendation[],
  profile: StudentProfile,
): CareerFitMemory[] {
  if (recommendations.length === 0) return []
  const limit = Math.max(1, shelfRevealCount(profile))

  const sorted = [...recommendations].sort(
    (a, b) => b.scorePercent - a.scorePercent,
  )

  const leftRecs = pickLeftShelf(sorted, 3)
  const rightRecs = pickRightShelf(sorted, leftRecs, 3)

  const leftMemories = leftRecs.map(toCareerFitMemory)
  const rightMemories = rightRecs.map(toCareerFitMemory)

  return interleaveShelfMemories(leftMemories, rightMemories).slice(0, limit)
}
