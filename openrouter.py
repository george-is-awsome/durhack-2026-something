import os
from openai import OpenAI

# Initialize the OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "<OPENROUTER_API_KEY>"),
    default_headers={
        # Optional headers for app attribution on OpenRouter's leaderboard
        "HTTP-Referer": "https://your-site-or-app.com",
        "X-Title": "My Test App",
    },
)

def generate_response(prompt):
    try:
        completion = client.chat.completions.create(
            # Use any free model tag or standard model slug
            model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            messages=[
                {"role": "system", "content": "Two words max per response"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        # Print the response content
        print(completion.choices[0].message.content)

    except Exception as e:
        print(f"An error occurred: {e}")

generate_response("Explain why the sky is blue in one sentence.")