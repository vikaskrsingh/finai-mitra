import streamlit as st
from google.cloud import storage, vision_v1p3beta1 as vision
import os
import io
import logging
from pypdf import PdfReader
from typing import Optional, Tuple

from src.config import GCP_PROJECT_ID, GCS_BUCKET_NAME, TEMP_UPLOAD_DIR
from src.utils.gcp_clients import get_vision_client
from src.constants import SUPPORTED_FILE_TYPES

logger = logging.getLogger(__name__)

# Ensure temp directory exists
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

@st.cache_resource
def get_gcs_client():
    """Initializes and returns a Google Cloud Storage client."""
    try:
        client = storage.Client(project=GCP_PROJECT_ID)
        logger.info("Google Cloud Storage client initialized.")
        return client
    except Exception as e:
        logger.exception(f"Failed to initialize GCS client: {e}")
        st.error(f"Failed to initialize Google Cloud Storage: {e}. Check your GCP credentials and project ID.")
        return None

def upload_to_gcs(uploaded_file) -> Optional[str]:
    """Uploads a file to Google Cloud Storage."""
    client = get_gcs_client()
    if not client:
        return None

    bucket = client.bucket(GCS_BUCKET_NAME)
    blob_name = os.path.join("uploads", uploaded_file.name) # Use a subfolder in GCS
    blob = bucket.blob(blob_name)

    try:
        blob.upload_from_file(uploaded_file, rewind=True) # Rewind the file pointer after reading
        logger.info(f"File '{uploaded_file.name}' uploaded to GCS as '{blob_name}'.")
        return blob.public_url # Or gs://bucket/blob_name if you prefer
    except Exception as e:
        logger.exception(f"Failed to upload file '{uploaded_file.name}' to GCS: {e}")
        st.error(f"Failed to upload file to Google Cloud Storage: {e}")
        return None

def delete_from_gcs(blob_path: str):
    """Deletes a blob from Google Cloud Storage."""
    client = get_gcs_client()
    if not client:
        return

    # Extract bucket name and blob path from the URL
    # Assuming blob_path is like 'https://storage.googleapis.com/your-bucket/uploads/your-file.pdf'
    if blob_path.startswith("https://storage.googleapis.com/"):
        parts = blob_path.replace("https://storage.googleapis.com/", "").split("/", 1)
        if len(parts) == 2:
            bucket_name = parts[0]
            blob_name = parts[1]
        else:
            logger.warning(f"Could not parse GCS blob path from URL: {blob_path}")
            return
    elif blob_path.startswith("gs://"):
        parts = blob_path.replace("gs://", "").split("/", 1)
        if len(parts) == 2:
            bucket_name = parts[0]
            blob_name = parts[1]
        else:
            logger.warning(f"Could not parse GCS blob path from gs:// URI: {blob_path}")
            return
    else:
        logger.warning(f"Unsupported GCS blob path format for deletion: {blob_path}")
        return

    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        logger.info(f"File '{blob_name}' deleted from GCS bucket '{bucket_name}'.")
    except Exception as e:
        logger.exception(f"Failed to delete file '{blob_name}' from GCS: {e}")
        # Not showing error to user as it's a background cleanup

def extract_text_from_pdf(uploaded_file) -> str:
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        logger.info(f"Text extracted from PDF. Length: {len(text)}")
        return text
    except Exception as e:
        logger.exception(f"Error extracting text from PDF: {e}")
        st.error(f"Error processing PDF: {e}. Please ensure it's a valid PDF.")
        return ""

def extract_text_from_image_gcs(gcs_uri: str) -> str:
    """Performs OCR on an image stored in GCS using Cloud Vision API."""
    vision_client = get_vision_client()
    if not vision_client:
        return ""

    image = vision.Image(source=vision.ImageSource(image_uri=gcs_uri))
    try:
        logger.info(f"Performing OCR on image from GCS URI: {gcs_uri}")
        response = vision_client.document_text_detection(image=image)
        full_text_annotation = response.full_text_annotation
        if full_text_annotation:
            logger.info(f"OCR successful. Text length: {len(full_text_annotation.text)}")
            return full_text_annotation.text
        logger.warning("No text detected by OCR for the image.")
        return ""
    except Exception as e:
        logger.exception(f"Error during Cloud Vision OCR from GCS: {e}")
        st.error(f"Error performing OCR on image: {e}. Ensure image is clear and text is readable.")
        return ""

def get_text_from_input_source(uploaded_file, pasted_text: str) -> str:
    """
    Determines the input source (file upload or pasted text) and extracts text.
    Handles PDF, image OCR via GCS, and direct text input.
    """
    document_text = ""
    st.session_state.uploaded_file_info = None # Reset file info

    if uploaded_file:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        st.session_state.uploaded_file_info = {
            "name": uploaded_file.name,
            "type": uploaded_file.type,
            "extension": file_extension
        }
        logger.info(f"Uploaded file: {uploaded_file.name}, Type: {uploaded_file.type}")

        if file_extension not in SUPPORTED_FILE_TYPES:
            st.error(f"Unsupported file type: .{file_extension}. Please upload a PDF, PNG, JPG, or JPEG.")
            logger.warning(f"Unsupported file type uploaded: .{file_extension}")
            return ""

        if file_extension == "pdf":
            document_text = extract_text_from_pdf(uploaded_file)
        elif file_extension in ["png", "jpg", "jpeg"]:
            with st.spinner("Uploading image to GCS for OCR..."):
                uploaded_file.seek(0) # Ensure file pointer is at the beginning
                gcs_uri = upload_to_gcs(uploaded_file)
            if gcs_uri:
                with st.spinner("Performing OCR on image..."):
                    document_text = extract_text_from_image_gcs(gcs_uri)
                delete_from_gcs(gcs_uri) # Clean up the uploaded image from GCS
            else:
                st.error("Failed to upload image for OCR.")
                document_text = "" # Ensure text is empty if upload fails
        else:
            st.error("Unhandled file type, this should not happen due to prior check.")
            logger.error(f"Unhandled file type '{file_extension}' reached text extraction.")

    elif pasted_text:
        document_text = pasted_text
        logger.info(f"Text pasted by user. Length: {len(document_text)}")

    return document_text