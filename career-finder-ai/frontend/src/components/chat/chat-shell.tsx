"use client"

import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

export function ChatShell({
  leftShelf,
  center,
  rightShelf,
  className,
  showSidePanels = true,
}: {
  leftShelf: ReactNode
  center: ReactNode
  rightShelf: ReactNode
  className?: string
  /** When false, shelf rails are omitted so the chat column uses full width (no empty shelves). */
  showSidePanels?: boolean
}) {
  if (!showSidePanels) {
    return (
      <div
        className={cn(
          "flex min-h-0 w-full min-w-0 flex-1 basis-0 flex-col overflow-hidden",
          className,
        )}
      >
        <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          {center}
        </section>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "flex min-h-0 w-full min-w-0 flex-1 basis-0 flex-col gap-4 overflow-hidden lg:overflow-y-hidden lg:overflow-x-clip",
        "lg:grid lg:grid-cols-[minmax(0,18rem)_minmax(28rem,1fr)_minmax(0,18rem)] lg:items-stretch lg:gap-8 xl:grid-cols-[minmax(0,18rem)_minmax(28rem,1fr)_minmax(0,18rem)]",
        className,
      )}
    >
      {/* Mobile / tablet: shelves as horizontal strips */}
      <aside className="order-1 shrink-0 overflow-x-clip overflow-y-visible pb-2 pt-2 lg:hidden">
        {leftShelf}
      </aside>

      <section className="order-2 flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden lg:relative lg:z-0 lg:order-2 lg:col-start-2">
        {center}
      </section>

      {/* Left shelf: clip X so widened shelf track never opens a horizontal scrollbar. */}
      <aside className="order-2 hidden min-h-0 min-w-0 flex-col overflow-x-clip lg:relative lg:z-20 lg:order-1 lg:col-start-1 lg:flex lg:justify-end">
        <div
          className={cn(
            "flex min-h-0 w-full max-w-full flex-1 justify-end overflow-x-clip overflow-y-auto overscroll-contain [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden lg:max-h-full lg:pl-5 lg:pr-7 lg:pt-10 lg:pb-12",
            "lg:-mr-16 lg:w-[calc(100%+4rem)] lg:max-w-none lg:pointer-events-none",
          )}
        >
          <div className="ml-auto flex w-max min-w-0 max-w-full justify-end lg:pointer-events-auto lg:pr-[5.75rem]">
            {leftShelf}
          </div>
        </div>
      </aside>

      {/* Right shelf: same — never overflow-x visible on the scrollport (avoids horizontal bar at bottom). */}
      <aside className="order-3 flex min-h-0 min-w-0 shrink-0 flex-col overflow-x-clip overflow-y-visible py-2 lg:relative lg:z-20 lg:order-3 lg:col-start-3 lg:flex lg:h-auto lg:w-auto lg:max-h-full lg:justify-start lg:overflow-x-clip lg:overflow-y-visible lg:py-0">
        <div
          className={cn(
            "flex w-full max-w-full justify-start",
            "lg:min-h-0 lg:flex-1 lg:-ml-16 lg:w-[calc(100%+4rem)] lg:max-w-none",
            "lg:overflow-x-clip lg:overflow-y-auto lg:overscroll-contain lg:pr-5 lg:pb-12 lg:pt-10",
            "[-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
            "lg:pointer-events-none",
          )}
        >
          <div className="flex w-max min-w-0 max-w-full justify-start lg:pointer-events-auto lg:pl-[5.75rem]">
            {rightShelf}
          </div>
        </div>
      </aside>
    </div>
  )
}
