import type { Metadata } from "next";
import "./globals.css";
import { cn } from "@/lib/utils";
import { Navbar } from "@/components/layout/navbar";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: {
    default: "CareerFinder.ai",
    template: "%s · CareerFinder.ai",
  },
  description:
    "AI-powered recommendations for Saudi COOP and internship opportunities for computing students.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("h-full", "antialiased", "font-sans")}>
      <body className="flex min-h-dvh flex-col">
        <Providers>
          <Navbar />
          <main className="flex min-h-0 flex-1 flex-col overflow-x-clip">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
