/** Parsed student profile returned by `/recommend` (snake_case, backend shape). */
export interface ParsedProfileApi {
  major: string | null
  university: string | null
  city: string | null
  preferred_locations: string[]
  skills: string[]
  qualifications: string[]
  interest: string | null
  program_type: string | null
  work_mode: string | null
  preferred_roles: string[]
  interview_preference: string | null
}

export interface ScoreBreakdownApi {
  major_fit_score: number
  skill_match_score: number
  role_interest_score: number
  city_match_score: number
  program_type_score: number
  work_mode_score: number
  verification_score: number
  interview_score: number
}

export interface OpportunityApi {
  id: string
  rank: number
  company: string
  title: string
  city: string
  work_mode: string
  program_type: string
  major_fit: string[]
  requirements: string
  skills_list: string[]
  source_url: string
  score: number
  match_score: number
  why_recommended: string[]
  skills_matched: string[]
  role_cluster: string
  interview_required: string
  missing_skills: string[]
  score_breakdown: ScoreBreakdownApi
}

/** Response body from `POST /recommend`. */
export interface RecommendApiResponse {
  profile: ParsedProfileApi
  recommendations: OpportunityApi[]
  total_candidates: number
}
