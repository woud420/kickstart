import {
  commandExamples,
  defaultProjectMeta,
  installCommand,
  installNotes,
  installPlatforms,
  isNotPoints,
  isPoints,
  type GeneratedComponent,
  type PositioningPoint,
  type ProjectMeta,
  type ReleaseNote,
  releaseNotes,
} from "./content";
import { escapeHtml, exampleTree, formatCommand, renderOutputTreeHtml } from "./format";
import { renderCopyButton, renderPageHead, renderPageScripts, renderSiteHeader } from "./shell";

const firstExample = commandExamples[0] ?? {
  key: "worker",
  label: "cf worker",
  title: "cloudflare worker",
  command: "kickstart create service edge-site --lang typescript --runtime cloudflare-workers",
  summary: "Writes a TypeScript Worker with Wrangler config, strict TypeScript, tests, and deploy commands.",
  output: ["wrangler.toml", "src/index.ts", "tests/worker.test.ts"],
  components: [
    {
      label: "HTTP fetch handler",
      detail: "src/index.ts routes requests.",
    },
  ],
};

function lineCount(text: string): number {
  return text.split("\n").length;
}

// Reserve room for the tallest command and tree so switching tabs never
// shifts the page.
const commandLines = Math.max(...commandExamples.map((example) => lineCount(formatCommand(example.command))));
const shapeLines = Math.max(...commandExamples.map((example) => lineCount(exampleTree(example))));

function renderPositioningPoints(points: PositioningPoint[]): string {
  return points
    .map(
      (point) => `
            <li class="positioning-point">
              <h4>${escapeHtml(point.title)}</h4>
              <p>${escapeHtml(point.body)}</p>
            </li>`,
    )
    .join("");
}

function renderCommandButtons(): string {
  return commandExamples
    .map((example, index) => {
      const isActive = index === 0;
      const key = escapeHtml(example.key);
      return `<button class="pick bracketed${isActive ? " active" : ""}" id="tab-${key}" data-command="${key}" type="button" role="tab" aria-selected="${isActive}" aria-controls="example-panel" tabindex="${isActive ? "0" : "-1"}">${escapeHtml(example.label)}</button>`;
    })
    .join("");
}

function currentReleaseNote(meta: ProjectMeta): ReleaseNote {
  return {
    version: meta.latestVersion,
    title: "Release assets",
    body: "GitHub Releases carry notes, optional Python package publishing, and Linux/macOS binary assets for this tag.",
    highlights: [
      "Installable Linux and macOS assets are attached to GitHub Releases.",
      "Website metadata is resolved from release configuration at deploy time.",
    ],
  };
}

function releaseNotesFor(meta: ProjectMeta): ReleaseNote[] {
  if (releaseNotes.some((entry) => entry.version === meta.latestVersion)) {
    return releaseNotes;
  }

  return [currentReleaseNote(meta), ...releaseNotes];
}

// Backtick spans in curated copy render as inline code; short ones never
// break across lines.
function renderInlineCode(text: string): string {
  return text
    .split("`")
    .map((part, index) => {
      if (index % 2 === 0) {
        return escapeHtml(part);
      }
      return part.length <= 32 ? `<code class="nowrap">${escapeHtml(part)}</code>` : `<code>${escapeHtml(part)}</code>`;
    })
    .join("");
}

function renderReleaseHighlights(highlights: string[]): string {
  return highlights.map((highlight) => `<li>${renderInlineCode(highlight)}</li>`).join("");
}

// The newest release is open; older ones collapse so the changelog
// supports the page instead of becoming most of it.
function renderReleaseNotes(meta: ProjectMeta): string {
  return releaseNotesFor(meta)
    .map(
      (entry, index) => `
          <details class="release-note"${index === 0 ? " open" : ""}>
            <summary>
              <span class="release-note-version">v${escapeHtml(entry.version)}</span>
              <span class="release-note-title">${escapeHtml(entry.title)}</span>
            </summary>
            <div class="release-note-body">
              <p>${renderInlineCode(entry.body)}</p>
              <ul class="release-highlights">
                ${renderReleaseHighlights(entry.highlights)}
              </ul>
            </div>
          </details>`,
    )
    .join("");
}

function releaseMetaText(meta: ProjectMeta): string {
  if (meta.latestVersion === meta.supportedFrom) {
    return "Support starts with this release line.";
  }

  return `Support starts at v${meta.supportedFrom}.`;
}

function renderComponentMap(components: GeneratedComponent[]): string {
  return components
    .map(
      (component) => `
                  <li class="component-node${component.agent ? " is-agent" : ""}">
                    <strong class="component-label">${escapeHtml(component.label)}</strong>
                    <span class="component-detail">${escapeHtml(component.detail)}</span>
                  </li>`,
    )
    .join("");
}

// Long install URLs wrap at path segments, never mid-word, and the pipe
// stays with the shell it feeds.
function renderBreakableCommand(command: string): string {
  return escapeHtml(command)
    .replace(/([^:/])\/(?=[^/])/g, "$1/<wbr>")
    .replace(/ \| (\S+)$/, ' <span class="nowrap">| $1</span>');
}

