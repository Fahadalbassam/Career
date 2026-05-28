/**
 * Auth client — stub implementations only (Auth-1).
 *
 * Later (Auth-2+): call FastAPI /auth/login, /auth/signup, /auth/logout, /auth/me
 * with credentials: "include". Never store tokens in localStorage.
 */

export type UserRole = "student" | "admin"

export interface User {
  id: string
  email: string
  displayName?: string
  role: UserRole
}

export interface AuthState {
  user: User | null
  isLoading: boolean
}

/** Simulated network delay for stub flows. */
const STUB_DELAY_MS = 400

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function emailLocalPart(email: string): string {
  const at = email.indexOf("@")
  if (at <= 0) return "Student"
  const local = email.slice(0, at).trim()
  if (!local) return "Student"
  return local.charAt(0).toUpperCase() + local.slice(1)
}

/** Returns null — no persisted auth in Auth-1. */
export function getMockAuthUser(): User | null {
  return null
}

function buildStubUser(email: string): User {
  const trimmed = email.trim().toLowerCase()
  return {
    id: `stub-${trimmed.replace(/[^a-z0-9]+/g, "-")}`,
    email: trimmed,
    displayName: emailLocalPart(trimmed),
    role: "student",
  }
}

export async function loginStub(
  email: string,
  password: string,
): Promise<User> {
  await delay(STUB_DELAY_MS)
  if (!email.trim()) {
    throw new Error("Email is required.")
  }
  if (!password) {
    throw new Error("Password is required.")
  }
  return buildStubUser(email)
}

export async function signupStub(
  email: string,
  password: string,
): Promise<User> {
  await delay(STUB_DELAY_MS)
  if (!email.trim()) {
    throw new Error("Email is required.")
  }
  if (password.length < 8) {
    throw new Error("Password must be at least 8 characters.")
  }
  return buildStubUser(email)
}

export async function logoutStub(): Promise<void> {
  await delay(STUB_DELAY_MS)
}
