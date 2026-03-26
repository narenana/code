"""
Base scraper class shared by all store scrapers.
"""
import time
import random
import logging
from dataclasses import dataclass, field
from typing import Optional
import requests
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


@dataclass
class ScrapedProduct:
    name: str
    brand: str
    category: str
    price_inr: float
    product_url: str
    image_url: str
    store_id: str
    stock: str = "in_stock"       # in_stock | out_of_stock | unknown
    description: str = ""
    specs: dict = field(default_factory=dict)
    sku: str = ""


FPV_CATEGORY_KEYWORDS = {
    "frame":             ["frame", "chassis"],
    "flight_controller": ["flight controller", "fc ", "f4 ", "f7 ", "f405", "f722", "f7 ", "betaflight"],
    "esc":               ["esc", "speed controller", "blheli", "4-in-1"],
    "motor":             ["motor", "stator", "kv"],
    "battery":           ["lipo", "battery", "lihv", "6s", "4s", "3s"],
    "vtx":               ["vtx", "video transmitter", "air unit", "avatar", "walksnail", "dji o3"],
    "receiver":          ["receiver", "rx ", "elrs", "expressLRS", "frsky", "crossfire"],
    "camera":            ["fpv camera", "cmos", "starlight"],
    "propeller":         ["prop", "propeller", "blade"],
}


def guess_category(name: str, description: str = "") -> str:
    text = (name + " " + description).lower()
    for category, keywords in FPV_CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "other"


def guess_brand(name: str) -> str:
    known_brands = [
        "iflight", "betafpv", "speedybee", "holybro", "dji", "t-motor",
        "emax", "flywoo", "geprc", "radiomaster", "expresslrs", "tattu",
        "hglrc", "foxeer", "runcam", "rushfpv", "luminier", "impulserc",
        "rotor riot", "shen drones", "tbs", "team blacksheep",
    ]
    name_lower = name.lower()
    for brand in known_brands:
        if brand in name_lower:
            return brand.title()
    # Return first word as brand guess
    return name.split()[0] if name else "Unknown"


class BaseScraper:
    store_id: str = ""
    store_name: str = ""
    base_url: str = ""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            ua = UserAgent()
            user_agent = ua.random
        except Exception:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept-Language": "en-IN,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        try:
            resp = self.session.get(url, timeout=15, **kwargs)
            resp.raise_for_status()
            time.sleep(random.uniform(1.0, 2.5))   # polite delay
            return resp
        except requests.RequestException as e:
            self.logger.warning(f"GET {url} failed: {e}")
            return None

    def scrape(self) -> list[ScrapedProduct]:
        raise NotImplementedError

    def run(self) -> list[ScrapedProduct]:
        self.logger.info(f"Starting scrape of {self.store_name} ({self.base_url})")
        products = self.scrape()
        self.logger.info(f"Finished — {len(products)} products found")
        return products
