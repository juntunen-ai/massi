"""
Centralized authentication management for Google Cloud services.
"""

import os
import logging
from google.auth import default
from google.oauth2 import service_account
import google.auth.transport.requests
from google.auth.exceptions import DefaultCredentialsError
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class GoogleCloudAuth:
    """Manages authentication for Google Cloud services."""
    
    def __init__(self):
        """Initialize authentication manager."""
        self.credentials = None
        self.project_id = None
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        """Initialize Google Cloud credentials."""
        try:
            # First, try application default credentials
            self.credentials, self.project_id = default()
            logger.info("Successfully authenticated using application default credentials")
            
            # Ensure credentials are valid
            self._refresh_credentials()
            
        except DefaultCredentialsError:
            logger.error("Failed to initialize credentials. Please run 'gcloud auth application-default login'")
            self.credentials = None
            self.project_id = None
    
    def _refresh_credentials(self):
        """Refresh the credentials if they're expired."""
        if self.credentials and self.credentials.expired:
            try:
                self.credentials.refresh(google.auth.transport.requests.Request())
                logger.debug("Credentials refreshed successfully")
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {str(e)}")
    
    def get_credentials(self) -> Optional[Tuple]:
        """Get current credentials and project ID."""
        if not self.credentials:
            self._initialize_credentials()
        return self.credentials, self.project_id
    
    def is_authenticated(self) -> bool:
        """Check if authenticated credentials are available."""
        return self.credentials is not None
    
    @staticmethod
    def initialize_for_bigquery():
        """Initialize authentication for BigQuery."""
        auth = GoogleCloudAuth()
        credentials, project_id = auth.get_credentials()
        
        if credentials is None:
            logger.error("BigQuery authentication failed. Check your Google Cloud credentials.")
            return None, None
            
        return credentials, project_id
    
    @staticmethod
    def initialize_for_vertex_ai(project_id: str, location: str):
        """Initialize authentication for Vertex AI."""
        auth = GoogleCloudAuth()
        credentials, detected_project = auth.get_credentials()
        
        if credentials is None:
            logger.error("Vertex AI authentication failed. Check your Google Cloud credentials.")
            return False
        
        # Use the explicitly provided project_id or fall back to detected one
        final_project = project_id or detected_project
        
        try:
            # This will initialize Vertex AI with the credentials
            import google.cloud.aiplatform as aiplatform
            aiplatform.init(
                project=final_project,
                location=location,
                credentials=credentials
            )
            logger.info(f"Vertex AI initialized for project: {final_project}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {str(e)}")
            return False

def init_google_auth():
    """Initialize Google Cloud authentication and return credentials and project ID."""
    auth = GoogleCloudAuth()
    credentials, project_id = auth.get_credentials()

    if credentials is None:
        raise RuntimeError("Failed to initialize Google Cloud authentication. Check your credentials.")

    return credentials, project_id