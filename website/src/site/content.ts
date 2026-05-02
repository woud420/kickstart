export interface CommandExample {
  key: string;
  label: string;
  title: string;
  command: string;
  summary: string;
  output: string[];
  components: GeneratedComponent[];
}

export interface GeneratedComponent {
  label: string;
  detail: string;
}

export interface ProblemPoint {
  title: string;
  body: string;
}

export interface ContractRow {
  axis: string;
  choice: string;
  reason: string;
}

export interface ProofPoint {
  title: string;
  body: string;
}

export interface ProjectMeta {
  latestVersion: string;
  repositoryUrl: string;
  releaseUrl: string;
  releaseLabel: string;
}

export interface ChangelogEntry {
  version: string;
  title: string;
  body: string;
}

export const defaultProjectMeta: ProjectMeta = {
  latestVersion: "0.4.0",
  repositoryUrl: "https://github.com/woud420/kickstart",
  releaseUrl: "https://github.com/woud420/kickstart/releases/tag/v0.4.0",
  releaseLabel: "Latest",
};

export const commandExamples: CommandExample[] = [
  {
    key: "service",
    label: "Python + Redis",
    title: "Generate an API service with clients",
    command: "kickstart create service api --lang python --database postgres --cache redis --auth jwt",
    summary: "Creates a FastAPI-style Python service, Dockerfile, Postgres client/migration code, Redis client code, JWT auth hook, requirements, and test directories. It does not yet create a docker-compose file that runs Redis/Postgres locally.",
    output: [
      "Dockerfile",
      "Makefile",
      "pyproject.toml",
      "requirements.txt",
      ".env.example",
      "src/main.py",
      "src/config/settings.py",
      "src/routes/health.py",
      "src/routes/users.py",
      "src/clients/database.py",
      "src/clients/cache.py",
      "src/handler/auth.py",
      "src/model/repository.py",
      "migrations/001_initial.sql",
      "tests/unit/",
      "tests/integration/",
      "architecture/README.md",
    ],
    components: [
      {
        label: "API process",
        detail: "src/main.py wires the Python HTTP service and generated routes.",
      },
      {
        label: "Postgres client",
        detail: "src/clients/database.py plus migrations/001_initial.sql.",
      },
      {
        label: "Redis client",
        detail: "src/clients/cache.py and redis dependency entries.",
      },
      {
        label: "JWT auth",
        detail: "src/handler/auth.py provides the auth extension hook.",
      },
      {
        label: "Container boundary",
        detail: "Dockerfile builds the app; dependency containers are not generated yet.",
      },
    ],
  },
  {
    key: "worker",
    label: "Cloudflare Worker",
    title: "Generate an edge service",
    command: "kickstart create service edge-site --lang typescript --runtime cloudflare-workers",
    summary: "Creates a TypeScript Worker with Wrangler config, strict TypeScript, a health endpoint, tests, and deploy commands.",
    output: [
      "wrangler.toml",
      "package.json",
      "tsconfig.json",
      "src/index.ts",
      "tests/worker.test.ts",
      "README.md",
      "Makefile",
      "architecture/README.md",
    ],
    components: [
      {
        label: "HTTP fetch handler",
        detail: "src/index.ts routes requests and returns health JSON.",
      },
      {
        label: "Cloudflare runtime",
        detail: "wrangler.toml points the Worker at src/index.ts.",
      },
      {
        label: "Verification",
        detail: "Vitest and TypeScript checks are scaffolded with package scripts.",
      },
    ],
  },
  {
    key: "mono",
    label: "Cloud Workspace",
    title: "Generate a cloud workspace",
    command: "kickstart create mono platform --cloud cloudflare --runtime cloudflare-workers --knowledge none",
    summary: "Creates a workspace shape with apps, packages, infrastructure folders, GitHub Actions, docs, and Cloudflare Worker deployment notes.",
    output: [
      "apps/",
      "packages/",
      "infra/cloudflare/",
      "infra/terraform/",
      ".github/workflows/build.yml",
      ".github/workflows/test.yml",
      ".github/workflows/deploy.yml",
      "docs/architecture/context.md",
      "docs/agents/recommended.md",
      "package.json",
      "turbo.json",
      "tsconfig.base.json",
    ],
    components: [
      {
        label: "Applications",
        detail: "apps/ is the place for deployable services and frontends.",
      },
      {
        label: "Shared packages",
        detail: "packages/ gives agents an obvious boundary for reusable code.",
      },
      {
        label: "Infrastructure",
        detail: "infra/ captures Cloudflare, Terraform, and deployment intent.",
      },
      {
        label: "CI contract",
        detail: ".github/workflows files define build, test, and deploy lanes.",
      },
    ],
  },
  {
    key: "cli",
    label: "Rust CLI",
    title: "Generate a command-line tool",
    command: "kickstart create cli ops-tool --lang rust",
    summary: "Creates a Rust command-line project with Cargo metadata, source entrypoint, test directory, Makefile, README, and architecture notes.",
    output: [
      "Cargo.toml",
      "src/main.rs",
      "tests/",
      "Makefile",
      "README.md",
      "architecture/README.md",
    ],
    components: [
      {
        label: "CLI entrypoint",
        detail: "src/main.rs owns command execution.",
      },
      {
        label: "Cargo project",
        detail: "Cargo.toml defines package metadata and dependencies.",
      },
      {
        label: "Review notes",
        detail: "architecture/README.md explains generated structure.",
      },
    ],
  },
];

