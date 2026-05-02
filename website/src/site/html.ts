import {
  changelogEntries,
  commandExamples,
  contractRows,
  defaultProjectMeta,
  problemPoints,
  proofPoints,
  type ChangelogEntry,
  type GeneratedComponent,
  type ProjectMeta,
} from "./content";

const firstExample = commandExamples[0] ?? {
  key: "worker",
  label: "Cloudflare Worker",
  title: "Generate an edge service",
  command: "kickstart create service edge-site --lang typescript --runtime cloudflare-workers",
  summary: "Creates a TypeScript Worker with Wrangler config, strict TypeScript, a health endpoint, tests, and deploy commands.",
  output: ["wrangler.toml", "src/index.ts", "tests/worker.test.ts"],
  components: [
    {
      label: "HTTP fetch handler",
      detail: "src/index.ts routes requests and returns health JSON.",
    },
  ],
};

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderProblemPoints(): string {
  return problemPoints
    .map(
      (point) => `
        <article class="argument">
          <h3>${escapeHtml(point.title)}</h3>
          <p>${escapeHtml(point.body)}</p>
        </article>`,
    )
    .join("");
}

function renderContractRows(): string {
  return contractRows
    .map(
      (row) => `
        <tr>
          <th>${escapeHtml(row.axis)}</th>
          <td>${escapeHtml(row.choice)}</td>
          <td>${escapeHtml(row.reason)}</td>
        </tr>`,
    )
    .join("");
}

function renderCommandButtons(): string {
  return commandExamples
    .map((example, index) => {
      const activeClass = index === 0 ? " active" : "";
      return `<button class="pick${activeClass}" data-command="${escapeHtml(example.key)}" type="button">[${escapeHtml(example.label)}]</button>`;
    })
    .join("");
}

function renderProofPoints(): string {
  return proofPoints
    .map(
      (point) => `
        <article class="proof-point">
          <h3>${escapeHtml(point.title)}</h3>
          <p>${escapeHtml(point.body)}</p>
        </article>`,
    )
    .join("");
}

function currentReleaseEntry(meta: ProjectMeta): ChangelogEntry {
  return {
    version: meta.latestVersion,
    title: "Current release",
    body: "Release notes, Python packages, and Linux/macOS binaries are published from GitHub Releases for this tag.",
  };
}

function changelogFor(meta: ProjectMeta): ChangelogEntry[] {
  if (changelogEntries.some((entry) => entry.version === meta.latestVersion)) {
    return changelogEntries;
  }

  return [currentReleaseEntry(meta), ...changelogEntries];
}

function renderChangelog(meta: ProjectMeta): string {
  return changelogFor(meta)
    .map(
      (entry) => `
        <article class="change">
          <div class="change-version">v${escapeHtml(entry.version)}</div>
          <div>
            <h3>${escapeHtml(entry.title)}</h3>
            <p>${escapeHtml(entry.body)}</p>
          </div>
        </article>`,
    )
    .join("");
}

function renderOutputTree(files: string[]): string {
  return files.map((file) => `./${escapeHtml(file)}`).join("\n");
}

function renderComponentMap(components: GeneratedComponent[]): string {
  return components
    .map(
      (component) => `
        <article class="component-node">
          <h3>${escapeHtml(component.label)}</h3>
          <p>${escapeHtml(component.detail)}</p>
        </article>`,
    )
    .join("");
}

