from google.cloud import secretmanager
import logging

logger = logging.getLogger(__name__)

class SecretsManager:
    _instance = None
    _api_key_cache = None
    
    def __new__(cls, project_id="massi-financial-analysis"):
        if cls._instance is None:
            cls._instance = super(SecretsManager, cls).__new__(cls)
            cls._instance.project_id = project_id
        return cls._instance
    
    def get_api_key_ai_studio(self):
        """Get Google AI Studio API key from Secret Manager."""
        if self._api_key_cache is not None:
            return self._api_key_cache
            
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{self.project_id}/secrets/gemini-api-key-ai-studio/versions/latest"
        
        try:
            response = client.access_secret_version(request={"name": name})
            self._api_key_cache = response.payload.data.decode("UTF-8")
            logger.info(f"Retrieved API key from Secret Manager (length: {len(self._api_key_cache)})")
            return self._api_key_cache
        except Exception as e:
            logger.error(f"Error retrieving API key: {e}")
            raise

# Create a singleton instance
secrets_manager = SecretsManager()