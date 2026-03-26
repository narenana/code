"""
QuadKart scraper  —  https://www.quadkart.in
Platform: WordPress / WooCommerce (UX-Blocks theme)
Pagination: /shop/page/{n}/
Resume from checkpoint + auto-retry after 1 hour on repeated failures.
"""

import sys
import json
import time
import random
import os
from pathlib import Path
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── paths ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE      = OUTPUT_DIR / "quadkart.json"
CHECKPOINT_FILE  = Path(__file__).parent / "quadkart_checkpoint.json"

STORE_ID   = "quadkart"
BASE_URL   = "https://www.quadkart.in"
SHOP_URL   = f"{BASE_URL}/shop/page/{{page}}/"
MAX_CONSECUTIVE_FAILURES = 5
RETRY_WAIT_SECONDS       = 3600   # 1 hour

# ── rotating user-agents ───────────────────────────────────────────────────
try:
    _ua = UserAgent()
    def random_ua():
        try:
            return _ua.random
        except Exception:
            return random.choice(FALLBACK_UAS)
except Exception:
    def random_ua():
        return random.choice(FALLBACK_UAS)

FALLBACK_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

# ── category guesser ───────────────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "frame":             ["frame", "chassis"],
    "flight_controller": ["flight controller", "fc ", "f4 ", "f7 ", "f405", "f722", "betaflight", "flight ctrl"],
    "esc":               ["esc", "speed controller", "blheli", "4-in-1", "4in1"],
    "motor":             ["motor", "2207", "2306", "1404", "1507", "stator", " kv"],
    "battery":           ["lipo", "battery", "lihv", "6s", "4s", "3s", "mah"],
    "vtx":               ["vtx", "video transmitter", "air unit", "avatar", "walksnail", "dji o3", "hdzero"],
    "receiver":          ["receiver", " rx ", "elrs", "expresslrs", "frsky", "crossfire", "ghst"],
    "camera":            ["fpv camera", "cmos", "starlight", "camera"],
    "propeller":         ["prop ", "propeller", "blade ", "5043", "5045", "3016"],
    "goggles":           ["goggle", "goggles", "headset", "fpv glasses"],
    "charger":           ["charger", "isdt", "charging"],
    "gps":               ["gps", "gnss", "m8n", "m10"],
    "antenna":           ["antenna", "lhcp", "rhcp", "dipole", "pagoda", "patch"],
    "accessory":         ["prop guard", "standoff", "screw", "nut ", "wire", "cable", "pigtail",
                          "solder", "heat shrink", "adapter", "mount", "pad ", "tape",
                          "wrench", "driver", "tool", "band", "velcro", "strap"],
}

def guess_category(name: str, breadcrumb: list = None, description: str = "") -> str:
    text = (name + " " + description).lower()
    # Use breadcrumb hints first
    if breadcrumb:
        bc = " ".join(breadcrumb).lower()
        if "motor" in bc:        return "motor"
        if "esc" in bc:          return "esc"
        if "frame" in bc:        return "frame"
        if "flight control" in bc: return "flight_controller"
        if "battery" in bc:      return "battery"
        if "vtx" in bc or "video" in bc: return "vtx"
        if "camera" in bc:       return "camera"
        if "receiver" in bc:     return "receiver"
        if "propeller" in bc or "prop" in bc: return "propeller"
        if "goggle" in bc:       return "goggles"
        if "charger" in bc:      return "charger"
        if "gps" in bc:          return "gps"
        if "antenna" in bc:      return "antenna"
        if "accessories" in bc or "accessory" in bc or "wire" in bc: return "accessory"
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return cat
    return "other"

def guess_brand(name: str) -> str:
    known = [
        "iflight", "betafpv", "speedybee", "holybro", "dji", "t-motor",
        "emax", "flywoo", "geprc", "radiomaster", "expresslrs", "tattu",
        "hglrc", "foxeer", "runcam", "rushfpv", "luminier", "impulserc",
        "tbs", "team blacksheep", "axis flying", "axis", "diatone", "lumenier",
        "caddx", "walksnail", "hdzero", "fatshark", "skyzone",
    ]
    low = name.lower()
    for b in known:
        if b in low:
            return b.title()
    return name.split()[0] if name else "Unknown"

def parse_price(text: str) -> float:
    if not text:
        return 0.0
    cleaned = text.replace("₹", "").replace(",", "").strip().split()[0]
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

# ── checkpoint helpers ─────────────────────────────────────────────────────
def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scraped_urls": [], "next_page": 1}

def save_checkpoint(cp: dict):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(cp, f)

# ── HTTP helper ────────────────────────────────────────────────────────────
import requests

session = requests.Session()

def get(url: str) -> requests.Response | None:
    headers = {
        "User-Agent": random_ua(),
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": BASE_URL,
    }
    try:
        resp = session.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        time.sleep(random.uniform(1.2, 2.8))
        return resp
    except requests.RequestException as e:
        print(f"  [WARN] GET failed: {url} — {e}")
        return None