export function renderSiteHtml(meta: ProjectMeta = defaultProjectMeta): string {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Kickstart</title>
    <meta
      name="description"
      content="Kickstart is a scaffold contract for humans and agents."
    />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Fraunces:opsz,wght@9..144,500..800&family=IBM+Plex+Mono:wght@400;500;700&display=swap"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="/assets/site.css" />
  </head>
  <body>
    <header class="shell topbar">
      <div>
        <a class="brand" href="/" aria-label="Kickstart home">Kickstart:</a>
        <span class="status">${escapeHtml(meta.releaseLabel)} v${escapeHtml(meta.latestVersion)} / Cloudflare Worker site</span>
      </div>
      <nav aria-label="Main navigation">
        <a href="#problem">[Problem]</a>
        <a href="#contract">[Contract]</a>
        <a href="#generate">[Generate]</a>
        <a href="#release">[Release]</a>
        <a href="#proof">[Proof]</a>
        <a href="#boundary">[Boundary]</a>
        <a href="${escapeHtml(meta.repositoryUrl)}">[GitHub]</a>
      </nav>
    </header>

    <main>
      <section class="hero shell" aria-labelledby="hero-title">
        <p class="kicker">A scaffold contract for humans and agents.</p>
        <h1 id="hero-title">Stop making agents rediscover your project structure.</h1>
        <p class="intro">
          Kickstart turns project intent into a working repo shape: commands, tests, docs, runtime files, CI, and deploy surfaces. The point is not templates. The point is eliminating setup entropy.
        </p>
        <div class="release-strip" aria-label="Project status">
          <span>${escapeHtml(meta.releaseLabel)} version</span>
          <strong>v${escapeHtml(meta.latestVersion)}</strong>
          <a href="${escapeHtml(meta.releaseUrl)}">Release notes</a>
          <a href="${escapeHtml(meta.repositoryUrl)}">GitHub repository</a>
        </div>
        <div class="hero-proof" aria-label="Generated output example">
          <div class="proof-label">generated artifact</div>
          <pre><code>${renderOutputTree(firstExample.output)}</code></pre>
        </div>
      </section>

      <section id="problem" class="shell split-section">
        <div class="section-index">[Problem]</div>
        <div>
          <h2>Every new repo begins with invisible work.</h2>
          <p class="section-lead">
            Someone has to decide the layout, test command, Docker shape, CI file, deploy target, docs, and conventions. When an agent starts from an empty folder, all of that becomes hidden prompt work.
          </p>
          <div class="argument-list">
${renderProblemPoints()}
          </div>
        </div>
      </section>

      <section id="contract" class="shell split-section">
        <div class="section-index">[Contract]</div>
        <div>
          <h2>Kickstart encodes the project shape once.</h2>
          <p class="section-lead">
            A generated project should tell the next human or agent what kind of thing it is, how it runs, how it is tested, and where it can deploy.
          </p>
          <table class="contract-table">
            <tbody>
${renderContractRows()}
            </tbody>
          </table>
        </div>
      </section>

      <section id="generate" class="shell split-section">
        <div class="section-index">[Generate]</div>
        <div>
          <h2>One command should produce something inspectable.</h2>
          <p class="section-lead">
            The examples below show the files and runtime pieces Kickstart creates. They also call out what is only a code hook today, so the scaffold contract is visible instead of implied.
          </p>
          <div class="command-panel">
            <div class="picker" role="tablist" aria-label="Project examples">
              ${renderCommandButtons()}
            </div>
            <div class="generated-view">
              <div>
                <div class="terminal">
                  <div class="copy-row">
                    <span id="command-title">${escapeHtml(firstExample.title)}</span>
                    <button class="copy" type="button">Copy</button>
                  </div>
                  <pre><code id="command">${escapeHtml(firstExample.command)}</code></pre>
                  <div class="terminal-rule"></div>
                  <div class="tree-label">selected generated files</div>
                  <pre><code id="output-tree">${renderOutputTree(firstExample.output)}</code></pre>
                </div>
                <p id="example-summary" class="example-summary">${escapeHtml(firstExample.summary)}</p>
              </div>
              <div class="component-map" aria-label="Generated components">
                <div class="map-label">component map</div>
                <div id="component-map" class="component-flow">
${renderComponentMap(firstExample.components)}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="release" class="shell split-section">
        <div class="section-index">[Release]</div>
        <div>
          <h2>Latest: v${escapeHtml(meta.latestVersion)}</h2>
          <p class="section-lead">
            This site maps the current public version to the project source, release notes, and the scaffold contract.
          </p>
          <div class="release-actions">
            <a href="${escapeHtml(meta.repositoryUrl)}">Open GitHub</a>
            <a href="${escapeHtml(meta.releaseUrl)}">View release</a>
            <a href="${escapeHtml(meta.repositoryUrl)}/releases">All releases</a>
          </div>
          <div class="changelog" aria-label="Small changelog">
${renderChangelog(meta)}
          </div>
        </div>
      </section>

      <section id="proof" class="shell split-section">
        <div class="section-index">[Proof]</div>
        <div>
          <h2>The value is not the landing page.</h2>
          <p class="section-lead">
            Kickstart has value when generated output is boring in the right way: predictable, typed, runnable, and covered by commands that another agent can execute without guessing.
          </p>
          <div class="proof-grid">
${renderProofPoints()}
          </div>
        </div>
      </section>

      <section id="boundary" class="shell split-section boundary">
        <div class="section-index">[Boundary]</div>
        <div>
          <h2>Not every stack. Your stack.</h2>
          <p class="section-lead">
            The weak version of a scaffold tool supports everything shallowly. The useful version is opinionated enough to keep Python, TypeScript, Rust, C++, SQL, Cloudflare, Docker, Kubernetes, and CI coherent.
          </p>
          <p class="closing-line">The contract is simple: generate less uncertainty.</p>
        </div>
      </section>
    </main>

    <footer class="shell">
      <span>Served by a Kickstart Cloudflare Worker.</span>
      <a href="/healthz">[healthz]</a>
    </footer>

    <script src="/assets/site.js" type="module"></script>
  </body>
</html>`;
}
