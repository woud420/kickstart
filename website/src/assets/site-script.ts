import { commandExamples } from "../site/content";

const examples = Object.fromEntries(
  commandExamples.map((example) => [
    example.key,
    {
      command: example.command,
      components: example.components,
      output: example.output.map((file) => `./${file}`).join("\\n"),
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

buttons.forEach((button) => {
  button.addEventListener("click", () => {
    const key = button.getAttribute("data-command");
    const example = examples[key];
    buttons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    title.textContent = example.title;
    command.textContent = example.command;
    outputTree.textContent = example.output;
    summary.textContent = example.summary;
    renderComponents(example.components);
  });
});

copy.addEventListener("click", async () => {
  await navigator.clipboard.writeText(command.textContent);
  copy.textContent = "Copied";
  window.setTimeout(() => {
    copy.textContent = "Copy";
  }, 1200);
});
`;
