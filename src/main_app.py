import streamlit as st
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

# Import modules from your src package
from src.config import GCP_PROJECT_ID, LOG_LEVEL
from src.utils.document_parser import get_text_from_input_source
from src.utils.llm_processor import call_gemini_api, get_summarize_prompt, get_simplify_prompt, get_qa_prompt, is_document_financial
from src.ui.components import render_header, render_input_section, render_config_section, render_output_section, render_qa_section, render_disclaimer
from src.constants import COUNTRIES, ACTIONS, COUNTRY_LANGUAGES

# Set logging level dynamically
logging.getLogger().setLevel(LOG_LEVEL)

# --- Streamlit App Entry Point ---

def main():
    # Set page config at the very beginning
    st.set_page_config(layout="wide", page_title="FinAI Mitra 🤝")

    # --- Initialize Session State Variables ---
    # These ensure that state persists across reruns of the Streamlit app
    if 'current_summary' not in st.session_state:
        st.session_state.current_summary = ""
    if 'raw_extracted_text' not in st.session_state:
        st.session_state.raw_extracted_text = ""
    if 'uploaded_file_info' not in st.session_state:
        st.session_state.uploaded_file_info = None
    if 'processed_output' not in st.session_state:
        st.session_state.processed_output = ""
    if 'selected_country' not in st.session_state:
        st.session_state.selected_country = COUNTRIES[0] # Default to first country
    if 'selected_language' not in st.session_state:
        # Default to English for the first country
        st.session_state.selected_language = list(COUNTRY_LANGUAGES[st.session_state.selected_country].keys())[0]
    if 'selected_action' not in st.session_state:
        st.session_state.selected_action = ACTIONS[0] # Default to Summarize
    if 'qa_answer' not in st.session_state:
        st.session_state.qa_answer = ""
    if 'gcp_project_id_display' not in st.session_state:
        st.session_state.gcp_project_id_display = GCP_PROJECT_ID


    # --- Render UI Components ---
    # Attempt to use a logo if it exists
    logo_path = os.path.join("src", "ui", "logo.png")
    if not os.path.exists(logo_path):
        logger.warning(f"Logo file not found at {logo_path}. Skipping logo rendering.")
        # Create a dummy logo file if it doesn't exist for the UI to render correctly (optional)
        # from PIL import Image
        # Image.new('RGB', (1, 1), color = 'red').save(logo_path)

    render_header()

    col1, col2 = st.columns([1, 1]) # Two columns for input/config and output

    with col1:
        uploaded_file, pasted_text = render_input_section()
        country_display_name, target_language_iso_code, action = render_config_section()

        # Process Document Button Logic
        if st.button("Process Document", type="primary", use_container_width=True):
            logger.info(f"Processing initiated. Country: {country_display_name}, Lang: {target_language_iso_code}, Action: {action}")

            # Clear previous outputs to show new results clearly
            st.session_state.qa_answer = ""
            st.session_state.processed_output = ""
            st.session_state.current_summary = ""
            st.session_state.raw_extracted_text = "" # Clear raw text for new process

            # Ensure there's some input from the user
            if not uploaded_file and not pasted_text:
                st.error("Please upload a file or paste text to proceed.")
                logger.warning("No input provided by user.")
                return

            try:
                # Step 1: Get text from input (handles OCR for images/PDFs, or uses pasted text)
                with st.spinner("Extracting text from document..."):
                    document_text = get_text_from_input_source(uploaded_file, pasted_text)

                if document_text:
                    logger.info(f"Text extracted successfully. Length: {len(document_text)} characters.")
                    st.session_state.raw_extracted_text = document_text # Store raw text in session state

                    # Step 2: NEW - Check if the document is financial using LLM
                    with st.spinner("Analyzing document content for financial relevance..."):
                        is_financial = is_document_financial(document_text, target_language_iso_code)

                    if not is_financial:
                        st.warning(
                            "This document does not appear to be financial. "
                            "FinAI Mitra is optimized for financial documents. "
                            "Please upload a financial document for best results."
                        )
                        st.session_state.processed_output = (
                            "**Document not recognized as financial.** "
                            "FinAI Mitra is specifically designed to understand and process "
                            "financial documents (e.g., loan agreements, insurance policies, tax documents). "
                            "Please upload a relevant financial document."
                        )
                        logger.info("Document classified as non-financial. Stopping further processing.")
                        return # Stop further processing if not financial

                    # Step 3: Determine which prompt function to use (Summarize or Simplify)
                    prompt_func = get_summarize_prompt if action == "Summarize" else get_simplify_prompt
                    main_prompt = prompt_func(document_text, country_display_name, target_language_iso_code)

                    # Step 4: Call LLM API for main processing (summarization or simplification)
                    with st.spinner(f"AI is {action.lower()}ing the financial document..."):
                        processed_output = call_gemini_api(main_prompt, target_language_iso_code)
                        st.session_state.processed_output = processed_output
                        st.session_state.current_summary = processed_output # Store for Q&A

                    st.success(f"Document {action.lower()}ed successfully! See output on the right.")
                    logger.info(f"Document {action.lower()} completed successfully.")
                else:
                    st.warning("No readable text could be extracted from the document or input was empty. Please ensure it's clear and well-formatted.")
                    logger.warning("No text extracted for processing.")

            except Exception as e:
                logger.exception("An error occurred during document processing.")
                st.error(f"An unexpected error occurred during processing: {e}. Please try again.")


    with col2:
        render_output_section(action)

        # Q&A Logic
        user_question = render_qa_section()
        if user_question:
            if not st.session_state.current_summary:
                st.error("Please process a document first to generate a summary/simplification for Q&A.")
                logger.warning("Q&A attempted without a summary/processed_output.")
                st.session_state.qa_answer = "Please process a document first to generate a summary/simplification for Q&A."
            else:
                try:
                    with st.spinner("Getting answer from AI..."):
                        qa_prompt = get_qa_prompt(st.session_state.current_summary, user_question, target_language_iso_code)
                        answer = call_gemini_api(qa_prompt, target_language_iso_code)
                        st.session_state.qa_answer = answer
                        logger.info("Q&A answer generated successfully.")
                except Exception as e:
                    logger.exception("Error during Q&A processing.")
                    st.session_state.qa_answer = f"Could not get an answer due to an AI error: {e}. Please try again."

    render_disclaimer()

if __name__ == "__main__":
    main()