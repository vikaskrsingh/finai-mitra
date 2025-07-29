import streamlit as st
import logging
import sys
import os
from geopy.geocoders import Nominatim
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

# Import modules from your src package
from src.config import GCP_PROJECT_ID, LOG_LEVEL
from src.utils.document_parser import get_text_from_input_source
from src.utils.llm_processor import call_gemini_api, get_summarize_prompt, get_simplify_prompt, get_qa_prompt, is_document_financial
from src.ui.components import render_header, render_input_section, render_config_section, render_output_section, render_qa_section, render_disclaimer
from src.constants import COUNTRIES, ACTIONS, COUNTRY_LANGUAGES, TTS_LANGUAGE_MAP

# Set logging level dynamically
logging.getLogger().setLevel(LOG_LEVEL)


def generate_product_recommendation_prompt(age, income, gender, occupation, country, lang_code,processed_output):
    return f"""
Please don't provide response as an email.
And share the products like credit card only if available in {country}.
You are a financial advisor for Deutsche Bank. Based on the following user profile, suggest a customized financial plan and recommend Deutsche Bank products that match the user's needs
with context {processed_output}
- Age: {age}  
- Gender: {gender}  
- Annual Income: ${income:,} USD  
- Occupation: {occupation}  
- Country: {country}  

Please structure your response in the following format:
1. **Financial Goals** (short-term and long-term)
2. **Investment Recommendations** (products from Deutsche Bank like mutual funds, retirement plans, insurance, etc.)
3. **Savings & Budgeting Advice**
4. **Risk Profile and Diversification**
5. **Additional Deutsche Bank Services**

Make sure the advice is relevant to {country}'s banking environment and Deutsche Bank's offerings. 
And do provide the financial recommendations example based on 10 year investment period adjusted with inflation with investment amount based on saving of {income}/240 every month.
Provide clear, actionable steps suitable for a {age}-year-old {occupation.lower()} with {income_category(income)} income level.


Respond in {lang_code}.
"""

def income_category(income):
    if income < 30000:
        return "low"
    elif income < 80000:
        return "moderate"
    else:
        return "high"


def render_product_recommendation_section(selected_country, selected_language_iso_code,section_number):
    # st.subheader("2. Get Financial Product Recommendations")

    # Ask user inputs
    age = st.number_input("Enter your age", min_value=18, max_value=100, step=1, key="user_age")
    income = st.slider(
        "Select your annual income",
        min_value=1000,
        max_value=1000000,
        value=50000,
        step=1000
    )
    gender = st.selectbox("Select your gender", ["Male", "Female", "Other"], key="user_gender")

    # Occupation as dropdown
    occupation = st.selectbox(
        "Select your occupation",
        [
            "Student",
            "Salaried Employee",
            "Self-Employed",
            "Government Employee",
            "Retired",
            "Homemaker",
            "Business Owner",
            "Freelancer",
            "Unemployed",
            "Other"
        ],
        key="user_occupation"
    )

    section_number = section_number + 1
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown(f"## {section_number}. Input Document")
    st.markdown("Upload a document or paste text below:")
    uploaded_file, pasted_text = render_input_section()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Section 3: Process Document ---
    # st.markdown('<div class="section">', unsafe_allow_html=True)
    # section_number = section_number + 1
    # st.markdown(f"## {section_number}. Process Document")
    if st.button("Upload", type="primary", use_container_width=True):
        st.spinner("Extracting text from document...")
        logger.info(
            f"Uploading initiated. Country: {selected_country}, Lang: {st.session_state.selected_language_iso_code}, Action: Summarize")

        # Clear previous outputs to show new results clearly
        st.session_state.qa_answer = ""
        st.session_state.processed_output = ""
        st.session_state.current_summary = ""
        st.session_state.raw_extracted_text = ""  # Clear raw text for new process

        # Ensure there's some input from the user
        if uploaded_file or pasted_text:
            try:
                # Step 1: Get text from input (handles OCR for images/PDFs, or uses pasted text)
                with st.spinner("Extracting text from document..."):
                    document_text = get_text_from_input_source(uploaded_file, pasted_text)

                if document_text:
                    logger.info(f"Text extracted successfully. Length: {len(document_text)} characters.")
                    st.session_state.raw_extracted_text = document_text  # Store raw text in session state

                    # Step 2: Check if the document is financial using LLM
                    with st.spinner("Analyzing document content for financial relevance..."):
                        is_financial = is_document_financial(document_text, st.session_state.selected_language_iso_code)

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
                        return  # Stop further processing if not financial

                    # Step 3: Determine which prompt function to use (Summarize or Simplify)
                    prompt_func = get_summarize_prompt
                    main_prompt = prompt_func(document_text, selected_country, st.session_state.selected_language_iso_code)

                    # Step 4: Call LLM API for main processing (summarization or simplification)
                    with st.spinner(f"AI is summarizing the financial document..."):
                        processed_output = call_gemini_api(main_prompt, st.session_state.selected_language_iso_code)

                        # Validate the AI response for hallucination
                        if not processed_output or "error" in processed_output.lower():
                            st.error(
                                "The AI response seems invalid or irrelevant. Please try again or check the input document.")
                            logger.warning("AI response validation failed. Possible hallucination detected.")
                            st.session_state.processed_output = "AI generated an invalid response. Please retry with a clearer document."
                        else:
                            st.session_state.processed_output = processed_output
                            st.session_state.current_summary = processed_output  # Store for Q&A

                    st.success(f"Document summarized successfully!")
                    logger.info(f"Document summarized completed successfully.")
                else:
                    st.warning(
                        "No readable text could be extracted from the document or input was empty. Please ensure it's clear and well-formatted.")
                    logger.warning("No text extracted for processing.")

            except Exception as e:
                logger.exception("An error occurred during document processing.")
                st.error(f"An unexpected error occurred during processing: {e}. Please try again.")
    st.markdown('</div>', unsafe_allow_html=True)



    if st.button("🎯 Financial Recommendation"):
        with st.spinner(f"Getting personalized financial recommendations for {selected_country}..."):
            # print("PO",processed_output)
            prompt = generate_product_recommendation_prompt(
                age, income, gender, occupation, selected_country, selected_language_iso_code,st.session_state.processed_output
            )
            print("FR", prompt)
            response = call_gemini_api(prompt, selected_language_iso_code)

        st.session_state.processed_output = response
        st.session_state.current_summary = response
        st.success("Recommendations generated!")
        st.markdown(response)



