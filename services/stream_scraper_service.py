import asyncio
import logging
import re
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup

from services.company_service import CompanyService


class StreamScraperService:
    def __init__(self, company_service: CompanyService, linkedin_cookies: list):
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        self.BASE_URL = "https://www.ycombinator.com"
        self.url = "https://www.ycombinator.com/companies?batch=Spring%202025"
        self.linkedin_url = "https://linkedin.com/search/results/companies/?keywords=YC%20S25&origin=CLUSTER_EXPANSION&sid=AoG"
        self.company_service = company_service
        self.linkedin_cookies = linkedin_cookies

    async def parse_page(self, html: str) -> int:
        """Parse HTML and save new companies to the database. Return count of new companies."""
        soup = BeautifulSoup(html, 'html.parser')
        new_company_count = 0

        # Find company cards
        companies = soup.find_all('a', class_=re.compile(r'.*_company.*'))
        if not companies:
            logging.warning("No company cards found on Y Combinator page")

        # Extract and save data from each company card
        for company in companies:
            name = company.find('span', class_=re.compile(r'.*coName.*'))
            location = company.find('span', class_=re.compile(r'.*coLocation.*'))
            description = company.find('div', class_=re.compile(r'.*text-sm.*'))
            description = description.find('span') if description else None

            name_text = name.text.strip() if name and name.text.strip() else None
            if not name_text:  # Skip if name is missing
                continue
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
                new_company_count += 1

        return new_company_count

    async def scroll_and_parse(self, page: Page) -> int:
        """Parse visible content, scroll, and save new companies. Return total new companies."""
        total_new_companies = 0

        # Parse initial content
        html = await page.content()
        new_companies = await self.parse_page(html)
        total_new_companies += new_companies
        logging.info(f"Y Combinator initial parse: found {new_companies} new companies")

        # Scroll until no new content is loaded
        last_height = await page.evaluate("document.body.scrollHeight")
        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            new_height = await page.evaluate("document.body.scrollHeight")

            html = await page.content()
            new_companies = await self.parse_page(html)
            total_new_companies += new_companies
            logging.info(f"Y Combinator scroll: added {new_companies} new companies")

            if new_height == last_height:
                logging.info("Y Combinator scrolling complete: no new data loaded")
                break
            last_height = new_height

        return total_new_companies

    async def parse_ycombinator_site(self) -> None:
        """Scrape Y Combinator website with real-time updates."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=self.user_agent)

            try:
                while True:
                    try:
                        await page.goto(self.url, wait_until="networkidle", timeout=30000)
                        new_companies = await self.scroll_and_parse(page)
                        logging.info(f"Y Combinator total new companies: {new_companies}")
                        await asyncio.sleep(30)
                    except Exception as e:
                        logging.error(f"Y Combinator error: {e}")
                        await asyncio.sleep(3)
            except KeyboardInterrupt:
                logging.info("Y Combinator scraping stopped by user")
            finally:
                await browser.close()

    async def parse_page_linkedin(self, html: str) -> int:
        """Parse LinkedIn HTML and save new companies. Return count of new companies."""
        soup = BeautifulSoup(html, 'html.parser')
        new_company_count = 0

        # Find company cards
        companies = soup.find('ul', role="list")
        companies = companies.find_all("li") if companies else []
        if not companies:
            logging.warning("No company cards found on LinkedIn page")

        # Extract and save data from each company card
        for company in companies:
            name = company.find("div", class_="t-roman t-sans") or None
            if not name:
                continue
            name = name.find("a")
            location = company.find('div', class_=re.compile(r'.*t-14 t-black t-normal.*'))
            description = company.find('p', class_=re.compile(r'.*entity-result__summary--2-lines.*'))

            location_pattern = r'•\s*([^\n<]+?)(?=<|$)'
            location_text = None
            if location and location.text.strip():
                match = re.search(location_pattern, location.text.strip())
                location_text = match.group(1).strip() if match else "N/A"

            name_text = name.text.strip() if name and name.text.strip() else "N/A"
            if name_text != "N/A":
                name_text = re.sub(r'\s*\(YC S25\)', '', name_text).strip()
            desc_text = description.text.strip() if description and description.text.strip() else "N/A"
            href = name.get('href') if name else None
            link = href if href and href.strip() else "N/A"

            # Check and save new company to database
            existing_company = await self.company_service.get_by_name(name_text)
            if not existing_company:
                await self.company_service.create_new(
                    name=name_text,
                    location=location_text if location_text else "N/A",
                    description=desc_text,
                    link=link
                )
                new_company_count += 1

        return new_company_count

    async def scroll_and_parse_linkedin(self, page: Page) -> int:
        """Parse LinkedIn content, scroll, and save new companies. Return total new companies."""
        total_new_companies = 0

        # Parse initial content
        html = await page.content()
        new_companies = await self.parse_page_linkedin(html)
        total_new_companies += new_companies
        logging.info(f"LinkedIn initial parse: found {new_companies} new companies")

        # Scroll until no new content is loaded
        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            button = page.locator('.artdeco-pagination__button--next')
            if await button.get_attribute('disabled') == '':
                logging.info("LinkedIn scrolling complete: no new data loaded")
                break
            await button.click()
            await asyncio.sleep(1)

            html = await page.content()
            new_companies = await self.parse_page_linkedin(html)
            total_new_companies += new_companies
            logging.info(f"LinkedIn scroll: added {new_companies} new companies")

        return total_new_companies

    async def parse_linkedin(self) -> None:
        """Scrape LinkedIn with real-time updates."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.user_agent)
            await context.add_cookies(self.linkedin_cookies)
            page = await context.new_page()

            try:
                while True:
                    try:
                        await page.goto(self.linkedin_url, wait_until="load", timeout=30000)
                        await asyncio.sleep(2)
                        new_companies = await self.scroll_and_parse_linkedin(page)
                        logging.info(f"LinkedIn total new companies: {new_companies}")
                        await asyncio.sleep(30)
                    except Exception as e:
                        logging.error(f"LinkedIn error: {e}")
                        await asyncio.sleep(3)
            except KeyboardInterrupt:
                logging.info("LinkedIn scraping stopped by user")
            finally:
                await context.close()
                await browser.close()