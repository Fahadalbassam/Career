"use client"

import { motion, useReducedMotion } from "framer-motion"
import { useMemo } from "react"

import { cn } from "@/lib/utils"

import { FitShelfWidget } from "@/components/chat/fit-shelf-widget"
import {
  SHELF_CARD_H_PX,
  SHELF_CARD_W_PX,
} from "@/components/chat/shelf-dimensions"

import type { CareerFitMemory } from "@/lib/types"
import {
  SHELF_EXIT_DURATION_S,
  SHELF_EXIT_RIGHT_DELAY_S,
} from "@/components/chat/fit-shelf-exit-timing"
import { buildShelfRowStacks } from "@/components/chat/fit-shelf-layout"

export { SHELF_CARD_H_PX, SHELF_CARD_W_PX } from "@/components/chat/shelf-dimensions"

export { mergeShelvesToGlobalOldestFirst } from "@/components/chat/fit-shelf-layout"

const SHELF_GAP_PX = 14

const GRID_COLS = 1
const GRID_ROWS = 3

/** Single column, top → middle → bottom */
const SLOT_ROW_COL: ReadonlyArray<{ row: number; col: number }> = [
  { row: 0, col: 0 },
  { row: 1, col: 0 },
  { row: 2, col: 0 },
]

export const SHELF_GRID_WIDTH_PX =
  GRID_COLS * SHELF_CARD_W_PX + (GRID_COLS - 1) * SHELF_GAP_PX
export const SHELF_GRID_HEIGHT_PX =
  GRID_ROWS * SHELF_CARD_H_PX + (GRID_ROWS - 1) * SHELF_GAP_PX

const shelfSlideEase = [0.22, 1, 0.36, 1] as const

const shelfSlideDuration = 0.56

function shelfSlideTransition(side: "left" | "right") {
  return {
    duration: shelfSlideDuration,
    ease: shelfSlideEase,
    delay: side === "right" ? 0.06 : 0,
  }
}

function shelfExitTransition(side: "left" | "right") {
  return {
    duration: SHELF_EXIT_DURATION_S,
    ease: shelfSlideEase,
    delay: side === "right" ? SHELF_EXIT_RIGHT_DELAY_S : 0,
  }
}

function slotOffsetPx(row: number, col: number) {
  return {
    left: col * (SHELF_CARD_W_PX + SHELF_GAP_PX),
    top: row * (SHELF_CARD_H_PX + SHELF_GAP_PX),
  }
}

/** Top→bottom rows; horizontal strip lists front-first (newest first), matching the grid’s front slot. */
function sideMemoriesFlattenForStrip(rows: CareerFitMemory[][]): CareerFitMemory[] {
  return rows.flatMap((stack) => [...stack].reverse())
}

