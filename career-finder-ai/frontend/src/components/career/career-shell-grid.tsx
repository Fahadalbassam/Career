"use client"

import type { ReactNode } from "react"

import { useEffect, useMemo, useState } from "react"

import { usePathname } from "next/navigation"

import { ChatShell } from "@/components/chat/chat-shell"

import { CareerFitShelf } from "@/components/chat/fit-shelf"

import { buildAllShelfCardsOldestFirst } from "@/components/chat/fit-shelf-layout"

import { CF_SHELF_SLIDE_FROM_HOME_KEY } from "@/components/home/home-exit-to-chat-context"

import { useCareerChrome } from "@/components/career/career-nav-context"

/**
 * Persistent Chat ↔ Search three-column shell so side shelves don’t remount on navigation
 * (avoids vertical jump / layout snap from asymmetric pages).
 */
export function CareerShellGrid({ children }: Readonly<{ children: ReactNode }>) {
  const pathname = usePathname()

  const {
    savedShelfMemoriesOldestFirst,
    newestShelfMemoryId,
    shelfExitToHomeActive,
    searchComposerBusy,
  } = useCareerChrome()

  const globalSavedOldestFirst = useMemo(
    () => buildAllShelfCardsOldestFirst(savedShelfMemoriesOldestFirst),
    [savedShelfMemoriesOldestFirst],
  )

  const searchShelfLoading = pathname === "/search" && searchComposerBusy

  /** Match chat: only widen to the 3-column shell when there are shelf cards — not for search-only skeleton (that jumped the center vs chat). */
  const showSidePanels = globalSavedOldestFirst.length > 0

  const [shelfSlideFromHome] = useState(() => {
    if (typeof window === "undefined") return false

    return sessionStorage.getItem(CF_SHELF_SLIDE_FROM_HOME_KEY) === "1"
  })

  useEffect(() => {
    if (!shelfSlideFromHome) return

    const id = window.setTimeout(() => {
      sessionStorage.removeItem(CF_SHELF_SLIDE_FROM_HOME_KEY)
    }, 1600)

    return () => window.clearTimeout(id)
  }, [shelfSlideFromHome])

  const leftShelfNodes = (
    <>
      <div className="hidden w-full max-w-[min(100%,18rem)] justify-end lg:flex">
        <CareerFitShelf
          side="left"
          globalSavedOldestFirst={globalSavedOldestFirst}
          newestId={newestShelfMemoryId}
          slideFromHomeIntro={shelfSlideFromHome}
          slideOutToHome={shelfExitToHomeActive}
          searchLoading={searchShelfLoading}
        />
      </div>

      <div className="lg:hidden">
        <CareerFitShelf
          side="left"
          globalSavedOldestFirst={globalSavedOldestFirst}
          newestId={newestShelfMemoryId}
          collapsed
          slideFromHomeIntro={shelfSlideFromHome}
          slideOutToHome={shelfExitToHomeActive}
          searchLoading={searchShelfLoading}
        />
      </div>
    </>
  )

  const rightShelfNodes = (
    <>
      <div className="hidden w-full max-w-[min(100%,18rem)] justify-start lg:flex">
        <CareerFitShelf
          side="right"
          globalSavedOldestFirst={globalSavedOldestFirst}
          newestId={newestShelfMemoryId}
          slideFromHomeIntro={shelfSlideFromHome}
          slideOutToHome={shelfExitToHomeActive}
          searchLoading={searchShelfLoading}
        />
      </div>

      <div className="lg:hidden">
        <CareerFitShelf
          side="right"
          globalSavedOldestFirst={globalSavedOldestFirst}
          newestId={newestShelfMemoryId}
          collapsed
          slideFromHomeIntro={shelfSlideFromHome}
          slideOutToHome={shelfExitToHomeActive}
          searchLoading={searchShelfLoading}
        />
      </div>
    </>
  )

  return (
    <ChatShell
      showSidePanels={showSidePanels}
      leftShelf={leftShelfNodes}
      center={children}
      rightShelf={rightShelfNodes}
      className="min-h-0 w-full min-w-0 flex-1 basis-0"
    />
  )
}
