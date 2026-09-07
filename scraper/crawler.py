import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig 


def get_filename(url:str) -> str:
    path = urlparse(url).path.strip("/")

    if not path:
        return "index"

    name = path.split("/")[-1]

    return name or "index"

async def crawl_page(url:str):
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)


    filename= get_filename(url)
    output_file = output_dir / f"{filename}.md"

    config = CrawlerRunConfig(
        word_count_threshold=50
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            config=config
        )

        if not result.success:
            print("❌ Crawling failed")
            print(result.error_message)
            return

        
        output_file.write_text(
            result.markdown,
            encoding="utf-8"
        )

        print("✅ Crawling successful")
        print(f"🌐 URL: {url}")
        print(f"📄 Saved to: {output_file}")
        print(f"📝 Characters: {len(result.markdown)}")


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print('python scraper/crawler.py "<URL>"')
        return

    url = sys.argv[1]

    asyncio.run(crawl_page(url))


if __name__ == "__main__":
    main()