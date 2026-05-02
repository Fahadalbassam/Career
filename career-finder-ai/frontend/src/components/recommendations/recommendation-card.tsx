import type { ReactNode } from "react"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import type { Recommendation } from "@/lib/types"
import { cn } from "@/lib/utils"

import { ScoreBadge } from "./score-badge"
import { SourceButton } from "./source-button"

function fitBadgeVariant(fitLevel: string): "default" | "secondary" | "outline" {
  const n = fitLevel.toLowerCase()
  if (n.includes("strong")) return "default"
  if (n.includes("good")) return "secondary"
  return "outline"
}

function MetaRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid gap-1 sm:grid-cols-[minmax(0,7.5rem)_1fr] sm:gap-3">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <span className="text-sm text-foreground">{children}</span>
    </div>
  )
}

export function RecommendationCard({
  recommendation,
  className,
}: {
  recommendation: Recommendation
  className?: string
}) {
  const {
    rank,
    companyName,
    programName,
    city,
    programType,
    workMode,
    fitLevel,
    scorePercent,
    matchedSkills,
    whyRecommended,
    sourceUrl,
    sourceLabel,
  } = recommendation

  return (
    <Card className={cn("overflow-hidden shadow-none ring-1 ring-border/80", className)}>
      <CardHeader className="gap-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex min-w-0 gap-3">
            <span
              className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-muted text-base font-semibold tabular-nums text-foreground"
              aria-label={`Rank ${rank}`}
            >
              {rank}
            </span>
            <div className="min-w-0 space-y-2">
              <CardTitle className="text-pretty text-lg leading-snug sm:text-xl">
                {companyName}
              </CardTitle>
              <p className="text-sm font-medium leading-snug text-foreground sm:text-base">
                {programName}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 lg:flex-col lg:items-stretch lg:gap-2">
            <ScoreBadge scorePercent={scorePercent} className="justify-center" />
            <Badge
              variant={fitBadgeVariant(fitLevel)}
              className="justify-center font-medium"
            >
              {fitLevel}
            </Badge>
          </div>
        </div>
        <div className="grid gap-3 rounded-xl bg-muted/40 p-3 sm:grid-cols-3 sm:p-4">
          <MetaRow label="City">{city}</MetaRow>
          <MetaRow label="Program type">{programType}</MetaRow>
          <MetaRow label="Work mode">{workMode}</MetaRow>
        </div>
      </CardHeader>
      <Separator />
      <CardContent className="space-y-5 pt-6">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Matched skills
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {matchedSkills.map((skill) => (
              <Badge key={skill} variant="secondary" className="font-normal">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Why recommended
          </p>
          <p className="mt-2 text-sm leading-relaxed text-pretty text-muted-foreground">
            {whyRecommended}
          </p>
        </div>
      </CardContent>
      <CardFooter className="border-t border-border/80 bg-muted/20">
        <SourceButton href={sourceUrl} label={sourceLabel ?? "View posting"} />
      </CardFooter>
    </Card>
  )
}
