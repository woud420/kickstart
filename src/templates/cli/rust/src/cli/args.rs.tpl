use clap::{Parser, Subcommand};

#[derive(Debug, Parser)]
#[command(
    version,
    about = "{{ service_name }} command line interface",
    arg_required_else_help = true
)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Command,
}

#[derive(Debug, Subcommand)]
pub enum Command {
    /// Run a scaffold smoke check.
    Check,
}
