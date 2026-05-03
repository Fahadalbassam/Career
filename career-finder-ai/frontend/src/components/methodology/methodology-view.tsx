import { Fragment, type ComponentProps } from "react"
import Link from "next/link"
import {
  BarChart3,
  Braces,
  Database,
  ListChecks,
} from "lucide-react"

import { MethodologyHeroPlanet } from "@/components/methodology/methodology-hero-planet"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const heroSummaryItems = [
  "Understands student goals",
  "Filters verified Saudi opportunities",
  "Ranks matches with explainable scoring",
] as const

const snapshotCards = [
  {
    kicker: "Dataset",
    title: "Verified Saudi COOP/internship records",
    desc: "Curated listings aligned with national training programs.",
  },
  {
    kicker: "Parser",
    title: "Extracts major, city, skills, and preferences",
    desc: "Structured profile fields from natural student messages.",
  },
  {
    kicker: "Scoring",
    title: "Combines fit, skills, location, and work mode",
    desc: "Weighted signals produce a comparable ranking.",
  },
  {
    kicker: "Output",
    title: "Returns ranked matches with reasons",
    desc: "Transparent explanations for every recommendation.",
  },
] as const

const pipelineSteps = [
  {
    num: "01",
    title: "Student Input",
    body: 'The student can write naturally, such as “I’m a cybersecurity student in Dammam looking for remote COOP.”',
    mini: ["major", "city", "skills", "training type"],
    stagger: false,
  },
  {
    num: "02",
    title: "Profile Parsing",
    body: "The system extracts structured fields from the message so the recommendation engine can compare them against the dataset.",
    mini: ["intent detection", "preference extraction", "normalized fields"],
    stagger: true,
  },
  {
    num: "03",
    title: "Dataset Filtering",
    body: "The system removes weak candidates and keeps opportunities that fit the student’s training type, location, and major direction.",
    mini: ["verified sources", "program type", "location match"],
    stagger: false,
  },
  {
    num: "04",
    title: "Fit Scoring",
    body: "Each candidate receives a weighted score using major fit, skills, city, work mode, and opportunity quality.",
    mini: ["major fit", "skills match", "city match", "work mode"],
    stagger: true,
  },
  {
    num: "05",
    title: "Ranked Recommendations",
    body: "The strongest matches are displayed first with short explanations so the student understands why each result was recommended.",
    mini: ["ranked cards", "match percentage", "explanation"],
    stagger: false,
  },
] as const

const scoringFactors = [
  {
    n: "01",
    title: "Major Fit",
    body: "How closely the opportunity matches the student’s academic field.",
  },
  {
    n: "02",
    title: "Skill Match",
    body: "Overlap between student skills/interests and opportunity requirements.",
  },
  {
    n: "03",
    title: "Location Match",
    body: "Exact, nearby, remote, hybrid, or national opportunities.",
  },
  {
    n: "04",
    title: "Program Type",
    body: "COOP, internship, Tamheer, or graduate training alignment.",
  },
  {
    n: "05",
    title: "Verification Quality",
    body: "Preference for official or trusted source-backed opportunities.",
  },
] as const

const comparisonCards = [
  {
    title: "Student-first matching",
    body: "Instead of only searching by job title, the system uses major, interests, skills, and location.",
  },
  {
    title: "Verified Saudi dataset",
    body: "The recommendations come from a curated dataset focused on Saudi COOP and internship opportunities.",
  },
  {
    title: "Explainable results",
    body: "Each recommendation includes reasons such as major fit, skill match, city match, and training type.",
  },
] as const

const explanationCards = [
  {
    title: "Data Collection",
    body: "Verified Saudi COOP and internship opportunities are collected from official company career pages, LinkedIn, and trusted platforms.",
    icon: Database,
  },
  {
    title: "Profile Understanding",
    body: "The system extracts major, city, skills, interests, program type, and work mode from the student’s message.",
    icon: Braces,
  },
  {
    title: "Scoring Engine",
    body: "Each opportunity receives a score based on major fit, skill match, city match, work mode match, and relevance.",
    icon: BarChart3,
  },
  {
    title: "Recommendation Output",
    body: "The best ranked opportunities are shown with personalized explanations to help students make better decisions.",
    icon: ListChecks,
  },
] as const

