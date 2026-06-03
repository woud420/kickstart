import type { CheckResult } from "../model/dto.js";

export function formatCheckResult(result: CheckResult): string {
  return `${result.status}: ${result.endpoint}`;
}
