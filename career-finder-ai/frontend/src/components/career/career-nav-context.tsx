"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ChangeEvent,
  type Dispatch,
  type KeyboardEvent,
  type MutableRefObject,
  type ReactNode,
  type SetStateAction,
} from "react"

import { useReducedMotion } from "framer-motion"
import { usePathname, useRouter } from "next/navigation"

import type { CareerFitMemory } from "@/lib/types"

import { CAREER_SHELF_EXIT_NAV_DELAY_MS } from "@/components/chat/fit-shelf-exit-timing"
import { CF_HOME_INTRO_FROM_CHAT_KEY } from "@/components/home/home-exit-to-chat-context"

export type CareerNavHandlers = {
  goChatToSearch: () => Promise<void>
  goSearchToChat: () => Promise<void>
}

export type ChatComposerBridge = {
  empty: boolean
  input: string
  setInput: (next: string) => void
  loading: boolean
  send: () => void
  onKeyDown: (e: KeyboardEvent<HTMLTextAreaElement>) => void
  onPickExamplePrompt: (prompt: string) => void
  onResumePdfChange: (e: ChangeEvent<HTMLInputElement>) => void
  resumeFileName: string | null
  clearResume: () => void
  triggerResumePick: () => void
  textareaRef: MutableRefObject<HTMLTextAreaElement | null>
  resumeInputRef: MutableRefObject<HTMLInputElement | null>
  /** Scroll/message column: faded as the composer rises (non-empty chat → search), same as hero typography. */
  threadFadeTargetRef: MutableRefObject<HTMLElement | null>
}


export type CareerChromeContextValue = {
  navHandlers: CareerNavHandlers | undefined
  composerBridge: ChatComposerBridge | null
  registerNavHandlers: (next: CareerNavHandlers | undefined) => void
  registerComposerBridge: (next: ChatComposerBridge | null) => void
  /** Shared shelf memories (chat finalize + search browse use the same rails). */
  savedShelfMemoriesOldestFirst: CareerFitMemory[]
  setSavedShelfMemoriesOldestFirst: Dispatch<SetStateAction<CareerFitMemory[]>>
  newestShelfMemoryId: string | null
  setNewestShelfMemoryId: Dispatch<SetStateAction<string | null>>
  /** True while shelves animate out to the sides before navigating Home */
  shelfExitToHomeActive: boolean
  /** Home: `layoutId` shrink/grow with empty chat shell; Search→Home keeps shelf delay + exit. */
  navigateHomeFromCareer: () => Promise<void>
  /** Search route: composer submit in-flight (shelves + example dots reflect this). */
  searchComposerBusy: boolean
  setSearchComposerBusy: Dispatch<SetStateAction<boolean>>
}

const CareerChromeContext = createContext<CareerChromeContextValue | null>(null)

export function CareerChromeProvider({ children }: { children: ReactNode }) {
  const router = useRouter()

  const pathname = usePathname()

  const prefersReducedMotion = useReducedMotion()

  const [navHandlers, setNavHandlers] = useState<CareerNavHandlers | undefined>(undefined)

  const [composerBridge, setComposerBridge] = useState<ChatComposerBridge | null>(
    null,
  )

  const [savedShelfMemoriesOldestFirst, setSavedShelfMemoriesOldestFirst] =
    useState<CareerFitMemory[]>([])

  const [newestShelfMemoryId, setNewestShelfMemoryId] = useState<string | null>(
    null,
  )

  const [shelfExitToHomeActive, setShelfExitToHomeActive] = useState(false)

  const [searchComposerBusy, setSearchComposerBusy] = useState(false)

  /**
   * `navigateHomeFromCareer` leaves this true while `/chat` | `/search` is still
   * the active path; the provider stays mounted on `/`, so we must clear when
   * entering career routes again or shelves stay off-screen.
   */
  useEffect(() => {
    if (pathname === "/chat" || pathname === "/search") {
      queueMicrotask(() => {
        setShelfExitToHomeActive(false)
      })
    }
  }, [pathname])

  const registerNavHandlers = useCallback((next: CareerNavHandlers | undefined) => {
    setNavHandlers(next)
  }, [])

  const registerComposerBridge = useCallback((next: ChatComposerBridge | null) => {
    setComposerBridge(next)
  }, [])

  const navigateHomeFromCareer = useCallback(async () => {
    if (prefersReducedMotion) {
      router.push("/")

      return
    }

    /** Chat→Home: navigate immediately so `layoutId` wordmark can morph without waiting on shelf delay. */
    if (pathname === "/chat") {
      if (typeof window !== "undefined") {
        sessionStorage.setItem(CF_HOME_INTRO_FROM_CHAT_KEY, "1")
      }

      router.push("/")

      return
    }

    /** Search→Home: unchanged — shelf exit, then intro + push. */
    setShelfExitToHomeActive(true)

    await new Promise<void>((resolve) => {
      window.setTimeout(resolve, CAREER_SHELF_EXIT_NAV_DELAY_MS)
    })

    if (typeof window !== "undefined") {
      sessionStorage.setItem(CF_HOME_INTRO_FROM_CHAT_KEY, "1")
    }

    router.push("/")
  }, [prefersReducedMotion, pathname, router])

  const value = useMemo<CareerChromeContextValue>(
    () => ({
      navHandlers,
      composerBridge,
      registerNavHandlers,
      registerComposerBridge,
      savedShelfMemoriesOldestFirst,
      setSavedShelfMemoriesOldestFirst,
      newestShelfMemoryId,
      setNewestShelfMemoryId,
      shelfExitToHomeActive,
      navigateHomeFromCareer,
      searchComposerBusy,
      setSearchComposerBusy,
    }),
    [
      navHandlers,
      composerBridge,
      registerNavHandlers,
      registerComposerBridge,
      savedShelfMemoriesOldestFirst,
      newestShelfMemoryId,
      shelfExitToHomeActive,
      navigateHomeFromCareer,
      searchComposerBusy,
    ],
  )

  return (
    <CareerChromeContext.Provider value={value}>{children}</CareerChromeContext.Provider>
  )
}

export function useCareerChrome() {
  const ctx = useContext(CareerChromeContext)

  if (!ctx) {
    throw new Error("useCareerChrome must be used within CareerChromeProvider")
  }

  return ctx
}

export function useOptionalCareerChrome() {
  return useContext(CareerChromeContext)
}
