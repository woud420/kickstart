import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import { App } from "../src/App";

it("renders the project name in the application heading", () => {
  const html = renderToStaticMarkup(<App />);
  expect(html).toContain("<h1>{{ service_name }}</h1>");
  expect(html).not.toContain("{".repeat(2));
});
