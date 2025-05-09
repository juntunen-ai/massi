from google.cloud import secretmanager

def test_secret_access():
    client = secretmanager.SecretManagerServiceClient()
    project_id = "massi-financial-analysis"
    name = f"projects/{project_id}/secrets/gemini-api-key-ai-studio/versions/latest"
    
    try:
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        print(f"Secret retrieved successfully. Length: {len(secret_value)}")
        print(f"First 10 chars: {secret_value[:10]}")
        print(f"Last 10 chars: {secret_value[-10:]}")
        return secret_value
    except Exception as e:
        print(f"Error accessing secret: {e}")
        return None

if __name__ == "__main__":
    test_secret_access()