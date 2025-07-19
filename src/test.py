import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import GCP_PROJECT_ID, LOG_LEVEL

print(GCP_PROJECT_ID, LOG_LEVEL)
print("Current Directory:", os.getcwd())
print("Src Path Exists:", os.path.exists(os.path.join(os.getcwd(), 'src')))