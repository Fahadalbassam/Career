import { CareerRouteShell } from "@/components/career/career-route-shell"
import { CareerShellGrid } from "@/components/career/career-shell-grid"

export default function CareerGroupedLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <CareerRouteShell>
      <div className="flex min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden px-4 md:px-6">
        <CareerShellGrid>{children}</CareerShellGrid>
      </div>
    </CareerRouteShell>
  )
}
