import type { ReactNode } from "react"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import type { StudentProfile } from "@/lib/types"
import { cn } from "@/lib/utils"

function ProfileRow({
  label,
  children,
  compact,
}: {
  label: string
  children: ReactNode
  compact?: boolean
}) {
  return (
    <div
      className={cn(
        "grid gap-1 sm:items-start sm:gap-3",
        compact
          ? "sm:grid-cols-[minmax(0,5.5rem)_1fr]"
          : "gap-1.5 sm:grid-cols-[140px_1fr] sm:gap-4"
      )}
    >
      <span
        className={cn(
          "font-medium uppercase tracking-wide text-muted-foreground",
          compact ? "text-[10px]" : "text-xs"
        )}
      >
        {label}
      </span>
      <span
        className={cn(
          "leading-relaxed text-foreground",
          compact ? "text-xs sm:text-sm" : "text-sm"
        )}
      >
        {children}
      </span>
    </div>
  )
}

export function ParsedProfileCard({
  profile,
  className,
  compact = false,
}: {
  profile: StudentProfile
  className?: string
  compact?: boolean
}) {
  return (
    <Card
      className={cn(
        "shadow-none ring-1 ring-border/80",
        compact && "gap-0 py-0",
        className
      )}
      size={compact ? "sm" : "default"}
    >
      <CardHeader className={cn(compact ? "gap-1 pb-3 pt-4" : "")}>
        <CardTitle className={cn(compact ? "text-sm font-semibold" : "")}>
          {compact ? "Parsed profile" : "Parsed student profile"}
        </CardTitle>
        {compact ? (
          <p className="text-[11px] leading-snug text-muted-foreground">
            Fields inferred for ranking (mock).
          </p>
        ) : (
          <CardDescription>
            Structured fields inferred from your conversation (mock preview).
          </CardDescription>
        )}
      </CardHeader>
      <Separator />
      <CardContent className={cn(compact ? "space-y-3 pb-4 pt-3" : "pt-6")}>
        <div className={cn("space-y-4", compact && "space-y-2.5")}>
          <ProfileRow label="Major" compact={compact}>
            {profile.major}
          </ProfileRow>
          <ProfileRow label="City" compact={compact}>
            {profile.city}
          </ProfileRow>
          <ProfileRow label="Interest" compact={compact}>
            {profile.interest}
          </ProfileRow>
          <ProfileRow label="Work mode" compact={compact}>
            {profile.workMode}
          </ProfileRow>
          <ProfileRow label="Program type" compact={compact}>
            {profile.programType}
          </ProfileRow>
          <ProfileRow label="Skills" compact={compact}>
            <div className="flex flex-wrap gap-1">
              {profile.skills.map((skill) => (
                <Badge
                  key={skill}
                  variant="outline"
                  className={cn("font-normal", compact && "text-[10px]")}
                >
                  {skill}
                </Badge>
              ))}
            </div>
          </ProfileRow>
        </div>
      </CardContent>
    </Card>
  )
}
