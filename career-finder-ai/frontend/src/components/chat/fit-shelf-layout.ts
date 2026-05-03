import type { CareerFitMemory } from "@/lib/types"

import { DEMO_SHELF_GLOBAL_SIX } from "@/data/demo-shelf-memories"

/** Visible shelf uses at most this many cards total (demo + saves). First N are kept, not latest N. */
export const SHELF_VISIBLE_GLOBAL_CARD_CAP = 18

/** Round-robin group size: 3 rows left + 3 rows right before repeating slots. */
const GROUP_CYCLE = 6

/** Rows per shelf; each stack holds at most this many cards */
const STACK_DEPTH_CAP = 3

/** Rows per shelf (slots) */
export const SHELF_ROWS = 3

/**
 * Single chronological list: the six fixed demo tiles first (global indices 0–5), then each
 * finalized save in the order it was added (oldest save → newest save).
 */
export function buildAllShelfCardsOldestFirst(
  finalizedSavedOldestFirst: CareerFitMemory[],
): CareerFitMemory[] {
  const combined = [...DEMO_SHELF_GLOBAL_SIX, ...finalizedSavedOldestFirst]
  if (combined.length <= SHELF_VISIBLE_GLOBAL_CARD_CAP) return combined
  return combined.slice(0, SHELF_VISIBLE_GLOBAL_CARD_CAP)
}

/**
 * Recover chronological saved order from alternating shelf storage:
 * odd saves prepend to left, even saves prepend to right.
 */
export function mergeShelvesToGlobalOldestFirst(
  leftNewestFirst: CareerFitMemory[],
  rightNewestFirst: CareerFitMemory[],
): CareerFitMemory[] {
  const odds = [...leftNewestFirst].reverse()
  const evens = [...rightNewestFirst].reverse()
  const out: CareerFitMemory[] = []
  const n = Math.max(odds.length, evens.length)
  for (let i = 0; i < n; i += 1) {
    const o = odds[i]
    const e = evens[i]
    if (o) out.push(o)
    if (e) out.push(e)
  }
  return out
}

/**
 * Shelf stacking from one global chronological list (demo six first, then saves).
 * slotIndex = globalIndex % 6; stackLayer = floor(globalIndex / 6), capped at 3 deep per row.
 * slotIndex 0–2 → left rows 0–2; 3–5 → right rows 0–2.
 * Row stacks are oldest → newest in array order; the renderer puts the newest on top (base
 * transform) and older cards behind — no reordering by confidence.
 */
export function buildShelfRowStacks(
  side: "left" | "right",
  globalOldestFirst: CareerFitMemory[],
): CareerFitMemory[][] {
  const rows: CareerFitMemory[][] = [[], [], []]

  for (let globalIdx = 0; globalIdx < globalOldestFirst.length; globalIdx += 1) {
    const slotIndex = globalIdx % GROUP_CYCLE
    const stackLayer = Math.floor(globalIdx / GROUP_CYCLE)
    if (stackLayer >= STACK_DEPTH_CAP) continue

    const assignLeft = slotIndex < SHELF_ROWS
    if (assignLeft !== (side === "left")) continue

    const row = assignLeft ? slotIndex : slotIndex - SHELF_ROWS
    const rowStacks = rows[row]
    if (!rowStacks || rowStacks.length >= STACK_DEPTH_CAP) continue
    rowStacks.push(globalOldestFirst[globalIdx]!)
  }

  return rows
}
