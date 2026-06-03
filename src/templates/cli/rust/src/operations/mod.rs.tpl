use crate::error::CliError;
use crate::model::dto::{CheckResult, CliConfig};

pub fn check(config: &CliConfig) -> Result<CheckResult, CliError> {
    Ok(CheckResult {
        status: "ok",
        endpoint: config.endpoint,
    })
}
