"use client"

import type { KeyboardEvent as ReactKeyboardEvent } from "react"
import { useMemo, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { ScoreBadge } from "@/components/recommendations/score-badge"
import { ShelfMetalSurface } from "@/components/chat/shelf-metal-surface"
import { cn } from "@/lib/utils"

/** Left shelf: left edge visually closer (+Y). Right: right edge closer (−Y). */
const SHELF_TILT_Y_DEG_LEFT = 14
const SHELF_TILT_Y_DEG_RIGHT = 16

export type FitShelfWidgetProps = {
  side: "left" | "right"
  /** In-slot pile layer after the first 6 grid slots are full; 0 = on-grid only. */
  pileInSlot: number
  /** Horizontal strip only: visual depth in the row. */
  stripDepthIndex?: number
  title: string
  confidence: number
  tags: string[]
  reason: string
  details: string
  layout?: "stack" | "strip"
  className?: string
  animateEnter?: boolean
  /** Pulse placeholders on the metal face (search in-flight). */
  loadingSkeleton?: boolean
  roleCluster?: string
  city?: string
  workMode?: string
  programType?: string
  interviewRequired?: string
  missingSkills?: string[]
  sourceUrl?: string
}

export function FitShelfWidget({
  side,
  pileInSlot,
  stripDepthIndex = 0,
  title,
  confidence,
  tags,
  reason,
  details,
  layout = "stack",
  className,
  animateEnter,
  loadingSkeleton = false,
  roleCluster,
  city,
  workMode,
  programType,
  interviewRequired,
  missingSkills,
  sourceUrl,
}: FitShelfWidgetProps) {
  const [hovered, setHovered] = useState(false)
  const [flipped, setFlipped] = useState(false)

  const isStrip = layout === "strip"
  const stripDepth = Math.min(stripDepthIndex, 5)

  /** Only the front card in a grid stack receives hover flatten / flip; behind cards stay tilted and static. */
  const stackInteractive =
    !loadingSkeleton && (isStrip || pileInSlot === 0)

  const tiltFree = stackInteractive && (hovered || flipped)

  const defaultTiltY = side === "left" ? SHELF_TILT_Y_DEG_LEFT : -SHELF_TILT_Y_DEG_RIGHT

  /** Strip / single-row: unchanged lift. Stack front: bias shadow toward chat so less pools on the card behind. Stack back: one soft layer so stacks blend instead of doubling dark rims. */
  const isBackOfStack = layout === "stack" && pileInSlot > 0

  const stripDefaultLiftShadow =
    "0 14px 34px -10px rgba(0,0,0,0.58), 0 6px 14px -6px rgba(0,0,0,0.45)"
  const stripHoverLiftShadow =
    "0 22px 48px -14px rgba(0,0,0,0.55), 0 12px 24px -12px rgba(0,0,0,0.42)"

  const stackFrontDefaultLeft =
    "7px 14px 34px -10px rgba(0,0,0,0.54), 4px 6px 14px -6px rgba(0,0,0,0.42)"
  const stackFrontDefaultRight =
    "-7px 14px 34px -10px rgba(0,0,0,0.54), -4px 6px 14px -6px rgba(0,0,0,0.42)"
  const stackFrontHoverLeft =
    "11px 22px 48px -14px rgba(0,0,0,0.52), 7px 12px 24px -12px rgba(0,0,0,0.40)"
  const stackFrontHoverRight =
    "-11px 22px 48px -14px rgba(0,0,0,0.52), -7px 12px 24px -12px rgba(0,0,0,0.40)"

  const stackBackLiftShadow = "0 5px 14px -12px rgba(0,0,0,0.16)"

  const defaultLiftShadow = isBackOfStack
    ? stackBackLiftShadow
    : isStrip
      ? stripDefaultLiftShadow
      : side === "left"
        ? stackFrontDefaultLeft
        : stackFrontDefaultRight

  const hoverLiftShadow = isBackOfStack
    ? stackBackLiftShadow
    : isStrip
      ? stripHoverLiftShadow
      : side === "left"
        ? stackFrontHoverLeft
        : stackFrontHoverRight

  const tiltShadow = tiltFree ? hoverLiftShadow : defaultLiftShadow

  const toggleFlip = () => setFlipped((f) => !f)

  const onKeyToggle = (e: ReactKeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      toggleFlip()
    }
  }

  const stackZ = flipped ? 80 : 28

  /** Strip row: subtle depth only (grid pile uses parent transforms in `fit-shelf`). */
  const stripTransform = useMemo(() => {
    if (!isStrip) return undefined
    const dz = stripDepth * 12
    const dy = stripDepth * 7
    const dzLift = tiltFree ? 14 : 0
    return `translateY(${dy}px) translateZ(${dzLift - dz}px)`
  }, [isStrip, stripDepth, tiltFree])

  /** Shelf tilt / hover flatten — never combined with flip rotation. */
  const tiltTransform = tiltFree ? "rotateY(0deg)" : `rotateY(${defaultTiltY}deg)`

  const tagRow = tags.slice(0, 3)

  const metaParts = [roleCluster, city, workMode, programType].filter(
    (part): part is string => Boolean(part?.trim()),
  )
  const metaLine = metaParts.join(" · ")
  const missingRow = missingSkills?.slice(0, 3) ?? []
  const interviewLine = interviewRequired?.trim()
  const applyUrl = sourceUrl?.trim()

  return (
    <div
      className={cn(
        "h-full w-full [transform-style:preserve-3d] transition-[transform,opacity] duration-300 ease-out",
        animateEnter && "animate-fit-shelf-enter",
        className,
      )}
      style={
        isStrip
          ? {
              zIndex: stackZ,
              transform: stripTransform,
              transformStyle: "preserve-3d",
            }
          : { transformStyle: "preserve-3d" }
      }
      data-side={side}
      data-pile={pileInSlot}
      data-flipped={flipped || undefined}
    >
      <div
        className={cn(
          "relative h-full w-full overflow-visible rounded-lg [transform-style:preserve-3d]",
          "[transition:transform_240ms_cubic-bezier(0.22,1,0.36,1),box-shadow_240ms_cubic-bezier(0.22,1,0.36,1)]",
        )}
        style={{
          width: "100%",
          height: "100%",
          transform: tiltTransform,
          boxShadow: tiltShadow,
        }}
        onMouseEnter={() => {
          if (stackInteractive) setHovered(true)
        }}
        onMouseLeave={() => {
          if (stackInteractive) setHovered(false)
        }}
      >
        <div
          role={stackInteractive ? "button" : undefined}
          tabIndex={stackInteractive ? 0 : -1}
          aria-pressed={stackInteractive ? flipped : undefined}
          aria-label={
            stackInteractive
              ? flipped
                ? "Show compact fit summary"
                : "Show detailed fit information"
              : undefined
          }
          className={cn(
            "relative z-[1] h-full w-full min-h-0 outline-none [transform-style:preserve-3d]",
            "[transition:transform_620ms_cubic-bezier(0.22,1,0.36,1)]",
            stackInteractive &&
              "cursor-pointer focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0",
          )}
          style={{
            transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
            pointerEvents: stackInteractive ? undefined : "none",
          }}
          onClick={(e) => {
            if (!stackInteractive) return
            e.stopPropagation()
            toggleFlip()
          }}
          onKeyDown={stackInteractive ? onKeyToggle : undefined}
        >
          <div
            className="absolute inset-0 h-full w-full overflow-hidden rounded-lg [backface-visibility:hidden] [-webkit-backface-visibility:hidden]"
            style={{ transform: "translateZ(0.5px) rotateY(0deg)" }}
          >
            <ShelfMetalSurface
              side={side}
              className="box-border h-full w-full min-h-0 px-3.5 py-2.5 sm:px-4 sm:py-3"
            >
              {loadingSkeleton ? (
                <div className="flex h-full min-h-0 flex-col gap-1.5 sm:gap-2">
                  <div className="flex min-h-0 items-start justify-between gap-2">
                    <div className="h-4 min-w-0 flex-1 animate-pulse rounded-md bg-white/15" />
                    <div className="h-6 w-11 shrink-0 animate-pulse rounded-md bg-white/15 sm:w-12" />
                  </div>
                  <div className="flex min-h-0 flex-col gap-1.5">
                    <div className="h-3 w-full animate-pulse rounded bg-white/12" />
                    <div className="h-3 w-[88%] animate-pulse rounded bg-white/12" />
                  </div>
                  <div className="mt-auto flex min-h-0 flex-wrap gap-1 pr-0.5">
                    <div className="h-5 w-14 animate-pulse rounded-md bg-white/12" />
                    <div className="h-5 w-16 animate-pulse rounded-md bg-white/12" />
                  </div>
                </div>
              ) : (
              <div className="flex h-full min-h-0 flex-col gap-1.5 font-sans font-extrabold leading-snug tracking-tight text-white sm:gap-2">
                <div className="flex min-h-0 items-start justify-between gap-2">
                  <p className="min-w-0 text-[13px] leading-snug sm:text-[14px] line-clamp-2">
                    {title}
                  </p>
                  <ScoreBadge
                    scorePercent={confidence}
                    className="shrink-0 !border-white/25 !bg-white/10 px-2 py-0.5 !text-[11px] !font-extrabold !text-white tabular-nums sm:!text-xs"
                  />
                </div>
                <p className="line-clamp-2 min-h-0 text-[11px] text-white/90 sm:text-xs">
                  {reason}
                </p>
                <div className="mt-auto flex min-h-0 flex-nowrap gap-1 overflow-hidden pr-0.5">
                  {tagRow.map((tag) => (
                    <Badge
                      key={tag}
                      variant="outline"
                      title={tag}
                      className="min-w-0 max-w-[34%] shrink !border-white/25 !bg-transparent truncate px-1.5 py-0.5 !text-[10px] !font-extrabold leading-none !text-white sm:!text-[11px]"
                    >
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
              )}
            </ShelfMetalSurface>
          </div>

          <div
            className={cn(
              "absolute inset-0 flex h-full w-full min-h-0 flex-col overflow-hidden rounded-lg border-2 border-black bg-white p-3 text-black [backface-visibility:hidden] [-webkit-backface-visibility:hidden] sm:p-3.5",
            )}
            style={{
              transform: "rotateY(180deg) translateZ(0.5px)",
              boxShadow:
                "0 20px 40px -12px rgba(0,0,0,0.35), 0 8px 16px -8px rgba(0,0,0,0.2)",
              color: "black",
              backgroundColor: "white",
            }}
          >
            <p className="shrink-0 text-[10px] font-extrabold uppercase tracking-wider text-neutral-700 sm:text-[11px]">
              Fit detail
            </p>
            <p className="mt-1 line-clamp-2 shrink-0 font-sans text-[12px] font-extrabold leading-snug tracking-tight text-black sm:mt-1.5 sm:text-sm">
              {title}
            </p>
            <div className="mt-1.5 shrink-0 sm:mt-2">
              <span className="inline-flex rounded border border-black/25 bg-neutral-50 px-2 py-0.5 font-mono text-[10px] font-extrabold tabular-nums text-black sm:text-xs">
                {Math.min(100, Math.max(0, Math.round(confidence)))}% match
              </span>
            </div>
            <p className="mt-2 min-h-0 flex-1 basis-0 overflow-y-auto text-[10px] font-semibold leading-relaxed tracking-tight text-black [overflow-wrap:anywhere] [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:mt-3 sm:text-[11px]">
              {details}
            </p>
            {metaLine ? (
              <p className="mt-1.5 shrink-0 text-[9px] font-bold uppercase tracking-wide text-neutral-600 sm:text-[10px]">
                {metaLine}
              </p>
            ) : null}
            {interviewLine ? (
              <p className="mt-1 shrink-0 text-[10px] font-semibold text-black sm:text-[11px]">
                Interview: {interviewLine}
              </p>
            ) : null}
            {missingRow.length > 0 ? (
              <div className="mt-1.5 flex shrink-0 flex-wrap gap-1">
                {missingRow.map((skill) => (
                  <span
                    key={skill}
                    className="rounded border border-black/20 bg-neutral-50 px-1.5 py-0.5 text-[9px] font-bold text-black sm:text-[10px]"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            ) : null}
            {applyUrl ? (
              <a
                href={applyUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex shrink-0 text-[10px] font-extrabold text-black underline underline-offset-2 hover:text-neutral-700 sm:text-[11px]"
                onClick={(e) => e.stopPropagation()}
              >
                Open posting →
              </a>
            ) : null}
            {tags.length > 0 ? (
              <div className="mt-2 flex shrink-0 flex-nowrap gap-1 overflow-hidden border-t border-black/10 pt-2 sm:mt-2 sm:gap-1 sm:pt-2">
                {tags.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    title={tag}
                    className="min-w-0 flex-1 truncate rounded border border-black px-1 py-0.5 text-center text-[9px] font-extrabold leading-none text-black sm:text-[10px]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}
