use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CliError {
    message: String,
    exit_code: i32,
}

impl CliError {
    pub fn exit_code(&self) -> i32 {
        self.exit_code
    }
}

impl fmt::Display for CliError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}", self.message)
    }
}

impl std::error::Error for CliError {}
