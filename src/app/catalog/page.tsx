'use client'
import { useState, useMemo } from 'react'
import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import ProductCard from '@/components/ProductCard'
import { MOCK_PRODUCTS } from '@/lib/mock-data'
import { CATEGORY_LABELS, Category } from '@/types'
import { Search, SlidersHorizontal } from 'lucide-react'
import { cn } from '@/lib/utils'

const ALL_CATEGORIES = Object.keys(CATEGORY_LABELS) as Category[]

function CatalogContent() {
  const searchParams = useSearchParams()
  const initialCategory = searchParams.get('category') as Category | null

  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(initialCategory)

  const filtered = useMemo(() => {
    return MOCK_PRODUCTS.filter((p) => {
      const matchCat = !selectedCategory || p.category === selectedCategory
      const matchSearch =
        !search ||
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.brand.toLowerCase().includes(search.toLowerCase())
      return matchCat && matchSearch
    })
  }, [search, selectedCategory])

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="mb-2 text-3xl font-extrabold text-white">FPV Parts Catalog</h1>
      <p className="mb-8 text-gray-400">
        {MOCK_PRODUCTS.length} parts from Indian FPV stores
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

      {/* Results */}
      {filtered.length === 0 ? (
        <div className="py-20 text-center text-gray-500">
          No parts found. Try a different search or category.
        </div>
      ) : (
        <>
          <p className="mb-4 text-sm text-gray-500">{filtered.length} results</p>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filtered.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
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