const logicRows = [
  {
    title: "Input Parsing",
    detail: "Converts free-text student messages into structured preferences.",
  },
  {
    title: "Candidate Filtering",
    detail: "Removes opportunities that do not match core constraints.",
  },
  {
    title: "Major Fit Matching",
    detail: "Compares the student’s major with opportunity fit labels.",
  },
  {
    title: "Weighted Scoring",
    detail: "Combines major, skill, city, work mode, and verification signals.",
  },
  {
    title: "Explanation Layer",
    detail: "Generates clear reasons for why each opportunity was recommended.",
  },
] as const

function MethodologyDotPatch({
  className,
  ...props
}: ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "methodology-page-dot-patch pointer-events-none absolute -z-10 rounded-[2rem] opacity-[0.38] dark:opacity-[0.22]",
        className,
      )}
      aria-hidden
      {...props}
    />
  )
}

function PipelineConnector() {
  return (
    <div
      className="methodology-pipeline-connector flex w-full shrink-0 flex-col items-center justify-center lg:h-auto lg:min-h-32 lg:w-auto lg:flex-1 lg:min-w-3 lg:max-w-10 lg:flex-col lg:justify-center"
      aria-hidden
    >
      <div className="methodology-pipeline-connector-line methodology-pipeline-connector-line--vertical lg:hidden" />
      <div className="methodology-pipeline-connector-node methodology-pipeline-connector-node--vertical lg:hidden" />
      <div className="methodology-pipeline-connector-row hidden w-full max-w-12 flex-1 items-center lg:flex">
        <div className="methodology-pipeline-connector-line methodology-pipeline-connector-line--horizontal" />
        <div className="methodology-pipeline-connector-arrow" />
      </div>
    </div>
  )
}

