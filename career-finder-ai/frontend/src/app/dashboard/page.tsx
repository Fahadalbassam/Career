import type { Metadata } from "next"

import { PlaceholderPage } from "@/components/layout/placeholder-page"

export const metadata: Metadata = {
  title: "Dashboard",
}

export default function DashboardPage() {
  return (
    <PlaceholderPage
      title="Dashboard"
      description="Saved roles, application progress, and recommendation history will live here."
    />
  )
}
