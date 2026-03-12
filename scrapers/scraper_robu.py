"""
Scraper for Robu.in — FPV/RC category
Uses requests + BeautifulSoup for static pages.
Run: python scrapers/scraper_robu.py
"""
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

STORE_ID = "robu"  # Match your Supabase store ID
BASE_URL = "https://robu.in"
CATEGORY_URLS = [
    "/category/fpv-racing-drones/",
    "/category/flight-controller/",
    "/category/electronic-speed-controller/",
    "/category/brushless-motor/",
    "/category/fpv-cameras/",
    "/category/fpv-video-transmitter/",
    "/category/lipo-battery/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FPVIndia-bot/1.0)",
    "Accept-Language": "en-IN,en;q=0.9",
}


def scrape_listing_page(url: str) -> list[dict]:
    """Scrape all products from a category listing page."""
    products = []
    page = 1
    while True:
        paged_url = f"{url}page/{page}/" if page > 1 else url
        resp = requests.get(BASE_URL + paged_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("li.product")
        if not items:
            break

        for item in items:
            link_tag = item.select_one("a.woocommerce-LoopProduct-link")
            price_tag = item.select_one("span.price ins span.amount") or item.select_one("span.price span.amount")
            name_tag = item.select_one("h2.woocommerce-loop-product__title")

            if not link_tag or not name_tag:
                continue

            price_text = price_tag.get_text(strip=True) if price_tag else ""
            price_inr = float(price_text.replace("₹", "").replace(",", "").strip()) if price_text else None

            products.append({
                "name": name_tag.get_text(strip=True),
                "url": link_tag.get("href", ""),
                "price_inr": price_inr,
                "store": STORE_ID,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })

        page += 1
        time.sleep(1.5)  # polite crawl delay

    return products


def scrape_product_detail(product_url: str) -> dict:
    """Scrape specs from a product detail page."""
    resp = requests.get(product_url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        return {}
    soup = BeautifulSoup(resp.text, "html.parser")

    specs = {}
    # Robu uses a product attributes table
    for row in soup.select("table.woocommerce-product-attributes tr"):
        label = row.select_one("th")
        value = row.select_one("td")
        if label and value:
            key = label.get_text(strip=True).lower().replace(" ", "_")
            specs[key] = value.get_text(strip=True)

    image = soup.select_one("div.woocommerce-product-gallery img")
    return {
        "specs": specs,
        "image_url": image.get("src") if image else "",
    }


def main():
    all_products = []
    for cat_url in CATEGORY_URLS:
        print(f"Scraping {cat_url}...")
        products = scrape_listing_page(cat_url)
        print(f"  Found {len(products)} products")
        all_products.extend(products)
        time.sleep(2)

    output_path = "scrapers/output_robu.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(all_products)} products to {output_path}")


if __name__ == "__main__":
    main()
