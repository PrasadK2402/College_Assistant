import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from retrieval.search import search


# --------------------------------------------------
# Configuration
# --------------------------------------------------
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise ValueError("HF_TOKEN is not in .env")

MODEL = "Qwen/Qwen3-32B"

# --------------------------------------------------
# Hugging Face client
# --------------------------------------------------
client = InferenceClient(
    api_key=HF_TOKEN,
    provider="auto",
)

# --------------------------------------------------
# Generate answer
# --------------------------------------------------
def generate_answer(question):
    """
    Retrieve relevent WCE information
    and use an LLM to generate an answer.
    """

    ## Retrieve relevent chunks
    results = search(
        question,
        top_k=3
    )
    if not results:
        return "I could not find relevant information about this in the available WCE documents."

    #Build context from retrieved chunks
    context = "\n\n".join(
        f"""
        SOURCE: {result['source']}
        RELEVANCE SCORE: {result['score']:.4f} 
        {result['text']}
        """     
        for result in results
    )

    # Create prompt 
    prompt = f"""You are an AI assistant for Walchand College of Engineering (WCE).

Answer the user's question using ONLY the information
provided in the context below.

If the answer cannot be found in the context,
say that you could not find the answer in the available
WCE information.

Context:
----------------
{context}
----------------

Question:
{question}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )
    return response.choices[0].message.content

# --------------------------------------------------
# Test
# --------------------------------------------------
if __name__== "__main__":

    question = input(
        "Ask question about WCE: "
    )

    answer = generate_answer(question)

    print(f"\n Answer:{answer}")
