import type { RecommendApiResponse } from "@/lib/api-types"

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000"

export async function recommendFromMessage(
  message: string,
): Promise<RecommendApiResponse> {
  const response = await fetch(`${API_BASE}/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  })

  if (!response.ok) {
    const detail = await response.text().catch(() => "")
    throw new Error(
      `POST /recommend failed (${response.status}${detail ? `: ${detail}` : ""})`,
    )
  }

  return response.json() as Promise<RecommendApiResponse>
}
