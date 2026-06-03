#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CliConfig {
    pub endpoint: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CheckResult {
    pub status: &'static str,
    pub endpoint: &'static str,
}
