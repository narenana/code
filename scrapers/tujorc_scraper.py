"""
Scraper for tujorc.com — WooCommerce / Woodmart theme (same structure as fpvguru.in)
Output: scrapers/output/tujorc.json

Resume behaviour:
  - Saves a checkpoint file (tujorc_checkpoint.json) after every scraped product.
  - On restart, skips already-scraped URLs and merges with previous results.
  - If site is unreachable, waits RETRY_WAIT_HOURS and retries automatically.
"""
import json
import re
import time
import os
import sys
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

BASE_URL          = "https://tujorc.com"
STORE_ID          = "tujorc"
OUTPUT_DIR        = os.path.join(os.path.dirname(__file__), "output")
OUTPUT_FILE       = os.path.join(OUTPUT_DIR, "tujorc.json")
CHECKPOINT_FILE   = os.path.join(OUTPUT_DIR, "tujorc_checkpoint.json")
RETRY_WAIT_HOURS  = 1
CONNECT_TIMEOUT   = 15
CONSEC_FAIL_LIMIT = 5

# ── User-Agent rotator ────────────────────────────────────────────────────────
try:
    _UA = UserAgent(browsers=["chrome", "firefox", "safari"], os=["windows", "macos"])
except Exception:
    _UA = None

_FALLBACK_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

def _random_ua() -> str:
    if _UA:
        try:
            return _UA.random
        except Exception:
            pass
    return random.choice(_FALLBACK_UAS)

BASE_HEADERS = {
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Category guesser ──────────────────────────────────────────────────────────
FPV_CATEGORY_KEYWORDS = {
    "flight_controller": ["flight controller", "fc ", "f4 ", "f7 ", "f405", "f722", "betaflight", "aio", "h743", "h7"],
    "esc":               ["esc", "speed controller", "blheli", "am32", "4-in-1", "35a", "45a", "60a"],
    "motor":             ["motor", "kv", "stator", "2306", "2207", "1404"],
    "frame":             ["frame", "chassis", "5 inch", "3 inch", "toothpick"],
    "battery":           ["lipo", "battery", "lihv", "6s", "4s", "3s", "mah"],
    "vtx":               ["vtx", "video transmitter", "air unit", "avatar", "walksnail", "dji o3", "vista"],
    "receiver":          ["receiver", " rx ", "elrs", "expresslrs", "frsky", "crossfire"],
    "camera":            ["camera", "cmos", "starlight"],
    "propeller":         ["prop ", "propeller", "blade", "5x4", "4x4"],
    "gps":               ["gps", "gnss", "compass", "m10"],
}

def guess_category(name: str) -> str:
    text = name.lower()
    for cat, kws in FPV_CATEGORY_KEYWORDS.items():
        if any(k in text for k in kws):
            return cat
    return "other"

def clean_price(text: str) -> float:
    nums = re.sub(r"[^\d.]", "", text.replace(",", ""))
    try:
        return float(nums)
    except ValueError:
        return 0.0

# ── Checkpoint helpers ────────────────────────────────────────────────────────
def load_checkpoint() -> tuple[list[str], list[dict]]:
    if not os.path.exists(CHECKPOINT_FILE):
        return [], []
    try:
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            cp = json.load(f)
        print(f"  [resume] Loaded checkpoint: {len(cp['products'])} products already scraped.")
        return cp["scraped_urls"], cp["products"]
    except Exception as e:
        print(f"  [resume] Checkpoint unreadable ({e}), starting fresh.")
        return [], []

def save_checkpoint(scraped_urls: list[str], products: list[dict]) -> None:
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"scraped_urls": scraped_urls, "products": products}, f, ensure_ascii=False)

def clear_checkpoint() -> None:
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

# ── HTTP helpers ──────────────────────────────────────────────────────────────
def site_is_reachable(session: requests.Session) -> bool:
    try:
        resp = session.get(
            f"{BASE_URL}/shop/",
            headers={**BASE_HEADERS, "User-Agent": _random_ua()},
            timeout=CONNECT_TIMEOUT,
        )
        return resp.status_code < 500
    except Exception:
        return False

def wait_for_site(session: requests.Session) -> None:
    attempt = 1
    while not site_is_reachable(session):
        wake = datetime.now().strftime("%H:%M:%S")
        retry_at = time.strftime("%H:%M:%S", time.localtime(time.time() + RETRY_WAIT_HOURS * 3600))
        print(f"\n  [blocked] Site unreachable at {wake}. "
              f"Waiting {RETRY_WAIT_HOURS}h — will retry at {retry_at} (attempt {attempt})")
        time.sleep(RETRY_WAIT_HOURS * 3600)
        attempt += 1
    print(f"  [unblocked] Site is reachable — resuming.")

