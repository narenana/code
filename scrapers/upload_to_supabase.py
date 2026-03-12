"""
Uploads scraped product data to Supabase.
Usage: python scrapers/upload_to_supabase.py scrapers/output_robu.json

Requires:
  pip install supabase
  SUPABASE_URL and SUPABASE_SERVICE_KEY env vars set
"""
import json
import os
import sys
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]  # service role key for writes

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_store_id(store_name: str) -> str | None:
    result = supabase.table("stores").select("id").eq("name", store_name).execute()
    if result.data:
        return result.data[0]["id"]
    return None


def upsert_product(product: dict) -> str | None:
    """Insert or update a product. Returns the product id."""
    data = {
        "name": product["name"],
        "brand": product.get("brand", "Unknown"),
        "category": product.get("category", "motor"),
        "description": product.get("description", ""),
        "image_url": product.get("image_url", ""),
        "specs": product.get("specs", {}),
    }
    result = supabase.table("products").upsert(data, on_conflict="name,brand").execute()
    if result.data:
        return result.data[0]["id"]
    return None


def upsert_listing(product_id: str, store_id: str, product: dict):
    data = {
        "product_id": product_id,
        "store_id": store_id,
        "price_inr": product.get("price_inr"),
        "stock": "in_stock" if product.get("price_inr") else "unknown",
        "product_url": product.get("url", ""),
    }
    supabase.table("product_listings").upsert(
        data, on_conflict="product_id,store_id"
    ).execute()

    # Record price history
    if product.get("price_inr"):
        supabase.table("price_history").insert({
            "product_id": product_id,
            "store_id": store_id,
            "price_inr": product["price_inr"],
        }).execute()


def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_to_supabase.py <json_file>")
        sys.exit(1)

    json_file = sys.argv[1]
    with open(json_file, encoding="utf-8") as f:
        products = json.load(f)

    store_id_cache: dict[str, str] = {}

    for p in products:
        store_name = p.get("store", "")
        if store_name not in store_id_cache:
            sid = get_store_id(store_name)
            if not sid:
                print(f"  Store '{store_name}' not found in DB, skipping.")
                continue
            store_id_cache[store_name] = sid
        store_id = store_id_cache[store_name]

        product_id = upsert_product(p)
        if not product_id:
            print(f"  Failed to upsert product: {p['name']}")
            continue

        upsert_listing(product_id, store_id, p)
        print(f"  ✓ {p['name']} — ₹{p.get('price_inr', 'N/A')}")

    print(f"\nDone. Uploaded {len(products)} products.")


if __name__ == "__main__":
    main()
