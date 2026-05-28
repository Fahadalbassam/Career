import { expect, test, type Page } from "@playwright/test"

const CHAT_MESSAGE =
  "I am a CS student in Khobar looking for cybersecurity COOP. I know Linux and networking."

/** Dev-only console noise that should not fail smoke tests. */
const BENIGN_CONSOLE_PATTERNS = [
  /Download the React DevTools/i,
  /webpack-hmr/i,
  /Fast Refresh/i,
  /\[HMR\]/i,
  /favicon\.ico/i,
  /Failed to load resource.*favicon/i,
  /ResizeObserver loop/i,
]

function isBenignConsoleMessage(text: string): boolean {
  return BENIGN_CONSOLE_PATTERNS.some((pattern) => pattern.test(text))
}

function attachConsoleCollector(page: Page) {
  const errors: string[] = []
  const pageErrors: string[] = []

  page.on("console", (msg) => {
    if (msg.type() !== "error") return
    const text = msg.text()
    if (isBenignConsoleMessage(text)) return
    errors.push(text)
  })

  page.on("pageerror", (err) => {
    pageErrors.push(err.message)
  })

  return {
    assertClean() {
      expect(
        pageErrors,
        `Uncaught page errors:\n${pageErrors.join("\n")}`,
      ).toEqual([])
      expect(
        errors,
        `Console errors:\n${errors.join("\n")}`,
      ).toEqual([])
    },
  }
}

test.describe("CareerFinder.ai smoke", () => {
  test("home page loads", async ({ page }) => {
    await page.goto("/")
    await expect(
      page.getByRole("heading", { name: /CareerFinder\.ai/i }),
    ).toBeVisible()
    await expect(
      page.getByRole("link", { name: /Start Career Match/i }),
    ).toBeVisible()
  })

  test("chat page loads", async ({ page }) => {
    await page.goto("/chat")
    await expect(
      page.getByPlaceholder("Ask CareerFinder.ai…"),
    ).toBeVisible()
    await expect(
      page.getByRole("navigation").getByRole("link", { name: "Chat" }),
    ).toBeVisible()
  })

  test("chat can submit a message", async ({ page }) => {
    test.setTimeout(90_000)

    await page.goto("/chat")
    const composer = page.getByPlaceholder("Ask CareerFinder.ai…")
    await expect(composer).toBeVisible()

    await composer.fill(CHAT_MESSAGE)
    await page.getByRole("button", { name: "Send message" }).click()

    const main = page.locator("main")

    // Scope to main so demo shelf tiles (hidden flip faces with "COOP") are not matched.
    await expect(async () => {
      const userBubble = main.getByText(CHAT_MESSAGE, { exact: false })
      const parsedProfile = main.getByText("Parsed profile")
      const assistantReply = main.getByText(
        /remote, hybrid, or on-site|recommend|match|profile|skills/i,
      )
      const shelfCard = main.getByText(/Saved .+ to your shelf/i)

      const visible =
        (await userBubble.isVisible()) ||
        (await parsedProfile.isVisible()) ||
        (await assistantReply.first().isVisible()) ||
        (await shelfCard.isVisible())

      expect(visible).toBeTruthy()
    }).toPass({ timeout: 45_000 })
  })

  test("search page loads", async ({ page }) => {
    await page.goto("/search")
    await expect(page.getByRole("navigation")).toBeVisible()
    await expect(
      page.getByRole("link", { name: "Search", exact: true }),
    ).toBeVisible()
    // Route shell is intentionally minimal until Phase 6.
    await expect(page.locator("body")).toBeVisible()
  })

  test("methodology page loads", async ({ page }) => {
    await page.goto("/methodology")
    await expect(
      page.getByRole("heading", { name: /Methodology/i }).first(),
    ).toBeVisible()
    await expect(page.getByText(/Methodology snapshot/i)).toBeVisible()
  })

  test("login page loads", async ({ page }) => {
    await page.goto("/login")
    await expect(page.getByText("Login to your account")).toBeVisible()
    await expect(page.getByLabel("Email")).toBeVisible()
    await expect(page.getByLabel("Password")).toBeVisible()
    await expect(page.getByRole("button", { name: /^Login$/i })).toBeVisible()
  })

  test("signup page loads", async ({ page }) => {
    await page.goto("/signup")
    await expect(page.getByText("Create your account")).toBeVisible()
    await expect(page.getByLabel("Email")).toBeVisible()
    await expect(page.getByLabel("Password", { exact: true })).toBeVisible()
    await expect(page.getByLabel("Confirm password")).toBeVisible()
    await expect(
      page.getByRole("button", { name: /Create account/i }),
    ).toBeVisible()
  })

  test.describe("chat input robustness", () => {
    async function submitChatMessage(page: Page, text: string) {
      await page.goto("/chat")
      const composer = page.getByPlaceholder("Ask CareerFinder.ai…")
      await expect(composer).toBeVisible()
      await composer.fill(text)
      await page.getByRole("button", { name: "Send message" }).click()
    }

    test("handles accidental tiny input without crash", async ({ page }) => {
      test.setTimeout(90_000)
      const collector = attachConsoleCollector(page)

      await submitChatMessage(page, "n")

      const main = page.locator("main")
      await expect(main).toBeVisible({ timeout: 15_000 })

      await expect(async () => {
        const asksForMore = main.getByText(
          /major|skills|city|profile|scanning|COOP|internship|personalised|personalized/i,
        )
        const userBubble = main.getByText("n", { exact: true })
        const visible =
          (await asksForMore.first().isVisible()) ||
          (await userBubble.isVisible())
        expect(visible).toBeTruthy()
      }).toPass({ timeout: 45_000 })

      collector.assertClean()
    })

    test("handles vague internship input", async ({ page }) => {
      test.setTimeout(90_000)

      await submitChatMessage(page, "I need internship")

      const main = page.locator("main")
      await expect(async () => {
        const reply = main.getByText(
          /major|skills|city|internship|COOP|profile|scanning|match/i,
        )
        const parsed = main.getByText("Parsed profile")
        expect(
          (await reply.first().isVisible()) || (await parsed.isVisible()),
        ).toBeTruthy()
      }).toPass({ timeout: 45_000 })
    })

    test("handles complete cybersecurity Khobar COOP input", async ({ page }) => {
      test.setTimeout(90_000)

      const message =
        "I am a CS student in Khobar looking for cybersecurity COOP. I know Linux, networking, and penetration testing."

      await submitChatMessage(page, message)

      const main = page.locator("main")
      await expect(async () => {
        const userBubble = main.getByText(message, { exact: false })
        const parsedProfile = main.getByText("Parsed profile")
        const assistantReply = main.getByText(
          /match|recommend|Khobar|cyber|security|shelf|profile/i,
        )
        const shelfCard = main.getByText(/Saved .+ to your shelf/i)

        const visible =
          (await userBubble.isVisible()) ||
          (await parsedProfile.isVisible()) ||
          (await assistantReply.first().isVisible()) ||
          (await shelfCard.isVisible())

        expect(visible).toBeTruthy()
      }).toPass({ timeout: 45_000 })
    })
  })

  test("no console errors on key pages", async ({ page }) => {
    const routes = ["/", "/chat", "/search", "/methodology"] as const
    const collector = attachConsoleCollector(page)

    for (const route of routes) {
      await page.goto(route)
      await page.waitForLoadState("domcontentloaded")
      // Allow chat shell / hero animations to settle without tight timing asserts.
      await page.waitForTimeout(500)
    }

    collector.assertClean()
  })
})