// Every example's map is in the page, stacked in one grid cell, so the
// panel always reserves the tallest map and switching tabs never moves it.
function renderComponentMaps(): string {
  const examples = commandExamples.length > 0 ? commandExamples : [firstExample];
  return examples
    .map(
      (example, index) => `
                  <ul class="component-flow${index === 0 ? " is-active" : ""}" data-example="${escapeHtml(example.key)}">
${renderComponentMap(example.components)}
                  </ul>`,
    )
    .join("");
}

function renderInstall(id: string): string {
  return `<div class="install" role="group" aria-labelledby="${id}-label">
            <div class="install-head">
              <span class="install-label" id="${id}-label">Install</span>
              ${renderCopyButton(id, "Copy install command")}
            </div>
            <pre><code id="${id}" data-copy="${escapeHtml(installCommand)}">${renderBreakableCommand(installCommand)}</code></pre>
            <p class="install-platforms">${escapeHtml(installPlatforms)} · verifies SHA-256</p>
          </div>`;
}

export function renderSiteHtml(meta: ProjectMeta = defaultProjectMeta): string {
  const version = escapeHtml(meta.latestVersion);
  const repositoryUrl = escapeHtml(meta.repositoryUrl);
  const releaseUrl = escapeHtml(meta.releaseUrl);

  return `<!doctype html>
<html lang="en">
  <head>
    ${renderPageHead(meta, {
      title: "kickstart · starter repos for humans and agents",
      description: "kickstart is a scaffold contract for humans and agents.",
    })}
  </head>
  <body>
    ${renderSiteHeader(meta)}

    <main id="main">
      <section class="hero shell" aria-labelledby="hero-title">
        <div class="hero-copy">
          <h1 id="hero-title">kickstart</h1>
          <p class="tagline">Starter repos for humans and agents.</p>
          <p class="intro">
            Opinionated scaffolds for agent-assisted projects. Files, commands, tests, docs, and boundaries from one project intent.
          </p>
          ${renderInstall("install-command")}
          <p class="link-row">
            <a class="bracketed" href="${repositoryUrl}">github</a>
            <a class="bracketed" href="${releaseUrl}">v${version} release</a>
            <a class="bracketed" href="#install">install notes</a>
          </p>
        </div>

        <div id="examples" class="command-panel">
          <h2 class="visually-hidden">Examples</h2>
          <div class="picker" role="tablist" aria-label="Project examples">
            ${renderCommandButtons()}
          </div>
          <div id="example-panel" role="tabpanel" aria-labelledby="tab-${escapeHtml(firstExample.key)}">
            <p id="example-summary" class="example-summary">${escapeHtml(firstExample.summary)}</p>
            <div class="generated-view">
              <div class="terminal">
                <div class="copy-row">
                  <span id="command-title">${escapeHtml(firstExample.title)}</span>
                  ${renderCopyButton("command", "Copy example command")}
                </div>
                <pre><code id="command" style="--command-lines: ${commandLines}" data-copy="${escapeHtml(firstExample.command)}">${escapeHtml(formatCommand(firstExample.command))}</code></pre>
                <div class="terminal-rule"></div>
                <div class="tree-label"><span>generated shape</span><span class="agent-legend">agent contract</span></div>
                <pre><code id="output-tree" style="--shape-lines: ${shapeLines}">${renderOutputTreeHtml(exampleTree(firstExample))}</code></pre>
              </div>
              <div class="component-map">
                <div class="map-label">component map</div>
                <div id="component-map" class="component-stack">
${renderComponentMaps()}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="positioning" class="shell section positioning-section" aria-labelledby="positioning-title">
        <h2 id="positioning-title">Useful setup. Not architecture.</h2>
        <div class="positioning-grid">
          <div>
            <h3 class="positioning-heading">It is</h3>
            <ul class="argument-list">
${renderPositioningPoints(isPoints)}
            </ul>
          </div>
          <div>
            <h3 class="positioning-heading">It is not</h3>
            <ul class="argument-list">
${renderPositioningPoints(isNotPoints)}
            </ul>
          </div>
        </div>
      </section>

      <section id="release" class="shell section release-section" aria-labelledby="release-title">
        <div class="release-aside">
          <h2 id="release-title">Releases</h2>
          <p class="release-meta">${escapeHtml(releaseMetaText(meta))}</p>
          <p class="link-row">
            <a class="bracketed" href="${releaseUrl}">release notes</a>
            <a class="bracketed" href="${repositoryUrl}">github</a>
            <a class="bracketed" href="${repositoryUrl}/releases">all releases</a>
          </p>
        </div>
        <div class="release-notes">
${renderReleaseNotes(meta)}
        </div>
      </section>

      <section id="install" class="shell section install-section" aria-labelledby="install-title">
        <h2 id="install-title">Install</h2>
        <div>
          ${renderInstall("install-command-again")}
          <ul class="install-notes">
            ${installNotes.map((note) => `<li>${renderInlineCode(note)}</li>`).join("\n            ")}
          </ul>
        </div>
      </section>
    </main>

    <footer class="shell">
      <span>Served by a kickstart Cloudflare Worker.</span>
      <a class="bracketed" href="/healthz">healthz</a>
    </footer>

    ${renderPageScripts(meta, true)}
  </body>
</html>`;
}
