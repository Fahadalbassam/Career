import { CareerRouteShell } from "@/components/career/career-route-shell"
import { CareerShellGrid } from "@/components/career/career-shell-grid"

export default function CareerGroupedLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <CareerRouteShell>
      <div className="flex min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden px-4 pt-4 pb-10 md:px-6 md:pt-5 md:pb-12">
        <CareerShellGrid>{children}</CareerShellGrid>
      </div>
    </CareerRouteShell>
  )
}