export function CareerFitShelf({
  side,
  globalSavedOldestFirst,
  newestId,
  className,
  collapsed,
  slideFromHomeIntro = false,
  slideOutToHome = false,
  searchLoading = false,
}: {
  side: "left" | "right"
  /** Full shelf history merge (oldest → newest); slots are derived per side. */
  globalSavedOldestFirst: CareerFitMemory[]
  newestId?: string | null
  className?: string
  collapsed?: boolean
  /** Home→career: slide shelf in from outer edge */
  slideFromHomeIntro?: boolean
  /** Career→Home: slide shelf out toward outer edge */
  slideOutToHome?: boolean
  /** Search composer submitted: pulse skeleton on visible card faces. */
  searchLoading?: boolean
}) {
  const reducedMotion = useReducedMotion()

  const runHomeSlide = slideFromHomeIntro && !reducedMotion

  const shelfRest = { x: 0, opacity: 1 }

  const shelfExitTarget = collapsed
    ? side === "left"
      ? { x: "-36vw", opacity: 0 }
      : { x: "36vw", opacity: 0 }
    : side === "left"
      ? { x: "-42vw", opacity: 0 }
      : { x: "42vw", opacity: 0 }

  const animateTarget =
    slideOutToHome && !reducedMotion ? shelfExitTarget : shelfRest

  const motionTransition =
    slideOutToHome && !reducedMotion
      ? shelfExitTransition(side)
      : shelfSlideTransition(side)

  const rowStacks = useMemo(
    () => buildShelfRowStacks(side, globalSavedOldestFirst),
    [side, globalSavedOldestFirst],
  )

  const totalOnSide = rowStacks.reduce((n, r) => n + r.length, 0)

  if (totalOnSide === 0 && !searchLoading) {
    return null
  }

  const skeletonOnly = totalOnSide === 0 && searchLoading

  if (skeletonOnly && collapsed) {
    return (
      <motion.div
        className={cn(
          "flex w-full gap-2 pb-1 pt-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
          slideOutToHome && !reducedMotion
            ? "overflow-x-hidden"
            : "overflow-x-auto",
          className,
        )}
        initial={
          runHomeSlide
            ? { x: side === "left" ? "-36vw" : "36vw", opacity: 0 }
            : false
        }
        animate={animateTarget}
        transition={motionTransition}
      >
        {[0, 1, 2].map((i) => (
          <div
            key={`search-sk-strip-${i}`}
            className="relative shrink-0 [transform-style:preserve-3d]"
            style={{
              width: SHELF_CARD_W_PX,
              height: SHELF_CARD_H_PX,
              maxWidth: "min(230px, 85vw)",
            }}
          >
            <FitShelfWidget
              side={side}
              pileInSlot={0}
              stripDepthIndex={i}
              title=""
              confidence={0}
              tags={[]}
              reason=""
              details=""
              layout="strip"
              loadingSkeleton
            />
          </div>
        ))}
      </motion.div>
    )
  }

  if (skeletonOnly) {
    return (
      <motion.div
        className={cn(
          "relative flex w-full flex-col items-center justify-start overflow-visible",
          className,
        )}
        style={{ minHeight: SHELF_GRID_HEIGHT_PX + 12 }}
        initial={
          runHomeSlide
            ? { x: side === "left" ? "-42vw" : "42vw", opacity: 0 }
            : false
        }
        animate={animateTarget}
        transition={motionTransition}
      >
        <div
          className={cn(
            "relative flex w-full overflow-visible",
            side === "left" ? "justify-end" : "justify-start",
          )}
          style={
            side === "left"
              ? {
                  perspective: "1150px",
                  perspectiveOrigin: "62% 50%",
                }
              : {
                  perspective: "900px",
                  perspectiveOrigin: "38% 50%",
                }
          }
        >
          <div
            data-shelf-tilt-root
            data-side={side}
            className="relative shrink-0 [transform-style:preserve-3d]"
            style={{
              width: SHELF_GRID_WIDTH_PX,
              height: SHELF_GRID_HEIGHT_PX,
              maxWidth: "100%",
            }}
          >
            {SLOT_ROW_COL.map((slot, slotIndex) => {
              const { row, col } = slot
              const { left, top } = slotOffsetPx(row, col)
              const rowFrontZ = slotIndex * 20

              return (
                <div
                  key={`search-sk-grid-${slotIndex}`}
                  className="absolute [transform-style:preserve-3d]"
                  style={{
                    left,
                    top,
                    width: SHELF_CARD_W_PX,
                    height: SHELF_CARD_H_PX,
                    zIndex: 20 + slotIndex * 40,
                  }}
                >
                  <div
                    className="absolute inset-0 [transform-style:preserve-3d]"
                    style={{
                      pointerEvents: "none",
                      zIndex: 10,
                      transform: `translateZ(${rowFrontZ}px)`,
                    }}
                  >
                    <FitShelfWidget
                      side={side}
                      pileInSlot={0}
                      title=""
                      confidence={0}
                      tags={[]}
                      reason=""
                      details=""
                      layout="stack"
                      loadingSkeleton
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </motion.div>
    )
  }

  if (collapsed) {
    const stripOrder = sideMemoriesFlattenForStrip(rowStacks)
    return (
      <motion.div
        className={cn(
          "flex w-full gap-2 pb-1 pt-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
          slideOutToHome && !reducedMotion
            ? "overflow-x-hidden"
            : "overflow-x-auto",
          className,
        )}
        initial={
          runHomeSlide
            ? { x: side === "left" ? "-36vw" : "36vw", opacity: 0 }
            : false
        }
        animate={animateTarget}
        transition={motionTransition}
      >
        {stripOrder.map((memory, index) => (
          <div
            key={memory.id}
            className="relative shrink-0 [transform-style:preserve-3d]"
            style={{
              width: SHELF_CARD_W_PX,
              height: SHELF_CARD_H_PX,
              maxWidth: "min(230px, 85vw)",
            }}
          >
            <FitShelfWidget
              side={side}
              pileInSlot={0}
              stripDepthIndex={index}
              title={memory.title}
              confidence={memory.matchConfidence}
              tags={memory.tags}
              reason={memory.shortReason}
              details={
                memory.detailText ?? memory.shortReason
              }
              layout="strip"
              animateEnter={memory.id === newestId}
              loadingSkeleton={searchLoading}
            />
          </div>
        ))}
      </motion.div>
    )
  }

  return (
    <motion.div
      className={cn(
        "relative flex w-full flex-col items-center justify-start overflow-visible",
        className,
      )}
      style={{ minHeight: SHELF_GRID_HEIGHT_PX + 12 }}
      initial={
        runHomeSlide
          ? { x: side === "left" ? "-42vw" : "42vw", opacity: 0 }
          : false
      }
      animate={animateTarget}
      transition={motionTransition}
    >
      <div
        className={cn(
          "relative flex w-full overflow-visible",
          side === "left" ? "justify-end" : "justify-start",
        )}
        style={
          side === "left"
            ? {
                perspective: "1150px",
                perspectiveOrigin: "62% 50%",
              }
            : {
                perspective: "900px",
                perspectiveOrigin: "38% 50%",
              }
        }
      >
        <div
          data-shelf-tilt-root
          data-side={side}
          className="relative shrink-0 [transform-style:preserve-3d]"
          style={{
            width: SHELF_GRID_WIDTH_PX,
            height: SHELF_GRID_HEIGHT_PX,
            maxWidth: "100%",
          }}
        >
          {rowStacks.map((stack, slotIndex) => {
            if (stack.length === 0) return null
            const { row, col } = SLOT_ROW_COL[slotIndex]!
            const { left, top } = slotOffsetPx(row, col)

            /** Row bias so shadows / depth-sort stay consistent top → bottom. */
            const rowFrontZ = slotIndex * 20

            return (
              <div
                key={`row-${slotIndex}`}
                className="absolute [transform-style:preserve-3d]"
                style={{
                  left,
                  top,
                  width: SHELF_CARD_W_PX,
                  height: SHELF_CARD_H_PX,
                  zIndex: 20 + slotIndex * 40 + stack.length - 1,
                }}
              >
                {stack.map((memory, stackIndex) => {
                  /** stack[] is oldest → newest; newest is pile 0 at the slot anchor; older piles recede toward shelf edge. */
                  const pile = stack.length - 1 - stackIndex
                  const isFront = pile === 0
                  /** Deeper layers: negative Z recedes into the screen; X shifts toward outer shelf edge (left shelf → left −x, right → +x). */
                  const depthZPerLayer = 22
                  /** Stronger X on the left shelf so back cards peek clearly west of the front tile. */
                  const edgeXPerLayer = side === "left" ? 26 : 7
                  const peekYPerLayer = 3
                  const zTranslate =
                    pile === 0
                      ? rowFrontZ
                      : rowFrontZ - depthZPerLayer * pile
                  const deckDx =
                    pile === 0
                      ? 0
                      : side === "left"
                        ? -edgeXPerLayer * pile
                        : edgeXPerLayer * pile
                  const deckDy = pile === 0 ? 0 : peekYPerLayer * pile
                  const pileTranslate =
                    deckDx !== 0 || deckDy !== 0
                      ? `translateZ(${zTranslate}px) translate(${deckDx}px, ${deckDy}px)`
                      : `translateZ(${zTranslate}px)`

                  return (
                    <div
                      key={memory.id}
                      className="absolute inset-0 [transform-style:preserve-3d]"
                      aria-hidden={!isFront}
                      style={{
                        pointerEvents: isFront ? "auto" : "none",
                        opacity: isFront ? 1 : pile === 1 ? 0.9 : 0.82,
                        zIndex: 10 + stackIndex,
                        transform: pileTranslate,
                      }}
                    >
                      <FitShelfWidget
                        side={side}
                        pileInSlot={pile}
                        title={memory.title}
                        confidence={memory.matchConfidence}
                        tags={memory.tags}
                        reason={memory.shortReason}
                        details={
                          memory.detailText ?? memory.shortReason
                        }
                        layout="stack"
                        animateEnter={memory.id === newestId}
                        loadingSkeleton={searchLoading && isFront}
                      />
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>
    </motion.div>
  )
}
