import json
import os
import re
from time import sleep

from dotenv import load_dotenv
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from unidecode import unidecode


load_dotenv()

IS_DEVELOPMENT: bool = os.getenv("ENV", "development") == 'development'
DATABASE_PATH: str = os.getenv("FILE_PATH", "cars.txt")
SEARCH_FOR = ["تیبا", "کوییک", "کوئیک", "quick"]
MAX_PRICE = 270_000_000
MIN_PRICE = 200_000_000


class DivarAdsCrawler:
    browser = None
    opts = None

    def __init__(self, headless: bool = True):
        self.opts = Options()
        if headless:
            self.opts.add_argument("--headless")

    def start(self):
        self.browser = Firefox(options=self.opts)

    def get_ads(self, ads_url: str = 'https://divar.ir/s/tehran/car?q=%D8%AA%DB%8C%D8%A8%D8%A7'):
        try:
            self.browser.get(ads_url)
        except Exception as e:
            print("Failed to fetch ads_url\nDetails: " + e)
            return None

        sleep(5 if IS_DEVELOPMENT else 1)

        for i in range(5):
            print(i)
            self.browser.execute_script("window.scrollTo(0, window.scrollMaxY)")
            sleep(2 if IS_DEVELOPMENT else 1)

        ads = self.browser.find_element(
            By.XPATH, "//div[starts-with(@class, 'browse-post-list-')]"
        )

        return ads

    def ads_parser(self, ads):
        fetched_cars = []
        all_cars = []
        for ad in ads.find_elements(By.XPATH, "//div[starts-with(@class, 'post-card-item')]"):
            link_elm = ad.find_element(By.TAG_NAME, "a")

            car_link = link_elm.get_attribute("href")
            if "karnameh" in car_link:
                continue

            title_elm = ad.find_element(By.CLASS_NAME, "kt-post-card__title")
            price_elms = ad.find_elements(
                By.CLASS_NAME, "kt-post-card__description")
            car_title = ""

            if len(title_elm.text) == 0:
                continue

            car_title = title_elm.text
            if not self.is_title_match(title_elm.text):
                continue

            for price_elm in price_elms:
                if not ("تومان" in price_elm.text):
                    continue
                else:
                    car_price = int(price_elm.text.replace(
                        "تومان", "").replace(",", ""))

            if car_price > MAX_PRICE or car_price < MIN_PRICE:
                continue

            fetched_cars.append(
                json.dumps(
                    {"link": car_link, "price": car_price, "title": car_title}
                )
            )

            return fetched_cars

    def update_and_get_unique_cars(self, fetched_cars):
        cars_file = open(DATABASE_PATH, "a+")

        for line in cars_file:
            if len(line.strip()) > 0:
                all_cars.append(line.strip())

        new_ads = set(fetched_cars) ^ set(all_cars)

        for fetched_car in fetched_cars:
            cars_file.write(fetched_car + "\n")

        return new_ads

    def is_title_match(self, title: str):
        for car in SEARCH_FOR:
            if car in title:
                return True

        return False

    def stop(self):
        self.browser.close()


if __name__ == '__main__':
    c = DivarAdsCrawler()
    c.start()
    ads = c.ads_parser(c.get_ads())
    unique_ads = c.update_and_get_unique_cars(ads)
    c.stop()
    print(unique_ads)