output "bronze_bucket_name" {
  description = "S3 bucket for Iceberg bronze tables"
  value       = module.lakehouse_storage.bronze_bucket_name
}

output "pipeline_role_arn" {
  description = "IAM role ARN for orchestration workers"
  value       = module.lakehouse_storage.pipeline_role_arn
}
