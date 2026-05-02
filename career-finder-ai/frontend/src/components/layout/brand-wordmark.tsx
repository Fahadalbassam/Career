"use client"

import { motion, useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"

/** Match `CareerRouteShell` home→chat composer intro so the wordmark shrink stays in sync. */
const brandSharedLayoutTransition = {
  type: "tween" as const,
  duration: 0.52,
  ease: [0.2, 0.75, 0.15, 1] as const,
}

export function BrandWordmark({
  size,
  className,
  enableSharedLayout = true,
}: Readonly<{
  size: "hero" | "shell"
  className?: string
  /** When false, skips shared layout projection (e.g. Home exit scale choreography). */
  enableSharedLayout?: boolean
}>) {
  const reduced = useReducedMotion()

  return (
    <motion.h1
      layoutId={
        enableSharedLayout ? "careerfinder-brand-wordmark" : undefined
      }
      className={cn(
        "brand-name inline-block max-w-[100vw] font-semibold leading-none tracking-tight text-foreground",
        size === "hero"
          ? "text-4xl text-balance sm:text-5xl"
          : "text-3xl md:text-4xl",
        className,
      )}
      transition={
        reduced ? { duration: 0 } : brandSharedLayoutTransition
      }
    >
      CareerFinder.ai
    </motion.h1>
  )
}
