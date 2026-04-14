import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
key = os.getenv("OPENAI_API_KEY")
print(f"Key loaded: {key[:10]}...{key[-5:]}")

client = OpenAI(api_key=key)
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=5
    )
    print("OpenAI success:", response.choices[0].message.content)
except Exception as e:
    print("OpenAI failed:", str(e))
