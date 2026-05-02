/** Snappy career→home shelf slide (see `CareerFitShelf` exit motion). */
export const SHELF_EXIT_DURATION_S = 0.4

export const SHELF_EXIT_RIGHT_DELAY_S = 0.05

/** Shared tween length for shelf sideways exit + career shell sliding down. */
export const CAREER_SHELL_EXIT_SYNC_DURATION_S =
  SHELF_EXIT_DURATION_S + SHELF_EXIT_RIGHT_DELAY_S

export const CAREER_SHELL_EXIT_SYNC_EASE = [0.22, 1, 0.36, 1] as const

/** Route change after shelf motion ends + short buffer (right shelf has stagger). */
export const CAREER_SHELF_EXIT_NAV_DELAY_MS =
  Math.ceil(CAREER_SHELL_EXIT_SYNC_DURATION_S * 1000) + 35
