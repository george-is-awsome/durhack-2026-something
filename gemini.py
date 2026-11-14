from google import genai

# Automatically picks up the GEMINI_API_KEY environment variable
client = genai.Client()

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Explain why the sky is blue in one sentence.",
)

print(response.text)

# dont use this it doesnt work