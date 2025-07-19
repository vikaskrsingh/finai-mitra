variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region to deploy resources."
  type        = string
  default     = "us-central1" # Or your preferred region
}

variable "app_name" {
  description = "The name of your application, used for resource naming."
  type        = string
  default     = "finai-mitra"
}

variable "gcs_document_bucket_name" {
  description = "Name for the GCS bucket to store uploaded documents."
  type        = string
  default     = "finai-mitra-docs-bucket" # This will be the bucket used by your app
}

variable "artifact_registry_repo_name" {
  description = "Name for the Artifact Registry repository for Docker images."
  type        = string
  default     = "finai-mitra-repo"
}

variable "cloud_run_service_name" {
  description = "Name for the Cloud Run service."
  type        = string
  default     = "finai-mitra-app"
}