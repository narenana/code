"""
Robu.in scraper  —  https://robu.in/product-category/drone-parts/
Platform : WordPress / WooCommerce
HTTP     : curl-cffi (Chrome124 TLS impersonation — plain requests gets 403)
Scope    : /product-category/drone-parts/ only (~68 pages)
Features : resume from checkpoint, auto-retry after 1 hour on failures
"""

import sys, json, time, random
from pathlib import Path
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── paths ──────────────────────────────────────────────────────────────────
OUTPUT_DIR      = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE     = OUTPUT_DIR / "robu.json"
CHECKPOINT_FILE = Path(__file__).parent / "robu_checkpoint.json"

STORE_ID   = "robu"
BASE_URL   = "https://robu.in"
CATEGORY   = "/product-category/drone-parts"
PAGE_URL   = f"{BASE_URL}{CATEGORY}/page/{{page}}/"
PAGE1_URL  = f"{BASE_URL}{CATEGORY}/"

MAX_FAILURES   = 5
RETRY_WAIT_SEC = 3600   # 1 hour

# ── HTTP session ───────────────────────────────────────────────────────────
session = cffi_requests.Session(impersonate="chrome124")
session.headers.update({
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": BASE_URL,
})

def get(url: str) -> cffi_requests.Response | None:
    try:
        resp = session.get(url, timeout=20)
        resp.raise_for_status()
        time.sleep(random.uniform(0.8, 2.0))
        return resp
    except Exception as e:
        print(f"  [WARN] GET failed: {url} — {e}")
        return None

# ── helpers ────────────────────────────────────────────────────────────────
def parse_price(text: str) -> float:
    if not text: return 0.0
    m = text.replace(",", "").replace("₹", "")
    try: return float("".join(c for c in m if c.isdigit() or c == ".").strip("."))
    except: return 0.0

CATEGORY_KEYWORDS = {
    "frame":             ["frame", "chassis"],
    "flight_controller": ["flight controller", "fc ", "f405", "f722", "betaflight", "flight ctrl"],
    "esc":               ["esc", "speed controller", "blheli", "4-in-1", "4in1"],
    "motor":             ["motor", "2207", "2306", "1404", "1507", "brushless", "kv"],
    "battery":           ["lipo", "battery", "lihv", "6s", "4s", "3s", "mah"],
    "vtx":               ["vtx", "video transmitter", "air unit", "walksnail", "hdzero"],
    "receiver":          ["receiver", " rx ", "elrs", "expresslrs", "frsky", "crossfire"],
    "camera":            ["fpv camera", "cmos", "starlight", "analog camera"],
    "propeller":         ["prop ", "propeller", "blade "],
    "goggles":           ["goggle", "fpv glasses", "headset"],
    "charger":           ["charger", "charging"],
    "gps":               ["gps", "gnss", "m8n"],
    "antenna":           ["antenna", "lhcp", "rhcp", "dipole"],
    "accessory":         ["wire", "cable", "connector", "solder", "heat shrink",
                          "standoff", "screw", "mount", "strap", "velcro", "tool",
                          "adapter", "pigtail", "buzzer", "led"],
}

def guess_category(name: str, breadcrumb: list = None, desc: str = "") -> str:
    text = (name + " " + (desc or "")).lower()
    bc   = " ".join(breadcrumb or []).lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in bc for kw in kws): return cat
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in kws): return cat
    return "other"

def guess_brand(name: str) -> str:
    brands = [
        "iflight", "betafpv", "speedybee", "holybro", "dji", "t-motor", "emax",
        "flywoo", "geprc", "radiomaster", "expresslrs", "tattu", "hglrc", "foxeer",
        "runcam", "rushfpv", "lumenier", "tbs", "team blacksheep", "diatone",
        "caddx", "walksnail", "hdzero", "fatshark", "skyzone", "simonk",
        "racerstar", "readytosky", "happymodel", "betaflight",
    ]
    low = name.lower()
    for b in brands:
        if b in low:
            return " ".join(w.capitalize() for w in b.split())
    return name.split()[0] if name else "Unknown"

# ── checkpoint ─────────────────────────────────────────────────────────────
def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"scraped_urls": [], "next_page": 1}

def save_checkpoint(cp: dict):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(cp, f)

# ── listing page ───────────────────────────────────────────────────────────
def get_total_pages() -> int:
    resp = get(PAGE1_URL)
    if not resp: return 68
    soup = BeautifulSoup(resp.text, "lxml")
    nums = [int(p.get_text(strip=True)) for p in soup.select(".page-numbers")
            if p.get_text(strip=True).isdigit()]
    return max(nums) if nums else 68

