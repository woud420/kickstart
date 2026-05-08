mod cli;
mod clients;
mod config;
mod error;
mod model;
mod operations;
mod output;

fn main() {
    if let Err(error) = cli::dispatch::run() {
        eprintln!("{error}");
        std::process::exit(error.exit_code());
    }
}
