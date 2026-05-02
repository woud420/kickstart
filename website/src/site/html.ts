import {
  changelogEntries,
  commandExamples,
  defaultProjectMeta,
  isNotPoints,
  isPoints,
  type ChangelogEntry,
  type GeneratedComponent,
  type PositioningPoint,
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

function renderPositioningPoints(points: PositioningPoint[]): string {
  return points
    .map(
      (point) => `
        <article class="positioning-point">
          <h3>${escapeHtml(point.title)}</h3>
          <p>${escapeHtml(point.body)}</p>
        </article>`,
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
      </div>
      <nav aria-label="Main navigation">
        <a href="#examples">[Example]</a>
        <a href="#positioning">[Position]</a>
        <a href="#release">[Release]</a>
        <a href="${escapeHtml(meta.repositoryUrl)}">[GitHub]</a>
      </nav>
    </header>

    <main>
      <section class="hero shell" aria-labelledby="hero-title">
        <div class="hero-copy">
          <p class="kicker">Opinionated scaffolds for agent-assisted projects.</p>
          <h1 id="hero-title">Kickstart</h1>
          <p class="tagline">Starter repos for humans and agents.</p>
          <p class="intro">
            Files, commands, tests, docs, and boundaries from one project intent.
          </p>
          <div class="hero-links" aria-label="Project links">
            <span>v${escapeHtml(meta.latestVersion)}</span>
            <a href="${escapeHtml(meta.releaseUrl)}">Release notes</a>
            <a href="${escapeHtml(meta.repositoryUrl)}">GitHub</a>
          </div>
        </div>

        <div id="examples" class="command-panel hero-panel">
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
                  <pre><code id="output-tree">${firstExample.output.map((file) => `./${escapeHtml(file)}`).join("\n")}</code></pre>
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
      </section>

      <section id="positioning" class="shell compact-section positioning-section">
        <div class="section-head">
          <div class="section-index">[Position]</div>
          <h2>Useful setup. Not architecture.</h2>
        </div>
        <div>
          <div class="positioning-grid">
            <div>
              <h3 class="positioning-heading">It is</h3>
              <div class="argument-list">
${renderPositioningPoints(isPoints)}
              </div>
            </div>
            <div>
              <h3 class="positioning-heading">It is not</h3>
              <div class="argument-list">
${renderPositioningPoints(isNotPoints)}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="release" class="shell compact-section boundary">
        <div class="section-head">
          <div class="section-index">[Release]</div>
          <h2>v${escapeHtml(meta.latestVersion)}</h2>
        </div>
        <div>
          <div class="release-actions">
            <a href="${escapeHtml(meta.releaseUrl)}">Release notes</a>
            <a href="${escapeHtml(meta.repositoryUrl)}">GitHub</a>
            <a href="${escapeHtml(meta.repositoryUrl)}/releases">All releases</a>
          </div>
          <div class="changelog" aria-label="Small changelog">
${renderChangelog(meta)}
          </div>
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
