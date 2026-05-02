import type { Metadata } from "next"

import { CareerChat } from "@/components/chat/career-chat"

export const metadata: Metadata = {
  title: "Chat",
}

export default function ChatPage() {
  return <CareerChat />
}
