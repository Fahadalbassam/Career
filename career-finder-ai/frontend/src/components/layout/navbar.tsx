"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"

import type { MouseEvent as ReactMouseEvent } from "react"
import { useState } from "react"

import { useOptionalCareerChrome } from "@/components/career/career-nav-context"
import { useHomeExitToChat } from "@/components/home/home-exit-to-chat-context"
import { LoginCardDialog } from "@/components/layout/login-card-dialog"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/", label: "Home" },
  { href: "/chat", label: "Chat" },
  { href: "/search", label: "Search" },
  { href: "/methodology", label: "Methodology" },
] as const

export function Navbar() {
  const pathname = usePathname()

  const router = useRouter()

  const careerChrome = useOptionalCareerChrome()

  const homeExit = useHomeExitToChat()

  const [loginOpen, setLoginOpen] = useState(false)

  async function interceptCareerNavigate(
    href: string,
    e: Pick<ReactMouseEvent<HTMLElement>, "preventDefault">,
  ) {
    if (pathname === "/" && href === "/chat") {
      e.preventDefault()

      await homeExit.navigateToChatFromHome()

      return true
    }

    if (pathname === "/" && href === "/search") {
      e.preventDefault()

      homeExit.navigateToSearchFromHome()

      return true
    }

    if (
      (pathname === "/chat" || pathname === "/search") &&
      href === "/"
    ) {
      e.preventDefault()

      if (careerChrome?.navigateHomeFromCareer) {
        await careerChrome.navigateHomeFromCareer()
      } else {
        router.push("/")
      }

      return true
    }

    const navHandlers = careerChrome?.navHandlers

    if (!navHandlers) return false

    if (pathname === "/chat" && href === "/search") {
      e.preventDefault()

      await navHandlers.goChatToSearch()

      return true
    }

    if (pathname === "/search" && href === "/chat") {
      e.preventDefault()

      await navHandlers.goSearchToChat()

      return true
    }

    return false
  }

  return (
    <>
    <header className="sticky top-0 z-50 isolate border-b border-border/80 bg-background shadow-sm">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4 sm:h-16 sm:px-6">
        <Link
          href="/"
          className="brand-name shrink-0 text-base font-semibold tracking-tight text-foreground transition-colors hover:text-primary sm:text-lg"
          onClick={(e) => {
            void interceptCareerNavigate("/", e)
          }}
        >
          CareerFinder.ai
        </Link>
        <nav
          className="flex min-w-0 flex-1 items-center justify-end gap-1 overflow-x-auto py-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:justify-center sm:gap-2"
          aria-label="Main"
        >
          {navItems.map(({ href, label }) => {
            const active =
              href === "/"
                ? pathname === "/"
                : pathname === href || pathname.startsWith(`${href}/`)

            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "shrink-0 rounded-xl px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                )}
                onClick={(e) => {
                  void interceptCareerNavigate(href, e)
                }}
              >
                {label}
              </Link>
            )
          })}
        </nav>
        <button
          type="button"
          className="brand-name shrink-0 cursor-pointer border-0 bg-transparent text-base font-semibold tracking-tight text-foreground underline-offset-4 transition-colors hover:text-primary focus-visible:underline focus-visible:outline-none sm:text-lg"
          onClick={() => setLoginOpen(true)}
        >
          login
        </button>
      </div>
    </header>
    <LoginCardDialog open={loginOpen} onOpenChange={setLoginOpen} />
    </>
  )
}
