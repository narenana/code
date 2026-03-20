"""
Setup manufacturers table, seed with known FPV brands + websites,
then link all products to their manufacturer via brand-name matching.
"""
import sys, json, re
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SUPABASE_URL = "http://127.0.0.1:54321"
SERVICE_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"

HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# ── Step 1: Run DDL via pg endpoint ────────────────────────────────────────
def run_sql(sql: str):
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
        headers=HEADERS,
        json={"query": sql},
    )
    return r

DDL = """
CREATE TABLE IF NOT EXISTS manufacturers (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL UNIQUE,
  slug        text NOT NULL UNIQUE,
  website     text,
  country     text,
  description text,
  logo_url    text,
  created_at  timestamptz DEFAULT now()
);
ALTER TABLE products ADD COLUMN IF NOT EXISTS manufacturer_id uuid REFERENCES manufacturers(id);
CREATE INDEX IF NOT EXISTS idx_products_manufacturer_id ON products(manufacturer_id);
"""

# ── Manufacturers data ──────────────────────────────────────────────────────
MANUFACTURERS = [
    # name, slug, website, country, description
    # ── International FPV brands ───
    ("iFlight",         "iflight",        "https://www.iflight-rc.com",       "China",        "Leading FPV drone manufacturer"),
    ("BetaFPV",         "betafpv",        "https://betafpv.com",              "China",        "Micro FPV drones and components"),
    ("SpeedyBee",       "speedybee",      "https://www.speedybee.com",        "China",        "Flight controllers, ESCs and tools"),
    ("Holybro",         "holybro",        "https://holybro.com",              "China",        "Pixhawk and professional drone hardware"),
    ("DJI",             "dji",            "https://www.dji.com",              "China",        "Consumer and professional drones"),
    ("T-Motor",         "t-motor",        "https://store.tmotor.com",         "China",        "Premium brushless motors for drones"),
    ("Emax",            "emax",           "https://emaxmodel.com",            "China",        "Brushless motors and FPV components"),
    ("Flywoo",          "flywoo",         "https://www.flywoo.net",           "China",        "FPV frames, motors and complete drones"),
    ("GEPRC",           "geprc",          "https://geprc.com",                "China",        "FPV racing drones and components"),
    ("RadioMaster",     "radiomaster",    "https://www.radiomasterrc.com",    "China",        "RC transmitters and ELRS equipment"),
    ("ExpressLRS",      "expresslrs",     "https://www.expresslrs.org",       "Open Source",  "Open-source RC link system"),
    ("Tattu",           "tattu",          "https://www.gensace.com",          "China",        "High-performance LiPo batteries"),
    ("HGLRC",           "hglrc",          "https://www.hglrc.com",            "China",        "FPV flight controllers, VTX, cameras"),
    ("Foxeer",          "foxeer",         "https://www.foxeer.com",           "China",        "FPV cameras, antennas and VTX"),
    ("RunCam",          "runcam",         "https://www.runcam.com",           "China",        "FPV cameras and accessories"),
    ("RushFPV",         "rushfpv",        "https://www.rushfpv.com",          "China",        "VTX and power systems"),
    ("Lumenier",        "lumenier",       "https://www.lumenier.com",         "USA",          "FPV racing components and motors"),
    ("TBS",             "tbs",            "https://www.team-blacksheep.com",  "Hong Kong",    "Team BlackSheep - RC links and accessories"),
    ("Diatone",         "diatone",        "https://www.diatone.us",           "China",        "FPV frames and stacks"),
    ("Caddx",           "caddx",          "https://www.caddxfpv.com",         "China",        "FPV cameras and Walksnail HD system"),
    ("Walksnail",       "walksnail",      "https://www.caddxfpv.com/walksnail","China",       "HD FPV system by Caddx"),
    ("HDZero",          "hdzero",         "https://www.hdzero.com",           "USA",          "Digital HD FPV system"),
    ("Fatshark",        "fatshark",       "https://www.fatshark.com",         "USA",          "FPV goggles"),
    ("Skyzone",         "skyzone",        "https://www.skyzonefpv.com",       "China",        "FPV goggles and monitors"),
    ("Racerstar",       "racerstar",      "https://www.racerstar.com",        "China",        "Budget FPV motors and ESCs"),
    ("Readytosky",      "readytosky",     "https://www.readytosky.com",       "China",        "Drone components and kits"),
    ("Happymodel",      "happymodel",     "https://www.happymodel.cn",        "China",        "Micro/nano drone hardware"),
    ("Betaflight",      "betaflight",     "https://betaflight.com",           "Open Source",  "Open-source FC firmware"),
    ("Gemfan",          "gemfan",         "https://gemfanhobby.com",          "China",        "Propellers for FPV racing"),
    ("HQProp",          "hqprop",         "https://www.hqprop.com",           "China",        "High-quality FPV propellers"),
    ("FrSky",           "frsky",          "https://www.frsky-rc.com",         "China",        "RC radio systems and receivers"),
    ("Eachine",         "eachine",        "https://www.eachine.com",          "China",        "Budget FPV drones and parts"),
    ("Matek",           "matek",          "https://www.mateksys.com",         "China",        "Flight controllers, OSD and GPS"),
    ("ImpulseRC",       "impulserc",      "https://www.impulserc.com",        "USA",          "Premium FPV frames"),
    ("FlyFishRC",       "flyfishrc",      "https://www.flyfishrc.com",        "China",        "FPV drones and cameras"),
    ("JHEMCU",          "jhemcu",         "https://www.jhemcu.com",           "China",        "FPV flight controllers and ESCs"),
    ("MAMBA",           "mamba",          "https://www.diatone.us",           "China",        "FPV stacks by Diatone"),
    ("Axisflying",      "axisflying",     "https://www.axisflying.com",       "China",        "FPV frames and freestyle gear"),
    ("Five33",          "five33",         "https://five33.com",               "USA",          "Premium FPV frames"),
    ("NeutronRC",       "neutronrc",      "https://neutronrc.com",            "China",        "FPV components"),
    ("NewBeeDrone",     "newbeedrone",    "https://newbeedrone.com",          "USA",          "Micro FPV drones"),
    ("RCINPower",       "rcinpower",      "https://rcinpower.com",            "China",        "FPV motors"),
    ("Ethix",           "ethix",          "https://www.ethixfpv.com",         "USA",          "FPV propellers and accessories"),
    ("Ovonic",          "ovonic",         "https://www.ovonicshop.com",       "China",        "LiPo batteries"),
    ("CNHL",            "cnhl",           "https://www.cnhl.cn",              "China",        "LiPo batteries"),
    ("iSDT",            "isdt",           "https://www.isdt.co",              "China",        "Balance chargers and power tools"),
    ("SkyRC",           "skyrc",          "https://www.skyrc.com",            "China",        "RC chargers and accessories"),
    ("ToolkitRC",       "toolkitrc",      "https://www.toolkitrc.com",        "China",        "FPV tools, meters and accessories"),
    ("Holybro",         "holybro",        "https://holybro.com",              "China",        "Pixhawk and professional drone hardware"),
    ("AKK",             "akk",            "https://www.akktek.com",           "China",        "Budget FPV cameras and VTX"),
    ("VAS",             "vas",            "https://www.vasaerials.com",       "USA",          "High-gain FPV antennas"),
    ("VIFLY",           "vifly",          "https://www.vifly.net",            "China",        "FPV whoop stacks and accessories"),
    ("BrainFPV",        "brainfpv",       "https://brainfpv.com",             "USA",          "Advanced flight controllers"),
    ("Amass",           "amass",          "https://www.amass-cn.com",         "China",        "XT60/XT30 connectors and accessories"),
    ("RadioLink",       "radiolink",      "https://www.radiolink.com",        "China",        "RC transmitters and flight controllers"),
    # ── Indian / Asia stores with own brand lines ───
    ("Orange HD",       "orange-hd",      "https://robu.in",                  "India",        "Orange HD propellers sold by Robu.in"),
    ("Pro-Range",       "pro-range",      "https://robu.in",                  "India",        "Pro-Range propellers sold by Robu.in"),
    ("Boscam",          "boscam",         "https://www.boscam.com",           "China",        "FPV video transmitters"),
    ("DYS",             "dys",            "https://www.dys.hk",               "China",        "Brushless motors and ESCs"),
    ("ImmersionRC",     "immersionrc",    "https://www.immersionrc.com",      "Ireland",      "FPV video systems"),
    ("Gorilla",         "gorilla",        "https://gorillafpv.com",           "China",        "FPV motors"),
    ("HOTA",            "hota",           "https://www.hotarc.com",           "China",        "Smart balance chargers"),
    ("HTRC",            "htrc",           "https://www.htrc.net",             "China",        "RC chargers"),
    ("MAD",             "mad",            "https://www.madrc.com",            "China",        "Heavy-lift drone motors"),
    ("MicoAir",         "micoair",        "https://micoair.com",              "China",        "Compact flight controllers"),
    ("Molicel",         "molicel",        "https://www.molicel.com",          "Canada",       "High-performance Li-ion cells"),
    ("Pyrodrone",       "pyrodrone",      "https://pyrodrone.com",            "USA",          "FPV parts and frames"),
    ("GAONENG",         "gaoneng",        "https://www.gaonengbattery.com",   "China",        "LiPo batteries"),
    ("Rubycon",         "rubycon",        "https://www.rubycon.co.jp",        "Japan",        "Capacitors and electronic components"),
    ("NightFire",       "nightfire",      "https://nightfirefpv.com",         "USA",          "FPV LEDs and accessories"),
    ("Sequre",          "sequre",         "https://sequremfg.com",            "China",        "Soldering irons and tools"),
    ("Wild",            "wild",           "https://wildfpv.com",              "China",        "FPV components"),
    ("Zerodrag",        "zerodrag",       "https://zerodragfpv.com",          "China",        "FPV cameras"),
    ("GoPro",           "gopro",          "https://www.gopro.com",            "USA",          "Action cameras"),
    ("FlySky",          "flysky",         "https://www.flysky-cn.com",        "China",        "RC radio transmitters and receivers"),
    ("AMAX",            "amax",           "https://amax-fpv.com",             "China",        "FPV motors"),
    ("SuperP",          "superp",         "https://superprc.com",             "China",        "Propellers"),
    ("VimanaFPV",       "vimanafpv",      "https://vimanafpv.com",            "India",        "Indian FPV brand"),
]

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