# ── listing page scraper ───────────────────────────────────────────────────
def get_product_urls_from_page(page: int) -> list[str]:
    url = SHOP_URL.format(page=page)
    resp = get(url)
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "lxml")
    links = set()
    for a in soup.select("a.woocommerce-LoopProduct-link, a.woocommerce-loop-product__link"):
        href = a.get("href", "")
        if href and quadkart_domain(href):
            links.add(href.split("?")[0].rstrip("/") + "/")
    return list(links)

def quadkart_domain(url: str) -> bool:
    return "quadkart.in" in url and "/shop/" not in url and "/product-category/" not in url

def get_total_pages() -> int:
    resp = get(SHOP_URL.format(page=1))
    if not resp:
        return 33  # fallback (388 products / 12 per page)
    soup = BeautifulSoup(resp.text, "lxml")
    pages = soup.select(".woocommerce-pagination .page-numbers:not(.next):not(.prev)")
    nums = []
    for p in pages:
        try:
            nums.append(int(p.get_text(strip=True)))
        except ValueError:
            pass
    return max(nums) if nums else 33

# ── product page scraper ───────────────────────────────────────────────────
def scrape_product(url: str) -> dict | None:
    resp = get(url)
    if not resp:
        return None
    soup = BeautifulSoup(resp.text, "lxml")

    name_el = soup.select_one("h1.product_title")
    if not name_el:
        return None
    name = name_el.get_text(strip=True)

    # Price — prefer sale price
    price = 0.0
    price_el = soup.select_one(".price ins .woocommerce-Price-amount") or \
               soup.select_one(".price .woocommerce-Price-amount")
    if price_el:
        price = parse_price(price_el.get_text())

    # Stock
    stock_el = soup.select_one("p.stock, .stock")
    if stock_el:
        sc = stock_el.get("class", [])
        stock = "in_stock" if "in-stock" in sc else "out_of_stock"
    else:
        # If there's an add-to-cart button, assume in stock
        stock = "in_stock" if soup.select_one("button.single_add_to_cart_button") else "unknown"

    # Image
    img_el = soup.select_one(".woocommerce-product-gallery__image img, .woocommerce-product-gallery img")
    image_url = ""
    if img_el:
        image_url = img_el.get("data-large_image") or img_el.get("data-src") or img_el.get("src", "")

    # Description
    desc_el = soup.select_one(".woocommerce-product-details__short-description") or \
              soup.select_one(".entry-summary .woocommerce-product-details__short-description")
    description = ""
    if desc_el:
        description = " ".join(desc_el.get_text(" ", strip=True).split())[:500]

    # Breadcrumb for category hint
    breadcrumb = [a.get_text(strip=True) for a in soup.select("nav.woocommerce-breadcrumb a, .woocommerce-breadcrumb a")]

    category = guess_category(name, breadcrumb, description)
    brand = guess_brand(name)

    return {
        "name": name,
        "brand": brand,
        "category": category,
        "price_inr": price,
        "product_url": url,
        "image_url": image_url,
        "store_id": STORE_ID,
        "stock": stock,
        "description": description,
        "specs": {},
        "sku": "",
    }

# ── main ───────────────────────────────────────────────────────────────────
def main():
    cp = load_checkpoint()
    scraped_urls: set = set(cp.get("scraped_urls", []))
    next_page: int     = cp.get("next_page", 1)

    # Load existing products
    products: list[dict] = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            products = json.load(f)
    print(f"Resuming from page {next_page}, {len(products)} products already scraped")

    total_pages = get_total_pages()
    print(f"Total pages: {total_pages}")

    consecutive_failures = 0

    for page in range(next_page, total_pages + 1):
        print(f"\n[Page {page}/{total_pages}]")

        urls = get_product_urls_from_page(page)
        if not urls:
            consecutive_failures += 1
            print(f"  No URLs on page {page} ({consecutive_failures} consecutive failures)")
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                print(f"  {MAX_CONSECUTIVE_FAILURES} failures in a row — waiting {RETRY_WAIT_SECONDS//60} min...")
                cp["next_page"] = page
                save_checkpoint(cp)
                time.sleep(RETRY_WAIT_SECONDS)
                consecutive_failures = 0
            continue

        consecutive_failures = 0
        new_urls = [u for u in urls if u not in scraped_urls]
        print(f"  {len(urls)} products on page, {len(new_urls)} new")

        for url in new_urls:
            print(f"  Scraping: {url}")
            product = scrape_product(url)
            if product:
                products.append(product)
                scraped_urls.add(url)
                price_str = f"Rs {product['price_inr']}" if product['price_inr'] else "no price"
                print(f"    OK  {product['name'][:55]} | {product['category']} | {price_str}")
            else:
                print(f"    SKIP (parse failed)")

            # Save after every product
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            cp["scraped_urls"] = list(scraped_urls)
            cp["next_page"]    = page
            save_checkpoint(cp)

        cp["next_page"] = page + 1
        save_checkpoint(cp)

    # Deduplicate by URL
    seen_urls = set()
    deduped = []
    for p in products:
        if p["product_url"] not in seen_urls:
            seen_urls.add(p["product_url"])
            deduped.append(p)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(deduped)} unique products saved to {OUTPUT_FILE}")
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

if __name__ == "__main__":
    main()
