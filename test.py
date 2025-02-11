import os
import litellm

# Set API Base URL and API Key
os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
os.environ["OPENAI_API_KEY"] = "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"
os.environ["LITELLM_LOG"] = "DEBUG"  # Enables logging

try:
    # Correct model name from your Groq list
    response = litellm.completion(
        model="llama-3.1-8b-instant",  # or use "llama3-8b-8192"
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        api_base="https://api.groq.com/openai/v1",
        api_key=os.environ["OPENAI_API_KEY"],  # Pass API key explicitly
    )
    
    print(response)
except Exception as e:
    print(f"Error: {e}")