# ── Fetch all products ──────────────────────────────────────────────────────
def get_all_products():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/products?select=id,name,brand&limit=10000",
        headers=HEADERS,
    )
    r.raise_for_status()
    return r.json()

# ── Insert manufacturers ────────────────────────────────────────────────────
def upsert_manufacturers():
    rows = []
    seen_slugs = set()
    for entry in MANUFACTURERS:
        name, slug, website, country, description = entry
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        rows.append({
            "name": name,
            "slug": slug,
            "website": website,
            "country": country,
            "description": description,
        })

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/manufacturers?on_conflict=slug",
        headers={**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"},
        json=rows,
    )
    if not r.ok:
        print(f"  WARN upsert: {r.status_code} {r.text[:300]}")
        r.raise_for_status()
    inserted = r.json()
    print(f"  Upserted {len(inserted)} manufacturers")
    return {m["name"]: m["id"] for m in inserted}

# ── Build brand → manufacturer_id mapping ──────────────────────────────────
BRAND_MAP: dict[str, str] = {}  # brand_lower → canonical manufacturer name

ALIASES = {
    # brand value in DB (lowercased) → manufacturer name
    # ── iFlight sub-models ─────────────────────────────────────────────────
    "iflight": "iFlight",
    "xing":    "iFlight",    # XING / XING2 motor series
    "chimera": "iFlight",    # Chimera7 frame
    "lava":    "iFlight",    # LAVA HD frame
    "blitz":   "iFlight",    # BLITZ FC series
    "mark4":   "iFlight",    # Mark4 frame series
    # ── GEPRC sub-models ───────────────────────────────────────────────────
    "geprc":   "GEPRC",
    "geprc-":  "GEPRC",
    "gep-":    "GEPRC",
    "goku":    "HGLRC",
    # ── BetaFPV sub-models ─────────────────────────────────────────────────
    "betafpv": "BetaFPV",
    "pavo":    "BetaFPV",    # Pavo20/25 whoop
    "air65":   "BetaFPV",
    "air75":   "BetaFPV",
    "meteor":  "BetaFPV",    # Meteor75
    "hummingbird": "BetaFPV",
    "aquila":  "BetaFPV",
    # ── RadioMaster sub-models ─────────────────────────────────────────────
    "radiomaster": "RadioMaster",
    "boxer":   "RadioMaster",
    "pocket":  "RadioMaster",
    "tx12":    "RadioMaster",
    "tx15":    "RadioMaster",
    "literadio": "RadioMaster",
    # ── Skyzone sub-models ─────────────────────────────────────────────────
    "skyzone": "Skyzone",
    "sky04x":  "Skyzone",
    # ── Flywoo sub-models ──────────────────────────────────────────────────
    "flywoo":  "Flywoo",
    "rekon":   "Flywoo",     # Rekon / Rekon35 LR frame
    # ── Happymodel sub-models ──────────────────────────────────────────────
    "happymodel": "Happymodel",
    "bandit":  "Happymodel",
    # ── Eachine goggles ────────────────────────────────────────────────────
    "eachine": "Eachine",
    "ev800":   "Eachine",
    # ── SkyRC chargers ─────────────────────────────────────────────────────
    "skyrc":   "SkyRC",
    "imax":    "SkyRC",      # iMAX B6 charger by SkyRC
    # ── GoPro ──────────────────────────────────────────────────────────────
    "gopro":   "GoPro",
    "iflight": "iFlight",
    "betafpv": "BetaFPV",
    "betafpv": "BetaFPV",
    "betafpv": "BetaFPV",
    "speedybee": "SpeedyBee",
    "holybro": "Holybro",
    "dji": "DJI",
    "dji": "DJI",
    "t-motor": "T-Motor",
    "tmotor": "T-Motor",
    "emax": "Emax",
    "flywoo": "Flywoo",
    "geprc": "GEPRC",
    "radiomaster": "RadioMaster",
    "expresslrs": "ExpressLRS",
    "elrs": "ExpressLRS",
    "tattu": "Tattu",
    "hglrc": "HGLRC",
    "foxeer": "Foxeer",
    "runcam": "RunCam",
    "rushfpv": "RushFPV",
    "rush": "RushFPV",
    "lumenier": "Lumenier",
    "luminier": "Lumenier",
    "tbs": "TBS",
    "team blacksheep": "TBS",
    "diatone": "Diatone",
    "caddx": "Caddx",
    "caddxfpv": "Caddx",
    "walksnail": "Walksnail",
    "hdzero": "HDZero",
    "fatshark": "Fatshark",
    "skyzone": "Skyzone",
    "racerstar": "Racerstar",
    "readytosky": "Readytosky",
    "happymodel": "Happymodel",
    "betaflight": "Betaflight",
    "gemfan": "Gemfan",
    "hqprop": "HQProp",
    "frsky": "FrSky",
    "eachine": "Eachine",
    "matek": "Matek",
    "mateksys": "Matek",
    "impulserc": "ImpulseRC",
    "flyfishrc": "FlyFishRC",
    "skystars": "Skystars",
    "jhemcu": "JHEMCU",
    "mamba": "MAMBA",
    "axis": "Axisflying",
    "axisflying": "Axisflying",
    "five33": "Five33",
    "neutronrc": "NeutronRC",
    "nuetronrc": "NeutronRC",
    "newbeedrone": "NewBeeDrone",
    "rcinpower": "RCINPower",
    "ethix": "Ethix",
    "ovonic": "Ovonic",
    "cnhl": "CNHL",
    "isdt": "iSDT",
    "skyrc": "SkyRC",
    "toolkitrc": "ToolkitRC",
    "akk": "AKK",
    "vas": "VAS",
    "vifly": "VIFLY",
    "brainfpv": "BrainFPV",
    "amass": "Amass",
    "radiolink": "RadioLink",
    "orange": "Orange HD",
    "pro-range": "Pro-Range",
    "boscam": "Boscam",
    "dys": "DYS",
    "immersionrc": "ImmersionRC",
    "gorilla": "Gorilla",
    "hota": "HOTA",
    "htrc": "HTRC",
    "mad": "MAD",
    "micoair": "MicoAir",
    "molicel": "Molicel",
    "pyrodrone": "Pyrodrone",
    "gaoneng": "GAONENG",
    "rubycon": "Rubycon",
    "nightfire": "NightFire",
    "sequre": "Sequre",
    "wild": "Wild",
    "zerodrag": "Zerodrag",
    "goku": "HGLRC",       # GOKU is HGLRC's sub-brand
    "simonk": "Readytosky",
    "ecoii": "Emax",
    "flysky": "FlySky",
    "fs-": "FlySky",
}

