import { installCommand } from "../site/content";

export type DocBlock =
  | { kind: "paragraph"; text: string }
  | { kind: "code"; value: string; language: "bash" | "text"; label: string }
  | { kind: "list"; items: readonly string[] }
  | { kind: "table"; headers: readonly string[]; rows: readonly (readonly string[])[] }
  | { kind: "note"; title: string; text: string }
  | { kind: "links"; items: readonly { title: string; href: string; description: string }[] };

export interface DocSection {
  id: string;
  title: string;
  blocks: readonly DocBlock[];
}

export interface DocPage {
  slug: string;
  title: string;
  group: "Get started" | "Guides" | "Reference";
  summary: string;
  sections: readonly DocSection[];
  sources: readonly string[];
}

const p = (text: string): DocBlock => ({ kind: "paragraph", text });
const code = (value: string, label = "Terminal", language: "bash" | "text" = "bash"): DocBlock =>
  ({ kind: "code", value, label, language });
const list = (...items: string[]): DocBlock => ({ kind: "list", items });
const note = (title: string, text: string): DocBlock => ({ kind: "note", title, text });
const table = (headers: readonly string[], rows: readonly (readonly string[])[]): DocBlock =>
  ({ kind: "table", headers, rows });
const links = (...items: { title: string; href: string; description: string }[]): DocBlock =>
  ({ kind: "links", items });

export const firstProjectCommand =
  "kickstart create service hello --lang typescript --runtime cloudflare-workers";

