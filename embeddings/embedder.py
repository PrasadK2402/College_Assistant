import json
import os
from pathlib import Path

import requests
import tiktoken
from dotenv import load_dotenv


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")

if not JINA_API_KEY:
    raise ValueError("JINA_API_KEY is not set in .env")


# --------------------------------------------------
# Jina configuration
# --------------------------------------------------

JINA_URL = "https://api.jina.ai/v1/embeddings"
MODEL = "jina-embeddings-v3"


# --------------------------------------------------
# Project paths
# --------------------------------------------------

CHUNKS_DIR = Path("data/chunks")
OUTPUT_FILE = Path("data/embeddings/embeddings.json")


# --------------------------------------------------
# Token limits
# --------------------------------------------------

# We keep this comfortably below Jina's 8194-token limit.
MAX_CHUNK_TOKENS = 6000

# Maximum estimated tokens sent in one API request.
MAX_BATCH_TOKENS = 7500


# --------------------------------------------------
# Tokenizer
# --------------------------------------------------

TOKENIZER = tiktoken.get_encoding(" ")


def count_tokens(text):
    """Return the estimated token count for text."""

    return len(TOKENIZER.encode(text))


# --------------------------------------------------
# Split large chunks
# --------------------------------------------------

def split_large_chunk(text, max_tokens=MAX_CHUNK_TOKENS):
    """
    Split a large text into smaller token-based pieces.

    We use a conservative token limit because
    Jina's tokenizer can count differently from
    tiktoken.
    """

    tokens = TOKENIZER.encode(text)

    pieces = []

    for start in range(0, len(tokens), max_tokens):

        token_slice = tokens[start:start + max_tokens]

        piece = TOKENIZER.decode(token_slice)

        pieces.append(piece)

    return pieces


# --------------------------------------------------
# Load chunks
# --------------------------------------------------

def load_chunks():
    """
    Load chunks from data/chunks/.

    If a chunk is too large, split it into
    smaller pieces.
    """

    chunks = []

    for file_path in sorted(CHUNKS_DIR.glob("*.txt")):

        text = file_path.read_text(
            encoding="utf-8"
        ).strip()

        if not text:
            continue

        token_count = count_tokens(text)

        print(
            f"{file_path.name}: "
            f"{len(text)} chars, "
            f"{token_count} tokens"
        )

        # ------------------------------------------
        # Normal chunk
        # ------------------------------------------

        if token_count <= MAX_CHUNK_TOKENS:

            chunks.append(
                {
                    "source": file_path.name,
                    "text": text,
                    "tokens": token_count,
                }
            )

        # ------------------------------------------
        # Large chunk
        # ------------------------------------------

        else:

            print(
                f"  → Splitting {file_path.name} "
                f"into smaller pieces..."
            )

            pieces = split_large_chunk(text)

            for index, piece in enumerate(pieces):

                piece_tokens = count_tokens(piece)

                chunks.append(
                    {
                        "source": file_path.name,
                        "chunk_id": index,
                        "text": piece,
                        "tokens": piece_tokens,
                    }
                )

                print(
                    f"     Part {index}: "
                    f"{piece_tokens} tokens"
                )

    return chunks


# --------------------------------------------------
# Create token-aware batches
# --------------------------------------------------

def create_batches(chunks):
    """
    Create API batches without exceeding
    MAX_BATCH_TOKENS.
    """

    batches = []

    current_batch = []
    current_tokens = 0

    for chunk in chunks:

        tokens = chunk["tokens"]

        # If adding this chunk would exceed
        # the batch limit, finish current batch.
        if (
            current_batch
            and current_tokens + tokens > MAX_BATCH_TOKENS
        ):
            batches.append(current_batch)

            current_batch = []
            current_tokens = 0

        current_batch.append(chunk)
        current_tokens += tokens

    # Add final batch
    if current_batch:
        batches.append(current_batch)

    return batches


# --------------------------------------------------
# Call Jina API
# --------------------------------------------------

def create_embeddings(texts):
    """Create embeddings for a batch of texts."""

    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL,
        "task": "retrieval.passage",
        "input": texts,
    }

    response = requests.post(
        JINA_URL,
        headers=headers,
        json=data,
    )

    if not response.ok:

        print("\n❌ Jina API error:")
        print(response.text)

    response.raise_for_status()

    result = response.json()

    return [
        item["embedding"]
        for item in result["data"]
    ]


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    # ----------------------------------------------
    # 1. Load chunks
    # ----------------------------------------------

    chunks = load_chunks()

    print(
        f"\nFound {len(chunks)} chunks "
        f"after splitting."
    )

    if not chunks:
        raise ValueError(
            "No chunks found in data/chunks/"
        )


    # ----------------------------------------------
    # 2. Create batches
    # ----------------------------------------------

    batches = create_batches(chunks)

    print(
        f"Created {len(batches)} batches."
    )


    # ----------------------------------------------
    # 3. Generate embeddings
    # ----------------------------------------------

    records = []

    for batch_number, batch in enumerate(
        batches,
        start=1
    ):

        batch_tokens = sum(
            chunk["tokens"]
            for chunk in batch
        )

        print(
            f"\nEmbedding batch "
            f"{batch_number}/{len(batches)} "
            f"({batch_tokens} estimated tokens)..."
        )

        texts = [
            chunk["text"]
            for chunk in batch
        ]

        embeddings = create_embeddings(texts)

        if len(embeddings) != len(batch):

            raise ValueError(
                "Number of embeddings does not match "
                "number of chunks in batch."
            )

        # ------------------------------------------
        # Store embedding + metadata
        # ------------------------------------------

        for chunk, embedding in zip(
            batch,
            embeddings
        ):

            record = {
                "source": chunk["source"],
                "text": chunk["text"],
                "embedding": embedding,
            }

            # Add chunk_id only for split chunks
            if "chunk_id" in chunk:
                record["chunk_id"] = chunk["chunk_id"]

            records.append(record)

        print(
            f"Batch complete: "
            f"{len(records)}/{len(chunks)}"
        )


    # ----------------------------------------------
    # 4. Create output directory
    # ----------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    # ----------------------------------------------
    # 5. Save embeddings
    # ----------------------------------------------

    OUTPUT_FILE.write_text(
        json.dumps(records),
        encoding="utf-8"
    )


    # ----------------------------------------------
    # 6. Final summary
    # ----------------------------------------------

    print(
        "\n✅ Embeddings created successfully!"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print(
        f"Total embeddings: {len(records)}"
    )

    print(
        f"Embedding dimensions: "
        f"{len(records[0]['embedding'])}"
    )


if __name__ == "__main__":
    main()