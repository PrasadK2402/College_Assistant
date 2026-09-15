import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")

if not JINA_API_KEY:
    raise ValueError("JINA_API_KEY is not set in .env")


JINA_URL = "https://api.jina.ai/v1/embeddings"
MODEL = "jina-embeddings-v3"

EMBEDDINGS_FILE = Path(
    "data/embeddings/embeddings.json"
)


# --------------------------------------------------
# Load stored embeddings
# --------------------------------------------------

def load_embeddings():
    """Load our stored WCE embeddings."""

    with open(
        EMBEDDINGS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# --------------------------------------------------
# Create query embedding
# --------------------------------------------------

def create_query_embedding(query):
    """Convert the user's question into an embedding."""

    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL,
        "task": "retrieval.query",
        "input": [query],
    }

    response = requests.post(
        JINA_URL,
        headers=headers,
        json=data,
    )

    if not response.ok:
        print("Jina API error:")
        print(response.text)

    response.raise_for_status()

    result = response.json()

    return result["data"][0]["embedding"]


# --------------------------------------------------
# Cosine similarity
# --------------------------------------------------

def cosine_similarity(vector_a, vector_b):
    """Calculate cosine similarity between two vectors."""

    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = sum(
        a * a
        for a in vector_a
    ) ** 0.5

    magnitude_b = sum(
        b * b
        for b in vector_b
    ) ** 0.5

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (
        magnitude_a * magnitude_b
    )


# --------------------------------------------------
# Search
# --------------------------------------------------

def search(query, top_k=3):
    """
    Find the most relevant WCE chunks
    for a user's question.
    """

    records = load_embeddings()

    query_embedding = create_query_embedding(query)

    results = []

    for record in records:

        score = cosine_similarity(
            query_embedding,
            record["embedding"]
        )

        results.append(
            {
                "source": record["source"],
                "text": record["text"],
                "score": score,
            }
        )

    # Highest similarity first
    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:top_k]


# --------------------------------------------------
# Test search
# --------------------------------------------------

if __name__ == "__main__":

    question = input(
        "Ask a question about WCE: "
    )

    results = search(
        question,
        top_k=3
    )

    print("\nTop results:\n")

    for index, result in enumerate(
        results,
        start=1
    ):

        print(
            f"--- Result {index} ---"
        )

        print(
            f"Score: {result['score']:.4f}"
        )

        print(
            f"Source: {result['source']}"
        )

        print(
            f"\n{result['text']}"
        )

        print()