export function MethodologyView() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <section className="relative border-b border-border/80 bg-linear-to-b from-muted/45 via-background to-background pb-2">
        <MethodologyDotPatch className="right-0 top-24 h-48 w-[min(100%,28rem)] translate-x-[12%] sm:top-28" />
        <div
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_-10%,oklch(0.88_0_0/0.5),transparent_55%)] dark:bg-[radial-gradient(ellipse_70%_50%_at_50%_-10%,oklch(0.28_0_0/0.35),transparent_55%)]"
          aria-hidden
        />
        <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-10 px-4 py-12 sm:gap-12 sm:px-6 sm:py-16 lg:grid-cols-[minmax(0,1fr)_minmax(260px,380px)] lg:gap-16 lg:py-20">
          <div className="min-w-0 max-w-xl lg:max-w-none">
            <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-muted-foreground">
              Overview
            </p>
            <h1 className="mt-3 font-heading text-3xl font-semibold tracking-tight text-foreground sm:text-4xl lg:text-[2.5rem] lg:leading-tight">
              Methodology
            </h1>
            <p className="mt-4 max-w-xl text-base leading-relaxed text-muted-foreground text-pretty sm:text-lg">
              How CareerFinder.ai turns student preferences into ranked COOP and
              internship recommendations.
            </p>

            <ul className="mt-6 flex list-none flex-col gap-2 sm:flex-row sm:flex-wrap sm:gap-2.5">
              {heroSummaryItems.map((item) => (
                <li
                  key={item}
                  className="rounded-full border border-border/90 bg-muted/35 px-3 py-1.5 text-left text-xs font-medium leading-snug text-foreground sm:text-[13px]"
                >
                  {item}
                </li>
              ))}
            </ul>

            <div className="mt-6 flex items-center gap-3 sm:mt-7">
              <span className="h-1.5 w-8 shrink-0 rounded-full bg-foreground" />
              <span className="flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-muted-foreground/45" />
                <span className="size-1.5 rounded-full bg-muted-foreground/45" />
                <span className="size-1.5 rounded-full bg-muted-foreground/45" />
              </span>
            </div>
          </div>
          <div className="relative flex min-h-[min(72vw,340px)] min-w-0 justify-center sm:min-h-[300px] lg:min-h-0 lg:justify-end">
            <MethodologyHeroPlanet />
          </div>
        </div>
      </section>

      <div className="flex min-h-0 flex-1 flex-col overflow-x-clip">
      <section className="relative border-t border-border/60 bg-background">
        <MethodologyDotPatch className="left-1/2 top-8 h-36 w-[min(92%,40rem)] -translate-x-1/2" />
        <div className="relative mx-auto max-w-6xl px-4 pt-8 pb-12 sm:px-6 sm:pt-10 sm:pb-14">
          <h2 className="text-center font-heading text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
            Methodology snapshot
          </h2>
          <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-4">
            {snapshotCards.map(({ kicker, title, desc }) => (
              <article
                key={kicker}
                className="flex flex-col rounded-xl border border-border/80 bg-card px-4 py-4 shadow-[0_10px_28px_-14px_oklch(0.2_0_0/0.08)] sm:px-5 sm:py-5"
              >
                <p className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                  {kicker}
                </p>
                <h3 className="mt-2.5 font-heading text-sm font-semibold leading-snug tracking-tight text-foreground">
                  {title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-muted-foreground sm:text-[13px]">
                  {desc}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="relative border-t border-border/70 bg-background">
        <MethodologyDotPatch className="bottom-8 right-[6%] h-44 w-[min(100%,26rem)] opacity-[0.32] dark:opacity-[0.2]" />
        <div className="relative mx-auto w-full max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:py-20">
          <h2 className="text-center font-heading text-xl font-semibold tracking-tight sm:text-2xl">
            From message to ranked matches
          </h2>
          <p className="mx-auto mt-4 max-w-3xl text-center text-sm leading-relaxed text-muted-foreground sm:text-base">
            CareerFinder.ai follows a structured pipeline: convert the student
            message into a profile, filter the verified opportunity dataset,
            calculate weighted scores, and return recommendations with clear
            explanations.
          </p>

          <div className="methodology-pipeline mt-10 flex flex-col items-stretch gap-2 sm:mt-12 sm:gap-4 lg:flex-row lg:items-start lg:justify-center lg:gap-0">
            {pipelineSteps.map((step, index) => (
              <Fragment key={step.num}>
                <article
                  className={cn(
                    "methodology-pipeline-card group relative mx-auto flex w-full min-w-0 max-w-sm flex-col rounded-lg border border-white/[0.07] bg-neutral-950 p-4 shadow-[0_14px_34px_-10px_rgba(0,0,0,0.58),0_6px_14px_-6px_rgba(0,0,0,0.45),inset_0_1px_0_rgba(255,255,255,0.07),inset_0_-1px_0_rgba(0,0,0,0.82)] sm:p-5 lg:mx-0 lg:w-44 lg:max-w-44 lg:shrink-0 xl:w-48 xl:max-w-48",
                    "transition-transform duration-300 ease-out will-change-transform",
                    "hover:-translate-y-1 hover:shadow-[0_18px_40px_-10px_rgba(0,0,0,0.62)]",
                    step.stagger && "lg:mt-8",
                  )}
                >
                  <div
                    className="pointer-events-none absolute inset-0 rounded-[inherit] opacity-[0.85]"
                    style={{
                      background:
                        "linear-gradient(168deg, rgba(255,255,255,0.04) 0%, transparent 38%, transparent 62%, rgba(0,0,0,0.58) 100%)",
                    }}
                    aria-hidden
                  />
                  <div className="relative z-10 flex flex-col gap-3">
                    <span className="font-mono text-[10px] font-medium uppercase tracking-widest text-white/45">
                      {step.num}
                    </span>
                    <h3 className="font-heading text-sm font-semibold leading-snug text-white sm:text-base">
                      {step.title}
                    </h3>
                    <p className="text-[11px] leading-relaxed text-white/60 sm:text-[13px]">
                      {step.body}
                    </p>
                    <ul className="mt-1 flex list-disc flex-col gap-0.5 pl-3.5 marker:text-white/35">
                      {step.mini.map((line) => (
                        <li
                          key={line}
                          className="text-[10px] leading-snug text-white/48 sm:text-[11px]"
                        >
                          {line}
                        </li>
                      ))}
                    </ul>
                  </div>
                </article>
                {index < pipelineSteps.length - 1 ? <PipelineConnector /> : null}
              </Fragment>
            ))}
          </div>
        </div>
      </section>

      <section className="relative border-t border-border/60 bg-muted/25">
        <MethodologyDotPatch className="left-[10%] top-20 h-40 w-[min(90%,32rem)]" />
        <div className="relative mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:py-20">
          <h2 className="text-center font-heading text-xl font-semibold tracking-tight sm:text-2xl">
            What the scoring considers
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-sm text-muted-foreground sm:text-base">
            Rankings blend academic alignment, skills, place of work, program
            format, and how trustworthy the listing is.
          </p>
          <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {scoringFactors.map((f) => (
              <article
                key={f.n}
                className="flex flex-col rounded-xl border border-border/80 bg-card p-5 shadow-[0_12px_32px_-14px_oklch(0.2_0_0/0.1)]"
              >
                <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-foreground font-mono text-xs font-bold text-background">
                  {f.n}
                </div>
                <h3 className="mt-4 font-heading text-sm font-semibold tracking-tight text-foreground">
                  {f.title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-muted-foreground sm:text-sm">
                  {f.body}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="relative border-t border-border/70 bg-background">
        <MethodologyDotPatch className="right-4 top-16 h-32 w-[min(100%,22rem)] translate-x-1/4 opacity-[0.3] sm:right-12 sm:translate-x-0" />
        <div className="relative mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:py-20">
          <h2 className="mx-auto max-w-3xl text-center font-heading text-xl font-semibold tracking-tight sm:text-2xl">
            Why this is different from a normal job search
          </h2>
          <div className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-3 md:gap-5">
            {comparisonCards.map((c) => (
              <article
                key={c.title}
                className="flex flex-col rounded-xl border border-border/85 bg-card px-5 py-5 shadow-sm sm:px-6 sm:py-6"
              >
                <h3 className="font-heading text-base font-semibold tracking-tight text-foreground">
                  {c.title}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                  {c.body}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="relative border-t border-border/60 bg-muted/20">
        <MethodologyDotPatch className="bottom-12 left-1/3 h-36 w-[min(85%,28rem)] -translate-x-1/2" />
        <div className="relative mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:py-20">
          <h2 className="text-center font-heading text-xl font-semibold tracking-tight sm:text-2xl">
            What happens under the hood
          </h2>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6">
            {explanationCards.map(({ title, body, icon: Icon }) => (
              <article
                key={title}
                className="flex flex-col rounded-2xl border border-border/80 bg-card p-5 shadow-sm"
              >
                <div className="mb-4 flex size-12 items-center justify-center rounded-full bg-foreground text-background">
                  <Icon className="size-5" strokeWidth={1.75} aria-hidden />
                </div>
                <h3 className="font-heading text-base font-semibold tracking-tight">
                  {title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {body}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="relative border-t border-border/70 bg-background">
        <div className="relative mx-auto w-full max-w-3xl px-4 py-12 sm:px-6 sm:py-16">
          <h2 className="font-heading text-xl font-semibold tracking-tight sm:text-2xl">
            Recommendation Logic
          </h2>
          <ul className="mt-8 divide-y divide-border/80 rounded-xl border border-border/80 bg-card/50">
            {logicRows.map(({ title, detail }) => (
              <li
                key={title}
                className="flex flex-col gap-1 px-4 py-4 first:rounded-t-xl last:rounded-b-xl sm:flex-row sm:items-start sm:gap-6 sm:px-5 sm:py-5"
              >
                <span className="shrink-0 font-mono text-xs font-semibold uppercase tracking-wide text-foreground">
                  {title}
                </span>
                <span className="text-sm leading-relaxed text-muted-foreground">
                  {detail}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="relative mt-auto border-t border-border/80 bg-muted/20">
        <div className="mx-auto max-w-6xl px-4 py-14 text-center sm:px-6 sm:py-20">
          <h2 className="font-heading text-xl font-semibold tracking-tight sm:text-2xl">
            Ready to try the assistant?
          </h2>
          <div className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center sm:justify-center">
            <Button asChild size="lg" className="w-full sm:w-auto">
              <Link href="/chat">Start Chatting</Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="w-full sm:w-auto">
              <Link href="/search">Search Manually</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
    </div>
  )
}
