import os

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# --------------------------------------------------
# Configuration
# --------------------------------------------------
load_dotenv()

HF_TOKEN= os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise ValueError("HF_TOKEN is not set in .env")

MODEL = "Qwen/Qwen3-32B"

# --------------------------------------------------
# Create Hugging Face client
# --------------------------------------------------
client = InferenceClient(
    api_key=HF_TOKEN,
    provider="auto",
)

# --------------------------------------------------
# Test the model
# --------------------------------------------------
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": "Explain what is RAG in two sentences.",
        }
    ],
)

# --------------------------------------------------
# Print response
# --------------------------------------------------
print(response.choices[0].message.content)
