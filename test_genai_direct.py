import google.generativeai as genai

# Use the key directly as retrieved from the test
api_key = "AIzaSyAs0NXSXG3LFqBaMBlWgJGFoJE3q4fVrIc"

# Test direct configuration
genai.configure(api_key=api_key)

# Test generation
try:
    model = genai.GenerativeModel("gemini-exp-1206")
    response = model.generate_content("Hello")
    print("Direct test successful!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Direct test failed: {e}")