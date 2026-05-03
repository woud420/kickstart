terraform {
  required_version = ">= 1.7.0"

{% if provider_targets %}
  required_providers {
{% if include_aws %}
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
{% endif %}
{% if include_gcp %}
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
{% endif %}
{% if include_cloudflare %}
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.19"
    }
{% endif %}
  }
{% endif %}
}

locals {
  name        = "{{ monorepo_name }}"
  environment = "{{ environment }}"
  labels = {
    app         = local.name
    environment = local.environment
    managed_by  = "terraform"
  }
}

{% if include_aws %}
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.labels
  }
}
{% endif %}
{% if include_gcp %}
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}
{% endif %}
{% if include_cloudflare %}
provider "cloudflare" {
  # Prefer CLOUDFLARE_API_TOKEN in local env and CI secrets.
}
{% endif %}

module "service_runtime" {
  source = "../../modules/service_runtime"

  name             = local.name
  environment      = local.environment
  provider_targets = var.provider_targets
}

output "runtime_summary" {
  value = module.service_runtime.summary
}
