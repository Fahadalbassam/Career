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

export default function SignupPage() {
  const router = useRouter()
  const { signup, isLoading } = useAuth()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (password !== confirmPassword) {
      setError("Passwords do not match.")
      return
    }
    try {
      await signup(email, password)
      router.push("/")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign up failed.")
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-lg flex-1 flex-col justify-center px-4 py-12 sm:px-6">
      <Card className="gap-8 py-8 shadow-lg">
        <CardHeader className="border-border/80 border-b px-8 pb-8">
          <CardTitle className="text-xl font-semibold leading-snug">
            Create your account
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Stub auth only — no email verification or backend yet.
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
              <label htmlFor="signup-email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="signup-email"
                type="email"
                autoComplete="email"
                placeholder="m@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <label htmlFor="signup-password" className="text-sm font-medium">
                Password
              </label>
              <Input
                id="signup-password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <div className="grid gap-2">
              <label
                htmlFor="signup-confirm-password"
                className="text-sm font-medium"
              >
                Confirm password
              </label>
              <Input
                id="signup-confirm-password"
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
          </CardContent>
          <CardFooter className="flex-col gap-3 border-border/80 border-t px-8 pt-8">
            <Button
              type="submit"
              className="w-full"
              disabled={
                isLoading ||
                password.length < 8 ||
                password !== confirmPassword
              }
            >
              {isLoading ? "Creating account…" : "Create account"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-medium text-foreground underline-offset-4 hover:underline"
              >
                Log in
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
