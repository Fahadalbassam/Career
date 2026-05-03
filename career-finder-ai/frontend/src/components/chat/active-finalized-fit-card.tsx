"use client"

import type { Recommendation } from "@/lib/types"

import { Button } from "@/components/ui/button"

export function ActiveFinalizedFitCard({
  recommendation,
  onFinalize,
  onKeepRefining,
}: {
  recommendation: Recommendation
  onFinalize: () => void
  onKeepRefining: () => void
}) {
  const rounded = Math.round(
    Math.min(100, Math.max(0, recommendation.scorePercent))
  )
  const tags = recommendation.matchedSkills.slice(0, 4).join(" · ")

  return (
    <div className="flex justify-start">
      <div className="max-w-[min(100%,28rem)] space-y-3 rounded-3xl border border-primary/20 bg-muted px-4 py-3 text-sm leading-relaxed text-foreground shadow-sm ring-1 ring-primary/10">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wide text-primary">
            Finalized fit
          </p>
          <p className="mt-1 text-pretty font-semibold text-foreground">
            {recommendation.programName}
          </p>
          <p className="text-pretty text-muted-foreground">
            {recommendation.companyName}
          </p>
          <p className="mt-2 text-xs tabular-nums text-muted-foreground">
            {rounded}% match
            {tags ? ` · ${tags}` : null}
          </p>
        </div>
        <p className="text-pretty text-sm text-muted-foreground">
          {recommendation.whyRecommended}
        </p>
        <div className="flex flex-wrap gap-2 pt-0.5">
          <Button type="button" size="sm" onClick={onFinalize}>
            Finalize fit
          </Button>
          <Button type="button" size="sm" variant="outline" onClick={onKeepRefining}>
            Keep refining
          </Button>
        </div>
      </div>
    </div>
  )
}
