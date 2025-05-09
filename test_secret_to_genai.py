from google.cloud import secretmanager
import google.generativeai as genai
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_secret_to_genai():
    # 1. Get API key from Secret Manager (same as your application)
    client = secretmanager.SecretManagerServiceClient()
    project_id = "massi-financial-analysis"
    name = f"projects/{project_id}/secrets/gemini-api-key-ai-studio/versions/latest"
    
    response = client.access_secret_version(request={"name": name})
    api_key = response.payload.data.decode("UTF-8")
    
    # Log key info (not the key itself)
    logger.info(f"Retrieved API key length: {len(api_key)}")
    logger.info(f"First 10 chars: {api_key[:10]}")
    logger.info(f"Last 10 chars: {api_key[-10:]}")
    
    # 2. Configure genai (same as your application)
    genai.configure(api_key=api_key)
    
    # 3. Test generation
    try:
        model = genai.GenerativeModel("gemini-exp-1206")
        response = model.generate_content("Hello")
        logger.info("Secret Manager to Genai test successful!")
        logger.info(f"Response: {response.text}")
        return True
    except Exception as e:
        logger.error(f"Test failed: {e}")
        
        # Let's also try with the key stripped of whitespace
        logger.info("Trying with stripped key...")
        genai.configure(api_key=api_key.strip())
        try:
            model = genai.GenerativeModel("gemini-exp-1206")
            response = model.generate_content("Hello")
            logger.info("Success with stripped key!")
            return True
        except Exception as e2:
            logger.error(f"Still failed: {e2}")
            
            # Raw bytes check
            logger.info(f"Raw bytes: {response.payload.data}")
            return False

if __name__ == "__main__":
    test_secret_to_genai()