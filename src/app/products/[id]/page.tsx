import { notFound } from 'next/navigation'
import Link from 'next/link'
import { supabase } from '@/lib/supabase'
import { CATEGORY_LABELS } from '@/types'
import { formatPrice } from '@/lib/utils'
import { ArrowLeft, ExternalLink, CheckCircle, XCircle, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  params: Promise<{ id: string }>
}

export default async function ProductPage({ params }: Props) {
  const { id } = await params

  // Fetch product + listings + store info in one query
  const { data: product, error } = await supabase
    .from('products')
    .select('*, product_listings(*, stores(*))')
    .eq('id', id)
    .single()

  if (error || !product) notFound()

  const listings = (product.product_listings ?? []) as any[]
  const inStock = listings.filter((l: any) => l.stock === 'in_stock' && l.price_inr > 0)
  const lowestPrice = inStock.length ? Math.min(...inStock.map((l: any) => l.price_inr)) : null
  const specs: Record<string, string | number> = product.specs ?? {}

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      {/* Back */}
      <Link
        href="/catalog"
        className="mb-6 inline-flex items-center gap-1 text-sm text-gray-400 hover:text-white transition"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Catalog
      </Link>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Image */}
        <div className="overflow-hidden rounded-2xl border border-white/10 bg-[#12121e] flex items-center justify-center min-h-64">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="text-8xl select-none">📦</span>
          )}
        </div>

        {/* Info */}
        <div className="flex flex-col gap-4">
          <div>
            <span className="rounded-full border border-white/10 bg-[#12121e] px-3 py-1 text-xs text-gray-400">
              {CATEGORY_LABELS[product.category as keyof typeof CATEGORY_LABELS] ?? product.category}
            </span>
            <p className="mt-2 text-sm text-gray-500">{product.brand}</p>
            <h1 className="mt-1 text-3xl font-extrabold text-white">{product.name}</h1>
          </div>

          {product.description && (
            <p className="text-gray-400">{product.description}</p>
          )}

          {lowestPrice && (
            <div className="rounded-xl border border-[#e94560]/20 bg-[#e94560]/5 p-4">
              <p className="text-xs text-gray-500">Lowest price in India</p>
              <p className="text-3xl font-bold text-[#e94560]">{formatPrice(lowestPrice)}</p>
            </div>
          )}

          {/* Specs */}
          {Object.keys(specs).length > 0 && (
            <div className="rounded-xl border border-white/10 bg-[#12121e] p-4">
              <h2 className="mb-3 text-sm font-semibold text-white uppercase tracking-wider">Specifications</h2>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(specs).map(([key, value]) => (
                  <div key={key} className="flex flex-col">
                    <span className="text-xs text-gray-500 capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="text-sm font-medium text-white">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compatibility shortcut */}
          <Link
            href={`/compatibility?product=${product.id}&category=${product.category}`}
            className="flex items-center justify-center gap-2 rounded-lg border border-white/10 py-2.5 text-sm font-medium text-gray-300 transition hover:border-[#e94560]/50 hover:text-[#e94560]"
          >
            Check compatibility with this part →
          </Link>
        </div>
      </div>

      {/* Price Comparison */}
      <div className="mt-10">
        <h2 className="mb-4 text-xl font-bold text-white">Price Comparison</h2>
        {listings.length === 0 ? (
          <p className="text-gray-500">No listings found for this product yet.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {[...listings]
              .sort((a, b) => a.price_inr - b.price_inr)
              .map((listing: any) => (
                <div
                  key={listing.id}
                  className={cn(
                    'flex items-center justify-between rounded-xl border p-4 transition',
                    listing.price_inr === lowestPrice && listing.stock === 'in_stock'
                      ? 'border-[#e94560]/40 bg-[#e94560]/5'
                      : 'border-white/10 bg-[#12121e]'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex flex-col">
                      <span className="font-semibold text-white">
                        {listing.stores?.name ?? listing.store_id}
                      </span>
                      <span className="flex items-center gap-1 text-xs">
                        {listing.stock === 'in_stock' ? (
                          <>
                            <CheckCircle className="h-3 w-3 text-green-400" />
                            <span className="text-green-400">In Stock</span>
                          </>
                        ) : listing.stock === 'out_of_stock' ? (
                          <>
                            <XCircle className="h-3 w-3 text-red-400" />
                            <span className="text-red-400">Out of Stock</span>
                          </>
                        ) : (
                          <>
                            <Clock className="h-3 w-3 text-gray-400" />
                            <span className="text-gray-400">Unknown</span>
                          </>
                        )}
                      </span>
                    </div>
                    {listing.price_inr === lowestPrice && listing.stock === 'in_stock' && (
                      <span className="rounded-full bg-[#e94560] px-2 py-0.5 text-xs font-medium text-white">
                        Best Price
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4">
                    <span className="text-xl font-bold text-white">
                      {formatPrice(listing.price_inr)}
                    </span>
                    <a
                      href={listing.product_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={cn(
                        'flex items-center gap-1 rounded-lg px-4 py-2 text-sm font-medium transition',
                        listing.stock === 'in_stock'
                          ? 'bg-[#e94560] text-white hover:bg-[#c73050]'
                          : 'border border-white/10 text-gray-400 cursor-not-allowed'
                      )}
                    >
                      Buy <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
              ))}
          </div>
        )}
        {listings[0]?.last_checked && (
          <p className="mt-3 text-xs text-gray-600">
            Prices last updated: {new Date(listings[0].last_checked).toLocaleDateString('en-IN')} — prices may vary.
          </p>
        )}
      </div>
    </div>
  )
}
