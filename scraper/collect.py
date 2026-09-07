import asyncio
from pathlib import Path

from crawler import crawl_page


URL_FILE = Path("data/urls/wce_urls.txt")


def load_urls() -> list[str]:
    urls = []

    for line in URL_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        # Ignore empty lines and comments
        if not line or line.startswith("#"):
            continue

        urls.append(line)

    return urls


async def main():
    urls = load_urls()

    print(f"Found {len(urls)} URLs")

    for index, url in enumerate(urls, start=1):
        print()
        print("=" * 60)
        print(f"[{index}/{len(urls)}] Crawling")
        print(url)
        print("=" * 60)

        try:
            await crawl_page(url)
        except Exception as error:
            print(f"❌ Error: {error}")

    print()
    print("🎉 Collection finished")


if __name__ == "__main__":
    asyncio.run(main())