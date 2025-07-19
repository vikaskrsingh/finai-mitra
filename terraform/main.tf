# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Google Cloud Storage Bucket for Document Uploads
resource "google_storage_bucket" "document_bucket" {
  name          = var.gcs_document_bucket_name
  location      = var.region
  project       = var.project_id
  uniform_bucket_level_access = true # Recommended for security
  force_destroy = false # Set to true carefully for development to allow easy deletion
}

# 2. Artifact Registry Repository for Docker Images
resource "google_artifact_registry_repository" "app_repo" {
  location      = var.region
  repository_id = var.artifact_registry_repo_name
  description   = "Docker repository for FinAI Mitra application images"
  format        = "DOCKER"
  project       = var.project_id
}

# 3. Service Account for Cloud Run (Runtime permissions)
resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.app_name}-cloud-run-sa"
  display_name = "Service account for FinAI Mitra Cloud Run service"
  project      = var.project_id
}

# IAM Bindings for the Cloud Run Service Account
# Permissions needed by your Streamlit app:
# - Cloud Vision API
# - Vertex AI (Generative Language API)
# - Cloud Storage (read/write to document_bucket)
resource "google_project_iam_member" "cloud_run_vision_access" {
  project = var.project_id
  role    = "roles/cloudvision.user"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_vertex_ai_access" {
  project = var.project_id
  # roles/aiplatform.user allows access to Vertex AI models
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_gcs_reader" {
  project = var.project_id
  role    = "roles/storage.objectViewer" # Read objects from any bucket in project
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_gcs_writer" {
  project = var.project_id
  role    = "roles/storage.objectAdmin" # Or storage.objectCreator/storage.objectWriter for specific bucket if preferred
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# 4. Cloud Run Service Definition (minimal, GitHub Actions will update the image)
# We define the service here, but the actual image deployment happens via GitHub Actions.
# The image field here can be a placeholder or a base image.
resource "google_cloud_run_v2_service" "finai_mitra_service" {
  name     = var.cloud_run_service_name
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run_sa.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repo_name}/${var.app_name}:latest" # Placeholder image
      ports {
        container_port = 8080 # Streamlit's default port
      }
      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi" # Adjust based on your app's needs (Gemini API calls can be memory intensive)
        }
      }
      # Environment variables for the Cloud Run service
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.document_bucket.name
      }
      env {
        name  = "VERTEX_AI_LOCATION"
        value = var.region
      }
      env {
        name  = "GEMINI_MODEL_NAME"
        value = "gemini-1.5-pro-preview-0514" # Ensure this matches config.py
      }
      env {
        name  = "LOG_LEVEL"
        value = "INFO" # Or DEBUG, ERROR etc.
      }
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 1 # Adjust for concurrency and expected load
    }
  }

  # Allow unauthenticated access to the Cloud Run service
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated invocations for Cloud Run service
resource "google_cloud_run_v2_service_iam_member" "allow_public_access" {
  name     = google_cloud_run_v2_service.finai_mitra_service.name
  location = google_cloud_run_v2_service.finai_mitra_service.location
  project  = google_cloud_run_v2_service.finai_mitra_service.project
  role     = "roles/run.invoker"
  member   = "allUsers" # Allows public access
}