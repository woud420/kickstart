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
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(560px, 1.2fr);
  align-items: start;
  gap: 48px;
  padding: 66px 0 72px;
  border-bottom: 1px solid var(--ink);
}

.kicker,
.section-index {
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
  max-width: 620px;
  margin-bottom: 16px;
  font-family: var(--font-display);
  font-size: clamp(52px, 6.4vw, 88px);
  font-weight: 680;
  line-height: 1;
  letter-spacing: 0;
}

.tagline {
  max-width: 520px;
  margin-bottom: 16px;
  font-family: var(--font-body);
  font-size: clamp(25px, 2.4vw, 34px);
  font-weight: 700;
  line-height: 1.18;
}

.intro {
  max-width: 520px;
  margin-bottom: 24px;
  color: var(--muted);
  font-size: 19px;
  line-height: 1.5;
}

.hero-links {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  width: max-content;
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--ink);
  padding: 12px 0;
  font-family: var(--font-mono);
  font-size: 13px;
}

.hero-links span {
  color: var(--accent);
  font-weight: 800;
}

.hero-links a,
.release-actions a {
  text-decoration: none;
}

.hero-links a:hover,
.release-actions a:hover {
  color: var(--accent);
}

.compact-section {
  display: grid;
  grid-template-columns: 190px minmax(0, 1fr);
  gap: 42px;
  padding: 62px 0;
  border-bottom: 1px solid var(--ink);
}

.positioning-section {
  display: block;
  padding: 58px 0 64px;
}

.positioning-section .section-head {
  display: grid;
  grid-template-columns: 170px minmax(0, 1fr);
  gap: 42px;
  align-items: end;
  margin-bottom: 34px;
}

.positioning-section h2 {
  max-width: none;
  font-size: clamp(36px, 4.4vw, 58px);
}

h2 {
  max-width: 640px;
  margin-bottom: 0;
  font-family: var(--font-body);
  font-size: clamp(34px, 4vw, 54px);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: 0;
}

.section-lead {
  max-width: 760px;
  margin-bottom: 32px;
  color: var(--muted);
  font-size: 21px;
  line-height: 1.6;
}

.argument-list {
  border-top: 1px solid var(--ink);
}

.argument,
.positioning-point,
.change {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 28px;
  padding: 22px 0;
  border-bottom: 1px solid var(--soft);
}

.argument h3,
.positioning-point h3,
.change h3 {
  margin-bottom: 4px;
  font-family: var(--font-body);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0;
}

.argument p,
.positioning-point p,
.change p {
  margin-bottom: 0;
  color: var(--muted);
}

.positioning-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 42px;
}

.positioning-heading {
  margin-bottom: 12px;
  color: var(--accent);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 800;
}

.positioning-point {
  grid-template-columns: 1fr;
  gap: 4px;
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

.command-panel {
  border: 1px solid var(--ink);
  background: var(--faint);
}

.generated-view {
  display: grid;
  grid-template-columns: minmax(0, 1.06fr) minmax(250px, 0.94fr);
  min-height: 610px;
}

.picker {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
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

.pick:last-child {
  border-right: 0;
}

.pick.active {
  background: var(--ink);
  color: var(--paper);
}

.terminal {
  padding: 20px;
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
  min-height: 112px;
  padding: 14px 20px;
  border-top: 1px solid var(--ink);
  background: var(--paper);
  color: var(--muted);
  font-size: 15px;
  line-height: 1.5;
}

.component-map {
  padding: 20px;
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
  gap: 12px;
}

.component-node {
  position: relative;
  border: 1px solid var(--ink);
  background: var(--paper);
  padding: 12px;
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
  font-size: 13px;
  line-height: 1.5;
}

#output-tree {
  display: block;
  max-height: 270px;
  overflow: auto;
}

.boundary {
  border-bottom: 0;
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
    grid-template-columns: 1fr;
    min-height: auto;
    padding: 36px 0 46px;
  }

  h1 {
    font-size: 50px;
  }

  .tagline {
    font-size: 26px;
  }

  .compact-section,
  .argument,
  .positioning-point,
  .change {
    grid-template-columns: 1fr;
    gap: 18px;
  }

  .positioning-grid {
    grid-template-columns: 1fr;
  }

  .positioning-section .section-head {
    grid-template-columns: 1fr;
    gap: 10px;
    margin-bottom: 24px;
  }

  .hero-links {
    width: 100%;
  }

  .generated-view {
    grid-template-columns: 1fr;
    min-height: 0;
  }

  .picker {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .pick:nth-child(2n) {
    border-right: 0;
  }

  .pick:nth-child(n + 3) {
    border-top: 1px solid var(--ink);
  }

  .example-summary {
    min-height: 0;
  }

  .component-map {
    border-top: 1px solid var(--ink);
    border-left: 0;
  }

  .compact-section {
    padding: 46px 0;
  }

  h2 {
    font-size: 38px;
  }

  .section-lead {
    font-size: 18px;
  }

  #output-tree {
    max-height: 280px;
  }
}
`;
