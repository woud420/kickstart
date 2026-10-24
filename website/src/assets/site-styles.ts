import { siteTheme } from "../site/theme";

export const siteStyles = `
:root {
  color-scheme: light;
  --ink: ${siteTheme.ink};
  --paper: ${siteTheme.paper};
  --muted: ${siteTheme.muted};
  --rule: ${siteTheme.rule};
  --faint: ${siteTheme.faint};
  --grid: ${siteTheme.rule};
  --code: ${siteTheme.code};
  --code-ink: ${siteTheme.codeInk};
  --code-muted: ${siteTheme.codeMuted};
  --accent: ${siteTheme.accent};
  --accent-tint: ${siteTheme.accentTint};
  --font-body: ${siteTheme.fontBody};
  --font-display: ${siteTheme.fontDisplay};
  --font-mono: ${siteTheme.fontMono};
  --radius: 6px;
  --radius-small: 4px;
  --shell: min(1080px, calc(100% - 36px));
  --section-space: clamp(56px, 7vw, 88px);
}

* {
  box-sizing: border-box;
}

@media (prefers-reduced-motion: no-preference) {
  html {
    scroll-behavior: smooth;
  }
}

body {
  margin: 0;
  color: var(--ink);
  background: var(--paper);
  font-family: var(--font-body);
  font-size: 17px;
  line-height: 1.62;
  text-rendering: optimizeLegibility;
}

::selection {
  background: var(--accent);
  color: var(--paper);
}

a {
  color: inherit;
  text-underline-offset: 0.22em;
  text-decoration-thickness: 1px;
}

:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}

.skip-link {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  padding: 8px 12px;
  background: var(--ink);
  color: var(--paper);
  font-family: var(--font-mono);
  font-size: 13px;
  text-decoration: none;
  transform: translateY(-200%);
}

.skip-link:focus-visible {
  transform: none;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}

.shell {
  width: var(--shell);
  margin: 0 auto;
}

h1,
h2,
h3,
h4,
p {
  margin-top: 0;
}

h1,
h2,
h3,
h4 {
  text-wrap: balance;
}

p,
li {
  text-wrap: pretty;
}

/* Top bar */

.topbar {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 24px;
  padding: 22px 0 18px;
  border-bottom: 1px solid var(--rule);
  font-family: var(--font-mono);
  font-size: 13px;
}

.brand {
  font-weight: 600;
  text-decoration: none;
}

.brand-version {
  margin-left: 10px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}

nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 4px 16px;
}

nav a,
.link-row a {
  text-decoration: none;
}

nav a:hover,
.link-row a:hover {
  color: var(--accent);
  text-decoration: underline;
}

/* Hero */

.hero {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
  align-items: start;
  gap: 56px;
  padding: 72px 0 var(--section-space);
  border-bottom: 1px solid var(--rule);
}

h1 {
  margin-bottom: 18px;
  font-family: var(--font-display);
  font-size: clamp(48px, 5.4vw, 76px);
  font-weight: 680;
  line-height: 1;
  letter-spacing: 0;
}

.tagline {
  max-width: 520px;
  margin-bottom: 16px;
  font-size: clamp(26px, 2.5vw, 34px);
  font-weight: 700;
  line-height: 1.16;
}

.intro {
  max-width: 34ch;
  margin-bottom: 32px;
  color: var(--muted);
  font-size: 19px;
  line-height: 1.5;
}

.install {
  overflow: hidden;
  margin-bottom: 18px;
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  background: var(--paper);
}

.install-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 6px 6px 14px;
  border-bottom: 1px solid var(--rule);
  /* Same treatment as the active example tab: the two places a visitor acts
     carry the accent tint, and the command sits on paper below it. */
  background: var(--accent-tint);
  font-family: var(--font-mono);
  font-size: 12px;
}

.install-label {
  color: var(--accent);
  font-weight: 600;
}

.install pre {
  padding: 14px 14px 10px;
  font-size: 13px;
  line-height: 1.55;
  white-space: pre-wrap;
}

.install pre code {
  display: block;
  padding-left: 2ch;
  text-indent: -2ch;
}

.install-platforms {
  margin: 0;
  padding: 0 14px 12px;
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 12px;
}

.nowrap {
  white-space: nowrap;
}

.install code::before,
#command::before {
  content: "$ ";
  color: var(--accent);
}

#command::before {
  color: var(--code-muted);
}

.link-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 20px;
  margin: 0;
  font-family: var(--font-mono);
  font-size: 13px;
}

.link-row a {
  display: inline-block;
  padding: 6px 0;
}

/* Brackets are the CLI's optional-argument mark; the empty alt text keeps
   screen readers from announcing them. */
.bracketed::before {
  content: "[";
  content: "[" / "";
}

.bracketed::after {
  content: "]";
  content: "]" / "";
}

/* Copy buttons */

.copy {
  min-width: 72px;
  min-height: 36px;
  padding: 0 12px;
  border: 1px solid currentColor;
  background: transparent;
  color: inherit;
  cursor: pointer;
  border-radius: var(--radius-small);
  font-family: var(--font-mono);
  font-size: 13px;
  transition: background-color 160ms ease-out, color 160ms ease-out, border-color 160ms ease-out;
}

.install .copy {
  min-height: 32px;
  border-color: var(--ink);
  background: var(--ink);
  color: var(--paper);
}

.install .copy:hover {
  border-color: var(--accent);
  background: var(--accent);
}

.terminal .copy,
.docs-code .copy {
  border-color: var(--rule);
  background: var(--paper);
  color: var(--ink);
}

.terminal .copy:hover,
.docs-code .copy:hover {
  border-color: var(--muted);
}

.copy[data-state="copied"],
.copy[data-state="selected"] {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--paper);
}

/* Examples panel */

.command-panel {
  overflow: hidden;
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  background: var(--faint);
}

.picker {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-bottom: 1px solid var(--rule);
}

.pick {
  min-height: 44px;
  padding: 0 10px;
  border: 0;
  border-right: 1px solid var(--rule);
  background: transparent;
  color: var(--ink);
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 13px;
  transition: background-color 160ms ease-out, color 160ms ease-out;
}

.pick:last-child {
  border-right: 0;
}

.pick:hover {
  background: var(--grid);
}

.pick.active {
  background: var(--accent-tint);
  color: var(--accent);
  font-weight: 600;
}

.pick:focus-visible {
  outline-offset: -5px;
}

.example-summary {
  min-height: calc(3em + 28px);
  margin: 0;
  padding: 14px 20px;
  border-bottom: 1px solid var(--rule);
  background: var(--paper);
  font-size: 15px;
  line-height: 1.5;
}

.generated-view {
  display: grid;
  grid-template-columns: minmax(0, 1.06fr) minmax(0, 0.94fr);
}

.terminal {
  padding: 20px;
  background: var(--code);
  color: var(--code-ink);
}

.copy-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  color: var(--code-muted);
  font-family: var(--font-mono);
  font-size: 13px;
}

.terminal-rule {
  height: 1px;
  margin: 20px 0;
  background: var(--rule);
}

.tree-label,
.map-label {
  margin: 0 0 10px;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
}

.tree-label {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 4px 12px;
  color: var(--muted);
}

.agent-legend {
  color: var(--accent);
  font-weight: 400;
}

.agent-legend::before {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 6px;
  background: currentColor;
  content: "";
}

.agent-path {
  color: var(--accent);
  font-weight: 600;
}

.tree-count {
  color: var(--muted);
}

.terminal .agent-path {
  color: var(--code-ink);
}

.terminal .agent-legend {
  color: var(--code-ink);
}

.terminal .agent-legend::before {
  background: var(--accent);
}

.terminal .tree-label,
.terminal .tree-count {
  color: var(--code-muted);
}

.terminal pre {
  scrollbar-color: var(--muted) transparent;
}

.map-label {
  color: var(--muted);
}

code {
  font-family: var(--font-mono);
}

pre code {
  font: inherit;
}

pre {
  margin: 0;
  overflow-x: auto;
  white-space: pre-wrap;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.42;
}

#command {
  display: block;
  min-height: calc(var(--command-lines, 1) * 1.42em);
  white-space: pre;
}

#output-tree {
  display: block;
  min-height: calc(var(--shape-lines, 1) * 1.3em);
  line-height: 1.3;
  white-space: pre;
}

.component-map {
  padding: 20px;
  border-left: 1px solid var(--rule);
  background:
    linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px),
    var(--faint);
  background-size: 28px 28px;
}

.component-stack {
  display: grid;
}

.component-stack > .component-flow {
  grid-area: 1 / 1;
}

.component-stack > .component-flow:not(.is-active) {
  visibility: hidden;
}

.component-flow {
  display: grid;
  align-content: start;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.component-node {
  padding: 8px 12px;
  border: 1px solid var(--rule);
  border-radius: var(--radius-small);
  background: var(--paper);
}

.component-label {
  display: block;
  margin-bottom: 2px;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
}

.component-node.is-agent .component-label {
  color: var(--accent);
}

.component-detail {
  display: block;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.4;
}

/* Sections */

.section {
  padding: var(--section-space) 0;
  border-bottom: 1px solid var(--rule);
}

h2 {
  margin-bottom: 0;
  font-family: var(--font-body);
  font-size: clamp(36px, 4.4vw, 58px);
  font-weight: 700;
  line-height: 1.05;
  letter-spacing: -0.015em;
}

.positioning-section h2 {
  margin-bottom: 40px;
}

.positioning-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 56px;
}

.positioning-heading {
  margin-bottom: 12px;
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
}

.argument-list {
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--rule);
  list-style: none;
}

.positioning-point {
  padding: 20px 0;
  border-bottom: 1px solid var(--rule);
}

.positioning-point h4 {
  margin-bottom: 4px;
  font-size: 18px;
  font-weight: 700;
}

.positioning-point p {
  margin-bottom: 0;
  color: var(--muted);
}

.release-section,
.install-section {
  display: grid;
  grid-template-columns: 230px minmax(0, 1fr);
  gap: 56px;
}

.install-section {
  border-bottom: 0;
}

.install-section .install {
  max-width: 640px;
}

.install-notes {
  max-width: 640px;
  margin: 20px 0 0;
  padding-left: 18px;
  color: var(--muted);
}

.install-notes li + li {
  margin-top: 8px;
}

.install-notes code,
.release-note-body code {
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
  padding: 0.08em 0.3em;
  border-radius: 3px;
  background: var(--faint);
  color: var(--ink);
  font-family: var(--font-mono);
  font-size: 0.84em;
  overflow-wrap: anywhere;
}

.release-aside {
  position: sticky;
  top: 32px;
  align-self: start;
}

.release-aside h2,
.install-section h2 {
  margin-bottom: 16px;
  font-size: clamp(30px, 3.4vw, 42px);
}

.release-meta {
  margin: 0 0 12px;
  color: var(--muted);
}

.release-notes {
  border-top: 1px solid var(--rule);
}

.release-note {
  border-bottom: 1px solid var(--rule);
}

.release-note summary {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr) 14px;
  align-items: baseline;
  gap: 20px;
  padding: 20px 0;
  cursor: pointer;
  list-style: none;
}

.release-note summary::-webkit-details-marker {
  display: none;
}

.release-note summary::after {
  width: 12px;
  height: 12px;
  align-self: center;
  background:
    linear-gradient(currentColor, currentColor) center / 12px 1.5px no-repeat,
    linear-gradient(currentColor, currentColor) center / 1.5px 12px no-repeat;
  content: "";
}

.release-note[open] summary::after {
  background: linear-gradient(currentColor, currentColor) center / 12px 1.5px no-repeat;
}

.release-note summary:hover .release-note-title {
  color: var(--accent);
}

.release-note summary:focus-visible {
  outline-offset: -2px;
}

.release-note-version {
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.release-note-title {
  display: block;
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.35;
  transition: color 160ms ease-out;
}

.release-note-body {
  padding: 0 34px 26px 84px;
}

.release-note-body > * {
  max-width: 54ch;
}

.release-note-body p {
  margin-bottom: 0;
}

.release-highlights {
  margin: 14px 0 0;
  padding-left: 18px;
  color: var(--muted);
}

.release-highlights li + li {
  margin-top: 6px;
}

footer {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 18px;
  padding: 26px 0 42px;
  border-top: 1px solid var(--rule);
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 13px;
}

footer a {
  color: var(--ink);
  text-decoration: none;
}

footer a:hover {
  color: var(--accent);
}

@media (max-width: 980px) {
  .hero {
    grid-template-columns: minmax(0, 1fr);
    gap: 40px;
    padding-top: 48px;
  }

  .intro {
    max-width: 46ch;
  }

  .hero-copy {
    max-width: 620px;
  }

  .release-section,
  .install-section {
    grid-template-columns: minmax(0, 1fr);
    gap: 28px;
  }

  .release-aside {
    position: static;
  }
}

@media (max-width: 720px) {
  .topbar {
    flex-direction: column;
    gap: 4px;
    padding: 16px 0 10px;
  }

  nav {
    justify-content: flex-start;
    gap: 0 18px;
  }

  nav a,
  .brand,
  .link-row a {
    display: inline-block;
    padding: 10px 0;
  }

  .hero {
    padding: 36px 0 48px;
  }

  h1 {
    font-size: 50px;
  }

  .tagline {
    font-size: 27px;
  }

  .intro {
    font-size: 18px;
  }

  .install .copy {
    min-height: 40px;
  }

  .generated-view {
    grid-template-columns: minmax(0, 1fr);
  }

  .picker {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .pick:nth-child(2n) {
    border-right: 0;
  }

  .pick:nth-child(n + 3) {
    border-top: 1px solid var(--rule);
  }

  .terminal .copy {
    min-height: 44px;
  }

  #command,
  #output-tree {
    min-height: 0;
  }

  .component-stack > .component-flow:not(.is-active) {
    display: none;
  }

  .component-map {
    border-top: 1px solid var(--rule);
    border-left: 0;
  }

  .positioning-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 32px;
  }

  .positioning-section h2 {
    margin-bottom: 28px;
  }

  .release-note summary {
    grid-template-columns: minmax(0, 1fr) 14px;
    gap: 4px 16px;
  }

  .release-note-version {
    grid-column: 1;
  }

  .release-note-title {
    grid-column: 1;
  }

  .release-note summary::after {
    grid-column: 2;
    grid-row: 1 / span 2;
  }

  .release-note-body {
    padding: 0 0 24px;
  }

  footer {
    flex-direction: column;
    gap: 4px;
  }

  footer a {
    padding: 10px 0;
  }
}
`;
