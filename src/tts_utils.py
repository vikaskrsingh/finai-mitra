# src/tts_utils.py

import io
import os
import logging # Import logging module
# Corrected import for texttospeech_v1 client and types
from google.cloud.texttospeech_v1 import TextToSpeechClient, SynthesisInput, VoiceSelectionParams, AudioConfig, SsmlVoiceGender, AudioEncoding
import streamlit as st

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Initialize the Text-to-Speech client using Streamlit's cache
# This ensures the client is created only once per session, improving performance.
@st.cache_resource
def get_tts_client():
    """Returns a Google Cloud Text-to-Speech client."""
    return TextToSpeechClient()

def synthesize_text_to_audio(text: str, language_code: str = "en-US", voice_name: str = None) -> bytes | None:
    """
    Synthesizes text into audio using Google Cloud Text-to-Speech.

    Args:
        text (str): The text to synthesize.
        language_code (str): The language code (e.g., "en-US", "de-DE", "hi-IN").
                              See https://cloud.google.com/text-to-speech/docs/voices for available options.
        voice_name (str, optional): The specific voice name (e.g., "en-US-Neural2-A").
                                     If None, a default voice for the language_code is chosen.

    Returns:
        bytes: The audio content in MP3 format if successful.
        None: If an error occurs.
    """
    if not text:
        st.warning("No text provided to synthesize for audio.")
        return None

    client = get_tts_client()
    synthesis_input = SynthesisInput(text=text)

    # Attempt to select a Neural2 voice for better quality if not specified
    if not voice_name:
        # Try a common Neural2 voice name pattern for the given language code
        try_voice_name = f"{language_code.replace('-', '_')}-Neural2-A"
        try:
            # Create a temporary VoiceSelectionParams to check if the voice exists
            temp_voice_params = VoiceSelectionParams(
                language_code=language_code,
                name=try_voice_name,
                ssml_gender=SsmlVoiceGender.NEUTRAL,
            )
            # Make a small, quick request to check voice validity without full synthesis
            client.synthesize_speech(
                input=SynthesisInput(text="."), # Synthesize a single character for a quick check
                voice=temp_voice_params,
                audio_config=AudioConfig(audio_encoding=AudioEncoding.MP3)
            )
            voice_selection_params = temp_voice_params
        except Exception:
            # Fallback to default voice selection if the specific neural voice isn't found
            logger.warning(f"Neural2-A voice '{try_voice_name}' not found for {language_code}. Falling back to standard voice selection.")
            voice_selection_params = VoiceSelectionParams(
                language_code=language_code,
                ssml_gender=SsmlVoiceGender.NEUTRAL,
            )
    else:
        voice_selection_params = VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=SsmlVoiceGender.NEUTRAL,
        )

    audio_config = AudioConfig(
        audio_encoding=AudioEncoding.MP3
    )

    try:
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_selection_params,
            audio_config=audio_config
        )
        return response.audio_content
    except Exception as e:
        st.error(f"Failed to synthesize speech: {e}")
        st.info("Please ensure 'Cloud Text-to-Speech API' is enabled in your GCP project and your authentication is set up correctly.")
        return None

# Optional: Function to list available voices (useful if you want a dynamic voice dropdown)
# Note: This makes an API call and can be slow if not cached.
@st.cache_data(ttl=3600) # Cache for 1 hour to reduce API calls
def list_available_voices(language_code: str = None) -> list[str]:
    """Lists available voices for a given language code."""
    client = get_tts_client()
    try:
        voices = client.list_voices(language_code=language_code).voices
        return sorted([voice.name for voice in voices if voice.name.startswith(language_code or '')])
    except Exception as e:
        st.error(f"Error listing voices: {e}")
        return []