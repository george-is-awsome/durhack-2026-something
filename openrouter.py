import os
from openai import OpenAI

def generate_response(prompt):
    """Request a completion from OpenRouter and return its text."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Set the OPENROUTER_API_KEY environment variable to use AI generation.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://your-site-or-app.com",
            "X-Title": "My Test App",
        },
    )
    completion = client.chat.completions.create(
        model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        messages=[
            {"role": "system", "content": "You are the dungeon master for a sci-fi text adventure game."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    content = completion.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("OpenRouter returned an empty response.")
    return content