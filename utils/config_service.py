import os
from utils.config import PROJECT_ID, DATASET_ID, TABLE_ID

class ConfigService:
    """
    A service to manage configuration settings for the application.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the ConfigService by loading environment variables.
        """
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._load_env_variables()

    def _load_env_variables(self):
        """
        Load configuration from environment variables.
        """
        self.project_id = PROJECT_ID
        self.dataset_id = DATASET_ID
        self.table_id = TABLE_ID
        self.location = os.getenv('REGION')

        # Load MODEL_NAME environment variable
        self.model_name = os.getenv('MODEL_NAME')

        # Ensure REGION is properly loaded
        self.region = os.getenv('REGION')
        if not self.region:
            raise EnvironmentError("Missing required environment variable: REGION")

        # Validate required configurations
        required_vars = ['PROJECT_ID', 'DATASET_ID', 'TABLE_ID', 'REGION', 'MODEL_NAME']
        for var in required_vars:
            if not getattr(self, var.lower()):
                raise EnvironmentError(f"Missing required environment variable: {var}")

    def get_database_uri(self):
        """
        Construct and return the database URI.
        """
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}/{self.db_name}"

config = ConfigService()