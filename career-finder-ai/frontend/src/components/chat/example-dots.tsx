"use client"

import { motion, useReducedMotion } from "framer-motion"

import { useId } from "react"

import { cn } from "@/lib/utils"

export function ExampleDots({
  prompts,
  disabled,
  busy,
  onPickPrompt,
  className,
}: {
  prompts: readonly string[]
  disabled: boolean
  busy?: boolean
  onPickPrompt: (text: string) => void
  className?: string
}) {
  const baseId = useId()

  const reduceMotion = useReducedMotion()

  return (
    <div
      className={cn("flex items-center justify-center gap-4", className)}
      role="group"
      aria-label="Example prompts"
    >
      {prompts.map((prompt, i) => {
        const tid = `${baseId}-tip-${i}`

        return (
          <div
            key={prompt}
            className="group/dot relative flex flex-col items-center pb-3 pt-1"
          >
            <motion.button
              type="button"
              disabled={disabled}
              aria-busy={busy || undefined}
              aria-label={`Send example: ${prompt}`}
              aria-describedby={tid}
              onClick={() => onPickPrompt(prompt)}
              animate={
                busy && !reduceMotion
                  ? { y: [0, -3.2, 0] }
                  : { y: 0 }
              }
              transition={
                busy && !reduceMotion
                  ? {
                      duration: 0.75,
                      ease: [0.4, 0, 0.2, 1],
                      repeat: Number.POSITIVE_INFINITY,
                      delay: i * 0.09,
                    }
                  : { duration: reduceMotion ? 0 : 0.2 }
              }
              className={cn(
                "relative z-10 size-2 shrink-0 rounded-full bg-black outline-none",
                busy && !disabled && !reduceMotion && "shadow-[0_0_0_4px_rgb(255_255_255/0)]",
                "hover:opacity-90 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                "disabled:pointer-events-none disabled:opacity-35",
                "motion-reduce:transition-none",
              )}
            />

            <div
              id={tid}
              role="tooltip"
              className={cn(
                "invisible absolute bottom-full left-1/2 z-20 mb-1 w-[min(18rem,calc(100vw-2rem))] -translate-x-1/2 opacity-0",
                "rounded-2xl border border-neutral-400/55 bg-white px-3 py-2 text-left text-[11px] font-medium leading-snug tracking-tight text-black shadow-[0_10px_28px_-8px_rgba(0,0,0,0.28),0_3px_10px_-4px_rgba(0,0,0,0.18)]",
                "transition-[opacity,visibility] duration-150 ease-out",
                "group-hover/dot:visible group-hover/dot:opacity-100",
                "group-focus-within/dot:visible group-focus-within/dot:opacity-100",
                busy && "hidden",
                "motion-reduce:transition-none",
              )}
            >
              <span className="text-pretty">{prompt}</span>
              <span
                className="pointer-events-none absolute -bottom-1 left-1/2 size-2.5 -translate-x-1/2 rotate-45 border border-neutral-400/55 border-t-0 border-l-0 bg-white shadow-[2px_2px_4px_-2px_rgba(0,0,0,0.15)]"
                aria-hidden
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
