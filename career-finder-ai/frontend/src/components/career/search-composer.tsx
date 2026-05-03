"use client"

import type { KeyboardEvent as ReactKeyboardEvent } from "react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { flushSync } from "react-dom"

import {
  Building2,
  Briefcase,
  GraduationCap,
  Loader2,
  MapPin,
  Search,
  SlidersHorizontal,
  UserCircle,
  X,
} from "lucide-react"

import { useCareerChrome } from "@/components/career/career-nav-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import {
  matchCommands,
  optionsForKind,
  type SearchFilterKind,
  type SearchSlashCommand,
} from "@/data/search-filter-options"

export type SearchFilterToken = {
  id: string
  kind: SearchFilterKind
  /** Canonical value (e.g. city name) */
  value: string
}

function tokenLabel(kind: SearchFilterKind): string {
  switch (kind) {
    case "location":
      return "Location"
    case "profession":
      return "Profession"
    case "major":
      return "Major"
    case "university":
      return "University"
    case "role":
      return "Role"
  }
}

function KindIcon({ kind, className }: { kind: SearchFilterKind; className?: string }) {
  const cls = cn("size-3.5 shrink-0 opacity-80", className)
  switch (kind) {
    case "location":
      return <MapPin className={cls} aria-hidden />
    case "profession":
      return <Briefcase className={cls} aria-hidden />
    case "major":
      return <GraduationCap className={cls} aria-hidden />
    case "university":
      return <Building2 className={cls} aria-hidden />
    case "role":
      return <UserCircle className={cls} aria-hidden />
  }
}

type SlashSegment =
  | { active: false }
  | {
      active: true
      /** start index of `/` in query */
      from: number
      /** end index (caret) */
      to: number
      partial: string
    }

function detectSlashSegment(text: string, cursor: number): SlashSegment {
  const before = text.slice(0, cursor)
  const m = before.match(/(?:^|\s)\/([^\s]*)$/)
  if (!m || m.index === undefined) return { active: false }
  const full = m[0]
  const partial = m[1] ?? ""
  const from = cursor - full.length
  return { active: true, from, to: cursor, partial }
}

function newTokenId(): string {
  return `sf-${Math.random().toString(36).slice(2, 11)}`
}

