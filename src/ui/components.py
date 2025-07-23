# src/ui/components.py

import streamlit as st
import os
import logging

# Import TTS functions
from src.tts_utils import synthesize_text_to_audio, list_available_voices
from src.constants import COUNTRIES, ACTIONS, COUNTRY_LANGUAGES, TTS_LANGUAGE_MAP
from src.utils.llm_processor import get_qa_prompt, call_gemini_api
from src.config import TEMP_UPLOAD_DIR, GCP_PROJECT_ID

logger = logging.getLogger(__name__)

def render_header():
    """Renders the application header."""
    st.image(os.path.join("src", "ui", "logo.png"), width=200)
    st.title("FinAI Mitra 🤝")
    st.markdown("Your intelligent assistant for **financial document insights**.")
    st.markdown("---")

def render_input_section():
    """Renders the document input section."""
    st.subheader("Input Document")
    uploaded_file = st.file_uploader("Upload a PDF/Image", type=["pdf", "png", "jpg", "jpeg"], key="file_uploader")
    pasted_text = st.text_area("Or paste text here", height=200, key="text_area_input")
    return uploaded_file, pasted_text

def render_config_section():
    """Renders the configuration options."""
    st.subheader("2. Configuration")
    
    # Select Country
    selected_country = st.selectbox("Select Country", COUNTRIES, key="country_select")
    
    # Get available languages for the selected country
    available_languages_for_country = list(COUNTRY_LANGUAGES.get(selected_country, {"English": "en"}).keys())
    
    # Ensure the session state selected language is valid for the current country
    if st.session_state.selected_language not in available_languages_for_country:
        st.session_state.selected_language = available_languages_for_country[0]

    # Select Language for Output
    selected_language = st.selectbox(
        "Select Language for Output",
        available_languages_for_country,
        index=available_languages_for_country.index(st.session_state.selected_language),
        key="lang_select"
    )
    
    selected_action = st.selectbox("Select Action", ACTIONS, key="action_select")
    
    # Return ISO code for LLM processing
    target_language_iso_code = COUNTRY_LANGUAGES.get(selected_country, {}).get(selected_language, "en") # Default to 'en'
    
    return selected_country, target_language_iso_code, selected_action

def render_output_section(action):
    """
    Renders the processed output and integrates Text-to-Speech functionality.
    """
    st.subheader(f"{action} Output")
    
    if st.session_state.processed_output:
        st.markdown(st.session_state.processed_output)

        st.markdown("---")
        st.subheader("🔊 Listen to Output")

        # Get the ISO code used for the LLM output language from session state
        # This ensures the TTS matches the LLM's output language
        llm_output_lang_iso = st.session_state.get('selected_language_iso_code', 'en')
        
        # Map this ISO code to a specific BCP-47 tag for Google TTS
        default_tts_lang_code = TTS_LANGUAGE_MAP.get(llm_output_lang_iso, "en-US")

        # Create display names for TTS options from the TTS_LANGUAGE_MAP
        tts_language_display_options_keys = list(TTS_LANGUAGE_MAP.keys())
        tts_language_display_options_values = list(TTS_LANGUAGE_MAP.values())
        
        # Reverse map for selectbox default (map BCP-47 code back to our ISO key for display)
        reverse_tts_map_display = {v: k for k, v in TTS_LANGUAGE_MAP.items()}
        
        # Determine the default selected name for the TTS dropdown based on the LLM output language
        default_tts_lang_name_for_display = next((k for k, v in TTS_LANGUAGE_MAP.items() if v == default_tts_lang_code), "en") # Default to 'en' if not found
        
        # Find the index of the default display name in the list of keys
        try:
            default_index = tts_language_display_options_keys.index(default_tts_lang_name_for_display)
        except ValueError:
            default_index = 0 # Fallback if not found

        selected_tts_lang_key = st.selectbox(
            "Select Language for Audio Playback",
            tts_language_display_options_keys,
            index=default_index,
            key="tts_lang_select_output" # Unique key for this selectbox
        )
        selected_tts_lang_code = TTS_LANGUAGE_MAP[selected_tts_lang_key] # Get the BCP-47 code for TTS
        
        if st.button("▶️ Read Output Aloud", help="Click to generate and play the audio of the processed text."):
            if st.session_state.get('processed_output'): # Check if output exists
                with st.spinner(f"Generating audio for {selected_tts_lang_key} ({selected_tts_lang_code})... This might take a moment."):
                    audio_bytes = synthesize_text_to_audio(
                        st.session_state.processed_output,
                        language_code=selected_tts_lang_code # Use the BCP-47 code here
                    )
                if audio_bytes:
                    st.audio(audio_bytes, format='audio/mp3', start_time=0)
                    st.success("Audio playback ready! You can now listen to the output.")
                else:
                    st.error("Failed to generate audio. Please ensure the 'Cloud Text-to-Speech API' is enabled and your authentication is set up correctly.")
            else:
                st.warning("No processed output available to read aloud. Please process a document first.")
    else:
        st.info("Output will appear here after processing.")

