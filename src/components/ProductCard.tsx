import Link from 'next/link'
import { Product, CATEGORY_LABELS } from '@/types'
import { formatPrice } from '@/lib/utils'
import { ExternalLink } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  product: Product
  lowestPrice?: number | null
  className?: string
}

const CATEGORY_COLORS: Record<string, string> = {
  frame: 'bg-purple-500/20 text-purple-300',
  flight_controller: 'bg-blue-500/20 text-blue-300',
  esc: 'bg-orange-500/20 text-orange-300',
  motor: 'bg-red-500/20 text-red-300',
  vtx: 'bg-green-500/20 text-green-300',
  camera: 'bg-yellow-500/20 text-yellow-300',
  goggles: 'bg-pink-500/20 text-pink-300',
  receiver: 'bg-teal-500/20 text-teal-300',
  battery: 'bg-emerald-500/20 text-emerald-300',
  propeller: 'bg-cyan-500/20 text-cyan-300',
  charger: 'bg-indigo-500/20 text-indigo-300',
  gps: 'bg-lime-500/20 text-lime-300',
  antenna: 'bg-sky-500/20 text-sky-300',
  accessory: 'bg-violet-500/20 text-violet-300',
  other: 'bg-gray-500/20 text-gray-300',
}

export default function ProductCard({ product, lowestPrice, className }: Props) {
  return (
    <Link
      href={`/products/${product.id}`}
      className={cn(
        'group flex flex-col overflow-hidden rounded-xl border border-white/10 bg-[#12121e] transition-all duration-200 hover:border-[#e94560]/50 hover:shadow-lg hover:shadow-[#e94560]/10',
        className
      )}
    >
      <div className="relative h-44 w-full overflow-hidden bg-[#0d0d1a]">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-gray-700 text-4xl select-none">
            📦
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', CATEGORY_COLORS[product.category] ?? 'bg-gray-500/20 text-gray-300')}>
            {CATEGORY_LABELS[product.category] ?? product.category}
          </span>
        </div>

        <div>
          <p className="text-xs text-gray-500">{product.brand}</p>
          <h3 className="font-semibold text-white line-clamp-2 leading-snug">{product.name}</h3>
        </div>

        <p className="text-xs text-gray-400 line-clamp-2">{product.description}</p>

        <div className="mt-auto pt-2 border-t border-white/5 flex items-center justify-between">
          {lowestPrice ? (
            <div>
              <p className="text-xs text-gray-500">From</p>
              <p className="font-bold text-[#e94560] text-lg">{formatPrice(lowestPrice)}</p>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Price unavailable</p>
          )}
          <span className="flex items-center gap-1 text-xs text-gray-500 group-hover:text-[#e94560] transition-colors">
            View <ExternalLink className="h-3 w-3" />
          </span>
        </div>
      </div>
    </Link>
  )
}
