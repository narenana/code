-- FPVIndia Supabase Schema
-- Run this in your Supabase SQL editor at https://app.supabase.com

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Stores
create table stores (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  url text not null,
  logo_url text,
  created_at timestamptz default now()
);

insert into stores (name, url) values
  ('RCMaster', 'https://rcmaster.in'),
  ('QuadKart', 'https://quadkart.in'),
  ('Robu.in', 'https://robu.in');

-- Products
create table products (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  brand text not null,
  category text not null check (category in (
    'frame','flight_controller','esc','motor','vtx',
    'camera','goggles','receiver','battery','propeller','charger'
  )),
  description text,
  image_url text,
  specs jsonb not null default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index idx_products_category on products(category);
create index idx_products_brand on products(brand);
create index idx_products_specs on products using gin(specs);

-- Product Listings (price per store)
create table product_listings (
  id uuid primary key default uuid_generate_v4(),
  product_id uuid references products(id) on delete cascade,
  store_id uuid references stores(id) on delete cascade,
  price_inr numeric(10,2) not null,
  stock text not null default 'unknown' check (stock in ('in_stock','out_of_stock','unknown')),
  product_url text not null,
  last_checked timestamptz default now(),
  unique(product_id, store_id)
);

create index idx_listings_product on product_listings(product_id);

-- Price history
create table price_history (
  id uuid primary key default uuid_generate_v4(),
  product_id uuid references products(id) on delete cascade,
  store_id uuid references stores(id) on delete cascade,
  price_inr numeric(10,2) not null,
  recorded_at timestamptz default now()
);

create index idx_price_history_product on price_history(product_id, recorded_at desc);

-- RLS policies (allow public read)
alter table products enable row level security;
alter table stores enable row level security;
alter table product_listings enable row level security;
alter table price_history enable row level security;

create policy "Public read products" on products for select using (true);
create policy "Public read stores" on stores for select using (true);
create policy "Public read listings" on product_listings for select using (true);
create policy "Public read price history" on price_history for select using (true);

-- Helper function: get lowest price for a product
create or replace function lowest_price(product_id uuid)
returns numeric as $$
  select min(price_inr) from product_listings
  where product_listings.product_id = $1 and stock = 'in_stock';
$$ language sql stable;
