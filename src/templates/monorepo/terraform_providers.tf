{% if include_aws %}
provider "aws" {
  region = var.aws_region
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
