import os
import json
import logging
from google.cloud import storage
from google.oauth2 import service_account
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cloud_storage.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CloudStorageManager:
    def __init__(self, bucket_name="udio-music-bot"):
        """Initialize the Cloud Storage Manager with credentials from environment."""
        self.bucket_name = bucket_name
        self._setup_client()

    # ... [Rest of the class implementation remains unchanged] ...
