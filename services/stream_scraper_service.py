import asyncio
import logging
import re
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup


class StreamScraperService:
    def __init__(self):
        self.url = "https://www.ycombinator.com/companies?batch=Spring%202025"
        self.seen_companies = set()  # Множество для отслеживания уникальных компаний

    async def parse_page(self, html: str) -> list:
        """Парсит HTML и возвращает список новых компаний"""
        soup = BeautifulSoup(html, 'html.parser')
        companies_data = []

        # Ищем <a> элементы с классом, содержащим '_company'
        companies = soup.find_all('a', class_=re.compile(r'.*_company.*'))
        if not companies:
            logging.warning("Карточки компаний не найдены, возможно, неверный класс")

        for company in companies:
            name = company.find('span', class_=re.compile(r'.*coName.*'))
            location = company.find('span', class_=re.compile(r'.*coLocation.*'))
            description = company.find('div', class_=re.compile(r'.*text-sm.*')).find('span') if company.find('div', class_=re.compile(r'.*text-sm.*')) else None

            name_text = name.text.strip() if name and name.text.strip() else "N/A"
            location_text = location.text.strip() if location and location.text.strip() else "N/A"
            desc_text = description.text.strip() if description and description.text.strip() else "N/A"
            link = company.get('href', 'N/A')

            # Проверяем, не видели ли эту компанию
            company_id = (name_text, link)
            if company_id not in self.seen_companies:
                self.seen_companies.add(company_id)
                company_data = {
                    "name": name_text,
                    "location": location_text,
                    "description": desc_text,
                    "link": link
                }
                companies_data.append(company_data)
                logging.info(f"Компания: {name_text}, Расположение: {location_text}, Описание: {desc_text}, Ссылка: {link}")

        return companies_data

    async def scroll_and_parse(self, page: Page) -> list:
        """Парсит видимую часть, затем прокручивает и парсит новые данные"""
        all_companies = []
        self.seen_companies.clear()  # Очищаем для нового цикла парсинга

        # Парсим начальную видимую часть
        html = await page.content()
        companies = await self.parse_page(html)
        all_companies.extend(companies)
        logging.info(f"Начальная часть: найдено {len(companies)} компаний")

        # Прокручиваем постепенно
        last_height = await page.evaluate("document.body.scrollHeight")
        while True:
            # Прокручиваем до конца текущей высоты
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            # Ждем подгрузки новых данных
            await asyncio.sleep(2)
            # Проверяем новую высоту
            new_height = await page.evaluate("document.body.scrollHeight")

            # Парсим новые данные
            html = await page.content()
            companies = await self.parse_page(html)
            all_companies.extend(companies)
            logging.info(f"Скролл: добавлено {len(companies)} новых компаний")

            if new_height == last_height:
                logging.info("Скролл завершён: новые данные не подгружаются")
                break
            last_height = new_height

        return all_companies

    async def parse_ycombinator_site(self) -> None:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )

            try:
                while True:
                    try:
                        await page.goto(self.url, wait_until="networkidle")
                        # Прокручиваем и парсим данные
                        companies = await self.scroll_and_parse(page)
                        logging.info(f"Всего найдено компаний: {len(companies)}")

                        # Пауза 30 секунд для real-time обновления
                        await asyncio.sleep(30)
                    except Exception as e:
                        logging.error(f"Ошибка: {e}")
                        await asyncio.sleep(3)
            except KeyboardInterrupt:
                logging.info("Парсинг остановлен пользователем")
            finally:
                await browser.close()
