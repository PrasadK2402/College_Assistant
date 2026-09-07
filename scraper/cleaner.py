from pathlib import Path
import re 
import sys


def clean_page(markdown: str) -> str:

    lines = markdown.splitlines()

    start_index = None
    # Find the first ## heading after the page title.
    for i, line in enumerate(lines):
        if line.startswith("## "):
            start_index = i
            break

    if start_index is None:
        raise ValueError("Could not find page content heading")

    content_lines = []

    for line in lines[start_index:]:
        # Stop before website sharing/footer section
        if line.strip().lower() == "* share this page,":
            break

        content_lines.append(line)

    content = "\n".join(content_lines).strip()
      # Remove image-only Markdown
    content = re.sub(r"!\[[^\]]*\]\([^)]+\)\n?", "", content)

    # Remove excessive blank lines
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content  

def clean_file(input_file: Path, output_file: Path):
    markdown = input_file.read_text(encoding="utf-8")

    cleaned = clean_page(markdown)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_file.write_text(
        cleaned,
        encoding="utf-8"
    )

    print("✅ Cleaning successful")
    print(f"📥 Input : {input_file}")
    print(f"📤 Output: {output_file}")
    print(f"📝 Characters: {len(cleaned)}")

def main():
    input_dir = Path("data/raw")
    output_dir = Path("data/clean")

    files = list(input_dir.glob("*.md"))

    if not files:
        print("❌ No Markdown files found")
        return

    print(f"Found {len(files)} Markdown files")

    successful = 0
    failed = 0

    for input_file in files:
        output_file = output_dir / input_file.name

        try:
            clean_file(input_file, output_file)
            successful += 1

        except Exception as error:
            failed += 1
            print(f"❌ Failed: {input_file.name}")
            print(f"   Reason: {error}")

    print()
    print("=" * 50)
    print("Cleaning finished")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed:     {failed}")
    print("=" * 50)


if __name__ == "__main__":
    main()