def main():
    print("=== Manufacturers Setup ===\n")

    # 1. Add FlySky to manufacturers list if not there
    # (We missed it above - add inline)
    flysky_extra = {
        "name": "FlySky",
        "slug": "flysky",
        "website": "https://www.flysky-cn.com",
        "country": "China",
        "description": "RC radio transmitters and receivers",
    }

    # 2. Upsert all manufacturers
    print("[1] Upserting manufacturers...")
    # Insert FlySky separately first
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/manufacturers?on_conflict=slug",
        headers={**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"},
        json=[flysky_extra],
    )
    if r.ok:
        print(f"  Added/updated FlySky")

    mfr_name_to_id = upsert_manufacturers()
    # Also include FlySky
    r2 = requests.get(
        f"{SUPABASE_URL}/rest/v1/manufacturers?select=id,name",
        headers=HEADERS,
    )
    r2.raise_for_status()
    all_mfrs = r2.json()
    mfr_name_to_id = {m["name"]: m["id"] for m in all_mfrs}
    print(f"  Total manufacturers in DB: {len(mfr_name_to_id)}")

    # Build reverse lookup: canonical_name_lower → id
    mfr_lower_to_id = {name.lower(): mid for name, mid in mfr_name_to_id.items()}

    print("\n[2] Fetching all products...")
    products = get_all_products()
    print(f"  {len(products)} products found")

    # 3. Match each product brand → manufacturer
    matched = 0
    unmatched_brands: set[str] = set()

    for product in products:
        brand = (product.get("brand") or "").strip()
        brand_lower = brand.lower()

        mfr_id = None

        # Try direct alias match
        for alias_key, mfr_name in ALIASES.items():
            if alias_key in brand_lower:
                canonical = mfr_name.lower()
                mfr_id = mfr_lower_to_id.get(canonical)
                break

        # Try direct name match
        if not mfr_id:
            mfr_id = mfr_lower_to_id.get(brand_lower)

        # Try starts-with match
        if not mfr_id:
            for mname_lower, mid in mfr_lower_to_id.items():
                if brand_lower.startswith(mname_lower) or mname_lower.startswith(brand_lower):
                    mfr_id = mid
                    break

        if mfr_id:
            # Update product
            r = requests.patch(
                f"{SUPABASE_URL}/rest/v1/products?id=eq.{product['id']}",
                headers={**HEADERS, "Prefer": "return=minimal"},
                json={"manufacturer_id": mfr_id},
            )
            if r.ok:
                matched += 1
        else:
            unmatched_brands.add(brand)

    print(f"\n[3] Results:")
    print(f"  Matched: {matched}/{len(products)} products to a manufacturer")
    print(f"  Unmatched brands ({len(unmatched_brands)}):")
    for b in sorted(unmatched_brands):
        print(f"    - {b!r}")

    print("\nDone!")

if __name__ == "__main__":
    main()
