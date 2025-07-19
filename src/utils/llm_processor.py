import streamlit as st
import logging
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded, GoogleAPICallError

from src.utils.gcp_clients import get_gemini_model
from src.config import MAX_SUMMARY_WORDS

logger = logging.getLogger(__name__)

# Define exceptions to retry on (transient errors)
RETRY_EXCEPTIONS = (ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded)

@retry(
    stop=stop_after_attempt(3), # Retry up to 3 times
    wait=wait_fixed(2),         # Wait 2 seconds between retries
    retry=retry_if_exception_type(RETRY_EXCEPTIONS),
    reraise=True # Re-raise the last exception if all retries fail
)
def call_gemini_api(prompt: str, target_language_iso_code: str) -> str:
    """Calls the Gemini API with a given prompt and target language."""
    gemini_model = get_gemini_model()
    if not gemini_model:
        st.error("Gemini model not initialized. Check your GCP configuration.")
        return "Error: AI model not available."

    try:
        # Add target_language instruction only if it's relevant for the prompt
        # The classification prompt does not need a specific language output
        if "Please provide the output in" not in prompt and not "YES" in prompt and not "NO" in prompt:
             full_prompt = f"{prompt}\n\n**Please provide the output in {target_language_iso_code.capitalize()}.**"
        else:
             full_prompt = prompt # For classification, we don't need a specific language output, or it's already in the prompt

        logger.info(f"Calling Gemini API with prompt (first 100 chars): {full_prompt[:100]}...")
        response = gemini_model.generate_content(full_prompt)
        response_text = response.text
        logger.info(f"Gemini API call successful (length: {len(response_text)}).")
        return response_text
    except GoogleAPICallError as e:
        logger.error(f"Gemini API call failed: {e}")
        st.error(f"AI processing failed: {e.message}. Please try again.")
        raise # Re-raise for retry
    except Exception as e:
        logger.error(f"Unexpected error during Gemini API call: {e}")
        st.error(f"An unexpected AI error occurred: {e}. Please try again.")
        raise # Re-raise for retry


def get_summarize_prompt(document_text: str, country: str, target_language_iso_code: str) -> str:
    """Constructs a prompt for document summarization."""
    common_elements = f"Highlight key terms and conditions, like interest rates, repayment periods, and penalties. Keep the summary concise (maximum {MAX_SUMMARY_WORDS} words)."

    if country == "India":
        if target_language_iso_code == "hi": # Use 'hi' for Hindi from constants
            return f"""Summarize the following Indian financial document in simple, colloquial , as if explaining it to a common person in a village. {common_elements}
            Document:
            {document_text}"""
        else: # English for India
            return f"""Summarize the following Indian financial document in simple, plain English, suitable for someone with limited financial literacy. {common_elements}
            Document:
            {document_text}"""
    elif country == "Germany":
        if target_language_iso_code == "de": # Use 'de' for German from constants
            return f"""Fasse das folgende deutsche Finanzdokument prägnant und in klarem, leicht verständlichem Deutsch zusammen. Betone die wichtigsten Bedingungen und Konditionen (z.B. Vertragsdauer, Kündigungsfristen, Kosten). Vermeide übermäßig komplizierte juristische Fachsprache, aber bleibe präzise. {common_elements.replace('words', 'Wörter')}
            Dokument:
            {document_text}"""
        else: # English for Germany
            return f"""Summarize the following German financial document into clear, plain English. Break down complex German terms and sentences. Ensure accuracy while making it accessible to a non-native speaker without a legal background. {common_elements}
            Document:
            {document_text}"""
    # Fallback if country not specifically handled
    return f"Summarize the following financial document in simple {target_language_iso_code.capitalize()} language. {common_elements} Document: {document_text}"


def get_simplify_prompt(document_text: str, country: str, target_language_iso_code: str) -> str:
    """Constructs a prompt for document simplification."""
    if country == "India":
        if target_language_iso_code == "hi":
            return f"""Simplify and rewrite the following Indian financial document text into very easy-to-understand, colloquial . Replace all jargon with simple words and rephrase complex sentences. Focus on clarity for someone with basic literacy.
            Document:
            {document_text}"""
        else: # English for India
            return f"""Simplify and rewrite the following Indian financial document text into very easy-to-understand, plain English. Replace all jargon with simple words and rephrase complex sentences. Focus on clarity for someone with basic literacy.
            Document:
            {document_text}"""
    elif country == "Germany":
        if target_language_iso_code == "de":
            return f"""Vereinfache und schreibe den folgenden Text aus einem deutschen Finanzdokument in klares, präzises und leicht verständliches Deutsch um. Zerlege lange Sätze und komplizierte Fachbegriffe, ohne die Genauigkeit zu verlieren.
            Dokument:
            {document_text}"""
        else: # English for Germany
            return f"""Simplify and rewrite the following German financial document text into clear, plain English. Break down complex German sentences and compound words. Ensure that the meaning is accurately conveyed, making it accessible to a non-native speaker without a legal background.
            Document:
            {document_text}"""
    # Fallback if country not specifically handled
    return f"Simplify and rewrite the following financial document text into very easy-to-understand, plain {target_language_iso_code.capitalize()} language. Document: {document_text}"


def get_qa_prompt(summary: str, question: str, target_language_iso_code: str) -> str:
    """Constructs a prompt for answering questions based on a summary."""
    return f"""
    You are an AI assistant answering questions about a financial document.
    Please answer the following question ONLY based on the provided summary of the document.
    If the answer is not present in the summary, state that you cannot find the answer there clearly in {target_language_iso_code.capitalize()}.

    **Summary of the Document:**
    {summary}

    **Question:**
    {question}

    **Answer in {target_language_iso_code.capitalize()}:**
    """

def get_financial_classification_prompt(document_text: str) -> str:
    """Constructs a prompt to classify if a document is financial."""
    return f"""
    Analyze the following document text.
    Determine if the primary content of this document is related to finance (e.g., banking, loans, investments, insurance, taxes, financial policies, legal agreements with financial implications, pay slips, balance sheets, invoices, financial news, etc.).
    Respond with 'YES' if it is clearly a financial document, and 'NO' if it is not.
    Provide ONLY 'YES' or 'NO' as your answer, with no additional text or explanation.

    Document Text:
    {document_text}
    """

def is_document_financial(document_text: str, current_language_iso_code: str) -> bool:
    """
    Uses the LLM to classify if the document is financial.
    Returns True if financial, False otherwise.
    """
    if not document_text.strip():
        logger.warning("No text provided for financial classification.")
        return False # No text means it can't be financial

    # Take a snippet for classification if the text is very long to save tokens
    # Gemini 1.5 Pro has a large context window, but a snippet is fine for classification
    text_snippet = document_text[:5000] # Increased snippet size for better classification accuracy if document is long

    classification_prompt = get_financial_classification_prompt(text_snippet)
    try:
        # We ask for the output in a general language, but LLM should just return YES/NO
        response = call_gemini_api(classification_prompt, current_language_iso_code)
        response_clean = response.strip().upper()
        if "YES" in response_clean:
            logger.info("Document classified as financial.")
            return True
        elif "NO" in response_clean:
            logger.info("Document classified as non-financial.")
            return False
        else:
            logger.warning(f"Unexpected classification response: '{response_clean}'. Defaulting to non-financial.")
            return False
    except Exception as e:
        logger.error(f"Error during financial classification: {e}")
        # If classification itself fails, we might want to default to allowing it to pass
        # or show a specific error. For now, defaulting to False (not financial)
        st.error("Could not classify document type due to an AI error. Please try again.")
        return False