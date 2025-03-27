from zoneinfo import available_timezones

import requests
from bs4 import BeautifulSoup
import time
import re
import sqlite3

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

base_url = "https://rozetka.com.ua/ua/mobile-phones/c80003/"
response = requests.get(f"{base_url}producer=apple/", headers)
soup = BeautifulSoup(response.text, "html.parser")
pattern = re.compile(r"Сторінка 1 з ", re.IGNORECASE)
last_page_number = int(soup.find("div", string=pattern).get_text().split()[-1])

page = 1

with sqlite3.connect("rozetka.db") as conn:
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS apples')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            link TEXT,
            image_url TEXT,
            availability TEXT)
        ''')

    while page <= last_page_number:
        url = f"{base_url}page={page};producer=apple/" if page != 1 else f"{base_url}producer=apple/"
        print(f"📄 Обробка сторінки {page}...")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ Помилка: {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        products = soup.find_all("div", class_="goods-tile")

        for product in products:
            title_tag = product.find("span", class_="goods-tile__title")
            price_tag = product.find("span", class_="goods-tile__price-value")
            link_tag = product.find("a")
            image_tag = product.find("img")
            availability_tag = product.find("div", class_="goods-tile__availability")

            product_price = float(price_tag.get_text().strip().replace("\xa0", "")[:-1]) if price_tag else None
            product_name = title_tag.get_text() if title_tag else None
            availability = availability_tag.get_text() if availability_tag else None
            product_link = link_tag['href'] if link_tag else None
            product_image = image_tag['src'] if image_tag else None
            cursor.execute(f'''
                INSERT INTO apples (name, price, link, image_url, availability) 
    VALUES (?, ?, ?, ?, ?)
    ''', (product_name, product_price, product_link, product_image, availability))
            
            print(f"📌 {product_name}")
            print(f"💰 Ціна: {product_price}")
            print(f"🔗 Посилання: {product_link}")
            print(f"🖼 Зображення: {product_image}")
            print(availability)
            print("-" * 50)

        page += 1
        time.sleep(2)
