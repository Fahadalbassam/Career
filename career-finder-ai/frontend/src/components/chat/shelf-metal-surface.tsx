"use client"

import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

/** Shared chrome for shelf tiles — identical treatment for left/right; avoids corner hot-spots. */
export function ShelfMetalSurface({
  side,
  className,
  children,
}: {
  side: "left" | "right"
  className?: string
  children?: ReactNode
}) {
  void side
  const shineGradient =
    "linear-gradient(100deg, transparent 34%, rgba(255,255,255,0.22) 50%, transparent 66%)"

  const staticSheen =
    "linear-gradient(168deg, rgba(255,255,255,0.04) 0%, transparent 38%, transparent 62%, rgba(0,0,0,0.58) 100%)"

  return (
    <div
      className={cn(
        "shelf-card-hit relative isolate overflow-hidden rounded-lg bg-neutral-950",
        "border border-white/[0.07]",
        "shadow-[0_14px_34px_-10px_rgba(0,0,0,0.58),0_6px_14px_-6px_rgba(0,0,0,0.45),inset_0_1px_0_rgba(255,255,255,0.07),inset_0_-1px_0_rgba(0,0,0,0.82)]",
        className
      )}
    >
      <div
        className="pointer-events-none absolute inset-0 rounded-[inherit]"
        style={{ background: staticSheen }}
        aria-hidden
      />
      <div
        className="shelf-moving-shine pointer-events-none absolute -left-[50%] -right-[50%] top-0 bottom-0"
        style={{
          backgroundImage: shineGradient,
          backgroundSize: "220% 100%",
          backgroundRepeat: "no-repeat",
        }}
        aria-hidden
      />
      {children != null ? <div className="relative z-10">{children}</div> : null}
    </div>
  )
}