export function SearchComposer({
  query,
  onQueryChange,
  pathname,
}: {
  query: string
  onQueryChange: (next: string) => void
  pathname: string
}) {
  const { searchComposerBusy: busy, setSearchComposerBusy: setBusy } =
    useCareerChrome()

  const [expanded, setExpanded] = useState(false)
  const [tokens, setTokens] = useState<SearchFilterToken[]>([])
  /** After choosing a /command — pick concrete value */
  const [valuePick, setValuePick] = useState<SearchFilterKind | null>(null)
  const [valueFilter, setValueFilter] = useState("")
  const [slashSeg, setSlashSeg] = useState<SlashSegment>({ active: false })
  const [cmdHighlight, setCmdHighlight] = useState(0)
  const [valueHighlight, setValueHighlight] = useState(0)

  const taRef = useRef<HTMLTextAreaElement | null>(null)

  useEffect(() => {
    if (pathname !== "/search") {
      queueMicrotask(() => {
        setExpanded(false)
        setValuePick(null)
        setSlashSeg({ active: false })
        setValueFilter("")
        setTokens([])
      })
    }
  }, [pathname])

  const syncSlash = useCallback(
    (text: string, cursor: number) => {
      if (!expanded || valuePick !== null) {
        setSlashSeg({ active: false })
        return
      }
      const seg = detectSlashSegment(text, cursor)
      setSlashSeg(seg)
      if (seg.active) {
        const list = matchCommands(seg.partial)
        setCmdHighlight((h) => (list.length === 0 ? 0 : Math.min(h, list.length - 1)))
      } else {
        setCmdHighlight(0)
      }
    },
    [expanded, valuePick],
  )

  const stripSlashFromQuery = useCallback(
    (from: number, to: number) => {
      const next = query.slice(0, from) + query.slice(to)
      onQueryChange(next)
      setSlashSeg({ active: false })
      requestAnimationFrame(() => {
        const el = taRef.current
        if (!el) return
        el.focus()
        const pos = from
        el.setSelectionRange(pos, pos)
        syncSlash(next, pos)
      })
    },
    [query, onQueryChange, syncSlash],
  )

  const matchedCommands = useMemo(() => {
    if (!slashSeg.active) return [] as SearchSlashCommand[]
    return [...matchCommands(slashSeg.partial)]
  }, [slashSeg])

  const valueOptions = useMemo(() => {
    if (!valuePick) return [] as string[]
    const all = optionsForKind(valuePick)
    const q = valueFilter.trim().toLowerCase()
    if (!q) return [...all]
    return all.filter((o) => o.toLowerCase().includes(q))
  }, [valuePick, valueFilter])

  const safeValueHighlight =
    valueOptions.length === 0
      ? 0
      : Math.min(valueHighlight, valueOptions.length - 1)

  const openValuePick = (kind: SearchFilterKind, cut?: SlashSegment) => {
    if (cut?.active) {
      const next = query.slice(0, cut.from) + query.slice(cut.to)
      onQueryChange(next)
      setSlashSeg({ active: false })
      requestAnimationFrame(() => {
        const el = taRef.current
        const pos = cut.from
        if (el) {
          el.focus()
          el.setSelectionRange(pos, pos)
        }
      })
    }
    setValuePick(kind)
    setValueFilter("")
    setValueHighlight(0)
  }

  const addOrReplaceToken = (kind: SearchFilterKind, value: string) => {
    setTokens((prev) => {
      const rest = prev.filter((t) => t.kind !== kind)
      return [...rest, { id: newTokenId(), kind, value }]
    })
    setValuePick(null)
    setValueFilter("")
    taRef.current?.focus()
  }

  const removeToken = (id: string) => {
    setTokens((prev) => prev.filter((t) => t.id !== id))
  }

  const submitSearch = () => {
    const text = query.trim()
    if (busy || (text.length === 0 && tokens.length === 0)) return
    setBusy(true)
    window.setTimeout(() => {
      setBusy(false)
      onQueryChange("")
      setValuePick(null)
      setSlashSeg({ active: false })
    }, 1100)
  }

  const onKeyDown = (e: ReactKeyboardEvent<HTMLTextAreaElement>) => {
    if (
      !expanded &&
      e.key === "/" &&
      !busy &&
      !e.ctrlKey &&
      !e.metaKey &&
      !e.altKey
    ) {
      const el = e.currentTarget
      const v = el.value
      const start = el.selectionStart ?? 0
      const end = el.selectionEnd ?? 0
      const withoutSelection = v.slice(0, start) + v.slice(end)
      if (withoutSelection.trim() === "" && tokens.length === 0) {
        flushSync(() => {
          setExpanded(true)
        })
      }
    }

    if (valuePick !== null) {
      if (e.key === "Escape") {
        e.preventDefault()
        setValuePick(null)
        setValueFilter("")
      }
      return
    }

    if (slashSeg.active && matchedCommands.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault()
        setCmdHighlight((h) => (h + 1) % matchedCommands.length)
        return
      }
      if (e.key === "ArrowUp") {
        e.preventDefault()
        setCmdHighlight(
          (h) => (h - 1 + matchedCommands.length) % matchedCommands.length,
        )
        return
      }
      if (e.key === "Enter") {
        e.preventDefault()
        const cmd = matchedCommands[cmdHighlight]
        if (cmd) openValuePick(cmd.kind, slashSeg)
        return
      }
      if (e.key === "Escape") {
        e.preventDefault()
        stripSlashFromQuery(slashSeg.from, slashSeg.to)
        return
      }
    }

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      submitSearch()
    }
  }

  const commandMenuOpen = expanded && valuePick === null && slashSeg.active
  const valueMenuOpen = expanded && valuePick !== null

  return (
    <>
      <Button
        type="button"
        variant="outline"
        size="icon"
        className={cn(
          "size-10 shrink-0 rounded-full border-border/70 bg-background/90 shadow-sm transition-[box-shadow,background-color,border-color]",
          expanded &&
            "border-primary/45 bg-primary/8 ring-2 ring-primary/20 ring-offset-2 ring-offset-background",
        )}
        aria-label={expanded ? "Collapse search field" : "Expand search field"}
        aria-expanded={expanded}
        aria-controls="career-search-query"
        disabled={busy}
        onClick={() => setExpanded((v) => !v)}
      >
        <SlidersHorizontal className="size-5" strokeWidth={2} aria-hidden />
      </Button>

      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        {tokens.length > 0 ? (
          <div className="flex flex-wrap gap-1.5 px-0.5 pt-0.5">
            {tokens.map((t) => (
              <Badge
                key={t.id}
                variant="secondary"
                className="max-w-full gap-1.5 py-1 pl-2 pr-1 font-medium"
              >
                <KindIcon kind={t.kind} />
                <span className="text-muted-foreground">
                  {tokenLabel(t.kind)}:
                </span>
                <span className="max-w-[14rem] truncate">{t.value}</span>
                <button
                  type="button"
                  className="rounded-sm p-0.5 text-muted-foreground hover:bg-background/80 hover:text-foreground"
                  aria-label={`Remove ${tokenLabel(t.kind)} filter`}
                  onClick={() => removeToken(t.id)}
                >
                  <X className="size-3.5" strokeWidth={2} aria-hidden />
                </button>
              </Badge>
            ))}
          </div>
        ) : null}

        <Textarea
          ref={taRef}
          id="career-search-query"
          value={query}
          onChange={(e) => {
            const v = e.target.value
            onQueryChange(v)
            const c = e.target.selectionStart ?? v.length
            syncSlash(v, c)
          }}
          onKeyDown={onKeyDown}
          onClick={(e) => {
            const c = e.currentTarget.selectionStart ?? query.length
            syncSlash(query, c)
          }}
          onKeyUp={(e) => {
            const c = e.currentTarget.selectionStart ?? query.length
            syncSlash(query, c)
          }}
          placeholder={
            expanded
              ? "Try /location , /profession , /major …"
              : "Search opportunities…"
          }
          aria-label="Search query"
          disabled={busy}
          rows={expanded ? 6 : 2}
          className={cn(
            "min-h-[44px] resize-none border-0 bg-transparent px-1 py-2 shadow-none transition-[min-height] duration-200 ease-out focus-visible:ring-0 md:text-sm",
            expanded
              ? "max-h-[min(320px,50vh)] min-h-[7.75rem]"
              : "max-h-[min(200px,40vh)]",
          )}
        />

        {commandMenuOpen && matchedCommands.length > 0 ? (
          <div
            className="max-h-44 overflow-y-auto rounded-xl border border-border/70 bg-popover px-1 py-1 text-sm shadow-md"
            role="listbox"
            aria-label="Slash commands"
          >
            {matchedCommands.map((cmd, i) => (
              <button
                key={cmd.kind}
                type="button"
                role="option"
                aria-selected={i === cmdHighlight}
                className={cn(
                  "flex w-full items-start gap-2 rounded-lg px-2 py-2 text-left",
                  i === cmdHighlight ? "bg-accent" : "hover:bg-muted/80",
                )}
                onMouseEnter={() => setCmdHighlight(i)}
                onClick={() => openValuePick(cmd.kind, slashSeg)}
              >
                <KindIcon kind={cmd.kind} className="mt-0.5" />
                <span className="min-w-0 flex-1">
                  <span className="font-semibold">{cmd.label}</span>
                  <span className="mt-0.5 block text-xs text-muted-foreground">
                    /{cmd.cmd} — {cmd.description}
                  </span>
                </span>
              </button>
            ))}
          </div>
        ) : null}

        {valueMenuOpen ? (
          <div className="rounded-xl border border-border/70 bg-popover p-2 shadow-md">
            <InputGroup className="mb-2 h-9">
              <InputGroupInput
                value={valueFilter}
                onChange={(e) => {
                  setValueFilter(e.target.value)
                  setValueHighlight(0)
                }}
                placeholder={`Search ${tokenLabel(valuePick!).toLowerCase()}…`}
                className="text-xs"
                autoFocus
                onKeyDown={(e) => {
                  if (valueOptions.length === 0) return
                  if (e.key === "ArrowDown") {
                    e.preventDefault()
                    setValueHighlight((h) => {
                      const safe = Math.min(h, valueOptions.length - 1)
                      return (safe + 1) % valueOptions.length
                    })
                  } else if (e.key === "ArrowUp") {
                    e.preventDefault()
                    setValueHighlight((h) => {
                      const safe = Math.min(h, valueOptions.length - 1)
                      return (safe - 1 + valueOptions.length) % valueOptions.length
                    })
                  } else if (e.key === "Enter") {
                    e.preventDefault()
                    const opt = valueOptions[safeValueHighlight]
                    if (opt) addOrReplaceToken(valuePick!, opt)
                  } else if (e.key === "Escape") {
                    e.preventDefault()
                    setValuePick(null)
                    setValueFilter("")
                    taRef.current?.focus()
                  }
                }}
              />
              <InputGroupAddon align="inline-end" className="text-[10px] text-muted-foreground">
                Esc
              </InputGroupAddon>
            </InputGroup>
            <div
              className="max-h-40 overflow-y-auto rounded-lg border border-border/50"
              role="listbox"
              aria-label={`Pick ${tokenLabel(valuePick!)}`}
            >
              {valueOptions.length === 0 ? (
                <p className="px-2 py-3 text-center text-xs text-muted-foreground">
                  No matches
                </p>
              ) : (
                valueOptions.map((opt, i) => (
                  <button
                    key={opt}
                    type="button"
                    role="option"
                    aria-selected={i === safeValueHighlight}
                    className={cn(
                      "flex w-full px-2 py-2 text-left text-xs",
                      i === safeValueHighlight ? "bg-accent" : "hover:bg-muted/80",
                    )}
                    onMouseEnter={() => setValueHighlight(i)}
                    onClick={() => addOrReplaceToken(valuePick!, opt)}
                  >
                    {opt}
                  </button>
                ))
              )}
            </div>
          </div>
        ) : null}
      </div>

      <Button
        type="button"
        size="icon"
        className="size-10 shrink-0 rounded-full"
        onClick={submitSearch}
        disabled={busy || (query.trim().length === 0 && tokens.length === 0)}
        aria-label={busy ? "Searching…" : "Search"}
        aria-busy={busy || undefined}
      >
        {busy ? (
          <Loader2 className="size-5 animate-spin" strokeWidth={2} aria-hidden />
        ) : (
          <Search className="size-5" strokeWidth={2} aria-hidden />
        )}
      </Button>
    </>
  )
}
