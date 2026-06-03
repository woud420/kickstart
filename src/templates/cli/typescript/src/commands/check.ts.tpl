import { BaseCommand } from "../base-command.js";
import { loadConfig } from "../config/index.js";
import { check } from "../operations/index.js";
import { formatCheckResult } from "../output/index.js";

export default class Check extends BaseCommand {
  static summary = "Run a scaffold smoke check.";

  async run(): Promise<void> {
    try {
      await this.parse(Check);
      const result = check(loadConfig());
      this.log(formatCheckResult(result));
    } catch (error) {
      this.handleCliError(error);
    }
  }
}
