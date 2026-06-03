import { defaultEndpoint } from "../clients/index.js";

export interface CliConfig {
  name: string;
  version: string;
  endpoint: string;
}

export function loadConfig(): CliConfig {
  return {
    name: "{{ package_name }}",
    version: "0.1.0",
    endpoint: defaultEndpoint(),
  };
}
