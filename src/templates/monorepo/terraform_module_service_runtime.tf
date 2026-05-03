variable "name" {
  type = string
}

variable "environment" {
  type = string
}

variable "provider_targets" {
  type = list(string)
}

locals {
  edge_enabled = contains(var.provider_targets, "cloudflare")

  summary = {
    name             = var.name
    environment      = var.environment
    provider_targets = var.provider_targets
    runtime          = "containerized-service"
    edge_enabled     = local.edge_enabled
  }
}

output "summary" {
  value = local.summary
}