export const problemPoints: ProblemPoint[] = [
  {
    title: "Blank repos invite drift",
    body: "Every agent has to infer layout, commands, test strategy, release shape, and deploy surface from scratch.",
  },
  {
    title: "Setup work hides inside the first feature",
    body: "The first real task becomes mixed with Docker, CI, directory naming, dependency choices, and docs.",
  },
  {
    title: "Reviewers cannot trust invisible conventions",
    body: "If the project shape is not encoded, humans review structure and implementation at the same time.",
  },
];

export const contractRows: ContractRow[] = [
  {
    axis: "Shape",
    choice: "service, frontend, library, CLI, monorepo",
    reason: "Start from the kind of thing being built, not a bag of files.",
  },
  {
    axis: "Stack",
    choice: "Python, TypeScript, Rust, C++, SQL",
    reason: "Stay inside the languages this scaffold is meant to keep sharp.",
  },
  {
    axis: "Runtime",
    choice: "container, Kubernetes, Cloudflare Workers",
    reason: "Generated code should already know where it is supposed to run.",
  },
  {
    axis: "Cloud",
    choice: "Cloudflare, AWS, GCP, none",
    reason: "Cloud is a deployment choice, not decoration.",
  },
  {
    axis: "Evidence",
    choice: "tests, docs, CI, release binaries",
    reason: "A scaffold is only useful if the generated project can prove it works.",
  },
];

export const proofPoints: ProofPoint[] = [
  {
    title: "Tests before polish",
    body: "Generated paths are covered by unit and integration tests so refactors can prove behavior did not move.",
  },
  {
    title: "Agent-readable structure",
    body: "Specs, layouts, template plans, and docs make the generated project easy for another agent to inspect.",
  },
  {
    title: "Deploy surfaces included",
    body: "Workers, Docker, Kubernetes, Terraform, GitHub Actions, and release binaries are part of the scaffold contract.",
  },
];

export const changelogEntries: ChangelogEntry[] = [
  {
    version: "0.4.0",
    title: "Modern Python stack and release binaries",
    body: "Updated dependency metadata, added real lint/typecheck/test/build commands, and built installable Linux and macOS binaries in CI.",
  },
  {
    version: "0.4.0",
    title: "Cloudflare as a first-class target",
    body: "Added Cloudflare cloud/runtime scaffolding, including TypeScript and Rust Worker project generation.",
  },
  {
    version: "0.4.0",
    title: "Agent-readable scaffold structure",
    body: "Split specs, layouts, stack registry, template plans, and docs so humans and agents can inspect the generation contract.",
  },
];
