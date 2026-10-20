import type { CommandExample } from "./content";

export function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

// Renders a command example's advertised paths as a `tree`-style listing.
// Directories with a single child collapse onto one line
// (`.kickstart/scaffold.json`) so the shape stays short enough to scan.

interface TreeNode {
  name: string;
  isDir: boolean;
  children: TreeNode[];
}

function buildTree(paths: string[]): TreeNode[] {
  const root: TreeNode = { name: "", isDir: true, children: [] };
  for (const path of paths) {
    const parts = path.replace(/\/$/, "").split("/");
    let node = root;
    parts.forEach((part, index) => {
      const isLast = index === parts.length - 1;
      let child = node.children.find((candidate) => candidate.name === part);
      if (!child) {
        child = { name: part, isDir: !isLast || path.endsWith("/"), children: [] };
        node.children.push(child);
      }
      node = child;
    });
  }
  return root.children;
}

function collapses(node: TreeNode): node is TreeNode & { children: [TreeNode] } {
  return node.isDir && node.children.length === 1;
}

function label(node: TreeNode): string {
  if (collapses(node)) {
    return `${node.name}/${label(node.children[0])}`;
  }
  return node.isDir ? `${node.name}/` : node.name;
}

function visibleChildren(node: TreeNode): TreeNode[] {
  return collapses(node) ? visibleChildren(node.children[0]) : node.children;
}

function leaves(node: TreeNode): TreeNode[] {
  return node.children.length === 0 ? [node] : node.children.flatMap(leaves);
}

// A folder cut off by the depth limit says how much it holds instead.
function summary(node: TreeNode): string {
  const contents = leaves(node);
  const noun = contents.every((leaf) => !leaf.isDir) ? "files" : "paths";
  return ` (${contents.length} ${noun})`;
}

function renderLines(nodes: TreeNode[], prefix: string, depthLeft: number): string[] {
  return nodes.flatMap((node, index) => {
    const isLast = index === nodes.length - 1;
    const children = visibleChildren(node);
    const line = `${prefix}${isLast ? "└── " : "├── "}${label(node)}`;
    if (children.length > 0 && depthLeft <= 1) {
      return [`${line}${summary(node)}`];
    }
    return [line, ...renderLines(children, `${prefix}${isLast ? "    " : "│   "}`, depthLeft - 1)];
  });
}

export function projectNameFromCommand(command: string): string {
  // `kickstart create <type> <name> ...`
  return command.split(/\s+/)[3] ?? "project";
}

export function renderOutputTree(projectName: string, paths: string[], maxDepth = Infinity): string {
  return [`${projectName}/`, ...renderLines(buildTree(paths), "", maxDepth)].join("\n");
}

// Breaks a long command onto one flag per line with shell continuations so
// it reads like a terminal session; the one-line form stays the copy value.
export function formatCommand(command: string): string {
  const [head = "", ...flags] = command.split(/\s+(?=--)/);
  return [head, ...flags.map((flag) => `    ${flag}`)].join(" \\\n");
}

// The hero shows the top level only, so the panel stays close to the
// height of the copy beside it; folders report what they hold.
export function exampleTree(example: CommandExample): string {
  return renderOutputTree(projectNameFromCommand(example.command), example.output, 1);
}

// Paths a coding agent reads first. The tree marks them so the "for agents"
// half of the pitch is visible in the generated output itself.
const AGENT_PATH = /^(AGENTS\.md|CLAUDE\.md|\.agents\/|\.kickstart\/)/;

export function renderOutputTreeHtml(tree: string): string {
  return tree
    .split("\n")
    .map((line) => {
      const [, prefix = "", label = "", count = ""] = /^([│├└─ ]*)(.*?)( \(\d+ (?:files|paths)\))?$/.exec(line) ?? [];
      const safeLabel = AGENT_PATH.test(label) ? `<span class="agent-path">${escapeHtml(label)}</span>` : escapeHtml(label);
      return count ? `${prefix}${safeLabel} <span class="tree-count">${count.trim()}</span>` : `${prefix}${safeLabel}`;
    })
    .join("\n");
}
