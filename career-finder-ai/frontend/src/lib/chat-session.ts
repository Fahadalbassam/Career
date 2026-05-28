import type { StudentProfile } from "@/lib/types"

export const STORAGE_KEY = "careerfinder.ai.anonymousChatSession.v1"

export interface AnonymousChatSession {
  userMessages: string[]
  /** Accumulated merged profile from all turns. */
  profile: StudentProfile | null
  updatedAt: string
}

export function loadAnonymousChatSession(): AnonymousChatSession | null {
  if (typeof window === "undefined") return null
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as AnonymousChatSession
    if (!Array.isArray(parsed.userMessages)) return null
    return parsed
  } catch {
    return null
  }
}

export function saveAnonymousChatSession(session: AnonymousChatSession): void {
  if (typeof window === "undefined") return
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  } catch {
    // Storage quota exceeded or unavailable — silently ignore
  }
}

export function clearAnonymousChatSession(): void {
  if (typeof window === "undefined") return
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Silently ignore
  }
}
