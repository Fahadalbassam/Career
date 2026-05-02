"use client"

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react"

import { usePathname, useRouter } from "next/navigation"

import { AnimatePresence, motion, useReducedMotion, type Transition as FMTransition } from "framer-motion"
import { ArrowUp, Pause, Plus } from "lucide-react"

import { ExampleDots } from "@/components/chat/example-dots"
import {
  useCareerChrome,
  type CareerNavHandlers,
} from "@/components/career/career-nav-context"
import { SearchComposer } from "@/components/career/search-composer"
import { CF_COMPOSER_INTRO_FROM_HOME_KEY } from "@/components/home/home-exit-to-chat-context"
import {
  CAREER_SHELL_EXIT_SYNC_DURATION_S,
  CAREER_SHELL_EXIT_SYNC_EASE,
} from "@/components/chat/fit-shelf-exit-timing"
import { BrandWordmark } from "@/components/layout/brand-wordmark"
import { HeroSubtitleSlot } from "@/components/layout/hero-subtitle-slot"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

import {
  CAREER_EMPTY_SUBTITLE,
  CAREER_EXAMPLE_PROMPTS,
} from "@/data/example-prompts"

/** ~navbar height + breathable gap beneath (navbar is `h-14 sm:h-16`) */
const COMPOSER_TOP =
  "clamp(4.25rem,calc(env(safe-area-inset-top) + 3.75rem + 12px),5.125rem)"

const COMPOSER_MAX_W = "min(42rem,calc(100vw - 2rem))"

/** Fixed distance from viewport bottom when composer is docked to the bottom rail */
const COMPOSER_BOTTOM_RAIL =
  "max(calc(env(safe-area-inset-bottom) + 16px), 16px)"

/** Home→Chat: translate down this far (px) so the docked composer starts fully below the fold */
function homeComposerIntroTranslateDownPx(): number {
  if (typeof window === "undefined") return 560

  return Math.round(Math.min(820, window.innerHeight * 0.62))
}

/** Bottom offset for the detached chat footer caption (below composer pill edge) */
const CHAT_KEYBOARD_CAPTION_BOTTOM_CSS =
  "calc(max(calc(env(safe-area-inset-bottom) + 16px), 16px) + 6.25rem)"

const springOpen: FMTransition = {
  type: "spring",
  stiffness: 420,
  damping: 40,
  mass: 0.85,
}

const springSnap: FMTransition = {
  type: "spring",
  stiffness: 520,
  damping: 44,
  mass: 0.82,
}

type DockOverride = "header" | "footer"

