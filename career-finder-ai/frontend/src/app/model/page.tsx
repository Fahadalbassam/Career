import type { Metadata } from "next"

import { PlaceholderPage } from "@/components/layout/placeholder-page"

export const metadata: Metadata = {
  title: "Model",
}

export default function ModelPage() {
  return (
    <PlaceholderPage
      title="Model information"
      description="Documentation on the ranking model, features, and evaluation metrics will be summarized here."
    />
  )
}
