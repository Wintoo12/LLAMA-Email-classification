import requests

api_key = "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"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get("https://api.groq.com/openai/v1/models", headers=headers)

print(response.json())  # Prints available models