import Link from 'next/link'
import { ArrowRight, Zap, ShieldCheck, Search, GitCompare } from 'lucide-react'
import ProductCard from '@/components/ProductCard'
import { MOCK_PRODUCTS } from '@/lib/mock-data'
import { CATEGORY_LABELS, Category } from '@/types'

const FEATURED_CATEGORIES: Category[] = [
  'frame', 'flight_controller', 'esc', 'motor', 'battery', 'vtx',
]

const FEATURES = [
  {
    icon: GitCompare,
    title: 'Compatibility Checker',
    desc: 'Instantly check if your motor, FC, ESC, and frame will work together before ordering.',
  },
  {
    icon: Search,
    title: 'Aggregated Catalog',
    desc: 'Every major FPV part from Indian stores in one place — fully spec-catalogued.',
  },
  {
    icon: ShieldCheck,
    title: 'Price Comparison',
    desc: 'narenana aggregates live prices from RCMaster, QuadKart, Robu and more. Always buy at the best price.',
  },
]

export default function HomePage() {
  const featured = MOCK_PRODUCTS.slice(0, 4)

  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="relative overflow-hidden px-4 py-24 text-center">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,_#e9456020_0%,_transparent_70%)]" />
        <div className="relative mx-auto max-w-3xl">
          <span className="mb-4 inline-block rounded-full border border-[#e94560]/30 bg-[#e94560]/10 px-3 py-1 text-xs font-medium text-[#e94560]">
            narenana — India&apos;s FPV Parts Aggregator
          </span>
          <h1 className="mt-4 text-5xl font-extrabold leading-tight tracking-tight text-white">
            Find. Compare. <span className="text-[#e94560]">Fly.</span>
          </h1>
          <p className="mt-5 text-lg text-gray-400">
            Browse FPV drone parts from Indian stores, compare prices, and check compatibility
            between motors, frames, ESCs, and flight controllers — all in one place.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              href="/catalog"
              className="flex items-center gap-2 rounded-lg bg-[#e94560] px-6 py-3 font-semibold text-white transition hover:bg-[#c73050]"
            >
              Browse Catalog <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/compatibility"
              className="flex items-center gap-2 rounded-lg border border-white/20 px-6 py-3 font-semibold text-white transition hover:border-[#e94560]/50 hover:bg-white/5"
            >
              <Zap className="h-4 w-4 text-[#e94560]" />
              Check Compatibility
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto w-full max-w-7xl px-4 py-12">
        <div className="grid gap-6 sm:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-xl border border-white/10 bg-[#12121e] p-6">
              <f.icon className="mb-3 h-8 w-8 text-[#e94560]" />
              <h3 className="mb-1 font-semibold text-white">{f.title}</h3>
              <p className="text-sm text-gray-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Categories */}
      <section className="mx-auto w-full max-w-7xl px-4 py-8">
        <h2 className="mb-4 text-xl font-bold text-white">Browse by Category</h2>
        <div className="flex flex-wrap gap-3">
          {FEATURED_CATEGORIES.map((cat) => (
            <Link
              key={cat}
              href={`/catalog?category=${cat}`}
              className="rounded-lg border border-white/10 bg-[#12121e] px-4 py-2 text-sm font-medium text-gray-300 transition hover:border-[#e94560]/50 hover:text-[#e94560]"
            >
              {CATEGORY_LABELS[cat]}
            </Link>
          ))}
          <Link
            href="/catalog"
            className="rounded-lg border border-dashed border-white/10 px-4 py-2 text-sm text-gray-500 hover:text-gray-300 transition"
          >
            View all →
          </Link>
        </div>
      </section>

      {/* Featured Products */}
      <section className="mx-auto w-full max-w-7xl px-4 py-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">Featured Parts</h2>
          <Link href="/catalog" className="text-sm text-[#e94560] hover:underline">
            View all →
          </Link>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {featured.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>

      {/* CTA Banner */}
      <section className="mx-auto w-full max-w-7xl px-4 py-12">
        <div className="relative overflow-hidden rounded-2xl border border-[#e94560]/30 bg-[#12121e] px-8 py-12 text-center">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,_#e9456015_0%,_transparent_70%)]" />
          <Zap className="relative mx-auto mb-4 h-10 w-10 text-[#e94560]" fill="currentColor" />
          <h2 className="relative text-2xl font-bold text-white">
            Will your build work together?
          </h2>
          <p className="relative mt-2 text-gray-400">
            Use our compatibility checker to verify motor mount patterns, stack sizes, and voltage before you buy.
          </p>
          <Link
            href="/compatibility"
            className="relative mt-6 inline-flex items-center gap-2 rounded-lg bg-[#e94560] px-6 py-3 font-semibold text-white transition hover:bg-[#c73050]"
          >
            Check Compatibility <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-white/10 py-8 text-center text-sm text-gray-600">
        narenana — Built for the Indian FPV community
      </footer>
    </div>
  )
}
