-- narenana Supabase Schema
-- Run this in your Supabase SQL editor at https://app.supabase.com

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ── Stores ────────────────────────────────────────────────────────────────────
create table if not exists stores (
  id         text primary key,           -- e.g. 'fpvguru', 'tujorc'
  name       text not null,
  url        text not null,
  logo_url   text,
  created_at timestamptz default now()
);

insert into stores (id, name, url) values
  ('rcmaster',  'RCMaster',   'https://rcmaster.in'),
  ('quadkart',  'QuadKart',   'https://quadkart.in'),
  ('robu',      'Robu.in',    'https://robu.in'),
  ('drkstore',  'DRK Store',  'https://drkstore.in'),
  ('fpvguru',   'FPV Guru',   'https://fpvguru.in'),
  ('tujorc',    'TujoRC',     'https://tujorc.com')
on conflict (id) do nothing;

-- ── Products ──────────────────────────────────────────────────────────────────
create table if not exists products (
  id          uuid primary key default uuid_generate_v4(),
  name        text not null,
  brand       text not null default 'Unknown',
  category    text not null check (category in (
                'frame','flight_controller','esc','motor','vtx',
                'camera','goggles','receiver','battery','propeller',
                'charger','gps','antenna','accessory','other'
              )),
  description text    default '',
  image_url   text    default '',
  specs       jsonb   not null default '{}',
  created_at  timestamptz default now(),
  updated_at  timestamptz default now(),
  unique (name, brand)
);

create index if not exists idx_products_category on products(category);
create index if not exists idx_products_brand    on products(brand);
create index if not exists idx_products_specs    on products using gin(specs);
create index if not exists idx_products_name_fts on products
  using gin(to_tsvector('english', name));

-- ── Product Listings (one row per product × store) ───────────────────────────
create table if not exists product_listings (
  id           uuid primary key default uuid_generate_v4(),
  product_id   uuid references products(id) on delete cascade,
  store_id     text references stores(id)   on delete cascade,
  price_inr    numeric(10,2) not null default 0,
  stock        text not null default 'unknown'
                 check (stock in ('in_stock','out_of_stock','unknown')),
  product_url  text    not null default '',
  sku          text    default '',
  last_checked timestamptz default now(),
  unique (product_id, store_id)
);

create index if not exists idx_listings_product on product_listings(product_id);
create index if not exists idx_listings_store   on product_listings(store_id);

-- ── Price History ─────────────────────────────────────────────────────────────
create table if not exists price_history (
  id          uuid primary key default uuid_generate_v4(),
  product_id  uuid references products(id) on delete cascade,
  store_id    text references stores(id)   on delete cascade,
  price_inr   numeric(10,2) not null,
  recorded_at timestamptz default now()
);

create index if not exists idx_price_history_product
  on price_history(product_id, recorded_at desc);

-- ── RLS: public read, service-role write ─────────────────────────────────────
alter table products         enable row level security;
alter table stores           enable row level security;
alter table product_listings enable row level security;
alter table price_history    enable row level security;

create policy "Public read products"      on products         for select using (true);
create policy "Public read stores"        on stores           for select using (true);
create policy "Public read listings"      on product_listings for select using (true);
create policy "Public read price history" on price_history    for select using (true);

-- ── Helper: lowest in-stock price for a product ──────────────────────────────
create or replace function lowest_price(p_product_id uuid)
returns numeric as $$
  select min(price_inr)
  from   product_listings
  where  product_id = p_product_id
    and  stock      = 'in_stock';
$$ language sql stable;

-- ── updated_at auto-trigger ───────────────────────────────────────────────────
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger products_updated_at
  before update on products
  for each row execute function set_updated_at();
