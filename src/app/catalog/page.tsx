'use client'
import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import ProductCard from '@/components/ProductCard'
import { supabase } from '@/lib/supabase'
import { CATEGORY_LABELS, Category, Product, ProductListing } from '@/types'
import { Search, SlidersHorizontal } from 'lucide-react'
import { cn } from '@/lib/utils'

const ALL_CATEGORIES = Object.keys(CATEGORY_LABELS) as Category[]

type ProductWithListings = Product & { product_listings: ProductListing[] }

function getLowestPrice(listings: ProductListing[]): number | null {
  const prices = listings
    .filter((l) => l.stock !== 'out_of_stock' && l.price_inr > 0)
    .map((l) => l.price_inr)
  return prices.length > 0 ? Math.min(...prices) : null
}

function CatalogContent() {
  const searchParams = useSearchParams()
  const initialCategory = searchParams.get('category') as Category | null

  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(initialCategory)
  const [products, setProducts] = useState<ProductWithListings[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchProducts() {
      setLoading(true)
      setError(null)
      const { data, error: fetchError } = await supabase
        .from('products')
        .select('*, product_listings(*)')
        .order('name')

      if (fetchError) {
        console.error('Supabase error:', fetchError)
        setError('Failed to load products. Is the local Supabase running?')
      } else {
        setProducts((data as ProductWithListings[]) ?? [])
      }
      setLoading(false)
    }
    fetchProducts()
  }, [])

  const filtered = useMemo(() => {
    return products.filter((p) => {
      const matchCat = !selectedCategory || p.category === selectedCategory
      const matchSearch =
        !search ||
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        (p.brand ?? '').toLowerCase().includes(search.toLowerCase())
      return matchCat && matchSearch
    })
  }, [products, search, selectedCategory])

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="mb-2 text-3xl font-extrabold text-white">FPV Parts Catalog</h1>
      <p className="mb-8 text-gray-400">
        {loading ? 'Loading parts…' : `${products.length} parts aggregated from Indian FPV stores`}
      </p>

      {/* Filters */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search parts, brands..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-[#12121e] py-2.5 pl-10 pr-4 text-sm text-white placeholder-gray-500 outline-none focus:border-[#e94560]/50"
          />
        </div>

        {/* Category filter */}
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-gray-500 shrink-0" />
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedCategory(null)}
              className={cn(
                'rounded-full px-3 py-1 text-xs font-medium transition',
                !selectedCategory
                  ? 'bg-[#e94560] text-white'
                  : 'border border-white/10 text-gray-400 hover:text-white'
              )}
            >
              All
            </button>
            {ALL_CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat === selectedCategory ? null : cat)}
                className={cn(
                  'rounded-full px-3 py-1 text-xs font-medium transition',
                  selectedCategory === cat
                    ? 'bg-[#e94560] text-white'
                    : 'border border-white/10 text-gray-400 hover:text-white'
                )}
              >
                {CATEGORY_LABELS[cat]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          ⚠️ {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="h-72 animate-pulse rounded-xl border border-white/5 bg-[#12121e]"
            />
          ))}
        </div>
      )}

      {/* Results */}
      {!loading && !error && (
        <>
          {filtered.length === 0 ? (
            <div className="py-20 text-center text-gray-500">
              No parts found. Try a different search or category.
            </div>
          ) : (
            <>
              <p className="mb-4 text-sm text-gray-500">{filtered.length} results</p>
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {filtered.map((product) => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    lowestPrice={getLowestPrice(product.product_listings)}
                  />
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}

export default function CatalogPage() {
  return (
    <Suspense fallback={<div className="p-10 text-gray-400">Loading catalog...</div>}>
      <CatalogContent />
    </Suspense>
  )
}
