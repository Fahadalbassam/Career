"use client"

import {
  useEffect,
  useLayoutEffect,
  useRef,
  useCallback,
} from "react"
import { motion, useAnimationControls, useReducedMotion } from "framer-motion"
import { usePathname, useRouter } from "next/navigation"

function methodologyPathFromHref(href: string) {
  const [path] = href.split("#")
  const [clean] = path.split("?")
  return clean ?? href
}

export function MethodologyHeroPlanet() {
  const planetRef = useRef<HTMLDivElement | null>(null)
  const exitingRef = useRef(false)
  const pathname = usePathname()
  const router = useRouter()
  const prefersReducedMotion = useReducedMotion()
  const slideControls = useAnimationControls()

  const runScrollLoop = useCallback(() => {
    const root = planetRef.current
    if (!root) return

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return
    }

    let ticking = false

    const update = () => {
      const y = window.scrollY

      root.style.setProperty("--planet-y", `${y * 0.03}px`)
      root.style.setProperty("--ring-one-rotate", `${y * 0.04}deg`)
      root.style.setProperty("--ring-two-rotate", `${y * -0.03}deg`)
      root.style.setProperty("--ring-one-y", `${y * -0.015}px`)
      root.style.setProperty("--ring-two-y", `${y * 0.02}px`)
      root.style.setProperty("--ring-three-rotate", `${y * 0.028}deg`)
      root.style.setProperty("--ring-four-rotate", `${y * -0.032}deg`)
      root.style.setProperty("--ring-five-rotate", `${y * 0.02}deg`)
      root.style.setProperty("--ring-three-y", `${y * 0.018}px`)
      root.style.setProperty("--ring-four-y", `${y * -0.014}px`)
      root.style.setProperty("--ring-five-y", `${y * 0.011}px`)
      root.style.setProperty("--dot-rotate", `${y * 0.06}deg`)

      ticking = false
    }

    const onScroll = () => {
      if (!ticking) {
        ticking = true
        window.requestAnimationFrame(update)
      }
    }

    update()
    window.addEventListener("scroll", onScroll, { passive: true })

    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  useEffect(() => {
    return runScrollLoop()
  }, [runScrollLoop])

  useLayoutEffect(() => {
    if (prefersReducedMotion) {
      void slideControls.set({ x: 0, opacity: 1 })
      return
    }

    const shift = Math.min(120, Math.round(window.innerWidth * 0.2))
    void slideControls.set({ x: shift, opacity: 0.78 })

    const id = window.requestAnimationFrame(() => {
      void slideControls.start({
        x: 0,
        opacity: 1,
        transition: { duration: 0.68, ease: [0.22, 1, 0.36, 1] },
      })
    })

    return () => window.cancelAnimationFrame(id)
  }, [prefersReducedMotion, slideControls])

  useEffect(() => {
    if (prefersReducedMotion) return

    const onClickCapture = (e: MouseEvent) => {
      if (pathname !== "/methodology" || exitingRef.current) return

      const target = e.target
      if (!(target instanceof Element)) return

      const link = target.closest("a[href]")
      if (!link) return

      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0)
        return

      const targetAttr = link.getAttribute("target")
      if (targetAttr && targetAttr !== "_self") return

      const href = link.getAttribute("href")
      if (!href || !href.startsWith("/")) return

      const path = methodologyPathFromHref(href)
      if (path === "/methodology" || path.startsWith("/methodology/")) return

      e.preventDefault()
      e.stopPropagation()
      exitingRef.current = true

      const shift = Math.min(140, Math.round(window.innerWidth * 0.22))

      void slideControls
        .start({
          x: shift,
          opacity: 0.72,
          transition: { duration: 0.42, ease: [0.22, 1, 0.36, 1] },
        })
        .then(() => {
          router.push(href)
        })
    }

    document.addEventListener("click", onClickCapture, true)

    return () => document.removeEventListener("click", onClickCapture, true)
  }, [pathname, prefersReducedMotion, router, slideControls])

  return (
    <motion.div
      className="mx-auto w-full max-w-[380px] will-change-transform"
      initial={false}
      animate={slideControls}
      style={{ transformOrigin: "50% 50%" }}
    >
      <div ref={planetRef} className="methodology-planet-root" aria-hidden>
        <div className="methodology-planet-dotted-bg" />
        <div className="methodology-planet-deco methodology-planet-deco--a" />
        <div className="methodology-planet-deco methodology-planet-deco--b" />

        <div className="methodology-planet-stage">
          <div className="methodology-planet-shift">
            <div className="methodology-planet-shadow" />
            <div className="methodology-planet-ring methodology-planet-ring--five" />
            <div className="methodology-planet-ring methodology-planet-ring--four" />
            <div className="methodology-planet-ring methodology-planet-ring--three" />
            <div className="methodology-planet-ring methodology-planet-ring--two" />
            <div className="methodology-planet-ring methodology-planet-ring--one" />
            <div className="methodology-planet-sphere" />
            <div className="methodology-planet-orbit-dots">
              <span className="methodology-planet-orbit-dot methodology-planet-orbit-dot--a" />
              <span className="methodology-planet-orbit-dot methodology-planet-orbit-dot--b" />
              <span className="methodology-planet-orbit-dot methodology-planet-orbit-dot--c" />
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
