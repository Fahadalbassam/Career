"use client"

import { useEffect, useState } from "react"

import { REGEXP_ONLY_DIGITS } from "input-otp"

import {
  Card,
  CardAction,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSeparator,
  InputOTPSlot,
} from "@/components/ui/input-otp"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

type AuthFlow = "login" | "signup"

type SignupStep = "email" | "otp" | "password"

export function LoginCardDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [flow, setFlow] = useState<AuthFlow>("login")
  const [signupStep, setSignupStep] = useState<SignupStep>("email")

  const [loginEmail, setLoginEmail] = useState("")
  const [loginPassword, setLoginPassword] = useState("")

  const [signupEmail, setSignupEmail] = useState("")
  const [otp, setOtp] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  useEffect(() => {
    if (!open) {
      queueMicrotask(() => {
        setFlow("login")
        setSignupStep("email")
        setLoginEmail("")
        setLoginPassword("")
        setSignupEmail("")
        setOtp("")
        setNewPassword("")
        setConfirmPassword("")
      })
    }
  }, [open])

  const goLogin = () => {
    setFlow("login")
    setSignupStep("email")
  }

  const goSignupEmail = () => {
    setFlow("signup")
    setSignupStep("email")
  }

  const headerTitle =
    flow === "login"
      ? "Login to your account"
      : signupStep === "email"
        ? "Create your account"
        : signupStep === "otp"
          ? "Check your email"
          : "Choose a password"

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={cn(
          "max-w-[calc(100%-2rem)] gap-0 border-0 bg-transparent p-0 shadow-none ring-0 sm:max-w-lg",
        )}
        showCloseButton
      >
        <DialogTitle className="sr-only">{headerTitle}</DialogTitle>
        <Card className="gap-8 py-8 shadow-lg">
          <CardHeader className="border-border/80 border-b px-8 pb-8 pr-16">
            <CardTitle className="text-xl font-semibold leading-snug">
              {headerTitle}
            </CardTitle>
            <CardAction>
              {flow === "login" ? (
                <Button
                  type="button"
                  variant="link"
                  className="h-auto px-0 text-foreground hover:text-primary"
                  onClick={goSignupEmail}
                >
                  Sign Up
                </Button>
              ) : (
                <Button
                  type="button"
                  variant="link"
                  className="h-auto px-0 text-foreground hover:text-primary"
                  onClick={goLogin}
                >
                  Log in
                </Button>
              )}
            </CardAction>
          </CardHeader>

          {flow === "login" ? (
            <>
              <CardContent className="grid gap-6 px-8">
                <div className="grid gap-2">
                  <label htmlFor="login-email" className="text-sm font-medium">
                    Email
                  </label>
                  <Input
                    id="login-email"
                    type="email"
                    autoComplete="email"
                    placeholder="m@example.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <label
                      htmlFor="login-password"
                      className="text-sm font-medium"
                    >
                      Password
                    </label>
                    <Button
                      type="button"
                      variant="link"
                      className="h-auto px-0 text-xs text-muted-foreground"
                    >
                      Forgot your password?
                    </Button>
                  </div>
                  <Input
                    id="login-password"
                    type="password"
                    autoComplete="current-password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                  />
                </div>
              </CardContent>
              <CardFooter className="flex-col gap-3 border-border/80 border-t px-8 pt-8">
                <Button
                  type="button"
                  className="w-full"
                  onClick={() => onOpenChange(false)}
                >
                  Login
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="w-full bg-transparent"
                >
                  Login with Google
                </Button>
              </CardFooter>
            </>
          ) : signupStep === "email" ? (
            <>
              <CardContent className="grid gap-6 px-8">
                <div className="grid gap-2">
                  <label htmlFor="signup-email" className="text-sm font-medium">
                    Email
                  </label>
                  <Input
                    id="signup-email"
                    type="email"
                    autoComplete="email"
                    placeholder="m@example.com"
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                  />
                </div>
              </CardContent>
              <CardFooter className="border-border/80 border-t px-8 pt-8">
                <Button
                  type="button"
                  className="w-full"
                  disabled={!signupEmail.trim()}
                  onClick={() => setSignupStep("otp")}
                >
                  Continue
                </Button>
              </CardFooter>
            </>
          ) : signupStep === "otp" ? (
            <>
              <CardContent className="grid gap-6 px-8">
                <p className="text-sm text-muted-foreground">
                  We sent a code to <span className="font-medium text-foreground">{signupEmail}</span>.
                </p>
                <div className="grid gap-3">
                  <span className="text-sm font-medium">One-time code</span>
                  <InputOTP
                    maxLength={6}
                    pattern={REGEXP_ONLY_DIGITS}
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    value={otp}
                    onChange={setOtp}
                    onComplete={() => setSignupStep("password")}
                  >
                    <InputOTPGroup>
                      <InputOTPSlot index={0} />
                      <InputOTPSlot index={1} />
                      <InputOTPSlot index={2} />
                    </InputOTPGroup>
                    <InputOTPSeparator />
                    <InputOTPGroup>
                      <InputOTPSlot index={3} />
                      <InputOTPSlot index={4} />
                      <InputOTPSlot index={5} />
                    </InputOTPGroup>
                  </InputOTP>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  className="h-auto justify-start px-0 text-muted-foreground hover:text-foreground"
                  onClick={() => setSignupStep("email")}
                >
                  ← Use a different email
                </Button>
              </CardContent>
              <CardFooter className="border-border/80 border-t px-8 pt-8">
                <Button
                  type="button"
                  className="w-full"
                  disabled={otp.length !== 6}
                  onClick={() => setSignupStep("password")}
                >
                  Verify
                </Button>
              </CardFooter>
            </>
          ) : signupStep === "password" ? (
            <>
              <CardContent className="grid gap-6 px-8">
                <div className="grid gap-2">
                  <label htmlFor="new-password" className="text-sm font-medium">
                    New password
                  </label>
                  <Input
                    id="new-password"
                    type="password"
                    autoComplete="new-password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <label htmlFor="confirm-password" className="text-sm font-medium">
                    Confirm password
                  </label>
                  <Input
                    id="confirm-password"
                    type="password"
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                </div>
              </CardContent>
              <CardFooter className="border-border/80 border-t px-8 pt-8">
                <Button
                  type="button"
                  className="w-full"
                  disabled={
                    newPassword.length < 8 ||
                    newPassword !== confirmPassword
                  }
                  onClick={() => {
                    onOpenChange(false)
                  }}
                >
                  Create account
                </Button>
              </CardFooter>
            </>
          ) : null}
        </Card>
      </DialogContent>
    </Dialog>
  )
}
