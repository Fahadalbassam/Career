import { ExternalLink } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function SourceButton({
  href,
  label = "View source",
  className,
}: {
  href: string
  label?: string
  className?: string
}) {
  return (
    <Button
      asChild
      variant="outline"
      size="sm"
      className={cn("w-full gap-2 sm:w-auto", className)}
    >
      <a href={href} target="_blank" rel="noopener noreferrer">
        <ExternalLink className="size-4 shrink-0" aria-hidden />
        {label}
      </a>
    </Button>
  )
}
