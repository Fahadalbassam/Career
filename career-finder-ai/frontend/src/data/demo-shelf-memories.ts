import { mockRecommendations } from "@/data/mock-recommendations"

import type { CareerFitMemory, Recommendation } from "@/lib/types"

/** Stable IDs — demo tiles only; mirrored on chat + search browse shell. */
export function demoShelfMemory(
  rec: Recommendation,
  stableId: string,
): CareerFitMemory {
  const reason =
    rec.whyRecommended.length > 140
      ? `${rec.whyRecommended.slice(0, 137)}…`
      : rec.whyRecommended

  return {
    id: stableId,

    title: rec.programName,

    matchConfidence: rec.scorePercent,

    tags: rec.matchedSkills.slice(0, 3),

    shortReason: reason,

    detailText: rec.whyRecommended,
  }
}

export const DEMO_SHELF_LEFT: CareerFitMemory[] = [
  demoShelfMemory(mockRecommendations[0], "demo-shelf-left-a"),

  demoShelfMemory(mockRecommendations[1], "demo-shelf-left-b"),

  demoShelfMemory(mockRecommendations[3], "demo-shelf-left-c"),
]

export const DEMO_SHELF_RIGHT: CareerFitMemory[] = [
  demoShelfMemory(mockRecommendations[2], "demo-shelf-right-a"),

  demoShelfMemory(mockRecommendations[4], "demo-shelf-right-b"),

  demoShelfMemory(mockRecommendations[1], "demo-shelf-right-c"),
]

/**
 * Global indices 0–5 for shelf slot mapping: left rows top→bottom, then right rows top→bottom.
 * These are the first six “chronological” shelf cards; user saves append after this block.
 */
export const DEMO_SHELF_GLOBAL_SIX: CareerFitMemory[] = [
  ...DEMO_SHELF_LEFT,
  ...DEMO_SHELF_RIGHT,
]
