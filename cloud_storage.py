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
    def __init__(self, bucket_name="suno-music-bot"):
        """Initialize the Cloud Storage Manager with credentials from environment."""
        self.bucket_name = bucket_name
        self._setup_client()

    def _setup_client(self):
        """Set up Google Cloud Storage client with credentials."""
        try:
            credentials_json = os.environ.get('GOOGLE_CLOUD_CREDENTIALS')
            if not credentials_json:
                raise ValueError("Google Cloud credentials not found in environment")

            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            self.client = storage.Client(credentials=credentials)
            
            # Get or create bucket
            try:
                self.bucket = self.client.get_bucket(self.bucket_name)
            except Exception:
                self.bucket = self.client.create_bucket(self.bucket_name)
                logger.info(f"Created new bucket: {self.bucket_name}")
            
            logger.info("Successfully initialized Cloud Storage client")
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Storage client: {str(e)}")
            raise

    def upload_file(self, file_path: str | Path, destination_path: str | None = None) -> str:
        """
        Upload a file to Google Cloud Storage.
        
        Args:
            file_path: Path to the local file
            destination_path: Optional custom path in the bucket (defaults to filename)
            
        Returns:
            Public URL of the uploaded file
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Use filename as destination if not specified
            if destination_path is None:
                destination_path = file_path.name

            # Upload the file
            blob = self.bucket.blob(destination_path)
            blob.upload_from_filename(str(file_path))
            
            # Make the file publicly accessible
            blob.make_public()
            
            logger.info(f"Successfully uploaded {file_path} to {destination_path}")
            return blob.public_url

        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {str(e)}")
            raise

    def list_files(self, prefix: str = "") -> list[str]:
        """List all files in the bucket with optional prefix filter."""
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            raise
