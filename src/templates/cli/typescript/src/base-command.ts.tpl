import { Command } from "@oclif/core";

import { CliError } from "./error/index.js";

export abstract class BaseCommand extends Command {
  protected handleCliError(error: unknown): never {
    if (error instanceof CliError) {
      this.error(error.message, { exit: error.exitCode });
    }
    throw error;
  }
}
