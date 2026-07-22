variable "aws_region" {
  description = "AWS region for lakehouse resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project prefix for resource naming"
  type        = string
  default     = "lakehouse-platform"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}
