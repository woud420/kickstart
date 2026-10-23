import { commandExamples } from "../site/content";
import { exampleTree, formatCommand, renderOutputTreeHtml } from "../site/format";
import { copyScript } from "./copy-script";

const examples = Object.fromEntries(
  commandExamples.map((example) => [
    example.key,
    {
      command: example.command,
      display: formatCommand(example.command),
      outputHtml: renderOutputTreeHtml(exampleTree(example)),
      summary: example.summary,
      title: example.title,
    },
  ]),
);

export const siteScript = `
const examples = ${JSON.stringify(examples)};
const tabs = Array.from(document.querySelectorAll(".pick"));
const panel = document.querySelector("#example-panel");
const command = document.querySelector("#command");
const title = document.querySelector("#command-title");
const outputTree = document.querySelector("#output-tree");
const summary = document.querySelector("#example-summary");
const componentMaps = Array.from(document.querySelectorAll("#component-map [data-example]"));

function selectExample(key, focusTab = false) {
  const example = examples[key];
  const activeTab = tabs.find((tab) => tab.getAttribute("data-command") === key);
  if (!example || !activeTab) {
    return false;
  }

  tabs.forEach((tab) => {
    const isActive = tab === activeTab;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-selected", String(isActive));
    tab.tabIndex = isActive ? 0 : -1;
  });
  panel.setAttribute("aria-labelledby", activeTab.id);
  title.textContent = example.title;
  command.textContent = example.display;
  command.setAttribute("data-copy", example.command);
  // outputHtml is escaped server-side from content.ts; it only adds spans.
  outputTree.innerHTML = example.outputHtml;
  summary.textContent = example.summary;
  componentMaps.forEach((map) => {
    map.classList.toggle("is-active", map.getAttribute("data-example") === key);
  });
  if (focusTab) {
    activeTab.focus();
  }
  return true;
}

function activate(tab, focusTab) {
  const key = tab.getAttribute("data-command");
  if (selectExample(key, focusTab)) {
    window.history.replaceState(null, "", "#" + key);
  }
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => activate(tab, false));
  tab.addEventListener("keydown", (event) => {
    const last = tabs.length - 1;
    const targets = {
      ArrowRight: index === last ? 0 : index + 1,
      ArrowLeft: index === 0 ? last : index - 1,
      Home: 0,
      End: last,
    };
    const target = targets[event.key];
    if (target === undefined) {
      return;
    }
    event.preventDefault();
    activate(tabs[target], true);
  });
});

selectExample(window.location.hash.slice(1));

${copyScript}
`;