export const documentationPages: readonly DocPage[] = [
  {
    slug: "get-started",
    title: "Get started with kickstart",
    group: "Get started",
    summary: "From an empty directory to a working project, with files and instructions your coding agent can follow.",
    sources: ["README.md", "docs/operations/install-binaries.md", "src/templates/cloudflare-workers/typescript/Makefile.tpl"],
    sections: [
      { id: "install", title: "Install kickstart", blocks: [
        p("Run the installer on Linux x64 or arm64, or macOS Apple Silicon. It downloads a release binary, verifies its SHA-256 checksum, and offers to add it to your PATH."),
        code(installCommand),
        code("kickstart --version", "Verify the installation"),
        p("On another platform, use a Python 3.12–3.14 source installation. The installation guide covers that path, custom directories, and updates."),
      ] },
      { id: "create", title: "Create your first project", blocks: [
        p("You need Git, Bun, and make for this walkthrough. It creates a TypeScript Cloudflare Worker that you can develop locally without a Cloudflare account."),
        p("Run this from the directory where you keep your projects. kickstart creates a new hello directory with a Worker, tests, local development commands, and documentation."),
        code(firstProjectCommand),
        note("A Worker runs on Cloudflare's runtime", "This scaffold uses Wrangler, not Docker. Your local checks do not deploy anything; deployment is a separate command."),
      ] },
      { id: "check-and-run", title: "Check it. Run it.", blocks: [
        p("Enter the project and run its verification target. For this Worker scaffold, make check installs dependencies, then runs lint, TypeScript, and tests."),
        code("cd hello\nmake check\nmake dev"),
        p("Open the local address printed by Wrangler. The root returns a greeting; /healthz returns a JSON health response. Stop the server with Ctrl+C."),
      ] },
      { id: "start-building", title: "Make it yours", blocks: [
        p("Read README.md and AGENTS.md before changing the code. The first maps the project for you; the second gives a coding agent the layout, commands, and boundaries it should follow."),
        links(
          { title: "Choose a project", href: "/docs/project-types", description: "Find the right type, language, and runtime." },
          { title: "Understand the generated files", href: "/docs/generated-output", description: "See what you own and what kickstart manages." },
          { title: "Work with an agent", href: "/docs/agent-workflow", description: "Give an agent a concrete starting contract." },
        ),
      ] },
    ],
  },
  {
    slug: "installation",
    title: "Installation",
    group: "Get started",
    summary: "Install a verified release binary, choose another installation path, and keep kickstart up to date.",
    sources: ["README.md", "docs/operations/install-binaries.md", "docs/contracts/telemetry.md"],
    sections: [
      { id: "release-binary", title: "Release binary", blocks: [
        code(installCommand),
        table(["Platform", "Binary"], [["Linux x64", "linux-x64"], ["Linux arm64", "linux-arm64"], ["macOS Apple Silicon", "macos-arm64"]]),
        p("The installer writes the launcher to ~/.local/bin/kickstart and offers to update your shell profile. Open a new terminal if your current shell has not picked up the PATH change."),
        code("kickstart --version\nkickstart --help", "Verify"),
      ] },
      { id: "source-install", title: "Install from source", blocks: [
        p("For platforms outside the binary matrix, use pipx with Python 3.12–3.14 and Git. This installs the repository source rather than a pinned release binary."),
        code("pipx install git+https://github.com/woud420/kickstart"),
        note("Check the package name", "The PyPI package named kickstart is an unrelated project. Use the Git URL above or a wheel attached to a kickstart GitHub Release."),
      ] },
      { id: "installer-options", title: "Choose the install location or version", blocks: [
        table(["Variable", "Purpose"], [
          ["KICKSTART_VERSION", "Release tag to install; defaults to latest"],
          ["KICKSTART_INSTALL_DIR", "Launcher directory; defaults to ~/.local/bin"],
          ["KICKSTART_APP_ROOT", "Directory for the binary payload"],
          ["KICKSTART_UPDATE_PROFILE", "prompt, yes, or no"],
          ["KICKSTART_ASSUME_YES", "Set to 1 to accept the PATH prompt"],
        ]),
        p("The install runbook has manual downloads, checksums, all installer options, and uninstall instructions."),
      ] },
      { id: "updates", title: "Update or remove kickstart", blocks: [
        code("kickstart upgrade", "Update"),
        p("An upgrade may print a separate managed-layout repair command. Follow the printed instructions rather than trying to move a running binary payload yourself. Use kickstart uninstall --help to review removal options."),
      ] },
      { id: "telemetry", title: "Choose your telemetry preference", blocks: [
        p("Release builds enable pseudonymous usage telemetry by default. Turn it off persistently, or use a process-level opt-out before the installer runs."),
        code("kickstart telemetry disable", "Disable for future commands"),
        code("curl -fsSL https://raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh | DO_NOT_TRACK=1 bash", "Opt out during installation too"),
        links({ title: "Telemetry contract", href: "https://github.com/woud420/kickstart/blob/master/docs/contracts/telemetry.md", description: "Events, fields, storage, and opt-out precedence." }),
      ] },
    ],
  },
  {
    slug: "project-types",
    title: "Choose a project",
    group: "Guides",
    summary: "Start with the kind of thing you are building. Then choose the language and runtime that fit it.",
    sources: ["docs/human-guide.md", "src/cli/create.py", "src/generator/specs.py"],
    sections: [
      { id: "types", title: "Five starting points", blocks: [
        table(["Type", "Use it for", "Languages"], [
          ["service", "An API or backend process", "Python, TypeScript, Rust, Go, C++"],
          ["frontend", "A React app with Vite and Bun", "TypeScript"],
          ["lib", "A reusable package", "Python, Rust"],
          ["cli", "A command-line tool", "Python, Rust, TypeScript"],
          ["system", "A repo that groups apps, services, libraries, and infrastructure", "Language-neutral root"],
        ]),
        code("kickstart create service api --lang python\nkickstart create frontend web\nkickstart create lib core --lang rust\nkickstart create cli ops-tool --lang typescript\nkickstart create system platform --cloud aws --runtime kubernetes", "One example per type"),
        p("Use system for aggregate repos. mono and monorepo remain legacy aliases. Use lowercase names made of letters, digits, dashes, or underscores."),
      ] },
      { id: "runtimes", title: "Choose the service runtime", blocks: [
        p("Container services are the default. Cloudflare Workers are supported for TypeScript and Rust; select cloudflare-workers explicitly. Workers use Wrangler and are not Docker containers."),
        code("kickstart create service edge --lang typescript --runtime cloudflare-workers"),
        p("Python uses FastAPI by default, with --framework minimal for the standard library. TypeScript container services use Bun and Hono; Rust container services use Actix-web. Go and C++ provide smaller starting points."),
      ] },
      { id: "extensions", title: "Add supported service extensions", blocks: [
        table(["Container service", "Extensions"], [
          ["Python / FastAPI", "Postgres or SQLite, Redis, JWT"],
          ["TypeScript", "Postgres, JWT"],
          ["Rust", "Redis, JWT"],
        ]),
        code("kickstart create service api --lang python --database postgres --cache redis --auth jwt"),
        p("These extensions have specific template support. Other combinations are rejected; adding an option does not provision a database, cache, identity provider, or production environment."),
      ] },
      { id: "systems", title: "Compose a system", blocks: [
        list("--cloud: aws, gcp, cloudflare, multi, or none.", "--runtime: kubernetes, cloudflare-workers, or hybrid.", "--helm selects Helm rather than the default Kustomize artifacts for Kubernetes.", "--workspace-tooling bun-turbo adds a Bun/Turbo workspace; none leaves the root language-neutral.", "--knowledge obsidian, backstage, or both adds external knowledge metadata; none is the default."),
        p("Cloudflare Containers are not implemented. A Cloudflare Worker profile does not imply container support. Project documentation and scaffold metadata are generated even with --knowledge none."),
      ] },
    ],
  },
  {
    slug: "generated-output",
    title: "Understand the generated files",
    group: "Guides",
    summary: "A scaffold is a starting repo with an orientation map, verification commands, and explicit ownership boundaries.",
    sources: ["docs/scaffold-contract.md", "docs/contracts/scaffold-ownership.md", "docs/contracts/plan-drift-scope.md"],
    sections: [
      { id: "read-first", title: "Read these first", blocks: [
        table(["Artifact", "Purpose"], [
          ["README.md", "Human orientation and project commands"],
          ["AGENTS.md", "Agent orientation: layout, commands, and boundaries"],
          ["CLAUDE.md", "Claude-specific discovery bridge"],
          ["Makefile", "The project's install, verification, and development targets"],
          ["docs/", "Architecture, contracts, decisions, and operational guidance"],
          [".kickstart/scaffold.json", "Machine-readable scaffold choices and provenance"],
          [".agents/skills/", "Reusable project workflow guidance"],
        ]),
        p("Language and runtime choices determine the source tree, dependency files, tests, and deployment artifacts. Read the generated README for that project's exact commands."),
      ] },
      { id: "ownership", title: "Know what you own", blocks: [
        p("Application code, domain decisions, and user-written documentation belong to you. Managed documentation sections use explicit kickstart fences. The scaffold manifest records the inputs and, where available, the per-file ownership envelope."),
        p("plan compares managed projections inside their fences. It does not compare your prose outside them. Files emitted once as starting points are not promises that kickstart will regenerate or maintain your application."),
        note("Keep the boundary intact", "Do not edit scaffold.json to claim features the generator did not produce, or remove ownership markers to hide drift. Use the inspection commands to understand a mismatch first."),
      ] },
      { id: "verification", title: "Use the project's checks", blocks: [
        code("make check"),
        p("The generated target is the verification entry point, but its exact steps depend on the language and runtime. Local checks establish local behavior; they do not prove a production deploy, cloud credentials, or external integrations work."),
      ] },
    ],
  },
  {
    slug: "agent-workflow",
    title: "Work with a coding agent",
    group: "Guides",
    summary: "Give your agent a project contract before asking it to add behavior.",
    sources: ["docs/agent-guide.md", "docs/agent-contributing.md", "AGENTS.md"],
    sections: [
      { id: "start-with-intent", title: "Start with a concrete intent", blocks: [
        p("Choose a supported project type, language, runtime, and destination before generating. Pass an explicit --root so the output stays separate from unrelated work. Add --gh only when you want kickstart to create a GitHub repository."),
        code("kickstart create service edge-api --lang typescript --runtime cloudflare-workers --root ./projects"),
      ] },
      { id: "read-the-contract", title: "Read before extending", blocks: [
        list("Read AGENTS.md for the generated layout, commands, and boundaries.", "Read README.md and the relevant docs/ category before changing a contract.", "Inspect .kickstart/scaffold.json for the resolved stack and ownership metadata.", "Check git status and preserve unrelated work before editing."),
        p("AGENTS.md is vendor-neutral guidance. CLAUDE.md is a compatibility entry point; vendor wiring does not replace the shared project contract."),
      ] },
      { id: "example-request", title: "A useful first request", blocks: [
        code("Read AGENTS.md, README.md, and .kickstart/scaffold.json.\nExplain the source layout and the verification command.\nAdd a small endpoint using the existing runtime and conventions.\nPreserve unrelated changes, run make check, and report what passed.", "Give this to your agent", "text"),
        p("Name the behavior you want next. The scaffold supplies setup and boundaries; your task supplies the domain model, API contract, tests, and acceptance criteria."),
      ] },
      { id: "verify", title: "Review the result", blocks: [
        list("Inspect the diff and the changed behavior.", "Run the generated verification target and any checks relevant to the change.", "Update human and agent guidance when commands, layout, or ownership change.", "Keep deployment and GitHub mutations separate from local implementation unless they are part of your request."),
      ] },
    ],
  },
  {
    slug: "existing-repositories",
    title: "Inspect an existing repo",
    group: "Guides",
    summary: "Check conformance, understand managed drift, and export metadata without confusing inspection with changes.",
    sources: ["docs/contracts/adoption-tiers.md", "docs/contracts/scaffold-drift.md", "docs/contracts/manifest-migration.md", "docs/contracts/external-io-export.md"],
    sections: [
      { id: "adopt", title: "Check conformance", blocks: [
        code("kickstart adopt path/to/repo --check\nkickstart adopt path/to/repo --check --json"),
        p("adopt --check is read-only. Level 1 checks the vendor-neutral repo artifacts without requiring a manifest. A repository with scaffold.json claims Level 2 and must also satisfy its manifest and managed-documentation contract. Recorded drift is included in the report."),
        p("Exit 0 means the claimed level is satisfied; 1 means gaps or drift; 2 means a usage error. Automatic adoption is not implemented."),
      ] },
      { id: "drift-and-plan", title: "Inspect managed drift", blocks: [
        code("kickstart drift path/to/repo --json\nkickstart plan path/to/repo\nkickstart plan path/to/repo --ownership"),
        p("drift checks recorded managed docs and structural facts such as Makefile targets and CI job identities. plan shows managed-document differences. --ownership inspects the recorded envelope. These commands do not rewrite the repo; generated-once seeds and prose outside managed fences remain user-owned."),
        p("Older manifests can lack ownership coverage. That is an explicit limitation, not proof that the repo has no drift. Read the command's report before interpreting its exit status."),
      ] },
      { id: "exports", title: "Export for other tools", blocks: [
        code("kickstart export backstage path/to/repo"),
        p("The Backstage export writes or refreshes catalog-info.yaml from scaffold.json. Derived fields are fenced; owner, lifecycle, type, and other unfenced content remain yours. This command writes a file, unlike the inspection commands above."),
        code("kickstart export external-io path/to/repo --input declaration.json --format markdown"),
        p("The external I/O export prints a declaration after validating its shape and cited source locations. It does not discover integrations automatically and does not require a scaffold manifest."),
      ] },
      { id: "migration", title: "Review a manifest migration", blocks: [
        code("kickstart migrate path/to/repo", "Preview only"),
        p("migrate previews the move from schema 3.x to 4.0. Adding --apply writes the migration. Review the plan and preserve user-owned content before applying it; migration does not invent historical ownership metadata."),
      ] },
    ],
  },
  {
    slug: "cli-reference",
    title: "CLI reference",
    group: "Reference",
    summary: "The main commands and options, with inspection and writing behavior made explicit.",
    sources: ["src/cli/main.py", "src/cli/create.py", "src/cli/exports.py", "docs/human-guide.md"],
    sections: [
      { id: "commands", title: "Commands", blocks: [
        table(["Command", "Behavior"], [
          ["create TYPE NAME", "Generate a new project; omitted type/name starts interactive prompts"],
          ["adopt PATH --check", "Read-only conformance and recorded-drift report"],
          ["drift PATH", "Read-only classed drift report"],
          ["plan PATH", "Read-only managed-document diff"],
          ["plan PATH --ownership", "Read-only ownership inspection"],
          ["migrate PATH", "Preview a manifest migration; --apply writes it"],
          ["export backstage PATH", "Write or refresh catalog-info.yaml"],
          ["export external-io PATH --input FILE", "Validate a declaration and print JSON; --format markdown prints Markdown"],
          ["install", "Manage the launcher and optional PATH setup"],
          ["upgrade", "Update the installation"],
          ["uninstall", "Remove the installation; inspect --help before using"],
          ["telemetry status / enable / disable / reset-id", "Inspect or change local telemetry preferences"],
          ["version / --version", "Show the installed version"],
        ]),
        code("kickstart --help\nkickstart create --help\nkickstart plan --help", "Ask your installed version"),
      ] },
      { id: "create-options", title: "Create options", blocks: [
        table(["Option", "Meaning"], [
          ["--root, -r", "Parent directory for the generated project"],
          ["--lang, -l", "Language; defaults to python, subject to project-type support"],
          ["--runtime", "Service execution model or system platform profile"],
          ["--framework", "Python HTTP framework; fastapi by default, or minimal"],
          ["--database", "Supported postgres or sqlite extension"],
          ["--cache", "Supported redis extension"],
          ["--auth", "Supported jwt extension"],
          ["--cloud", "System provider target; defaults to multi"],
          ["--workspace-tooling", "System root tooling: none or bun-turbo"],
          ["--knowledge", "External metadata: none, obsidian, backstage, or both"],
          ["--helm", "Add Helm artifacts for a supported service/system"],
          ["--gh", "Create a GitHub repo; requires GitHub access"],
        ]),
        p("Options are not freely interchangeable across every stack. The project guide lists implemented runtime and extension combinations; unsupported combinations fail explicitly."),
      ] },
      { id: "machine-output", title: "Machine-readable reports", blocks: [
        p("adopt --check, drift, and plan support --json. Use the exit status and report together; a nonzero result may represent an expected conformance gap rather than a crashed command. Check the installed command's --help for its exact contract."),
      ] },
    ],
  },
  {
    slug: "configuration",
    title: "Configuration and privacy",
    group: "Reference",
    summary: "Control where a scaffold is written, what metadata is added, and whether eligible commands send telemetry.",
    sources: ["src/cli/create.py", "docs/operations/install-binaries.md", "docs/contracts/telemetry.md"],
    sections: [
      { id: "project-inputs", title: "Project inputs", blocks: [
        p("Pass the type and name for a noninteractive invocation. --root selects the parent directory, while --lang, --runtime, --cloud, and the extension options describe the intended scaffold. Inspect the resulting scaffold.json rather than assuming an option produced an integration."),
        code("kickstart create system platform --cloud aws --runtime kubernetes --knowledge none --root ./projects"),
      ] },
      { id: "knowledge", title: "External knowledge metadata", blocks: [
        p("--knowledge defaults to none. obsidian, backstage, and both add metadata for external knowledge systems. This option does not turn baseline project documentation or scaffold.json on and off."),
      ] },
      { id: "telemetry", title: "Telemetry controls", blocks: [
        code("kickstart telemetry status\nkickstart telemetry disable"),
        list("DO_NOT_TRACK=1 disables telemetry for that process.", "KICKSTART_TELEMETRY_DISABLED=1 is the kickstart-specific process opt-out.", "kickstart telemetry disable persists an opt-out for later commands.", "Release builds carry public capture configuration; direct Git source installs do not bundle it."),
        p("Use a process opt-out during installation if you want to suppress the install command's first eligible event. Read the telemetry contract for the actual event and field inventory rather than treating these events as complete installation or upgrade counts."),
      ] },
      { id: "secrets", title: "Runtime secrets stay outside the scaffold", blocks: [
        p("Generated environment examples and runtime configuration are starting points. Supply real application secrets through the runtime's supported secret mechanism, keep them out of Git, and verify external services separately. kickstart does not provision those services merely because their files are present."),
      ] },
    ],
  },
  {
    slug: "troubleshooting",
    title: "Troubleshooting",
    group: "Reference",
    summary: "Start with the failing command, the installed version, and the actual generated project.",
    sources: ["README.md", "docs/operations/install-binaries.md", "docs/human-guide.md"],
    sections: [
      { id: "command-not-found", title: "kickstart: command not found", blocks: [
        p("The default launcher is ~/.local/bin/kickstart. Open a new terminal after accepting the installer's PATH update. If it still fails, check that the launcher exists and your shell PATH includes its directory."),
        code("~/.local/bin/kickstart --version"),
      ] },
      { id: "wrong-package", title: "The command does not match these docs", blocks: [
        code("kickstart --version\nkickstart --help"),
        p("Check the installed version and installation source. The PyPI package named kickstart belongs to a different project. Install this project's release binary or use the documented Git URL. Use your installed command's --help when comparing versions."),
      ] },
      { id: "unsupported-stack", title: "An option combination is rejected", blocks: [
        p("Check the project guide's language, runtime, and extension matrix. For example, Cloudflare Workers require TypeScript or Rust; the container database and cache extensions are not general Worker options. Cloudflare Containers are not implemented."),
        links({ title: "Choose a supported stack", href: "/docs/project-types", description: "Project types, runtimes, and extension combinations." }),
      ] },
      { id: "checks-fail", title: "The generated checks fail", blocks: [
        p("Run the exact command from the generated README in the project directory. Verify the selected language toolchain is installed. Read the first failing step: dependency/network failures, type errors, and failed assertions need different fixes."),
        p("For the get-started Worker, make check needs Bun and make. make dev prints the local address. A local success does not verify production credentials or a cloud deployment."),
      ] },
      { id: "get-help", title: "Report a useful problem", blocks: [
        list("Include kickstart --version, your OS/architecture, and the exact generation or inspection command.", "Include the first relevant error and the expected result.", "Use a minimal reproduction. Remove credentials, personal paths, and private application data before sharing logs."),
        links({ title: "GitHub issues", href: "https://github.com/woud420/kickstart/issues", description: "Search existing reports or open a reproducible issue." }),
      ] },
    ],
  },
];

export const docGroups = ["Get started", "Guides", "Reference"] as const;

export function docPath(page: DocPage): string {
  return `/docs/${page.slug}`;
}

export function findDocPage(slug: string): DocPage | undefined {
  return documentationPages.find((page) => page.slug === slug);
}
