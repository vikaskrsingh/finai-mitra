terraform {
  required_version = ">= 1.0" # Specify your Terraform version requirement

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0" # Specify your Google provider version
    }
  }

  # (Optional but Recommended) Remote Backend for State Management
  # This stores your Terraform state in a GCS bucket,
  # crucial for collaboration and CI/CD.
  backend "gcs" {
    bucket  = "finai-mitra-terraform-state-bucket" # REMEMBER TO CREATE THIS BUCKET MANUALLY FIRST!
    prefix  = "terraform/state"
  }
}