export type SearchFilterKind =
  | "location"
  | "profession"
  | "major"
  | "university"
  | "role"

export type SearchSlashCommand = {
  kind: SearchFilterKind
  /** Primary slash token, e.g. `location` for `/location` */
  cmd: string
  label: string
  description: string
  /** Extra prefixes that match this command */
  aliases?: readonly string[]
}

export const SEARCH_SLASH_COMMANDS: readonly SearchSlashCommand[] = [
  {
    kind: "location",
    cmd: "location",
    label: "Location",
    description: "City or region in Saudi Arabia",
    aliases: ["loc", "city"],
  },
  {
    kind: "profession",
    cmd: "profession",
    label: "Profession",
    description: "Target job or career path",
    aliases: ["prof", "job"],
  },
  {
    kind: "major",
    cmd: "major",
    label: "Major",
    description: "Field of study",
    aliases: ["study", "degree"],
  },
  {
    kind: "university",
    cmd: "university",
    label: "University",
    description: "Saudi university or college",
    aliases: ["uni", "school"],
  },
  {
    kind: "role",
    cmd: "role",
    label: "Role type",
    description: "Internship / COOP / employment type",
    aliases: ["type"],
  },
] as const

/** Curated list — extend or wire to API later */
export const SAUDI_LOCATIONS: readonly string[] = [
  "Riyadh",
  "Jeddah",
  "Mecca",
  "Medina",
  "Dammam",
  "Khobar",
  "Dhahran",
  "Taif",
  "Abha",
  "Tabuk",
  "Buraidah",
  "Khamis Mushait",
  "Hail",
  "Najran",
  "Al Jubail",
  "Yanbu",
  "Al Hofuf",
  "Al Qatif",
  "Al Ahsa",
]

export const PROFESSION_OPTIONS: readonly string[] = [
  "Software Engineer",
  "Backend Engineer",
  "Frontend Engineer",
  "Full-stack Engineer",
  "Mobile Developer",
  "Data Scientist",
  "ML Engineer",
  "Data Engineer",
  "DevOps / SRE",
  "Security Engineer",
  "QA / Test Engineer",
  "Product Manager",
  "UX / UI Designer",
  "Solutions Architect",
  "IT Consultant",
]

export const MAJOR_OPTIONS: readonly string[] = [
  "Computer Science",
  "Software Engineering",
  "Computer Engineering",
  "Information Systems",
  "Information Technology",
  "Data Science",
  "Artificial Intelligence",
  "Cybersecurity",
  "Electrical Engineering",
  "Mathematics & Computing",
]

export const UNIVERSITY_OPTIONS: readonly string[] = [
  "King Fahd University of Petroleum & Minerals (KFUPM)",
  "King Saud University (KSU)",
  "King Abdulaziz University (KAU)",
  "Imam Abdulrahman Bin Faisal University (IAU)",
  "Umm Al-Qura University (UQU)",
  "KAUST",
  "Princess Nourah University (PNU)",
  "Effat University",
  "Alfaisal University",
  "Prince Sultan University",
]

export const ROLE_OPTIONS: readonly string[] = [
  "COOP",
  "Internship",
  "Graduate program",
  "Part-time",
  "Full-time",
  "Summer program",
]

const BY_KIND: Record<SearchFilterKind, readonly string[]> = {
  location: SAUDI_LOCATIONS,
  profession: PROFESSION_OPTIONS,
  major: MAJOR_OPTIONS,
  university: UNIVERSITY_OPTIONS,
  role: ROLE_OPTIONS,
}

export function optionsForKind(kind: SearchFilterKind): readonly string[] {
  return BY_KIND[kind]
}

export function matchCommands(afterSlash: string): readonly SearchSlashCommand[] {
  const q = afterSlash.trim().toLowerCase()
  if (!q) return SEARCH_SLASH_COMMANDS
  return SEARCH_SLASH_COMMANDS.filter((c) => {
    if (c.cmd.startsWith(q)) return true
    if (c.label.toLowerCase().startsWith(q)) return true
    return (c.aliases ?? []).some((a) => a.startsWith(q) || q.startsWith(a))
  })
}
