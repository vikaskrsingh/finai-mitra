# src/constants.py

COUNTRIES = [
    "United States",
    "Germany",
    "India"
]

# Mapping of Country Display Name to {Language Display Name: ISO 639-1 Code}
COUNTRY_LANGUAGES = {
    "United States": {
        "English": "en"
    },
    "Germany": {
        "German": "de",
        "English": "en"
    },
    "India": {
        "Hindi": "hi",
        "English": "en",
        "Tamil": "ta"
    }
}

ACTIONS = [
    "Summarize",
    "Simplify"
]

# Supported languages for Text-to-Speech (ISO 639-1 code for voice selection)
# This is a separate mapping to ensure TTS voices are correctly selected.
# Note: Google TTS uses BCP-47 language tags (e.g., en-US, de-DE), not just ISO 639-1.
# We'll map our simplified ISO codes to the more specific BCP-47 tags for TTS.
TTS_LANGUAGE_MAP = {
    "English": "en-US",
    "German": "de-DE",
    "Hindi": "hi-IN",
    "Tamil": "ta-IN"
}

# For file processing
SUPPORTED_FILE_TYPES = ["pdf", "png", "jpg", "jpeg"]