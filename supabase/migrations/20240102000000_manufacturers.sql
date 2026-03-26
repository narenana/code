-- Manufacturers table
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

-- Add manufacturer_id FK to products
ALTER TABLE products
  ADD COLUMN IF NOT EXISTS manufacturer_id uuid REFERENCES manufacturers(id);

-- Index for FK lookups
CREATE INDEX IF NOT EXISTS idx_products_manufacturer_id ON products(manufacturer_id);
