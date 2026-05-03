"use client"

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ChangeEvent,
  type KeyboardEvent,
} from "react"
import { createPortal } from "react-dom"

import { ActiveFinalizedFitCard } from "@/components/chat/active-finalized-fit-card"

import { CareerLoader } from "@/components/chat/career-loader"

import { mockRecommendations } from "@/data/mock-recommendations"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

import { useCareerChrome } from "@/components/career/career-nav-context"

import { Button } from "@/components/ui/button"

import type { CareerFitMemory, Recommendation } from "@/lib/types"

const ASSISTANT_TURN_REPLY =
  "Thanks — I’m using that to narrow Saudi COOP and internship options for you. Ask a follow-up anytime to go deeper or change filters."

/** Minimum mock delay before the assistant message appears (independent of loader CSS). */
const ASSISTANT_LOAD_MIN_MS = 4000

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

function recommendationToMemory(rec: Recommendation): CareerFitMemory {
  const reason =
    rec.whyRecommended.length > 140
      ? `${rec.whyRecommended.slice(0, 137)}…`
      : rec.whyRecommended

  return {
    id: uid(),

    title: rec.programName,

    matchConfidence: rec.scorePercent,

    tags: rec.matchedSkills.slice(0, 3),

    shortReason: reason,

    detailText: rec.whyRecommended,
  }
}

type ChatEntry =
  | { id: string; role: "user"; content: string }
  | { id: string; role: "assistant"; variant: "standard" }
  | {
      id: string

      role: "assistant"

      variant: "finalized"

      recommendation: Recommendation

      status: "open" | "saved" | "refining"
    }

