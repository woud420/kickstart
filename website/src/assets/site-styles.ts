export const siteStyles = `
:root {
  color-scheme: light;
  --ink: #101010;
  --paper: #f7f4ed;
  --muted: #666158;
  --soft: #ded7ca;
  --faint: #ebe6dc;
  --accent: #a1372f;
  --code: #191815;
  --font-body: "Atkinson Hyperlegible", "Avenir Next", Avenir, ui-sans-serif, system-ui, sans-serif;
  --font-display: "Fraunces", "Iowan Old Style", "Palatino Linotype", Georgia, ui-serif, serif;
  --font-mono: "IBM Plex Mono", "SFMono-Regular", Consolas, ui-monospace, monospace;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
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

a {
  color: inherit;
}

.shell {
  width: min(1080px, calc(100% - 36px));
  margin: 0 auto;
}

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 22px 0 18px;
  border-bottom: 1px solid var(--ink);
  font-family: var(--font-mono);
  font-size: 13px;
}

.brand {
  font-weight: 800;
  text-decoration: none;
}

.status {
  display: block;
  margin-top: 4px;
  color: var(--muted);
}

nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px 16px;
}

nav a {
  text-decoration: none;
}

nav a:hover {
  color: var(--accent);
}

.hero {
  min-height: calc(100vh - 78px);
  padding: 86px 0 92px;
  border-bottom: 1px solid var(--ink);
}

.kicker,
.section-index,
.proof-label {
  margin: 0;
  color: var(--accent);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  max-width: 1040px;
  margin-bottom: 28px;
  font-family: var(--font-display);
  font-size: clamp(56px, 9vw, 126px);
  font-weight: 650;
  line-height: 0.95;
  letter-spacing: 0;
}

.intro {
  max-width: 800px;
  margin-bottom: 42px;
  color: var(--muted);
  font-size: clamp(20px, 2vw, 26px);
  line-height: 1.55;
}

.hero-proof {
  max-width: 520px;
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--ink);
  padding: 16px 0;
}

.hero-proof pre {
  margin-top: 12px;
}

.release-strip {
  display: grid;
  grid-template-columns: max-content max-content max-content max-content;
  align-items: center;
  gap: 12px;
  width: fit-content;
  max-width: 100%;
  margin-bottom: 34px;
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--ink);
  padding: 12px 0;
  font-family: var(--font-mono);
  font-size: 13px;
}

.release-strip span {
  color: var(--muted);
}

.release-strip strong {
  color: var(--accent);
}

.release-strip a,
.release-actions a {
  text-decoration: none;
}

.release-strip a:hover,
.release-actions a:hover {
  color: var(--accent);
}

.split-section {
  display: grid;
  grid-template-columns: 190px minmax(0, 1fr);
  gap: 42px;
  padding: 74px 0;
  border-bottom: 1px solid var(--ink);
}

h2 {
  max-width: 820px;
  margin-bottom: 18px;
  font-family: var(--font-display);
  font-size: clamp(40px, 5vw, 72px);
  font-weight: 620;
  line-height: 1.02;
  letter-spacing: 0;
}

.section-lead {
  max-width: 760px;
  margin-bottom: 32px;
  color: var(--muted);
  font-size: 21px;
  line-height: 1.6;
}

.argument-list,
.proof-grid {
  border-top: 1px solid var(--ink);
}

.argument,
.proof-point,
.change {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 28px;
  padding: 22px 0;
  border-bottom: 1px solid var(--soft);
}

.argument h3,
.proof-point h3,
.change h3 {
  margin-bottom: 4px;
  font-family: var(--font-body);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0;
}

.argument p,
.proof-point p,
.change p {
  margin-bottom: 0;
  color: var(--muted);
}

.release-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 18px;
  margin-bottom: 28px;
  font-family: var(--font-mono);
  font-size: 13px;
}

.release-actions a::before {
  content: "[";
}

.release-actions a::after {
  content: "]";
}

.changelog {
  border-top: 1px solid var(--ink);
}

.change-version {
  color: var(--accent);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 800;
}

.contract-table {
  width: 100%;
  border-collapse: collapse;
  border-top: 1px solid var(--ink);
  font-size: 15px;
}

.contract-table tr {
  border-bottom: 1px solid var(--soft);
}

.contract-table th,
.contract-table td {
  padding: 18px 14px 18px 0;
  text-align: left;
  vertical-align: top;
}

.contract-table th {
  width: 128px;
  font-family: var(--font-mono);
  font-size: 13px;
}

.contract-table td:first-of-type {
  width: 38%;
  font-weight: 700;
}

.contract-table td:last-of-type {
  color: var(--muted);
}

.command-panel {
  border: 1px solid var(--ink);
  background: var(--faint);
}

.generated-view {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(280px, 0.95fr);
}

.picker {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  border-bottom: 1px solid var(--ink);
}

.pick {
  min-height: 44px;
  border: 0;
  border-right: 1px solid var(--ink);
  background: transparent;
  color: var(--ink);
  cursor: pointer;
  font: inherit;
  font-family: var(--font-mono);
  font-size: 13px;
  padding: 0 14px;
}

.pick.active {
  background: var(--ink);
  color: var(--paper);
}

.terminal {
  padding: 24px;
  background: var(--code);
  color: #f8f2e7;
  min-height: 100%;
}

.copy-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
  font-family: var(--font-mono);
  font-size: 13px;
}

.copy-row span {
  color: #d8cfbf;
}

.copy {
  min-height: 32px;
  border: 1px solid #f8f2e7;
  background: transparent;
  color: #f8f2e7;
  cursor: pointer;
  font: inherit;
  padding: 0 10px;
}

.terminal-rule {
  height: 1px;
  margin: 22px 0;
  background: rgba(248, 242, 231, 0.3);
}

.tree-label,
.map-label {
  margin-bottom: 10px;
  color: #d8cfbf;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
}

.example-summary {
  margin: 0;
  padding: 18px 24px;
  border-top: 1px solid var(--ink);
  background: var(--paper);
  color: var(--muted);
  font-size: 16px;
}

.component-map {
  padding: 24px;
  border-left: 1px solid var(--ink);
  background:
    linear-gradient(var(--soft) 1px, transparent 1px),
    linear-gradient(90deg, var(--soft) 1px, transparent 1px),
    var(--faint);
  background-size: 28px 28px;
}

.component-map .map-label {
  color: var(--accent);
}

.component-flow {
  display: grid;
  gap: 14px;
}

.component-node {
  position: relative;
  border: 1px solid var(--ink);
  background: var(--paper);
  padding: 14px;
}

.component-node + .component-node::before {
  position: absolute;
  top: -15px;
  left: 22px;
  width: 1px;
  height: 14px;
  background: var(--ink);
  content: "";
}

.component-node h3 {
  margin-bottom: 4px;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 800;
}

.component-node p {
  margin: 0;
  color: var(--muted);
  font-size: 15px;
  line-height: 1.45;
}

pre {
  overflow-x: auto;
  margin: 0;
  white-space: pre-wrap;
  font-family: var(--font-mono);
  font-size: 14px;
}

.boundary {
  border-bottom: 0;
}

.closing-line {
  margin-top: 36px;
  margin-bottom: 0;
  font-family: var(--font-display);
  font-size: clamp(32px, 5vw, 64px);
  line-height: 1;
  font-weight: 650;
}

footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 26px 0 42px;
  border-top: 1px solid var(--ink);
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 13px;
}

footer a {
  color: var(--ink);
  text-decoration: none;
}

@media (max-width: 820px) {
  .topbar,
  footer {
    flex-direction: column;
  }

  nav {
    justify-content: flex-start;
  }

  .hero {
    min-height: auto;
    padding: 56px 0 68px;
  }

  .split-section,
  .argument,
  .proof-point,
  .change {
    grid-template-columns: 1fr;
    gap: 18px;
  }

  .release-strip {
    grid-template-columns: 1fr;
  }

  .generated-view {
    grid-template-columns: 1fr;
  }

  .component-map {
    border-top: 1px solid var(--ink);
    border-left: 0;
  }

  .split-section {
    padding: 54px 0;
  }

  .contract-table,
  .contract-table tbody,
  .contract-table tr,
  .contract-table th,
  .contract-table td {
    display: block;
    width: 100%;
  }

  .contract-table th {
    padding-bottom: 4px;
  }

  .contract-table td {
    padding: 4px 0 14px;
  }
}
`;
