import re
from playwright.async_api import async_playwright
import asyncio
from bs4 import BeautifulSoup
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def scroll_to_bottom(page):
    last_height = await page.evaluate("document.body.scrollHeight")
    while True:
        # Прокручиваем вниз
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        # Ждем подгрузки новых данных
        await asyncio.sleep(2)  # Пауза для загрузки
        # Проверяем новую высоту страницы
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break  # Если высота не изменилась, прокрутка завершена
        last_height = new_height


async def parse_website():
    url = "https://www.ycombinator.com/companies?batch=Spring%202025"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )

        while True:
            try:
                await page.goto(url, wait_until="networkidle")

                # Прокручиваем до конца
                await scroll_to_bottom(page)

                html = await page.content()

                # Парсим HTML с BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')

                # Ищем карточки компаний (классы могут отличаться, проверь через F12)
                companies = soup.find_all('a', class_=re.compile(r'.*_company.*'))
                if not companies:
                    logging.warning("Карточки компаний не найдены, возможно, неверный класс")

                for company in companies:
                    name = company.find('span', class_=re.compile(r'.*coName.*'))
                    location = company.find('span', class_=re.compile(r'.*coLocation.*'))
                    description = company.find('div', class_=re.compile('.*text-sm')).find('span')

                    name_text = name.text.strip() if name else "N/A"
                    location_text = location.text.strip() if location else "N/A"
                    desc_text = description.text.strip() if description else "N/A"

                    logging.info(f"Компания: {name_text}, Расположение: {location_text}, Описание: {desc_text}")

                # Пауза 60 секунд для real-time обновления
                await asyncio.sleep(60)
            except Exception as e:
                logging.error(f"Ошибка: {e}")
                await asyncio.sleep(5)  # Задержка при ошибке

        await browser.close()

async def main():
    await parse_website()


if __name__ == "__main__":
    asyncio.run(main())