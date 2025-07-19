import streamlit as st
import os
from src.constants import COUNTRIES, COUNTRY_LANGUAGES, ACTIONS
from src.config import TEMP_UPLOAD_DIR, GCP_PROJECT_ID

def render_header():
    """Renders the application header."""
    st.image(os.path.join("src", "ui", "logo.png"), width=150) # Assuming a logo.png in src/ui
    st.title("FinAI Mitra 🤝")
    st.markdown("Your AI Assistant for Financial Document Understanding")
    st.markdown("---")

def render_input_section():
    """Renders the document input section."""
    st.subheader("1. Input Document")
    uploaded_file = st.file_uploader(
        "Upload a PDF or Image (PNG, JPG)",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=False,
        key="file_uploader"
    )
    st.write("--- OR ---")
    pasted_text = st.text_area(
        "Paste Document Text Here",
        height=250,
        placeholder="Paste your financial document text here...",
        key="text_area"
    )

    if uploaded_file and pasted_text:
        st.warning("Please upload a file OR paste text, not both. Prioritizing uploaded file.")
        pasted_text = "" # Clear pasted text if file is uploaded

    return uploaded_file, pasted_text

def render_config_section():
    """Renders the configuration options (country, language, action)."""
    st.subheader("2. Configure AI Processing")
    selected_country = st.selectbox(
        "Select Country Context",
        COUNTRIES,
        index=COUNTRIES.index(st.session_state.selected_country),
        key="country_selector"
    )
    st.session_state.selected_country = selected_country

    available_languages = COUNTRY_LANGUAGES[selected_country]
    selected_language_display = st.selectbox(
        "Select Output Language",
        options=list(available_languages.values()),
        index=list(available_languages.values()).index(COUNTRY_LANGUAGES[st.session_state.selected_country][st.session_state.selected_language]),
        key="language_selector"
    )
    # Get the ISO code from the display name
    target_language_iso_code = next(
        (iso for iso, display in available_languages.items() if display == selected_language_display),
        "en" # Default to English ISO if not found
    )
    st.session_state.selected_language = target_language_iso_code # Store ISO code

    selected_action = st.radio(
        "Choose Action",
        ACTIONS,
        index=ACTIONS.index(st.session_state.get('selected_action', ACTIONS[0])), # Default to Summarize
        horizontal=True,
        key="action_selector"
    )
    st.session_state.selected_action = selected_action # Store selected action

    return selected_country, target_language_iso_code, selected_action

def render_output_section(action: str):
    """Renders the processed output section."""
    st.subheader(f"3. AI Processed Output ({action})")
    st.markdown(st.session_state.processed_output, unsafe_allow_html=True)

def render_qa_section():
    """Renders the Q&A section."""
    st.subheader("4. Ask a Question")
    user_question = st.text_input(
        "Ask a follow-up question about the document:",
        placeholder="e.g., 'What is the interest rate?' or 'What are the repayment terms?'",
        key="user_question_input"
    )

    if st.session_state.qa_answer:
        st.info(st.session_state.qa_answer)
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