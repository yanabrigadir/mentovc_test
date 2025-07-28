import asyncio
import logging

from db.database import async_session_maker
from services.company_service import CompanyService
from services.stream_scraper_service import StreamScraperService


async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    company_service = CompanyService(async_session_maker)
    scraper = StreamScraperService(company_service)

    while True:
        try:
            await scraper.parse_ycombinator_site()
        except Exception as e:
            logging.error(f"Error in scraper: {e}")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())