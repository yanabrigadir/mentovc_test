import asyncio
import logging

from db.database import async_session_maker
from services.company_service import CompanyService
from services.stream_scraper_service import StreamScraperService
from script import load_and_convert_cookies, JSON_COOKIE_PATH


async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    ln_cookie = load_and_convert_cookies(JSON_COOKIE_PATH)
    company_service = CompanyService(async_session_maker)
    scraper = StreamScraperService(company_service, ln_cookie)

    while True:
        try:
            await asyncio.gather(
                scraper.parse_ycombinator_site(),
                scraper.parse_linkedin(),
                return_exceptions=True
            )
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())