def handle_country_change():
    """
    Callback to reset the language when the country changes.
    This prevents errors if the previously selected language is not
    available in the newly selected country.
    """
    new_country = st.session_state.selected_country
    logger.info(f"Country selection changed to {new_country}. Resetting language.")

    # Get the list of languages for the new country
    available_languages = list(COUNTRY_LANGUAGES[new_country].keys())

    # Reset the selected language to the first one in the new list
    st.session_state.selected_language = available_languages[0]

# --- Helper Functions ---
def get_user_location():
    """Fetch user's location based on IP address."""
    try:
        response = requests.get("http://ip-api.com/json", timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        if data.get("status") == "success" and "country" in data:
            country = data["country"]
            # Ensure the detected country is in your supported list
            if country in COUNTRIES:
                logger.info(f"User's location detected: {country}")
                return country
            else:
                logger.warning(f"Detected country '{country}' is not in the supported list. Defaulting to India.")
                return "India"
        else:
            logger.warning(f"Could not detect user's location from API. Response: {data}. Defaulting to India.")
            return "India"  # Default if API call fails or doesn't return country
    except Exception as e:
        logger.error(f"Error detecting user location: {e}")
        return "India"  # Default to India in case of an error

# --- Main Application ---
def main():
    # Set page config at the very beginning
    #st.set_page_config(layout="wide", page_title="FinAI Mitra 🤝", page_icon="🤝")

    # --- Initialize Session State Variables ---
    if 'selected_country' not in st.session_state:
        st.session_state.selected_country = get_user_location()  # Default to India
    if 'selected_language' not in st.session_state:
        st.session_state.selected_language = list(COUNTRY_LANGUAGES[get_user_location()].keys())[0]  # Default language for India
    if 'selected_language_iso_code' not in st.session_state:
        st.session_state.selected_language_iso_code = TTS_LANGUAGE_MAP[st.session_state.selected_language]
    if 'selected_action' not in st.session_state:
        st.session_state.selected_action = ACTIONS[0]  # Default action
    if 'current_summary' not in st.session_state:
        st.session_state.current_summary = ""
    if 'raw_extracted_text' not in st.session_state:
        st.session_state.raw_extracted_text = ""
    if 'uploaded_file_info' not in st.session_state:
        st.session_state.uploaded_file_info = None
    if 'processed_output' not in st.session_state:
        st.session_state.processed_output = ""
    if 'qa_answer' not in st.session_state:
        st.session_state.qa_answer = ""

    # --- Custom Styling ---
    st.markdown(
        """
        <style>
        body {
            background-color: #f4f4f4;
            font-family: 'Roboto', sans-serif;
        }
        .stButton > button {
            background-color: #007BFF;
            color: white;
            border-radius: 5px;
            padding: 0.5em 1em;
            font-size: 16px;
            border: none;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stTextInput, .stSelectbox {
            border-radius: 5px;
            padding: 0.5em;
            font-size: 14px;
            border: 1px solid #ddd;
        }
        .stMarkdown {
            font-size: 16px;
            color: #333;
        }
        .stInfo {
            background-color: #e9f5ff;
            border-left: 5px solid #007BFF;
            padding: 1em;
            border-radius: 5px;
        }
        .header {
            background-color: #007BFF;
            color: white;
            padding: 1em;
            text-align: center;
            border-radius: 5px;
            margin-bottom: 1em;
        }
        .section {
            background-color: white;
            padding: 1.5em;
            border-radius: 5px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1em;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


    # --- Header Section ---
    # st.markdown('<div class="header"><h1>FinAI Mitra 🤝</h1><p>Your Financial AI Assistant</p></div>', unsafe_allow_html=True)
    logo_path = os.path.join("src", "ui", "logo.png")
    if not os.path.exists(logo_path):
        logger.warning(f"Logo file not found at {logo_path}. Skipping logo rendering.")
    render_header()
    # --- Section 1: Select Location ---
    section_number = 1
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown(f"## {section_number}. Select Location")
    st.markdown("Choose your country and language preferences below:")
    selected_country = st.selectbox("Select your country:", COUNTRIES,key="selected_key" ,on_change=handle_country_change())
    #index=COUNTRIES.index(st.session_state.selected_country)

    st.session_state.selected_country = selected_country

    # Update language options based on selected country
    available_languages = list(COUNTRY_LANGUAGES[selected_country].keys())
    selected_language = st.selectbox("Select Language:", available_languages,key="selected_language" )
    #index=available_languages.index(st.session_state.selected_language)
    #st.session_state.selected_language = selected_language
    st.session_state.selected_language_iso_code = TTS_LANGUAGE_MAP[selected_language]

    # Allow user to change action
    selected_action = st.selectbox("Select Action:", ACTIONS, index=ACTIONS.index(st.session_state.selected_action))
    # selected_action = st.radio(
    #     "Select Action:",
    #     ACTIONS,
    #     index=ACTIONS.index(st.session_state.selected_action),
    #     horizontal=True  # Change to True for horizontal bullets
    # )
    st.session_state.selected_action = selected_action

    # Display updated configuration
    st.info(f"Configuration: Country - {selected_country}, Language - {selected_language}, Action - {selected_action}")
    st.markdown('</div>', unsafe_allow_html=True)
    # Inside your main app logic

    if  st.session_state.selected_action == "Financial Planning":
        section_number = section_number + 1
        st.subheader(f"{section_number}. Get Financial Recommendations")
        render_product_recommendation_section(selected_country,  st.session_state.selected_language_iso_code, section_number)


    # --- Section 2: Input Document ---
    else:
        section_number = section_number + 1
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown(f"## {section_number}. Input Document")
        st.markdown("Upload a document or paste text below:")
        uploaded_file, pasted_text = render_input_section()
        st.markdown('</div>', unsafe_allow_html=True)

        # --- Section 3: Process Document ---
        st.markdown('<div class="section">', unsafe_allow_html=True)
        section_number = section_number + 1
        st.markdown(f"## {section_number}. Process Document")
        if st.button("Process Document", type="primary", use_container_width=True):
            logger.info(f"Processing initiated. Country: {selected_country}, Lang: {st.session_state.selected_language_iso_code}, Action: {selected_action}")

            # Clear previous outputs to show new results clearly
            st.session_state.qa_answer = ""
            st.session_state.processed_output = ""
            st.session_state.current_summary = ""
            st.session_state.raw_extracted_text = ""  # Clear raw text for new process

            # Ensure there's some input from the user
            if st.session_state.selected_action != "Financial Planning" and (not uploaded_file and not pasted_text):
                st.error("Please upload a file or paste text to proceed.")
                logger.warning("No input provided by user.")
                return

            try:
                # Step 1: Get text from input (handles OCR for images/PDFs, or uses pasted text)
                with st.spinner("Extracting text from document..."):
                    document_text = get_text_from_input_source(uploaded_file, pasted_text)

                if document_text:
                    logger.info(f"Text extracted successfully. Length: {len(document_text)} characters.")
                    st.session_state.raw_extracted_text = document_text  # Store raw text in session state

                    # Step 2: Check if the document is financial using LLM
                    with st.spinner("Analyzing document content for financial relevance..."):
                        is_financial = is_document_financial(document_text, st.session_state.selected_language_iso_code)

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
                        return  # Stop further processing if not financial

                    # Step 3: Determine which prompt function to use (Summarize or Simplify)
                    prompt_func = get_summarize_prompt if selected_action == "Summarize" else get_simplify_prompt
                    main_prompt = prompt_func(document_text, selected_country, st.session_state.selected_language_iso_code)

                    # Step 4: Call LLM API for main processing (summarization or simplification)
                    with st.spinner(f"AI is {selected_action.lower()}ing the financial document..."):
                        processed_output = call_gemini_api(main_prompt, st.session_state.selected_language_iso_code)

                        # Validate the AI response for hallucination
                        if not processed_output or "error" in processed_output.lower():
                            st.error("The AI response seems invalid or irrelevant. Please try again or check the input document.")
                            logger.warning("AI response validation failed. Possible hallucination detected.")
                            st.session_state.processed_output = "AI generated an invalid response. Please retry with a clearer document."
                        else:
                            st.session_state.processed_output = processed_output
                            st.session_state.current_summary = processed_output  # Store for Q&A

                    st.success(f"Document {selected_action.lower()}ed successfully! See output on the right.")
                    logger.info(f"Document {selected_action.lower()} completed successfully.")
                else:
                    st.warning("No readable text could be extracted from the document or input was empty. Please ensure it's clear and well-formatted.")
                    logger.warning("No text extracted for processing.")

            except Exception as e:
                logger.exception("An error occurred during document processing.")
                st.error(f"An unexpected error occurred during processing: {e}. Please try again.")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- Section 4: Output ---
        st.markdown('<div class="section">', unsafe_allow_html=True)
        section_number = section_number + 1
        st.markdown(f"## {section_number}. Output")
        render_output_section(selected_action)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Section 5: Q&A ---
    st.markdown('<div class="section">', unsafe_allow_html=True)
    section_number = section_number + 1
    st.markdown(f"## {section_number}. Q&A")
    user_question = render_qa_section()
    if user_question:
        if not st.session_state.current_summary:
            st.error("Please process a document first or ask questions to generate a summary/simplification for Q&A.")
            logger.warning("Q&A attempted without a summary/processed_output.")
            st.session_state.qa_answer = "Please process a document first to generate a summary/simplification for Q&A."
        else:
            try:
                with st.spinner("Getting answer from AI..."):
                    qa_prompt = get_qa_prompt(st.session_state.current_summary, user_question, st.session_state.selected_language_iso_code)
                    print("QA Prompt is",qa_prompt)
                    answer = call_gemini_api(qa_prompt, st.session_state.selected_language_iso_code)
                    st.session_state.qa_answer = answer
                    logger.info("Q&A answer generated successfully.")
            except Exception as e:
                logger.exception("Error during Q&A processing.")
                st.session_state.qa_answer = f"Could not get an answer due to an AI error: {e}. Please try again."

    # Display the answer if available
    if st.session_state.get('qa_answer'):
        st.markdown(f"**Answer:** {st.session_state.qa_answer}")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Section 6: Feedback ---
    st.markdown('<div class="section">', unsafe_allow_html=True)
    section_number = section_number + 1
    st.markdown(f"## {section_number}. Feedback")
    feedback = st.text_area("Provide feedback on the AI-generated output:")
    if st.button("Submit Feedback"):
        try:
            # Save feedback to a file
            with open("feedback.txt", "a") as f:
                f.write(f"{feedback}\n")
            st.success("Thank you for your feedback!")
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
            st.error("An error occurred while saving your feedback.")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Section 7: Disclaimer ---
    section_number = section_number + 1
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown(f"## {section_number}. Disclaimer")
    render_disclaimer()
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()