export function CareerChat() {
  const [entries, setEntries] = useState<ChatEntry[]>([])

  const [input, setInput] = useState("")

  const [loading, setLoading] = useState(false)

  const [resumeFileName, setResumeFileName] = useState<string | null>(null)

  /** Body portal root so Clean slate stacks above the route-shell composer (chat column uses z-0). */
  const [cleanSlatePortalReady, setCleanSlatePortalReady] = useState(false)

  const assistantTimeoutRef = useRef<number | null>(null)

  const assistantTurnIdRef = useRef(0)

  const messagesScrollRef = useRef<HTMLDivElement>(null)

  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const resumeInputRef = useRef<HTMLInputElement>(null)

  const {
    registerComposerBridge,
    setSavedShelfMemoriesOldestFirst,
    newestShelfMemoryId,
    setNewestShelfMemoryId,
  } = useCareerChrome()

  const assistantsRemaining = useRef(3)

  const finalizeGateOpen = useRef(false)

  const offerIndexRef = useRef(0)

  const empty = entries.length === 0 && !loading

  const syncMessagesViewport = useCallback(() => {
    const el = messagesScrollRef.current
    if (!el) return

    // Short threads: pin to top so the column reads from under the nav (no hollow gap).
    const fitsInViewport = el.scrollHeight <= el.clientHeight + 16
    el.scrollTop = fitsInViewport ? 0 : el.scrollHeight - el.clientHeight
  }, [])

  useLayoutEffect(() => {
    syncMessagesViewport()
  }, [entries, loading, syncMessagesViewport])

  useEffect(() => {
    if (empty && !loading) {
      textareaRef.current?.focus()
    }
  }, [empty, loading])

  useEffect(() => {
    if (!loading && entries.length > 0) {
      textareaRef.current?.focus()
    }
  }, [loading, entries.length])

  useEffect(() => {
    if (!newestShelfMemoryId) return

    const t = window.setTimeout(() => setNewestShelfMemoryId(null), 700)

    return () => window.clearTimeout(t)
  }, [newestShelfMemoryId, setNewestShelfMemoryId])

  useEffect(() => {
    setCleanSlatePortalReady(true)
  }, [])

  useEffect(() => {
    return () => {
      if (assistantTimeoutRef.current != null) {
        window.clearTimeout(assistantTimeoutRef.current)
        assistantTimeoutRef.current = null
      }
    }
  }, [])

  const runAssistantTurn = useCallback((userText: string) => {
    setEntries((prev) => [
      ...prev,
      { id: uid(), role: "user", content: userText },
    ])

    setLoading(true)

    if (assistantTimeoutRef.current != null) {
      window.clearTimeout(assistantTimeoutRef.current)
    }

    const turnId = ++assistantTurnIdRef.current

    assistantTimeoutRef.current = window.setTimeout(() => {
      assistantTimeoutRef.current = null

      if (turnId !== assistantTurnIdRef.current) return

      setLoading(false)

      if (!finalizeGateOpen.current) {
        assistantsRemaining.current -= 1

        if (assistantsRemaining.current <= 0) {
          finalizeGateOpen.current = true

          assistantsRemaining.current = 999

          const id = uid()

          const rec =
            mockRecommendations[
              offerIndexRef.current % mockRecommendations.length
            ]

          offerIndexRef.current += 1

          setEntries((prev) => [
            ...prev,

            {
              id,

              role: "assistant",

              variant: "finalized",

              recommendation: rec,

              status: "open",
            },
          ])

          return
        }
      }

      setEntries((prev) => [
        ...prev,
        { id: uid(), role: "assistant", variant: "standard" },
      ])
    }, ASSISTANT_LOAD_MIN_MS)
  }, [])

  const send = useCallback(() => {
    const text = input.trim()

    if (!text || loading) return

    setInput("")

    runAssistantTurn(text)
  }, [input, loading, runAssistantTurn])

  const onExamplePromptPick = useCallback(
    (prompt: string) => {
      if (loading) return

      runAssistantTurn(prompt)
    },
    [loading, runAssistantTurn],
  )

  const clearConversation = () => {
    if (assistantTimeoutRef.current != null) {
      window.clearTimeout(assistantTimeoutRef.current)
      assistantTimeoutRef.current = null
    }

    assistantTurnIdRef.current += 1

    setEntries([])

    setLoading(false)

    setInput("")

    setResumeFileName(null)

    if (resumeInputRef.current) resumeInputRef.current.value = ""

    setSavedShelfMemoriesOldestFirst([])

    setNewestShelfMemoryId(null)

    assistantsRemaining.current = 3

    finalizeGateOpen.current = false

    offerIndexRef.current = 0

    textareaRef.current?.focus()
  }

  const onFinalizeFit = useCallback((entryId: string, rec: Recommendation) => {
    finalizeGateOpen.current = false

    assistantsRemaining.current = 3

    const memory = recommendationToMemory(rec)

    setNewestShelfMemoryId(memory.id)

    setSavedShelfMemoriesOldestFirst((prev) => [...prev, memory])

    setEntries((prev) =>
      prev.map((e) =>
        e.id === entryId && e.role === "assistant" && e.variant === "finalized"
          ? { ...e, status: "saved" }
          : e,
      ),
    )
  }, [])

  const onKeepRefining = useCallback((entryId: string) => {
    finalizeGateOpen.current = false

    assistantsRemaining.current = 3

    setEntries((prev) =>
      prev.map((e) =>
        e.id === entryId && e.role === "assistant" && e.variant === "finalized"
          ? { ...e, status: "refining" }
          : e,
      ),
    )
  }, [])

  const onKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()

        send()
      }
    },
    [send],
  )

  const onResumePdfChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]

    e.target.value = ""

    if (!file) return

    const isPdf =
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf")

    if (!isPdf) return

    setResumeFileName(file.name)
  }, [])

  const triggerResumePick = useCallback(() => {
    resumeInputRef.current?.click()
  }, [])

  const clearResumeFile = useCallback(() => {
    setResumeFileName(null)

    if (resumeInputRef.current) resumeInputRef.current.value = ""
  }, [])

  useLayoutEffect(() => {
    registerComposerBridge({
      empty,

      input,

      setInput,

      loading,

      send,

      onKeyDown,

      onPickExamplePrompt: onExamplePromptPick,

      onResumePdfChange,

      resumeFileName,

      clearResume: clearResumeFile,

      triggerResumePick,

      textareaRef,

      resumeInputRef,

      threadFadeTargetRef: messagesScrollRef,
    })

    return () => registerComposerBridge(null)
  }, [
    clearResumeFile,
    empty,

    input,

    loading,

    onExamplePromptPick,

    onKeyDown,

    onResumePdfChange,

    registerComposerBridge,

    resumeFileName,

    send,

    triggerResumePick,
  ])

  const cleanSlateTrigger = (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="text-muted-foreground"
        >
          Clean slate
        </Button>
      </AlertDialogTrigger>

      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Start with a clean slate?</AlertDialogTitle>

          <AlertDialogDescription>
            This clears your messages and resets the mock assistant flow. Demo shelf
            tiles return until you finalize new fits.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel asChild>
            <Button type="button" variant="outline" size="sm">
              Cancel
            </Button>
          </AlertDialogCancel>

          <AlertDialogAction asChild>
            <Button type="button" size="sm" onClick={clearConversation}>
              Yes, clean slate
            </Button>
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )

  const centerColumn = (
    <div className="relative flex min-h-0 w-full min-w-0 flex-1 basis-0 flex-col overflow-hidden pb-48 md:pb-52">
      <div
        ref={messagesScrollRef}
        className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        {empty ? (
          <div
            className="flex min-h-full flex-col items-center px-4 py-12"
            aria-hidden
          >
            <div className="h-[min(520px,calc(100vh-320px))] w-full max-w-2xl md:max-w-3xl" />
          </div>
        ) : (
          <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 pb-20 pt-2 md:max-w-3xl md:pb-24 md:pt-3">
            {entries.map((entry) =>
              entry.role === "user" ? (
                <div key={entry.id} className="flex justify-end">
                  <div className="max-w-[min(100%,28rem)] rounded-3xl bg-primary px-4 py-3 text-sm leading-relaxed text-primary-foreground shadow-sm">
                    {entry.content}
                  </div>
                </div>
              ) : entry.variant === "standard" ? (
                <div key={entry.id} className="flex justify-start">
                  <div className="max-w-[min(100%,28rem)] rounded-3xl bg-muted px-4 py-3 text-sm leading-relaxed text-foreground shadow-sm">
                    {ASSISTANT_TURN_REPLY}
                  </div>
                </div>
              ) : (
                <div key={entry.id} className="flex flex-col gap-3">
                  {entry.status === "open" ? (
                    <ActiveFinalizedFitCard
                      recommendation={entry.recommendation}
                      onFinalize={() =>
                        onFinalizeFit(entry.id, entry.recommendation)
                      }
                      onKeepRefining={() => onKeepRefining(entry.id)}
                    />
                  ) : entry.status === "saved" ? (
                    <div className="flex justify-start">
                      <div className="max-w-[min(100%,28rem)] rounded-3xl bg-muted px-4 py-3 text-sm leading-relaxed text-muted-foreground shadow-sm">
                        Saved{" "}
                        <span className="font-medium text-foreground">
                          {entry.recommendation.programName}
                        </span>{" "}
                        to your shelf as a career-fit memory.
                      </div>
                    </div>
                  ) : (
                    <div className="flex justify-start">
                      <div className="max-w-[min(100%,28rem)] rounded-3xl bg-muted px-4 py-3 text-sm leading-relaxed text-muted-foreground shadow-sm">
                        Continuing to refine your profile — send another message
                        when you&apos;re ready.
                      </div>
                    </div>
                  )}
                </div>
              ),
            )}

            {loading && (
              <div className="flex justify-start">
                <div className="max-w-[min(100%,28rem)] px-4 py-3 text-sm leading-relaxed">
                  <CareerLoader variant="loading" />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {cleanSlatePortalReady &&
        !empty &&
        createPortal(
          <div
            className="pointer-events-none fixed right-2 bottom-[calc(max(calc(env(safe-area-inset-bottom)+16px),16px)+5rem)] z-[70] sm:right-5 md:right-10"
          >
            <div className="pointer-events-auto">{cleanSlateTrigger}</div>
          </div>,
          document.body,
        )}
    </div>
  )

  return centerColumn
}
