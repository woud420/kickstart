variable "name" {
  type = string
}

variable "environment" {
  type = string
}

variable "clouds" {
  type = list(string)
}

locals {
  edge_enabled = contains(var.clouds, "cloudflare")

  summary = {
    name         = var.name
    environment  = var.environment
    clouds       = var.clouds
    runtime      = "containerized-service"
    edge_enabled = local.edge_enabled
  }
}

output "summary" {
  value = local.summary
}
