# Terraform

Minimal IaC for lakehouse bronze storage on AWS.

## Layout

```
modules/
  storage/     # S3 bronze bucket + pipeline IAM (implemented)
environments/  # dev/prod workspaces (planned)
main.tf        # Root module wiring
```

## Usage

```bash
cd infra/terraform
terraform init
terraform validate
terraform plan -var="environment=dev"
```

Production would add: MWAA/Composer, Iceberg REST catalog, Marquez on ECS/EKS.
