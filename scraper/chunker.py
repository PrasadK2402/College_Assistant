from pathlib import Path
import re

INPUT_DIR = Path("data/clean")
OUTPUT_DIR = Path("data/chunks")

MAX_CHARS = 3000
OVERLAP = 300

def split_by_headings(markdown:str) -> list[dict]:
    """ 
    Split Markdown into sections using ## heading.
    """

    lines = markdown.splitlines()

    sections = []
    current_title = None
    current_lines = []

    for line in lines:

        if line.startswith("## "):

            # Save previous section
            if current_title is not None:
                sections.append({
                    "title": current_title,
                    "content": "\n".join(current_lines).strip()
                })

            current_title = line[3:].strip()
            current_lines = []

        else:
            current_lines.append(line)

    # Save final section
    if current_title is not None:
        sections.append({
            "title": current_title,
            "content": "\n".join(current_lines).strip()
        })

    return sections

def split_large_text(text: str) -> list[str]:
    """
    Split large text into smaller chunks with overlap.
    """

    if len(text) <= MAX_CHARS:
        return [text]

    chunks = []

    start = 0

    while start < len(text):

        end = start + MAX_CHARS

        chunk = text[start:end]

        chunks.append(chunk.strip())

        if end >= len(text):
            break

        start = end - OVERLAP

    return chunks

def create_chunks(markdown: str, source: str) -> list[dict]:

    sections = split_by_headings(markdown)

    chunks = []

    for section in sections:

        title = section["title"]
        content = section["content"]

        if not content:
            continue

        text = f"{title}\n\n{content}"

        section_chunks = split_large_text(text)

        for index, chunk in enumerate(section_chunks):

            chunks.append({
            "source": source,
            "section": title,
            "chunk_index": index,
            "text": chunk
        })

    return chunks

def process_file(input_file: Path):

    markdown = input_file.read_text(encoding="utf-8")

    chunks = create_chunks(
        markdown,
        input_file.name
    )

    output_file = OUTPUT_DIR / f"{input_file.stem}.txt"

    with output_file.open("w", encoding="utf-8") as file:

            for index, chunk in enumerate(chunks):

                file.write(f"--- CHUNK {index} ---\n")
                file.write(f"Source: {chunk['source']}\n")
                file.write(f"Section: {chunk['section']}\n")
                file.write("\n")
                file.write(chunk["text"])
                file.write("\n\n")

    print(
        f"✅ {input_file.name}: "
        f"{len(chunks)} chunks"
    )

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    files = list(
        INPUT_DIR.glob("*.md")
    )

    if not files:
        print("❌ No cleaned Markdown files found")
        return

    print(
            f"Found {len(files)} cleaned files"
    )

    total_chunks = 0

    for input_file in files:

        try:

            process_file(input_file)

        except Exception as error:

            print(
                f"❌ Failed: {input_file.name}"
            )

            print(
                f"   Reason: {error}"
            )

    print()
    print("=" * 50)
    print("Chunking finished")
    print("=" * 50)


if __name__ == "__main__":
    main()