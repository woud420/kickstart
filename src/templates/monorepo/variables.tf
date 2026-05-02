variable "clouds" {
  description = "Cloud providers enabled for this environment."
  type        = list(string)
  default     = [{% for provider in clouds %}"{{ provider }}"{% if not loop.last %}, {% endif %}{% endfor %}]
}

{% if include_aws %}
variable "aws_region" {
  description = "AWS region for regional resources."
  type        = string
  default     = "us-east-1"
}
{% endif %}

{% if include_gcp %}
variable "gcp_project_id" {
  description = "GCP project id. Required when gcp is enabled."
  type        = string
  default     = ""
}

variable "gcp_region" {
  description = "GCP region for regional resources."
  type        = string
  default     = "us-central1"
}
{% endif %}

{% if include_cloudflare %}
variable "cloudflare_account_id" {
  description = "Cloudflare account id. Required when Cloudflare resources are added."
  type        = string
  default     = ""
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone id for DNS, Workers routes, or Tunnel records when needed."
  type        = string
  default     = ""
}
{% endif %}