def render_qa_section():
    """Renders the Q&A section."""
    st.subheader("4. Ask a Question (Q&A)")
    user_question = st.text_input("Ask about the document or summary:", key="qa_input")

    # Check if a question is provided
    if user_question:
        if not st.session_state.get('current_summary'):
            st.warning("Please process a document first to generate a summary or output for Q&A.")
        else:
            try:
                # Generate the Q&A prompt
                qa_prompt = get_qa_prompt(
                    st.session_state.current_summary,  # Use the processed summary
                    user_question,
                    st.session_state.selected_language_iso_code  # Language for Q&A
                )

                # Call the LLM API to get the answer
                with st.spinner("Getting answer from AI..."):
                    answer = call_gemini_api(qa_prompt, st.session_state.selected_language_iso_code)

                # Update the session state with the answer
                st.session_state.qa_answer = answer
                st.success("Answer generated successfully!")
            except Exception as e:
                logger.exception("Error during Q&A processing.")
                st.error(f"An error occurred while generating the answer: {e}")

    # Display the answer if available
    if st.session_state.get('qa_answer'):
        st.markdown(f"**Answer:** {st.session_state.qa_answer}")

    return user_question

def render_disclaimer():
    """Renders the disclaimer at the bottom."""
    st.markdown("---")
    st.markdown(f"""
    <small>
    **Disclaimer:** FinAI Mitra is an AI assistant and does not provide financial or legal advice.
    Always consult with a qualified professional for personalized advice.
    Powered by Google Cloud Vision AI and Vertex AI (Gemini).
    </small>
    """, unsafe_allow_html=True)
    if GCP_PROJECT_ID:
        st.markdown(f"<small>GCP Project: `{GCP_PROJECT_ID}`</small>", unsafe_allow_html=True)

def get_qa_prompt(summary, question, language_iso_code):
    """
    Generates a prompt for the Q&A section based on the summary and user question.

    Args:
        summary (str): The processed summary of the document.
        question (str): The user's question.
        language_iso_code (str): The ISO code for the language.

    Returns:
        str: The generated prompt for the Q&A.
    """
    return f"Based on the following summary:\n\n{summary}\n\nAnswer the question:\n\n{question}\n\nProvide the response in {language_iso_code}."

def call_gemini_api(prompt, language_iso_code):
    """
    Calls the LLM API to generate a response based on the given prompt.

    Args:
        prompt (str): The prompt to send to the LLM API.
        language_iso_code (str): The ISO code for the language.

    Returns:
        str: The response generated by the LLM API.
    """
    # Example implementation (replace with actual API call logic)
    try:
        # Simulate API call (replace with actual API integration)
        response = f"Simulated response for prompt: {prompt} in language: {language_iso_code}"
        return response
    except Exception as e:
        logger.exception("Error calling LLM API.")
        return f"Error: {e}"