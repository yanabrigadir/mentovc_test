import asyncio
import logging
import re
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup

from services.company_service import CompanyService


class StreamScraperService:
    def __init__(self, company_service: CompanyService):
        # Initialize base URL and target URL for Y Combinator
        self.BASE_URL = "https://www.ycombinator.com"
        self.url = "https://www.ycombinator.com/companies?batch=Spring%202025"
        self.company_service = company_service

    async def parse_page(self, html: str) -> list:
        """Parse HTML and return a list of new companies."""
        soup = BeautifulSoup(html, 'html.parser')
        companies_data = []

        # Find company cards
        companies = soup.find_all('a', class_=re.compile(r'.*_company.*'))
        if not companies:
            logging.warning("No company cards found, possibly incorrect class")

        # Extract data from each company card
        for company in companies:
            name = company.find('span', class_=re.compile(r'.*coName.*'))
            location = company.find('span', class_=re.compile(r'.*coLocation.*'))
            description = company.find('div', class_=re.compile(r'.*text-sm.*')).find('span') if company.find('div', class_=re.compile(r'.*text-sm.*')) else None

            name_text = name.text.strip() if name and name.text.strip() else "N/A"
            location_text = location.text.strip() if location and location.text.strip() else "N/A"
            desc_text = description.text.strip() if description and description.text.strip() else "N/A"
            href = company.get('href')
            link = f"{self.BASE_URL}{href}" if href and href.strip() else "N/A"

            # Check and save new company to database
            existing_company = await self.company_service.get_by_name(name_text)
            if not existing_company:
                await self.company_service.create_new(
                    name=name_text,
                    location=location_text,
                    description=desc_text,
                    link=link
                )
                companies_data.append({
                    "name": name_text,
                    "location": location_text,
                    "description": desc_text,
                    "link": link
                })

        return companies_data

    async def scroll_and_parse(self, page: Page) -> list:
        """Parse visible content, scroll, and parse new data."""
        all_companies = []

        # Parse initial content
        html = await page.content()
        companies = await self.parse_page(html)
        all_companies.extend(companies)
        logging.info(f"Initial parse: found {len(companies)} companies")

        # Scroll until no new content is loaded
        last_height = await page.evaluate("document.body.scrollHeight")
        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            new_height = await page.evaluate("document.body.scrollHeight")

            html = await page.content()
            companies = await self.parse_page(html)
            all_companies.extend(companies)
            logging.info(f"Scroll: added {len(companies)} new companies")

            if new_height == last_height:
                logging.info("Scrolling complete: no new data loaded")
                break
            last_height = new_height

        return all_companies

    async def parse_ycombinator_site(self) -> None:
        """Scrape Y Combinator website with real-time updates."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )

            try:
                while True:
                    try:
                        # Navigate and scrape
                        await page.goto(self.url, wait_until="networkidle")
                        companies = await self.scroll_and_parse(page)
                        logging.info(f"Total companies found: {len(companies)}")

                        # Pause for real-time updates
                        await asyncio.sleep(30)
                    except Exception as e:
                        logging.error(f"Error: {e}")
                        await asyncio.sleep(3)
            except KeyboardInterrupt:
                logging.info("Scraping stopped by user")
            finally:
                await browser.close()
