"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState, type FormEvent } from "react"

import { useAuth } from "@/components/auth/auth-provider"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoading } = useAuth()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await login(email, password)
      router.push("/")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.")
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-lg flex-1 flex-col justify-center px-4 py-12 sm:px-6">
      <Card className="gap-8 py-8 shadow-lg">
        <CardHeader className="border-border/80 border-b px-8 pb-8">
          <CardTitle className="text-xl font-semibold leading-snug">
            Login to your account
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Stub auth only — any email and password will sign you in for this
            milestone.
          </p>
        </CardHeader>
        <form onSubmit={(e) => void onSubmit(e)}>
          <CardContent className="grid gap-6 px-8">
            {error ? (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            ) : null}
            <div className="grid gap-2">
              <label htmlFor="login-email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="login-email"
                type="email"
                autoComplete="email"
                placeholder="m@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <label htmlFor="login-password" className="text-sm font-medium">
                Password
              </label>
              <Input
                id="login-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </CardContent>
          <CardFooter className="flex-col gap-3 border-border/80 border-t px-8 pt-8">
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Signing in…" : "Login"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              No account?{" "}
              <Link
                href="/signup"
                className="font-medium text-foreground underline-offset-4 hover:underline"
              >
                Sign up
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
