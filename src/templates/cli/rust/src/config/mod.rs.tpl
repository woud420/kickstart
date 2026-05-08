use crate::clients;
use crate::model::dto::CliConfig;

pub fn load() -> CliConfig {
    CliConfig {
        endpoint: clients::default_endpoint(),
    }
}
