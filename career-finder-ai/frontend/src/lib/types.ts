/** Structured student preferences used when requesting recommendations. */
export interface StudentProfile {
  major: string
  city: string
  interest: string
  workMode: string
  programType: string
  skills: string[]
}

/** Single ranked opportunity returned by the recommender (API-aligned shape). */
export interface Recommendation {
  rank: number
  companyName: string
  programName: string
  city: string
  programType: string
  workMode: string
  fitLevel: string
  scorePercent: number
  matchedSkills: string[]
  whyRecommended: string
  sourceUrl: string
  sourceLabel?: string
}

/** Payload for a future `/recommend`-style request. */
export interface RecommendRequest {
  profile: StudentProfile
  studentQuery?: string
}

/** Compact career fit saved to the left/right shelf (mock UI state). */
export interface CareerFitMemory {
  id: string
  /** Primary label — typically role or program title. */
  title: string
  matchConfidence: number
  tags: string[]
  shortReason: string
  /** Longer copy for the shelf card back; falls back to {@link shortReason} when absent. */
  detailText?: string
}
