export const copyScript = `
const copyStatus = document.querySelector("#copy-status");
const resetTimers = new WeakMap();

async function copyFrom(button) {
  const source = document.getElementById(button.getAttribute("data-copy-target"));
  if (!source) {
    return;
  }

  const text = source.getAttribute("data-copy") ?? source.textContent;
  try {
    await navigator.clipboard.writeText(text);
    button.textContent = "copied";
    button.setAttribute("data-state", "copied");
    copyStatus.textContent = "Copied to clipboard.";
  } catch {
    window.getSelection()?.selectAllChildren(source);
    button.textContent = "selected";
    button.setAttribute("data-state", "selected");
    copyStatus.textContent = "The browser blocked the clipboard. The command is selected so you can copy it.";
  }

  window.clearTimeout(resetTimers.get(button));
  resetTimers.set(
    button,
    window.setTimeout(() => {
      button.textContent = "copy";
      button.removeAttribute("data-state");
    }, 1600),
  );
}

document.querySelectorAll("[data-copy-target]").forEach((button) => {
  button.addEventListener("click", () => copyFrom(button));
});
`;
