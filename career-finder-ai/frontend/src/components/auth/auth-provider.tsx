"use client"

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import {
  loginStub,
  logoutStub,
  signupStub,
  type User,
} from "@/lib/auth"

type AuthContextValue = {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true)
    try {
      const nextUser = await loginStub(email, password)
      setUser(nextUser)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const signup = useCallback(async (email: string, password: string) => {
    setIsLoading(true)
    try {
      const nextUser = await signupStub(email, password)
      setUser(nextUser)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    setIsLoading(true)
    try {
      await logoutStub()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      login,
      signup,
      logout,
    }),
    [user, isLoading, login, signup, logout],
  )

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return ctx
}