export function CareerRouteShell({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname()

  const router = useRouter()

  const prefersReducedMotion = useReducedMotion()

  const [composerSlideFromHome] = useState(() => {
    if (typeof window === "undefined") return false

    return sessionStorage.getItem(CF_COMPOSER_INTRO_FROM_HOME_KEY) === "1"
  })

  const {
    composerBridge: bridge,
    registerNavHandlers,
    shelfExitToHomeActive,
    searchComposerBusy: searchBusy,
    setSearchComposerBusy: setSearchBusy,
  } = useCareerChrome()

  const [exitSlideDistPx, setExitSlideDistPx] = useState(920)

  useLayoutEffect(() => {
    if (typeof window === "undefined") return

    // Viewport-sized exit slide; must run after layout (state update) — refs are forbidden here by `react-hooks/refs` if read during render.
    queueMicrotask(() => {
      setExitSlideDistPx(Math.round(window.innerHeight * 0.92))
    })
  }, [])

  const exitSlideY =
    shelfExitToHomeActive && !prefersReducedMotion ? exitSlideDistPx : 0

  /**
   * Chat→Home: don’t translate the hero/dots band with the shelf exit so the shared
   * `layoutId` wordmark can morph up into the home hero. Search→Home: keep sliding (`exitSlideY`).
   */
  const heroDotsOverlayExitY =
    shelfExitToHomeActive && !prefersReducedMotion && pathname === "/chat"
      ? 0
      : exitSlideY

  const exitShellTransition = prefersReducedMotion
    ? ({ duration: 0 } satisfies FMTransition)
    : ({
        duration: CAREER_SHELL_EXIT_SYNC_DURATION_S,
        ease: CAREER_SHELL_EXIT_SYNC_EASE,
      } satisfies FMTransition)

  useEffect(() => {
    if (!composerSlideFromHome) return

    const id = window.setTimeout(() => {
      sessionStorage.removeItem(CF_COMPOSER_INTRO_FROM_HOME_KEY)
    }, 1200)

    return () => window.clearTimeout(id)
  }, [composerSlideFromHome])

  /** Temporarily biases composer placement during animated cross-route choreography */
  const [dockOverride, setDockOverride] = useState<DockOverride | null>(null)

  const composerPinnedHeader =
    pathname === "/search"
      ? dockOverride !== "footer"
      : dockOverride === "header"

  /** Composer anchored to viewport bottom rail (captions hide when pinning under nav) */
  const composerDockedBottom = !composerPinnedHeader

  const [searchDraft, setSearchDraft] = useState("")

  /** After chat→search dock animation completes, flip to search chrome before pathname updates. */
  const [snapSearchComposer, setSnapSearchComposer] = useState(false)

  /** After search→chat dock animation completes, flip to chat chrome before pathname updates. */
  const [snapChatComposer, setSnapChatComposer] = useState(false)

  const composerRef = useRef<HTMLDivElement>(null)

  const heroClusterRef = useRef<HTMLDivElement>(null)

  /** Synced from context bridge in layout — overlap loop must not close over `bridge` (hook immutability lint). */
  const overlapThreadFadeRefRef =
    useRef<React.MutableRefObject<HTMLElement | null> | null>(null)

  const overlapChatHasMessagesRef = useRef(false)

  useLayoutEffect(() => {
    overlapThreadFadeRefRef.current =
      bridge !== null ? bridge.threadFadeTargetRef : null

    overlapChatHasMessagesRef.current =
      bridge !== null && !bridge.empty
  }, [bridge])

  const animDoneRef = useRef<(() => void) | null>(null)

  /** Guards `waitComposerAnimationFinish` against stray Motion completions */
  const awaitingComposerFinishRef = useRef(false)

  const routerRef = useRef(router)

  useLayoutEffect(() => {
    routerRef.current = router
  }, [router])

  const composerTransition = prefersReducedMotion
    ? ({ duration: 0 } satisfies FMTransition)
    : dockOverride === "footer"
      ? springSnap
      : springOpen

  const composerMotionTransition =
    shelfExitToHomeActive && !prefersReducedMotion
      ? exitShellTransition
      : composerSlideFromHome &&
          composerDockedBottom &&
          !prefersReducedMotion &&
          pathname === "/chat"
        ? ({
            type: "tween",
            duration: 0.52,
            ease: [0.2, 0.75, 0.15, 1],
          } satisfies FMTransition)
        : composerTransition

  const needsHomeComposerIntroY =
    composerSlideFromHome &&
    composerDockedBottom &&
    !prefersReducedMotion &&
    pathname === "/chat"

  /** One translate value for the whole intro; recomputes only when `needsHomeComposerIntroY` flips. */
  const homeComposerIntroY = useMemo(() => {
    if (!needsHomeComposerIntroY) return 0

    return homeComposerIntroTranslateDownPx()
  }, [needsHomeComposerIntroY])
  /**
   * Empty-chat hero (wordmark + subtitle) must mount on the first /chat paint so
   * shared layoutId can pick up from Home without waiting for CareerChat's bridge effect.
   */
  const chatEmptyHeroSurface =
    pathname === "/chat" && (bridge === null || bridge.empty)

  /** Search→chat: keep hero mounted while composer drops (`dockOverride` footer on /search). */
  const heroRevealDuringSearchToChat =
    pathname === "/search" && dockOverride === "footer"

  /** CareerFinder.ai wordmark + subtitle; fades with composer overlap (rise + fall). */
  const showHeroTypography =
    chatEmptyHeroSurface || heroRevealDuringSearchToChat

  const showDotsStack =
    chatEmptyHeroSurface || pathname === "/search"

  const waitComposerAnimationFinish = () =>
    new Promise<void>((resolve) => {
      awaitingComposerFinishRef.current = true

      animDoneRef.current = resolve

      window.setTimeout(() => {
        if (!awaitingComposerFinishRef.current) return

        awaitingComposerFinishRef.current = false

        const resolver = animDoneRef.current

        animDoneRef.current = null

        resolver?.()
      }, 1100)
    })

  const goChatToSearch = useCallback(async () => {
    if (prefersReducedMotion) {
      routerRef.current.push("/search")
      return
    }

    const composerMovement = waitComposerAnimationFinish()

    setDockOverride("header")

    await composerMovement

    setSnapSearchComposer(true)

    routerRef.current.push("/search")
  }, [prefersReducedMotion])

  const goSearchToChat = useCallback(async () => {
    if (prefersReducedMotion) {
      routerRef.current.push("/chat")
      return
    }

    const composerMovement = waitComposerAnimationFinish()

    setDockOverride("footer")

    await composerMovement

    setSnapChatComposer(true)

    routerRef.current.push("/chat")
  }, [prefersReducedMotion])

  const navHandlers = useMemo<CareerNavHandlers>(
    () => ({
      goChatToSearch,
      goSearchToChat,
    }),
    [goChatToSearch, goSearchToChat],
  )

  useLayoutEffect(() => {
    registerNavHandlers(navHandlers)

    return () => registerNavHandlers(undefined)
  }, [navHandlers, registerNavHandlers])

  /**
   * Clear temporary dock overrides only after pathname commits. Doing this in the same tick as
   * `router.push` caused a frame where pathname was still `/chat` but override was cleared,
   * snapping the composer down and flashing hero + chat icons again.
   */
  useLayoutEffect(() => {
    queueMicrotask(() => {
      if (pathname === "/search") {
        setDockOverride((d) => (d === "header" ? null : d))

        setSnapSearchComposer(false)
      }

      if (pathname === "/chat") {
        setDockOverride((d) => (d === "footer" ? null : d))

        setSnapChatComposer(false)
      }
    })
  }, [pathname])

  /** Reset micro-state when leaving grouped routes — defer to satisfy hook lint rules */
  useEffect(() => {
    if (pathname === "/chat" || pathname === "/search") return

    queueMicrotask(() => {
      setDockOverride(null)

      setSnapSearchComposer(false)

      setSnapChatComposer(false)
    })
  }, [pathname])

  /**
   * Overlap-driven fade for composer vs hero / thread:
   * - Rise (chat→search, composer to header): hide as the bar moves up into the cluster.
   * - Fall (search→chat, composer to footer): reveal as the bar drops past the cluster.
   */
  useEffect(() => {
    const heroElStatic = heroClusterRef.current

    const clearStyles = () => {
      const h = heroClusterRef.current

      const t = overlapThreadFadeRefRef.current?.current ?? null

      if (h) h.style.opacity = ""

      if (t) t.style.opacity = ""
    }

    if (prefersReducedMotion) {
      clearStyles()

      return
    }

    const riseActive =
      pathname === "/chat" && composerPinnedHeader

    const fallActive =
      dockOverride === "footer" &&
      (pathname === "/search" ||
        (pathname === "/chat" && composerDockedBottom))

    if (!riseActive && !fallActive) {
      clearStyles()

      return
    }

    let raf = 0

    const tick = () => {
      const rA = pathname === "/chat" && composerPinnedHeader

      const fA =
        dockOverride === "footer" &&
        (pathname === "/search" ||
          (pathname === "/chat" && !composerPinnedHeader))

      if (!rA && !fA) {
        clearStyles()

        return
      }

      const mode = rA ? "rise" : "fall"

      const fadeHero = !!showHeroTypography

      const threadEl = overlapThreadFadeRefRef.current?.current ?? null

      const fadeThread =
        pathname === "/chat" &&
        overlapChatHasMessagesRef.current &&
        !!threadEl

      if (!fadeHero && !fadeThread) {
        const h = heroClusterRef.current

        if (h) h.style.opacity = ""

        if (threadEl) threadEl.style.opacity = ""

        return
      }

      const compEl = composerRef.current

      if (!compEl) {
        raf = window.requestAnimationFrame(tick)

        return
      }

      const composerTopPx = compEl.getBoundingClientRect().top

      if (fadeHero) {
        const heroEl = heroClusterRef.current

        if (!heroEl) {
          raf = window.requestAnimationFrame(tick)

          return
        }

        if (threadEl) threadEl.style.opacity = ""

        const heroBottom = heroEl.getBoundingClientRect().bottom

        if (mode === "rise") {
          heroEl.style.opacity =
            heroBottom <= composerTopPx + 22 ? "0" : "1"

          const overlapping =
            composerTopPx < heroBottom && heroBottom > composerTopPx - 260

          if (overlapping) raf = window.requestAnimationFrame(tick)
        } else {
          heroEl.style.opacity = composerTopPx > heroBottom + 22 ? "1" : "0"

          const overlapping = composerTopPx < heroBottom + 260

          if (overlapping) raf = window.requestAnimationFrame(tick)
        }

        return
      }

      const heroReset = heroClusterRef.current

      if (heroReset) heroReset.style.opacity = ""

      const heroBottomThread = threadEl!.getBoundingClientRect().bottom

      if (mode === "rise") {
        threadEl!.style.opacity =
          heroBottomThread <= composerTopPx + 22 ? "0" : "1"

        const overlappingThread =
          composerTopPx < heroBottomThread &&
          heroBottomThread > composerTopPx - 260

        if (overlappingThread) raf = window.requestAnimationFrame(tick)
      } else {
        threadEl!.style.opacity =
          composerTopPx > heroBottomThread + 22 ? "1" : "0"

        const overlappingThread = composerTopPx < heroBottomThread + 260

        if (overlappingThread) raf = window.requestAnimationFrame(tick)
      }
    }

    tick()

    return () => {
      if (raf !== 0) window.cancelAnimationFrame(raf)

      if (heroElStatic) heroElStatic.style.opacity = ""

      const tEnd = overlapThreadFadeRefRef.current?.current ?? null

      if (tEnd) tEnd.style.opacity = ""
    }
  }, [
    composerDockedBottom,
    composerPinnedHeader,
    dockOverride,
    pathname,
    prefersReducedMotion,
    showHeroTypography,
  ])

  const onDotsPickPrompt = useCallback(
    (text: string) => {
      if (pathname === "/chat") {
        bridge?.onPickExamplePrompt(text)

        return
      }

      if (pathname === "/search") {
        setSearchDraft(text)

        if (!searchBusy) {
          setSearchBusy(true)

          window.setTimeout(() => setSearchBusy(false), 1100)
        }
      }
    },
    [pathname, bridge, searchBusy, setSearchBusy],
  )

  const resumeGhostRef = useRef<HTMLInputElement>(null)

  const footerHintChat =
    bridge?.resumeFileName != null ? (
      <p className="mt-2 text-center text-[11px] text-muted-foreground">
        Resume:{" "}
        <span className="font-medium text-foreground">{bridge.resumeFileName}</span>
        <button
          type="button"
          className="ms-2 rounded-sm text-primary underline-offset-2 hover:underline"
          onClick={() => bridge.clearResume()}
        >
          Remove
        </button>
      </p>
    ) : null

  const footerHint = pathname === "/chat" ? footerHintChat : null

  const dotsEnterTx = prefersReducedMotion
    ? { duration: 0 }
    : { duration: 0.24, ease: [0.4, 0, 0.2, 1] as const }

  const chatCaptionMotionTx = prefersReducedMotion
    ? { duration: 0 }
    : { duration: 0.2, ease: [0.4, 0, 0.2, 1] as const }

  const captionMotionTransition =
    prefersReducedMotion
      ? ({ duration: 0 } satisfies FMTransition)
      : shelfExitToHomeActive
        ? exitShellTransition
        : (chatCaptionMotionTx satisfies FMTransition)

  /** Stable shell: morph swaps controls inside without scaling the whole row (avoids ghost/double pill). */
  const composerRowClass =
    "flex w-full min-h-12 items-end gap-2 [contain:layout]"

  function renderMorphingComposerRow() {
    const showSearchComposer =
      snapSearchComposer ||
      (pathname === "/search" && !snapChatComposer)

    if (showSearchComposer) {
      return (
        <div className={composerRowClass}>
          <input
            ref={resumeGhostRef}
            type="file"
            accept="application/pdf,.pdf"
            className="pointer-events-none sr-only"
            tabIndex={-1}
            aria-hidden
            disabled
          />

          <SearchComposer
            query={searchDraft}
            onQueryChange={setSearchDraft}
            pathname={pathname}
          />
        </div>
      )
    }

    if (bridge) {
      return (
        <div className={composerRowClass}>
          <input
            ref={bridge.resumeInputRef}
            type="file"
            accept="application/pdf,.pdf"
            className="sr-only"
            tabIndex={-1}
            onChange={(e) => bridge.onResumePdfChange(e)}
            aria-hidden
          />

          <Button
            type="button"
            variant="outline"
            size="icon"
            className="size-10 shrink-0 rounded-full border-border/70 bg-background/90 shadow-sm"
            disabled={bridge.loading}
            onClick={() => bridge.triggerResumePick()}
            aria-label="Attach resume PDF"
          >
            <Plus className="size-5" strokeWidth={2} aria-hidden />
          </Button>

          <Textarea
            ref={bridge.textareaRef}
            value={bridge.input}
            onChange={(e) => bridge.setInput(e.target.value)}
            onKeyDown={bridge.onKeyDown}
            placeholder="Ask CareerFinder.ai…"
            rows={2}
            className="max-h-[min(200px,40vh)] min-h-[44px] flex-1 resize-none border-0 bg-transparent px-1 py-2.5 shadow-none focus-visible:ring-0 md:text-sm"
          />

          <Button
            type="button"
            size="icon"
            className="size-10 shrink-0 rounded-full"
            onClick={() => bridge.send()}
            disabled={bridge.loading || !bridge.input.trim()}
            aria-label={
              bridge.loading
                ? "Assistant is replying — sending is paused"
                : "Send message"
            }
          >
            {bridge.loading ? (
              <Pause className="size-5" strokeWidth={2} aria-hidden />
            ) : (
              <ArrowUp className="size-5" strokeWidth={2} aria-hidden />
            )}
          </Button>
        </div>
      )
    }

    return (
      <div className={composerRowClass}>
        <input
          ref={resumeGhostRef}
          type="file"
          className="pointer-events-none sr-only"
          tabIndex={-1}
          disabled
        />

        <Button
          type="button"
          variant="outline"
          size="icon"
          className="size-10 shrink-0 rounded-full border-border/70 bg-background/90 opacity-50 shadow-sm"
          disabled
          aria-label="Attach resume PDF"
        >
          <Plus className="size-5" strokeWidth={2} aria-hidden />
        </Button>

        <Textarea
          rows={2}
          readOnly
          disabled
          placeholder="Ask CareerFinder.ai…"
          className="max-h-[min(200px,40vh)] min-h-[44px] flex-1 resize-none border-0 bg-transparent px-1 py-2.5 text-sm opacity-60 shadow-none focus-visible:ring-0 md:text-sm"
        />

        <Button
          type="button"
          size="icon"
          className="size-10 shrink-0 rounded-full"
          disabled
          aria-label="Send message"
        >
          <ArrowUp className="size-5" strokeWidth={2} aria-hidden />
        </Button>
      </div>
    )
  }

  return (
    <div className="relative flex min-h-0 w-full min-w-0 flex-1 basis-0 flex-col overflow-hidden">
      <motion.div
        className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden"
        animate={{ y: exitSlideY }}
        transition={exitShellTransition}
      >
        {children}
      </motion.div>

      {(showDotsStack || showHeroTypography) && (
        <motion.div
          className="pointer-events-none fixed inset-x-0 top-14 z-[40] flex flex-col items-center justify-center px-5 sm:top-16"
          style={{
            bottom:
              "max(calc(env(safe-area-inset-bottom) + 13.75rem), 13.75rem)",
          }}
          aria-hidden={!showDotsStack}
          animate={{ y: heroDotsOverlayExitY }}
          transition={exitShellTransition}
        >
          <div className="relative flex w-full max-w-2xl flex-col items-center gap-10 md:max-w-3xl">
            {showHeroTypography && (
              <div
                ref={heroClusterRef}
                data-career-shell-hero
                className="pointer-events-none max-w-lg space-y-3 text-center"
              >
                <BrandWordmark
                  size="shell"
                  enableSharedLayout={chatEmptyHeroSurface}
                />

                <HeroSubtitleSlot variant="shell">
                  <p className="text-pretty text-sm text-muted-foreground md:text-base">
                    {CAREER_EMPTY_SUBTITLE}
                  </p>
                </HeroSubtitleSlot>
              </div>
            )}

            {showDotsStack &&
            !showHeroTypography &&
            pathname === "/search" ? (
              <div
                className="pointer-events-none max-w-lg select-none space-y-3 text-center invisible"
                aria-hidden
              >
                <p className="brand-name inline-block max-w-[100vw] text-3xl font-semibold leading-none tracking-tight text-foreground md:text-4xl">
                  CareerFinder.ai
                </p>
                <div className="min-h-[2.875rem] md:min-h-[3.125rem]" />
              </div>
            ) : null}

            {showDotsStack && (
              <motion.div
                className="pointer-events-auto"
                initial={false}
                animate={{ opacity: 1, y: 0 }}
                transition={dotsEnterTx}
              >
                <ExampleDots
                  disabled={
                    (pathname === "/chat" && !!bridge?.loading) ||
                    (pathname === "/search" && searchBusy)
                  }
                  prompts={CAREER_EXAMPLE_PROMPTS}
                  busy={pathname === "/search" && searchBusy}
                  onPickPrompt={onDotsPickPrompt}
                />
              </motion.div>
            )}
          </div>
        </motion.div>
      )}

      <motion.div
        ref={composerRef}
        layout={false}
        className="fixed z-[56] px-5"
        initial={
          composerSlideFromHome &&
          composerDockedBottom &&
          !prefersReducedMotion &&
          pathname === "/chat"
            ? {
                bottom: COMPOSER_BOTTOM_RAIL,
                top: "auto",
                x: "-50%",
                y: homeComposerIntroY,
              }
            : false
        }
        transition={composerMotionTransition}
        style={{
          left: "50%",
          width: COMPOSER_MAX_W,
          transformOrigin: "bottom center",
          willChange: "transform, bottom, top",
        }}
        animate={
          composerPinnedHeader
            ? {
                top: COMPOSER_TOP,
                bottom: "auto",
                x: "-50%",
                y: exitSlideY,
              }
            : {
                bottom: COMPOSER_BOTTOM_RAIL,
                top: "auto",
                x: "-50%",
                y: exitSlideY,
              }
        }
        onAnimationComplete={() => {
          if (!awaitingComposerFinishRef.current) return

          awaitingComposerFinishRef.current = false

          const resolver = animDoneRef.current

          animDoneRef.current = null

          resolver?.()
        }}
      >
        <div className="bg-background/95 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2 backdrop-blur-sm">
          <div className="mx-auto w-full">
            <div className="overflow-hidden rounded-[1.75rem] border border-border/80 bg-muted/35 p-2 shadow-lg">
              {renderMorphingComposerRow()}
            </div>

            {footerHint}
          </div>
        </div>
      </motion.div>

      <AnimatePresence mode="sync">
        {pathname === "/chat" && composerDockedBottom ? (
          <motion.div
            key="chat-keyboard-caption"
            className="pointer-events-none fixed left-1/2 z-[54] w-[min(42rem,calc(100vw-2rem))] max-w-none -translate-x-1/2 px-5"
            style={{ bottom: CHAT_KEYBOARD_CAPTION_BOTTOM_CSS }}
            initial={
              prefersReducedMotion ? false : { opacity: 0, y: 28 }
            }
            animate={{ opacity: 1, y: exitSlideY }}
            exit={
              prefersReducedMotion ? undefined : { opacity: 0, y: 56 }
            }
            transition={captionMotionTransition}
          >
            <p className="text-center text-[11px] text-muted-foreground">
              Enter to send, Shift+Enter for a new line.
            </p>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  )
}
