"""
Upload scraped products to Supabase.

Usage:
  python scrapers/upload_to_supabase.py scrapers/output/tujorc.json
  python scrapers/upload_to_supabase.py scrapers/output/fpvguru.json

Requires .env.local in project root with:
  SUPABASE_URL=https://xxxx.supabase.co
  SUPABASE_SERVICE_KEY=eyJ...   <-- service role key (Settings > API)
"""
import json
import os
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv
from supabase import create_client

# Load from .env.local in project root
ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env.local")

SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env.local")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

VALID_CATEGORIES = {
    "frame", "flight_controller", "esc", "motor", "vtx",
    "camera", "goggles", "receiver", "battery", "propeller",
    "charger", "gps", "antenna", "accessory", "other",
}


def upsert_product(p: dict) -> str | None:
    """Insert or update product by (name, brand). Returns product id."""
    category = p.get("category", "other")
    if category not in VALID_CATEGORIES:
        category = "other"

    data = {
        "name":        p["name"][:255],
        "brand":       (p.get("brand") or "Unknown")[:100],
        "category":    category,
        "description": (p.get("description") or "")[:1000],
        "image_url":   p.get("image_url") or "",
        "specs":       p.get("specs") or {},
    }
    res = supabase.table("products").upsert(data, on_conflict="name,brand").execute()
    if res.data:
        return res.data[0]["id"]
    return None


def upsert_listing(product_id: str, p: dict):
    """Insert or update listing (price + stock) for the product's store."""
    price = p.get("price_inr") or 0
    stock = p.get("stock") or ("in_stock" if price > 0 else "unknown")

    data = {
        "product_id":  product_id,
        "store_id":    p["store_id"],
        "price_inr":   price,
        "stock":       stock,
        "product_url": p.get("product_url") or "",
        "sku":         p.get("sku") or "",
    }
    supabase.table("product_listings").upsert(
        data, on_conflict="product_id,store_id"
    ).execute()

    if price > 0:
        supabase.table("price_history").insert({
            "product_id": product_id,
            "store_id":   p["store_id"],
            "price_inr":  price,
        }).execute()


def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_to_supabase.py <scraped.json>")
        sys.exit(1)

    json_file = sys.argv[1]
    with open(json_file, encoding="utf-8") as f:
        products = json.load(f)

    print(f"Uploading {len(products)} products from {json_file}...")
    ok = fail = 0

    for p in products:
        if not p.get("name") or not p.get("store_id"):
            fail += 1
            continue

        product_id = upsert_product(p)
        if not product_id:
            print(f"  ✗ Failed to upsert: {p['name']}")
            fail += 1
            continue

        upsert_listing(product_id, p)
        print(f"  OK {p['name'][:60]:60s}  Rs{p.get('price_inr', 0):>8.0f}  [{p.get('category','?')}]")
        ok += 1

    print(f"\nDone: {ok} uploaded, {fail} failed.")


if __name__ == "__main__":
    main()
