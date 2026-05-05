import { commandExamples } from "../site/content";

const examples = Object.fromEntries(
  commandExamples.map((example) => [
    example.key,
    {
      command: example.command,
      components: example.components,
      output: example.output.map((file) => `./${file}`).join("\n"),
      summary: example.summary,
      title: example.title,
    },
  ]),
);

export const siteScript = `
const examples = ${JSON.stringify(examples)};
const buttons = Array.from(document.querySelectorAll(".pick"));
const command = document.querySelector("#command");
const title = document.querySelector("#command-title");
const outputTree = document.querySelector("#output-tree");
const summary = document.querySelector("#example-summary");
const componentMap = document.querySelector("#component-map");
const copy = document.querySelector(".copy");

function renderComponents(components) {
  componentMap.replaceChildren();
  components.forEach((component) => {
    const node = document.createElement("article");
    const heading = document.createElement("h3");
    const body = document.createElement("p");
    node.className = "component-node";
    heading.textContent = component.label;
    body.textContent = component.detail;
    node.append(heading, body);
    componentMap.append(node);
  });
}

function selectExample(key) {
  const example = examples[key];
  const activeButton = buttons.find((button) => button.getAttribute("data-command") === key);
  if (!example || !activeButton) {
    return;
  }

  buttons.forEach((button) => {
    button.classList.remove("active");
    button.setAttribute("aria-selected", "false");
  });
  activeButton.classList.add("active");
  activeButton.setAttribute("aria-selected", "true");
  title.textContent = example.title;
  command.textContent = example.command;
  outputTree.textContent = example.output;
  outputTree.scrollTop = 0;
  summary.textContent = example.summary;
  renderComponents(example.components);
}

buttons.forEach((button) => {
  button.addEventListener("click", () => {
    const key = button.getAttribute("data-command");
    selectExample(key);
    window.history.replaceState(null, "", "#" + key);
  });
});

selectExample(window.location.hash.slice(1));

copy.addEventListener("click", async () => {
  await navigator.clipboard.writeText(command.textContent);
  copy.textContent = "copied";
  window.setTimeout(() => {
    copy.textContent = "copy";
  }, 1200);
});
`;
