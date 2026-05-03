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
