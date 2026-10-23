export const docsStyles = `
.docs-shell { width: min(1256px, calc(100% - 64px)); margin-inline: auto; }
.docs-wordmark { margin-left: 22px; padding-left: 22px; border-left: 1px solid var(--rule); color: var(--muted); }
.docs-layout { display: grid; grid-template-columns: 210px minmax(0, 690px) 160px; gap: 48px; align-items: start; padding-top: 48px; }
.docs-sidebar { position: sticky; top: 32px; padding-bottom: 36px; }
.docs-nav { display: block; font-size: 14px; line-height: 1.45; }
.docs-nav-group { margin-bottom: 26px; }
.docs-nav-label { margin-bottom: 10px; color: var(--muted); font-family: var(--font-mono); font-size: 10px; font-weight: 400; letter-spacing: .08em; text-transform: uppercase; }
.docs-nav a { display: block; margin: 3px 0; padding: 7px 12px; border-left: 2px solid transparent; text-decoration: none; }
.docs-nav a:hover { color: var(--accent); background: var(--faint); text-decoration: none; }
.docs-nav a[aria-current="page"] { border-color: var(--accent); background: var(--accent-tint); color: var(--accent); font-weight: 700; }
.docs-source-link { display: inline-block; margin-top: 8px; color: var(--muted); font-family: var(--font-mono); font-size: 11px; text-decoration: none; }
.docs-agent-links { padding-top: 20px; border-top: 1px solid var(--rule); }
.docs-agent-links a { font-family: var(--font-mono); font-size: 12px; }
.docs-format { display: inline-block; margin-top: 16px; color: var(--muted); font-family: var(--font-mono); font-size: 10px; text-decoration: none; }
.docs-format:hover { color: var(--accent); }
.docs-menu { display: none; }
.docs-article { min-width: 0; padding-bottom: 64px; outline: none; }
.docs-heading { margin-bottom: 40px; padding-bottom: 30px; border-bottom: 1px solid var(--rule); }
.docs-eyebrow { margin-bottom: 20px; color: var(--accent); font-family: var(--font-mono); font-size: 11px; }
.docs-eyebrow span { margin-inline: 8px; color: var(--muted); }
.docs-heading h1 { margin-bottom: 20px; font-family: var(--font-display); font-size: clamp(32px, 3.4vw, 44px); font-weight: 680; line-height: 1.12; letter-spacing: 0; text-wrap: pretty; }
.docs-lead { margin: 0; color: var(--muted); font-size: 18px; line-height: 1.6; }
.docs-section { margin-bottom: 40px; scroll-margin-top: 28px; }
.docs-section h2 { margin: 0 0 16px; font-family: var(--font-body); font-size: 23px; font-weight: 700; line-height: 1.25; letter-spacing: 0; }
.docs-section h2 a { text-decoration: none; }
.docs-section h2 a:hover { color: var(--accent); }
.docs-section p, .docs-section li { font-size: 16px; line-height: 1.75; }
.docs-section p { margin-bottom: 18px; }
.docs-section ul { padding-left: 22px; }
.docs-section li { margin-bottom: 8px; }
.docs-section p code, .docs-section li code { padding: 2px 5px; background: var(--faint); border-radius: var(--radius-small); font-family: var(--font-mono); font-size: .83em; overflow-wrap: anywhere; }
.docs-code { overflow: hidden; margin: 20px 0; border: 1px solid var(--rule); border-radius: var(--radius); background: var(--code); color: var(--code-ink); }
.docs-code-head { display: flex; align-items: center; justify-content: space-between; padding: 9px 16px; border-bottom: 1px solid var(--code-muted); color: var(--code-muted); font-family: var(--font-mono); font-size: 10px; letter-spacing: .02em; }
.docs-code pre { margin: 0; padding: 18px; overflow-x: auto; font-family: var(--font-mono); font-size: 12px; line-height: 1.8; tab-size: 2; }
.docs-code code { font-family: inherit; }
.docs-note { margin: 24px 0; padding: 16px 20px; border-left: 2px solid var(--accent); background: var(--accent-tint); }
.docs-note p.docs-note-title { margin-bottom: 5px; color: var(--accent); font-size: 14px; font-weight: 700; }
.docs-note p:last-child { margin-bottom: 0; font-size: 14px; }
.docs-table { overflow-x: auto; margin: 20px 0; }
.docs-table table { width: 100%; border-collapse: collapse; font-size: 14px; line-height: 1.6; text-align: left; }
.docs-table th { padding: 12px 12px 12px 0; border-bottom: 1px solid var(--ink); font-weight: 700; }
.docs-table td { padding: 13px 12px 13px 0; border-bottom: 1px solid var(--rule); vertical-align: top; }
.docs-table td:first-child { min-width: 140px; color: var(--accent); font-family: var(--font-mono); font-size: 12px; }
.docs-links { list-style: none; padding: 0 !important; border-top: 1px solid var(--rule); }
.docs-links li { padding: 16px 0; margin: 0; border-bottom: 1px solid var(--rule); }
.docs-links a { display: flex; justify-content: space-between; gap: 12px; color: var(--accent); font-weight: 700; text-decoration: none; }
.docs-links a:hover { text-decoration: underline; }
.docs-links p { margin: 4px 0 0; color: var(--muted); font-size: 14px; }
.docs-outline { position: sticky; top: 32px; }
.docs-outline nav { display: block; font-size: 12px; line-height: 1.5; }
.docs-outline nav a { display: block; padding: 6px 0; color: var(--muted); text-decoration: none; }
.docs-outline nav a:hover { color: var(--accent); }
.docs-outline-note { margin-top: 30px; padding-top: 18px; border-top: 1px solid var(--rule); color: var(--muted); font-size: 12px; line-height: 1.6; }
.docs-footer { margin-top: 48px; padding-top: 22px; border-top: 1px solid var(--rule); color: var(--muted); font-family: var(--font-mono); font-size: 10px; overflow-wrap: anywhere; }
.docs-footer p { margin-bottom: 8px; }
.docs-footer ul { padding: 0; list-style: none; }
.docs-footer li { margin-bottom: 5px; }
.docs-pager { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 32px; padding-top: 22px; border-top: 1px solid var(--rule); font-size: 15px; }
.docs-pager a { color: var(--accent); }
.docs-pager a:last-child { text-align: right; }
.docs-pager span { display: block; margin-bottom: 7px; color: var(--muted); font-family: var(--font-mono); font-size: 10px; }
@media (max-width: 1150px) {
  .docs-layout { grid-template-columns: 190px minmax(0, 1fr); gap: 36px; }
  .docs-outline { display: none; }
}
@media (max-width: 760px) {
  .docs-shell { width: calc(100% - 36px); }
  .docs-body .topbar { gap: 12px; font-size: 12px; }
  .docs-body .topbar nav { gap: 8px; }
  .docs-wordmark { display: none; }
  .docs-layout { display: block; padding-top: 20px; }
  .docs-sidebar { display: none; }
  .docs-menu { display: block; margin-bottom: 34px; border-bottom: 1px solid var(--rule); }
  .docs-menu summary { padding: 8px 0 18px; color: var(--accent); font-family: var(--font-mono); font-size: 12px; cursor: pointer; }
  .docs-menu .docs-nav { padding: 12px 0; }
  .docs-heading { margin-bottom: 30px; padding-bottom: 24px; }
  .docs-heading h1 { font-size: 32px; }
  .docs-lead { font-size: 17px; }
  .docs-section h2 { font-size: 22px; }
  .docs-code pre { padding: 14px; font-size: 11px; white-space: pre-wrap; overflow-wrap: anywhere; }
  .docs-note { padding: 14px 16px; }
}
`;
