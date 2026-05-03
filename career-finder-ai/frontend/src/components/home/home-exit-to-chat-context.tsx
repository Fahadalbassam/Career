"use client"

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  type ReactNode,
} from "react"

import { useReducedMotion } from "framer-motion"
import { useRouter } from "next/navigation"

export type HomeExitToChatContextValue = {
  registerHomeExitRunner: (runner: () => void | Promise<void>) => () => void
  navigateToChatFromHome: () => Promise<void>
  /**
   * Sets composer intro flag and `router.push("/chat")`.
   * Call from the home exit runner at the start of the exit sequence so `router.push`
   * and the wordmark `layoutId` morph begin immediately alongside hero exit motion.
   */
  beginChatNavigationFromHome: () => void
  /** Sets shelf intro flag and navigates to /search (Home → Search). */
  navigateToSearchFromHome: () => void
}

/**
 * Survives Strict Mode double-mount: shell reads this key on first paint after Home→Chat.
 */
export const CF_COMPOSER_INTRO_FROM_HOME_KEY = "cf_intro_composer_from_home_v1"

/** One-shot: slide side shelves in from edges after Home→/chat or Home→/search */
export const CF_SHELF_SLIDE_FROM_HOME_KEY = "cf_shelf_slide_from_home_v1"

/** One-shot: Home hero separator + feature cards rise in after Chat/Search→Home */
export const CF_HOME_INTRO_FROM_CHAT_KEY = "cf_home_intro_from_chat_v1"

const HomeExitToChatContext =
  createContext<HomeExitToChatContextValue | null>(null)

export function HomeExitToChatProvider({ children }: { children: ReactNode }) {
  const router = useRouter()

  const prefersReducedMotion = useReducedMotion()

  const exitRunnerRef = useRef<(() => void | Promise<void>) | null>(null)

  const navigatingRef = useRef(false)

  /** Cleared at start of each navigate; set when push is scheduled */
  const chatNavigationCommittedRef = useRef(false)

  const registerHomeExitRunner = useCallback((runner: () => void | Promise<void>) => {
    exitRunnerRef.current = runner

    return () => {
      exitRunnerRef.current = null
    }
  }, [])

  const beginChatNavigationFromHome = useCallback(() => {
    if (chatNavigationCommittedRef.current) return

    chatNavigationCommittedRef.current = true

    if (typeof window !== "undefined") {
      sessionStorage.setItem(CF_COMPOSER_INTRO_FROM_HOME_KEY, "1")
      if (!prefersReducedMotion) {
        sessionStorage.setItem(CF_SHELF_SLIDE_FROM_HOME_KEY, "1")
      }
    }

    router.push("/chat")
  }, [prefersReducedMotion, router])

  const navigateToSearchFromHome = useCallback(() => {
    if (!prefersReducedMotion && typeof window !== "undefined") {
      sessionStorage.setItem(CF_SHELF_SLIDE_FROM_HOME_KEY, "1")
    }

    router.push("/search")
  }, [prefersReducedMotion, router])

  const navigateToChatFromHome = useCallback(async () => {
    if (navigatingRef.current) return

    navigatingRef.current = true

    chatNavigationCommittedRef.current = false

    try {
      if (prefersReducedMotion) {
        beginChatNavigationFromHome()

        return
      }

      const run = exitRunnerRef.current

      if (run) await run()

      if (!chatNavigationCommittedRef.current) {
        beginChatNavigationFromHome()
      }
    } finally {
      navigatingRef.current = false
    }
  }, [prefersReducedMotion, beginChatNavigationFromHome])

  const value = useMemo(
    () => ({
      registerHomeExitRunner,
      navigateToChatFromHome,
      beginChatNavigationFromHome,
      navigateToSearchFromHome,
    }),
    [
      registerHomeExitRunner,
      navigateToChatFromHome,
      beginChatNavigationFromHome,
      navigateToSearchFromHome,
    ],
  )

  return (
    <HomeExitToChatContext.Provider value={value}>
      {children}
    </HomeExitToChatContext.Provider>
  )
}

export function useHomeExitToChat() {
  const ctx = useContext(HomeExitToChatContext)

  if (!ctx) {
    throw new Error(
      "useHomeExitToChat must be used within HomeExitToChatProvider",
    )
  }

  return ctx
}
