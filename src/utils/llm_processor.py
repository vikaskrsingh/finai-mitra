# src/utils/llm_processor.py

import streamlit as st
import logging
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
from src.config import GCP_PROJECT_ID, GCP_REGION, GEMINI_MODEL_NAME

logger = logging.getLogger(__name__)

# Initialize Vertex AI client (cached)
@st.cache_resource
def get_gemini_model():
    """Initializes and returns the Gemini GenerativeModel."""
    try:
        vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
        return GenerativeModel(GEMINI_MODEL_NAME)
    except Exception as e:
        logger.error(f"Failed to initialize Vertex AI or Gemini model: {e}")
        st.error(f"Failed to initialize AI services. Check GCP Project ID, Region, and API enablement: {e}")
        st.stop() # Stop app if essential AI services can't be initialized

def call_gemini_api(prompt: str, target_language_iso_code: str = "en") -> str:
    """Calls the Gemini API with the given prompt."""
    model = get_gemini_model()
    try:
        # It's good practice to explicitly tell the model the desired output language
        # within the prompt itself, as models are primarily text-based.
        response = model.generate_content([prompt])
        if response.candidates and response.candidates[0].content.parts:
            return "".join(part.text for part in response.candidates[0].content.parts)
        else:
            logger.warning("Gemini generated an empty or unexpected response.")
            return "No response from AI."
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        raise # Re-raise to be caught by Streamlit's error handling

# --- Prompt functions (ensure they use target_language_iso_code) ---

def get_summarize_prompt(document_text: str, country_name: str, target_language_iso_code: str) -> str:
    """Generates a prompt for summarizing a financial document."""
    return f"""
    You are an expert financial analyst. Summarize the following financial document from {country_name}.
    Focus on key financial figures, balances, transactions, and any significant financial details.
    The summary should be concise, in bullet points, and **MUST be in {target_language_iso_code} language**.

    Document Content:
    ---
    {document_text}
    ---
    Summary:
    """

def get_simplify_prompt(document_text: str, country_name: str, target_language_iso_code: str) -> str:
    """Generates a prompt for simplifying a financial document."""
    return f"""
    You are an expert in explaining complex financial concepts simply. Simplify the following financial document from {country_name}.
    Explain it in plain language, avoiding jargon where possible. Highlight the most important aspects for a non-financial audience.
    The explanation should be easy to understand and **MUST be in {target_language_iso_code} language**.

    Document Content:
    ---
    {document_text}
    ---
    Simplified Explanation:
    """

def get_qa_prompt(summary_text: str, question: str, target_language_iso_code: str) -> str:
    """Generates a prompt for answering a question based on a summary."""
    return f"""
    Based on the following financial summary, answer the question. If the answer is not in the summary, state that you don't have enough information.
    The answer **MUST be in {target_language_iso_code} language**.

    Financial Summary:
    ---
    {summary_text}
    ---
    Question: {question}
    Answer:
    """

def is_document_financial(document_text: str, target_language_iso_code: str) -> bool:
    """Checks if a document is financial using the Gemini LLM."""
    model = get_gemini_model()
    prompt = f"""
    Analyze the following document content and determine if it appears to be a financial document (e.g., invoice, bank statement, financial report, loan document, tax form, balance sheet, income statement, insurance policy).
    Respond with 'YES' if it is clearly financial, 'NO' if it is not.
    The response **MUST be in English**.

    Document Content:
    ---
    {document_text}
    ---
    Classification:
    """
    try:
        response_text = call_gemini_api(prompt, "en") # Classification response should always be in English
        return response_text.strip().upper() == "YES"
    except Exception as e:
        logger.error(f"Error during financial document classification: {e}")
        st.error("Could not classify document type due to an AI error. Please try again.")
        return False # Assume not financial if classification fails