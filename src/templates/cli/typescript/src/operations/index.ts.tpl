import type { CliConfig } from "../config/index.js";
import type { CheckResult } from "../model/dto.js";

export function check(config: CliConfig): CheckResult {
  return {
    status: "ok",
    endpoint: config.endpoint,
  };
}
