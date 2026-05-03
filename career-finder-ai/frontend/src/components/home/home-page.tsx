"use client"

import Link from "next/link"
import { BadgeCheck, GraduationCap, Sparkles } from "lucide-react"
import {
  motion,
  useAnimationControls,
  useReducedMotion,
} from "framer-motion"
import { useLayoutEffect, useEffect, useState, type MouseEvent } from "react"

import { BrandWordmark } from "@/components/layout/brand-wordmark"
import { HeroSubtitleSlot } from "@/components/layout/hero-subtitle-slot"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import {
  CF_HOME_INTRO_FROM_CHAT_KEY,
  useHomeExitToChat,
} from "@/components/home/home-exit-to-chat-context"

const features = [
  {
    title: "Verified Saudi Opportunities",
    description:
      "Focus on curated COOP and internship listings aligned with the Saudi ecosystem so you spend time on real openings.",
    icon: BadgeCheck,
  },
  {
    title: "Major-Fit Recommendation",
    description:
      "Signals from your computing major and interests drive ranking — not generic job-board noise.",
    icon: GraduationCap,
  },
  {
    title: "Explainable AI Results",
    description:
      "See why roles surfaced for you with transparent scoring cues you can trust and iterate on.",
    icon: Sparkles,
  },
] as const

export function HomePage() {
  const {
    registerHomeExitRunner,
    navigateToChatFromHome,
    beginChatNavigationFromHome,
    navigateToSearchFromHome,
  } = useHomeExitToChat()

  const prefersReducedMotion = useReducedMotion()

  const [introFromCareer] = useState(() => {
    if (typeof window === "undefined") return false

    return sessionStorage.getItem(CF_HOME_INTRO_FROM_CHAT_KEY) === "1"
  })

  const sepCtrl = useAnimationControls()

  const cardsCtrl = useAnimationControls()

  const heroExtrasCtrl = useAnimationControls()

  useEffect(() => {
    if (!introFromCareer) return

    const id = window.setTimeout(() => {
      sessionStorage.removeItem(CF_HOME_INTRO_FROM_CHAT_KEY)
    }, 2000)

    return () => window.clearTimeout(id)
  }, [introFromCareer])

  useLayoutEffect(() => {
    if (!introFromCareer || prefersReducedMotion) return

    const travel =
      typeof window !== "undefined"
        ? Math.round(window.innerHeight * 1.12 + 40)
        : 920

    const ease = [0.22, 1, 0.36, 1] as const

    void sepCtrl.set({ y: travel })
    void cardsCtrl.set({ y: 280, opacity: 0 })
    void heroExtrasCtrl.set({
      opacity: 0.48,
      y: 42,
      scale: 0.94,
      filter: "blur(5px)",
    })

    requestAnimationFrame(() => {
      void sepCtrl.start({
        y: 0,
        transition: { duration: 0.62, ease },
      })

      void cardsCtrl.start({
        y: 0,
        opacity: 1,
        transition: { duration: 0.56, ease, delay: 0.06 },
      })

      void heroExtrasCtrl.start({
        opacity: 1,
        y: 0,
        scale: 1,
        filter: "blur(0px)",
        transition: { duration: 0.54, ease },
      })
    })
  }, [
    introFromCareer,
    prefersReducedMotion,
    sepCtrl,
    cardsCtrl,
    heroExtrasCtrl,
  ])

  useLayoutEffect(() => {
    return registerHomeExitRunner(() => {
      if (prefersReducedMotion) return

      const travel =
        typeof window !== "undefined"
          ? Math.round(window.innerHeight * 1.12 + 40)
          : 920

      const ease = [0.22, 1, 0.36, 1] as const

      beginChatNavigationFromHome()

      void sepCtrl.start({
        y: travel,
        transition: { duration: 0.62, ease },
      })

      void cardsCtrl.start({
        y: 260,
        opacity: 0,
        transition: { duration: 0.56, ease },
      })

      void heroExtrasCtrl.start({
        scale: 0.82,
        y: -14,
        opacity: 0,
        filter: "blur(5px)",
        transition: { duration: 0.58, ease },
      })
    })
  }, [
    prefersReducedMotion,
    registerHomeExitRunner,
    beginChatNavigationFromHome,
    sepCtrl,
    cardsCtrl,
    heroExtrasCtrl,
  ])

  function onNavigateToChatClick(e: MouseEvent<HTMLAnchorElement>) {
    if (
      e.metaKey ||
      e.ctrlKey ||
      e.shiftKey ||
      e.altKey ||
      e.button !== 0
    ) {
      return
    }

    e.preventDefault()

    void navigateToChatFromHome()
  }

  function onNavigateToSearchClick(e: MouseEvent<HTMLAnchorElement>) {
    if (
      e.metaKey ||
      e.ctrlKey ||
      e.shiftKey ||
      e.altKey ||
      e.button !== 0
    ) {
      return
    }

    e.preventDefault()

    navigateToSearchFromHome()
  }

  return (
    <div className="flex flex-1 flex-col">
      <section
        className="relative overflow-x-clip bg-gradient-to-b from-muted/40 via-background to-background pb-px sm:overflow-visible"
      >
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.35]"
          aria-hidden
          style={{
            backgroundImage:
              "radial-gradient(ellipse 80% 60% at 50% -30%, oklch(0.55 0.15 220 / 0.25), transparent 55%), radial-gradient(ellipse 50% 40% at 100% 0%, oklch(0.6 0.12 160 / 0.12), transparent 45%)",
          }}
        />
        <div className="relative mx-auto flex max-w-6xl flex-col gap-10 px-4 py-16 sm:px-6 sm:py-24 lg:gap-12 lg:py-28">
          <div className="mx-auto flex max-w-3xl flex-col items-center text-center">
            <div className="mx-auto w-full max-w-lg">
              <BrandWordmark size="hero" />
            </div>

            <motion.div
              animate={heroExtrasCtrl}
              initial={false}
              className="w-full origin-top will-change-[transform,opacity,filter]"
            >
              <HeroSubtitleSlot variant="marketing">
                <p className="mx-auto max-w-2xl text-lg leading-relaxed text-muted-foreground text-pretty sm:text-xl">
                  AI-powered Saudi COOP and internship recommendations tailored to
                  computing students — structured filters plus intelligent,
                  explainable ranking.
                </p>
              </HeroSubtitleSlot>

              <div className="mt-10 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
                <Button asChild size="lg" className="w-full sm:w-auto">
                  <Link href="/chat" onClick={onNavigateToChatClick}>
                    Start Career Match
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="w-full sm:w-auto">
                  <Link href="/search" onClick={onNavigateToSearchClick}>
                    Manual Search
                  </Link>
                </Button>
              </div>
            </motion.div>
          </div>
        </div>

        <motion.div
          aria-hidden
          animate={sepCtrl}
          initial={false}
          className="pointer-events-none absolute inset-x-0 bottom-0 z-[2] h-px bg-border/60 will-change-transform"
        />
      </section>

      <motion.section
        animate={cardsCtrl}
        initial={false}
        className="mx-auto w-full max-w-6xl flex-1 px-4 py-14 sm:px-6 sm:py-20 will-change-transform"
      >
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(({ title, description, icon: Icon }) => (
            <Card key={title} className="border-border/80 shadow-none">
              <CardHeader className="gap-3">
                <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Icon className="size-5" aria-hidden />
                </div>
                <CardTitle className="text-lg">{title}</CardTitle>
                <CardDescription className="text-base leading-relaxed">
                  {description}
                </CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </motion.section>
    </div>
  )
}
