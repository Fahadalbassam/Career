"use client"

import {
  AnimatePresence,
  motion,
  useReducedMotion,
} from "framer-motion"
import { usePathname } from "next/navigation"
import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react"

import { Skeleton } from "@/components/ui/skeleton"
import {
  CF_COMPOSER_INTRO_FROM_HOME_KEY,
  CF_HOME_INTRO_FROM_CHAT_KEY,
} from "@/components/home/home-exit-to-chat-context"
import { cn } from "@/lib/utils"

function useBriefSubtitleSkeletonOnHomeCareerCross(ms: number) {
  const pathname = usePathname()
  const prevRef = useRef<string | null>(null)
  const [show, setShow] = useState(false)

  useEffect(() => {
    const prev = prevRef.current
    prevRef.current = pathname

    if (prev === null) {
      return
    }

    const careerSurface = pathname === "/chat" || pathname === "/search"
    const prevCareerSurface = prev === "/chat" || prev === "/search"

    const crossHomeCareer =
      (prev === "/" && careerSurface) || (prevCareerSurface && pathname === "/")

    if (!crossHomeCareer) {
      return
    }

    /** Orchestrated Home→Chat shares layoutId wordmark + composer intro — skeleton swap shifts height and glitches. */
    if (
      prev === "/" &&
      pathname === "/chat" &&
      typeof window !== "undefined" &&
      window.sessionStorage.getItem(CF_COMPOSER_INTRO_FROM_HOME_KEY) === "1"
    ) {
      return
    }

    /** Chat→Home: shared `layoutId` wordmark + intro — skip skeleton so subtitle height doesn’t fight the morph. */
    if (
      pathname === "/" &&
      prev === "/chat" &&
      typeof window !== "undefined" &&
      window.sessionStorage.getItem(CF_HOME_INTRO_FROM_CHAT_KEY) === "1"
    ) {
      return
    }

    setShow(true)
    const t = window.setTimeout(() => setShow(false), ms)
    return () => window.clearTimeout(t)
  }, [pathname, ms])

  return show
}

function MarketingSubtitleSkeleton() {
  return (
    <div
      className="mx-auto flex max-w-2xl flex-col gap-3"
      aria-hidden
    >
      <Skeleton className="mx-auto h-5 w-full max-w-xl rounded-lg sm:h-6" />
      <Skeleton className="mx-auto h-5 w-full max-w-lg rounded-lg sm:h-6" />
      <Skeleton className="mx-auto h-5 w-4/5 max-w-md rounded-lg sm:h-6" />
    </div>
  )
}

function ShellSubtitleSkeleton() {
  return (
    <div
      className="mx-auto flex max-w-lg flex-col gap-2.5 px-1"
      aria-hidden
    >
      <Skeleton className="mx-auto h-4 w-full rounded-md md:h-[1.125rem]" />
      <Skeleton className="mx-auto h-4 w-[92%] rounded-md md:h-[1.125rem]" />
    </div>
  )
}

export function HeroSubtitleSlot({
  variant,
  children,
}: Readonly<{
  variant: "marketing" | "shell"
  children: ReactNode
}>) {
  const reduced = useReducedMotion()
  const showSkeleton = useBriefSubtitleSkeletonOnHomeCareerCross(400)

  if (reduced) {
    return children
  }

  const skeleton =
    variant === "marketing" ? (
      <MarketingSubtitleSkeleton />
    ) : (
      <ShellSubtitleSkeleton />
    )

  return (
    <div
      className={cn(
        "relative",
        variant === "marketing"
          ? "mt-5 min-h-[5.5rem] sm:min-h-[6rem]"
          : "min-h-[2.875rem] md:min-h-[3.125rem]",
      )}
    >
      <AnimatePresence mode="wait" initial={false}>
        {showSkeleton ? (
          <motion.div
            key="hero-sub-skeleton"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
          >
            {skeleton}
          </motion.div>
        ) : (
          <motion.div
            key="hero-sub-content"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.22 }}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
