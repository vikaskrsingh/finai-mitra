import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# --- GCP Configuration ---
# Get GCP Project ID from environment variable or hardcode if not set
# It's recommended to set this as an environment variable in production
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "finai-mitra-project")
GCP_REGION = os.getenv("GCP_REGION", "us-central1") # Default region for Vertex AI, Cloud Run, Storage

# --- Application Specific Configuration ---
MAX_SUMMARY_WORDS = 250 # Max words for AI summarization
TEMP_UPLOAD_DIR = "temp_uploads" # Directory to temporarily store uploaded files
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "finai-mitra-docs-bucket") # This MUST match your Terraform bucket name

# --- AI Model Configuration ---
# You can specify the model if needed, or let Vertex AI pick latest compatible
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash") # or "gemini-1.5-pro-preview-0514"

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()