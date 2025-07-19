output "cloud_run_service_url" {
  description = "The URL of the deployed Cloud Run service."
  value       = google_cloud_run_v2_service.finai_mitra_service.uri
}

output "artifact_registry_repo_url" {
  description = "The URL of the Artifact Registry Docker repository."
  value       = google_artifact_registry_repository.app_repo.name
}

output "document_bucket_url" {
  description = "The URL of the GCS bucket for documents."
  value       = google_storage_bucket.document_bucket.url
}