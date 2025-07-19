import streamlit as st
# Removed unused import
#from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel
import google.auth
import logging
import vertexai
from src.config import GCP_PROJECT_ID, GCP_REGION, GEMINI_MODEL_NAME

logger = logging.getLogger(__name__)

# --- GCP Client Initialization ---
# Using Streamlit's caching to avoid re-initializing clients on every rerun
# This is crucial for performance and avoiding API rate limits during development

@st.cache_resource
def get_vision_client():
    """Initializes and returns a Google Cloud Vision API client."""
    if not GCP_PROJECT_ID:
        logger.error("GCP_PROJECT_ID is not set. Cannot initialize Vision client.")
        st.error("GCP Project ID is not configured. Please set the GCP_PROJECT_ID in config.py or as an environment variable.")
        return None
    try:
        credentials, project = google.auth.default()
        logger.info("Google Cloud Vision API client initialized.")
        client = get_vision_client.ImageAnnotatorClient(credentials=credentials)
        return client
    except Exception as e:
        logger.exception(f"Failed to initialize Google Cloud Vision API client: {e}")
        st.error(f"Failed to initialize Vision AI: {e}. Check your GCP credentials and project ID.")
        return None

@st.cache_resource
def get_gemini_model():
    """Initializes and returns a Google Vertex AI GenerativeModel (Gemini)."""
    if not GCP_PROJECT_ID:
        logger.error("GCP_PROJECT_ID is not set. Cannot initialize Gemini model.")
        st.error("GCP Project ID is not configured. Please set the GCP_PROJECT_ID in config.py or as an environment variable.")
        return None
    if not GCP_REGION:
        logger.error("GCP_REGION is not set. Cannot initialize Gemini model.")
        st.error("GCP Region is not configured. Please set the GCP_REGION in config.py or as an environment variable.")
        return None
    try:
        # Initialize the Vertex AI SDK
        vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
        model = GenerativeModel("gemini-2.5-flash")  # Use the model name as per your configuration
        # aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
        # model = aiplatform.preview.generative_models.GenerativeModel(GEMINI_MODEL_NAME)
        logger.info(f"Vertex AI GenerativeModel '{GEMINI_MODEL_NAME}' initialized for project '{GCP_PROJECT_ID}' in region '{GCP_REGION}'.")
        return model
    except Exception as e:
        logger.exception(f"Failed to initialize Vertex AI GenerativeModel: {e}")
        st.error(f"Failed to initialize Vertex AI (Gemini): {e}. Check your GCP project ID, region, and ensure Vertex AI API is enabled.")
        return None