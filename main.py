import re
from playwright.async_api import async_playwright
import asyncio
from bs4 import BeautifulSoup
import logging
from services.stream_scraper_service import StreamScraperService


async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    scraper = StreamScraperService()
    await scraper.parse_ycombinator_site()


if __name__ == "__main__":
    asyncio.run(main())