def get_soup(url: str, session: requests.Session) -> BeautifulSoup | None:
    headers = {**BASE_HEADERS, "User-Agent": _random_ua()}
    try:
        resp = session.get(url, headers=headers, timeout=CONNECT_TIMEOUT)
        resp.raise_for_status()
        time.sleep(random.uniform(0.9, 2.0))
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        print(f"  [WARN] GET {url} — {e}", file=sys.stderr)
        return None

# ── Scraping logic ────────────────────────────────────────────────────────────
def collect_product_urls(session: requests.Session) -> list[str]:
    urls = []
    page = 1
    while True:
        shop_url = f"{BASE_URL}/shop/page/{page}/" if page > 1 else f"{BASE_URL}/shop/"
        print(f"  Scanning shop page {page}: {shop_url}")
        soup = get_soup(shop_url, session)
        if soup is None:
            wait_for_site(session)
            soup = get_soup(shop_url, session)
            if soup is None:
                break

        page_urls = list(dict.fromkeys(
            a["href"] for a in soup.find_all("a", href=True)
            if a["href"].startswith(BASE_URL + "/product/")
        ))
        if not page_urls:
            break

        urls.extend(page_urls)
        print(f"    Found {len(page_urls)} products (total so far: {len(urls)})")

        if not soup.select_one("a.next.page-numbers"):
            break
        page += 1

    return list(dict.fromkeys(urls))


def scrape_product(url: str, session: requests.Session) -> dict | None:
    soup = get_soup(url, session)
    if soup is None:
        return None

    name_el = soup.select_one("h1.product_title, h1.entry-title")
    name = name_el.get_text(strip=True) if name_el else ""
    if not name:
        return None

    price = 0.0
    ins_el = soup.select_one("p.price ins .amount, p.price ins bdi")
    reg_el = soup.select_one("p.price .amount, p.price bdi")
    if ins_el:
        price = clean_price(ins_el.get_text())
    elif reg_el:
        price = clean_price(reg_el.get_text())

    img_el = soup.select_one(".woocommerce-product-gallery__image img")
    image_url = ""
    if img_el:
        image_url = img_el.get("src") or img_el.get("data-src") or ""

    stock_el = soup.select_one("p.stock")
    stock = "unknown"
    if stock_el:
        t = stock_el.get_text(strip=True).lower()
        stock = "in_stock" if "in stock" in t else ("out_of_stock" if "out of stock" in t else "unknown")

    desc_el = soup.select_one(".woocommerce-product-details__short-description, .product-short-description")
    description = desc_el.get_text(" ", strip=True)[:300] if desc_el else ""

    sku_el = soup.select_one(".sku")
    sku = sku_el.get_text(strip=True) if sku_el else ""

    specs: dict = {}
    for row in soup.select("table.woocommerce-product-attributes tr"):
        th = row.select_one("th")
        td = row.select_one("td")
        if th and td:
            specs[th.get_text(strip=True)] = td.get_text(" ", strip=True)

    return {
        "name": name,
        "brand": name.split()[0] if name else "Unknown",
        "category": guess_category(name),
        "price_inr": price,
        "product_url": url,
        "image_url": image_url,
        "store_id": STORE_ID,
        "store_name": "TujoRC",
        "stock": stock,
        "description": description,
        "specs": specs,
        "sku": sku,
    }


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    session = requests.Session()

    print("=== TujoRC Scraper (with resume + auto-retry) ===")
    print("Checking site availability...")
    wait_for_site(session)

    scraped_urls, products = load_checkpoint()
    scraped_set = set(scraped_urls)

    print("\nStep 1: Collecting product URLs...")
    product_urls = collect_product_urls(session)
    print(f"Total unique product URLs: {len(product_urls)}")

    if not product_urls:
        print("No products found.", file=sys.stderr)
        sys.exit(1)

    remaining = [u for u in product_urls if u not in scraped_set]
    already_done = len(product_urls) - len(remaining)

    print(f"\nStep 2: Scraping product details...")
    if already_done:
        print(f"  Skipping {already_done} already-scraped products (resuming from checkpoint).")

    consec_failures = 0

    for i, url in enumerate(remaining, 1):
        global_i = already_done + i
        print(f"  [{global_i}/{len(product_urls)}] {url.split('/')[-2]}")

        data = scrape_product(url, session)

        if data is None:
            consec_failures += 1
            if consec_failures >= CONSEC_FAIL_LIMIT:
                print(f"\n  [{consec_failures} consecutive failures] Assuming site blocked.")
                wait_for_site(session)
                consec_failures = 0
            continue

        consec_failures = 0
        products.append(data)
        scraped_urls.append(url)
        save_checkpoint(scraped_urls, products)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Scraped {len(products)} products from TujoRC")
    print(f"✓ Saved to {OUTPUT_FILE}")
    clear_checkpoint()
    print("✓ Checkpoint cleared")

    print("\n--- Sample products ---")
    for p in products[:5]:
        print(f"  {p['name'][:60]:60s}  ₹{p['price_inr']:>8.0f}  [{p['category']}]")


if __name__ == "__main__":
    main()
