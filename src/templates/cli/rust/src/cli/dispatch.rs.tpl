use clap::Parser;

use crate::cli::args::{Cli, Command};
use crate::error::CliError;
use crate::{config, operations, output};

pub fn run() -> Result<(), CliError> {
    execute(Cli::parse())
}

pub fn execute(cli: Cli) -> Result<(), CliError> {
    match cli.command {
        Command::Check => {
            let config = config::load();
            let result = operations::check(&config)?;
            output::print_text(&format!("{}: {}", result.status, result.endpoint));
        }
    }
    Ok(())
}
