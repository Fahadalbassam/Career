import type { ComponentPropsWithoutRef } from "react"

import { cn } from "@/lib/utils"

export type CareerLoaderProps = Omit<ComponentPropsWithoutRef<"span">, "children"> & {
  /**
   * Hides screen-reader/live-region semantics; use when nested in a labeled button or link.
   */
  decorative?: boolean
  /** `idle`: static black dots. `loading`: animated dots while the assistant replies. */
  variant?: "idle" | "loading"
}

/** CareerFinder.ai 4-dot indicator — black dots; animation only when `variant="loading"`. */
export function CareerLoader({
  className,
  decorative = false,
  variant = "loading",
  role,
  ...rest
}: CareerLoaderProps) {
  const isLoading = variant === "loading"

  return (
    <span
      {...rest}
      role={decorative ? "presentation" : (role ?? (isLoading ? "status" : undefined))}
      aria-live={decorative ? undefined : isLoading ? "polite" : undefined}
      aria-label={decorative ? undefined : isLoading ? "CareerFinder.ai is thinking" : undefined}
      aria-busy={decorative ? undefined : isLoading ? true : undefined}
      className={cn(
        "career-loader-dots shrink-0",
        variant === "idle" ? "career-loader-dots--idle" : "career-loader-dots--loading",
        className
      )}
    >
      {!decorative && isLoading ? <span className="sr-only">Loading</span> : null}
    </span>
  )
}
