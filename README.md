To run FinAI Mitra locally, follow these steps:

Prerequisites
Python 3.8+

pip (Python package installer)

Google Cloud SDK (gcloud CLI) installed and configured

A Google Cloud Project with Billing Enabled

Enabled APIs in your GCP Project:

Cloud Vision API

Vertex AI API

Cloud Text-to-Speech API

Cloud Storage API

A Google Cloud Storage (GCS) bucket created in your GCP project.

1. Clone the Repository
git clone <your-repository-url>
cd finai-mitra

(Note: Replace <your-repository-url> with the actual URL if this project is hosted on Git.)

2. Set up a Virtual Environment
It's highly recommended to use a virtual environment to manage dependencies.

python -m venv venv
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

3. Install Dependencies
Install the required Python packages:

pip install -r requirements.txt

requirements.txt content:

streamlit
google-cloud-vision
google-cloud-aiplatform
google-generativeai
google-cloud-texttospeech
python-dotenv

4. Configure Google Cloud Credentials
Ensure your gcloud CLI is authenticated and configured for your project.

gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_ACTUAL_NEW_GCP_PROJECT_ID

Replace YOUR_ACTUAL_NEW_GCP_PROJECT_ID with your project ID.

5. Configure Project Settings
Create and update the src/config.py file with your specific GCP details.

src/config.py content:

# src/config.py

# --- Google Cloud Project Configuration ---
GCP_PROJECT_ID = "YOUR_ACTUAL_NEW_GCP_PROJECT_ID" # e.g., "finai-mitra-new-project-12345"
GCP_REGION = "YOUR_ACTUAL_CHOSEN_GCP_REGION"     # e.g., "us-central1"
GCS_BUCKET_NAME = "YOUR_ACTUAL_NEW_GCS_BUCKET_NAME" # e.g., "finai-mitra-new-docs-bucket-xyz"

# --- Gemini Model Configuration ---
GEMINI_MODEL_NAME = "gemini-2.5-flash"

# --- Application Logging Level ---
LOG_LEVEL = "INFO"

Remember to replace the placeholder values with your actual GCP Project ID, Region, and GCS Bucket Name.

6. Run the Application
Navigate to the root of your project directory and run the Streamlit app:

streamlit run main_app.py

This will open the FinAI Mitra application in your web browser.