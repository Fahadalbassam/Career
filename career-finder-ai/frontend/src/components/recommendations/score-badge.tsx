import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

function badgeTone(scorePercent: number): "default" | "secondary" | "outline" {
  const s = Math.min(100, Math.max(0, scorePercent))
  if (s >= 85) return "default"
  if (s >= 72) return "secondary"
  return "outline"
}

export function ScoreBadge({
  scorePercent,
  className,
}: {
  scorePercent: number
  className?: string
}) {
  const clamped = Math.min(100, Math.max(0, scorePercent))
  const rounded = Math.round(clamped)

  return (
    <Badge
      variant={badgeTone(clamped)}
      className={cn(
        "tabular-nums text-xs font-semibold sm:text-sm",
        className
      )}
      title={`Match score ${rounded}%`}
    >
      {rounded}% match
    </Badge>
  )
}
