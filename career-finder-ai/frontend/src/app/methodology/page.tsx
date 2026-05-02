import type { Metadata } from "next"

import { PlaceholderPage } from "@/components/layout/placeholder-page"

export const metadata: Metadata = {
  title: "Methodology",
}

export default function MethodologyPage() {
  return (
    <PlaceholderPage
      title="Methodology"
      description="Data sources, cleaning rules, fairness considerations, and explainability approach will be outlined here."
    />
  )
}