def get_product_urls(page: int) -> list[str]:
    url  = PAGE1_URL if page == 1 else PAGE_URL.format(page=page)
    resp = get(url)
    if not resp: return []
    soup = BeautifulSoup(resp.text, "lxml")
    urls = []
    for a in soup.select("a.woocommerce-LoopProduct-link"):
        href = a.get("href", "").split("?")[0].rstrip("/") + "/"
        if href and "robu.in/product/" in href:
            urls.append(href)
    return list(dict.fromkeys(urls))  # dedupe preserving order

# ── product page ───────────────────────────────────────────────────────────
def scrape_product(url: str) -> dict | None:
    resp = get(url)
    if not resp: return None
    soup = BeautifulSoup(resp.text, "lxml")

    name_el = soup.select_one("h1.product_title, .product_title h1, .product_title")
    if not name_el: return None
    name = name_el.get_text(strip=True)

    price_el = (soup.select_one(".price ins .woocommerce-Price-amount") or
                soup.select_one(".price .woocommerce-Price-amount"))
    price = parse_price(price_el.get_text() if price_el else "")

    stock_el = soup.select_one("p.stock")
    if stock_el:
        stock = "in_stock" if "in-stock" in stock_el.get("class", []) else "out_of_stock"
    else:
        stock = "in_stock" if soup.select_one("button.single_add_to_cart_button") else "unknown"

    img_el = soup.select_one(".woocommerce-product-gallery__image img")
    image_url = ""
    if img_el:
        image_url = img_el.get("data-large_image") or img_el.get("data-src") or img_el.get("src", "")

    desc_el = soup.select_one(".woocommerce-product-details__short-description")
    description = " ".join(desc_el.get_text(" ", strip=True).split())[:500] if desc_el else ""

    breadcrumb = [a.get_text(strip=True) for a in soup.select(".woocommerce-breadcrumb a")]

    category = guess_category(name, breadcrumb, description)
    brand    = guess_brand(name)

    return {
        "name": name, "brand": brand, "category": category,
        "price_inr": price, "product_url": url, "image_url": image_url,
        "store_id": STORE_ID, "stock": stock, "description": description,
        "specs": {}, "sku": "",
    }

# ── main ───────────────────────────────────────────────────────────────────
def main():
    cp            = load_checkpoint()
    scraped_urls  = set(cp.get("scraped_urls", []))
    next_page     = cp.get("next_page", 1)

    products: list[dict] = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            products = json.load(f)
    print(f"Resuming from page {next_page}, {len(products)} products already scraped")

    # Warm up session with homepage
    session.get(BASE_URL, timeout=15)

    total_pages   = get_total_pages()
    print(f"Total pages: {total_pages}")

    consecutive_failures = 0

    for page in range(next_page, total_pages + 1):
        print(f"\n[Page {page}/{total_pages}]")

        urls = get_product_urls(page)
        if not urls:
            consecutive_failures += 1
            print(f"  No URLs ({consecutive_failures} consecutive failures)")
            if consecutive_failures >= MAX_FAILURES:
                print(f"  Waiting {RETRY_WAIT_SEC // 60} min before retry...")
                cp["next_page"] = page
                save_checkpoint(cp)
                time.sleep(RETRY_WAIT_SEC)
                consecutive_failures = 0
            continue

        consecutive_failures = 0
        new_urls = [u for u in urls if u not in scraped_urls]
        print(f"  {len(urls)} products, {len(new_urls)} new")

        for url in new_urls:
            product = scrape_product(url)
            if product:
                products.append(product)
                scraped_urls.add(url)
                price_str = f"Rs {product['price_inr']:.0f}" if product["price_inr"] else "no price"
                print(f"    OK  {product['name'][:55]} | {product['category']} | {price_str}")
            else:
                print(f"    SKIP {url}")

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            cp["scraped_urls"] = list(scraped_urls)
            cp["next_page"]    = page
            save_checkpoint(cp)

        cp["next_page"] = page + 1
        save_checkpoint(cp)

    # Final dedup
    seen, deduped = set(), []
    for p in products:
        if p["product_url"] not in seen:
            seen.add(p["product_url"])
            deduped.append(p)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(deduped)} unique products -> {OUTPUT_FILE}")
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

if __name__ == "__main__":
    main()
