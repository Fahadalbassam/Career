"use client"

import { LayoutGroup } from "framer-motion"

import { CareerChromeProvider } from "@/components/career/career-nav-context"
import { HomeExitToChatProvider } from "@/components/home/home-exit-to-chat-context"
import { TooltipProvider } from "@/components/ui/tooltip"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <LayoutGroup id="careerfinder-root">
      <TooltipProvider delayDuration={300}>
        <HomeExitToChatProvider>
          <CareerChromeProvider>{children}</CareerChromeProvider>
        </HomeExitToChatProvider>
      </TooltipProvider>
    </LayoutGroup>
  )
}
