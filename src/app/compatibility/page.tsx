'use client'
import { useState, useMemo } from 'react'
import { MOCK_PRODUCTS } from '@/lib/mock-data'
import { CATEGORY_LABELS, COMPATIBILITY_PAIRS, Category, Product } from '@/types'
import { checkCompatibility, cn } from '@/lib/utils'
import { CheckCircle, XCircle, AlertCircle, Plus, Trash2, Zap } from 'lucide-react'
import Link from 'next/link'

type SelectedParts = Partial<Record<Category, Product>>

interface CompatResult {
  label: string
  catA: string
  catB: string
  nameA: string
  nameB: string
  compatible: boolean | null
  reason: string
}

function computeCompatibility(parts: SelectedParts): CompatResult[] {
  const results: CompatResult[] = []

  for (const pair of COMPATIBILITY_PAIRS) {
    const productA = parts[pair.a]
    const productB = parts[pair.b]
    if (!productA || !productB) continue

    for (const rule of pair.rules) {
      const valA = productA.specs[rule.specA]
      const valB = productB.specs[rule.specB]
      const compatible = checkCompatibility(valA, valB)

      results.push({
        label: rule.label,
        catA: CATEGORY_LABELS[pair.a],
        catB: CATEGORY_LABELS[pair.b],
        nameA: productA.name,
        nameB: productB.name,
        compatible: valA !== undefined && valB !== undefined ? compatible : null,
        reason:
          valA === undefined || valB === undefined
            ? 'Spec not available for one or both parts'
            : compatible
            ? `Both use ${String(valA)}`
            : `${productA.name} uses ${String(valA)}, but ${productB.name} uses ${String(valB)}`,
      })
    }
  }

  return results
}

const SELECTABLE_CATEGORIES: Category[] = [
  'frame', 'flight_controller', 'esc', 'motor', 'battery', 'vtx', 'receiver', 'propeller',
]

export default function CompatibilityPage() {
  const [selectedParts, setSelectedParts] = useState<SelectedParts>({})
  const [activeCategory, setActiveCategory] = useState<Category | null>(null)
  const [search, setSearch] = useState('')

  const results = useMemo(() => computeCompatibility(selectedParts), [selectedParts])

  const compatible = results.filter((r) => r.compatible === true)
  const issues = results.filter((r) => r.compatible === false)
  const unknown = results.filter((r) => r.compatible === null)

  const filteredProducts = useMemo(() => {
    if (!activeCategory) return []
    return MOCK_PRODUCTS.filter(
      (p) =>
        p.category === activeCategory &&
        (p.name.toLowerCase().includes(search.toLowerCase()) ||
          p.brand.toLowerCase().includes(search.toLowerCase()))
    )
  }, [activeCategory, search])

  function selectPart(product: Product) {
    setSelectedParts((prev) => ({ ...prev, [product.category]: product }))
    setActiveCategory(null)
    setSearch('')
  }

  function removePart(cat: Category) {
    setSelectedParts((prev) => {
      const next = { ...prev }
      delete next[cat]
      return next
    })
  }

  const selectedCount = Object.keys(selectedParts).length

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <div className="mb-2 flex items-center gap-2">
        <Zap className="h-7 w-7 text-[#e94560]" fill="currentColor" />
        <h1 className="text-3xl font-extrabold text-white">Compatibility Checker</h1>
      </div>
      <p className="mb-8 text-gray-400">
        Select parts from your build to instantly check if they are compatible with each other.
      </p>

      <div className="grid gap-8 lg:grid-cols-[1fr_1.4fr]">
        {/* LEFT — Part selector */}
        <div className="flex flex-col gap-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400">Your Build</h2>

          {/* Selected parts */}
          <div className="flex flex-col gap-2">
            {SELECTABLE_CATEGORIES.map((cat) => {
              const part = selectedParts[cat]
              return (
                <div
                  key={cat}
                  className={cn(
                    'flex items-center justify-between rounded-xl border p-3 transition',
                    part
                      ? 'border-white/20 bg-[#12121e]'
                      : activeCategory === cat
                      ? 'border-[#e94560]/50 bg-[#e94560]/5'
                      : 'border-dashed border-white/10 bg-transparent'
                  )}
                >
                  <div className="flex flex-col min-w-0">
                    <span className="text-xs text-gray-500">{CATEGORY_LABELS[cat]}</span>
                    {part ? (
                      <span className="truncate text-sm font-medium text-white">{part.name}</span>
                    ) : (
                      <span className="text-sm text-gray-600">Not selected</span>
                    )}
                  </div>
                  {part ? (
                    <button
                      onClick={() => removePart(cat)}
                      className="ml-2 shrink-0 text-gray-600 hover:text-red-400 transition"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  ) : (
                    <button
                      onClick={() => {
                        setActiveCategory(cat === activeCategory ? null : cat)
                        setSearch('')
                      }}
                      className="ml-2 shrink-0 flex items-center gap-1 rounded-lg border border-white/10 px-2 py-1 text-xs text-gray-400 hover:border-[#e94560]/50 hover:text-[#e94560] transition"
                    >
                      <Plus className="h-3 w-3" /> Add
                    </button>
                  )}
                </div>
              )
            })}
          </div>

          {/* Part picker panel */}
          {activeCategory && (
            <div className="rounded-xl border border-[#e94560]/30 bg-[#12121e] p-4">
              <p className="mb-3 text-sm font-medium text-white">
                Select a {CATEGORY_LABELS[activeCategory]}
              </p>
              <input
                type="text"
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="mb-3 w-full rounded-lg border border-white/10 bg-[#0a0a0f] px-3 py-2 text-sm text-white placeholder-gray-600 outline-none focus:border-[#e94560]/50"
                autoFocus
              />
              <div className="flex max-h-64 flex-col gap-1 overflow-y-auto">
                {filteredProducts.length === 0 ? (
                  <p className="text-sm text-gray-500">No products found.</p>
                ) : (
                  filteredProducts.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => selectPart(p)}
                      className="flex flex-col rounded-lg px-3 py-2 text-left transition hover:bg-white/5"
                    >
                      <span className="text-sm font-medium text-white">{p.name}</span>
                      <span className="text-xs text-gray-500">{p.brand}</span>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT — Results */}
        <div className="flex flex-col gap-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
            Compatibility Results
          </h2>

          {selectedCount < 2 ? (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 py-16 text-center text-gray-500">
              <Zap className="mb-3 h-10 w-10 text-gray-700" />
              <p>Select at least 2 parts to see compatibility results.</p>
            </div>
          ) : results.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 py-16 text-center text-gray-500">
              <AlertCircle className="mb-3 h-10 w-10 text-gray-700" />
              <p>No compatibility rules apply to the selected parts combination.</p>
            </div>
          ) : (
            <>
              {/* Summary bar */}
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-3 text-center">
                  <p className="text-2xl font-bold text-green-400">{compatible.length}</p>
                  <p className="text-xs text-gray-400">Compatible</p>
                </div>
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-3 text-center">
                  <p className="text-2xl font-bold text-red-400">{issues.length}</p>
                  <p className="text-xs text-gray-400">Issues</p>
                </div>
                <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/5 p-3 text-center">
                  <p className="text-2xl font-bold text-yellow-400">{unknown.length}</p>
                  <p className="text-xs text-gray-400">Unknown</p>
                </div>
              </div>

              {/* Result cards */}
              <div className="flex flex-col gap-3">
                {results.map((r, i) => (
                  <div
                    key={i}
                    className={cn(
                      'rounded-xl border p-4',
                      r.compatible === true
                        ? 'border-green-500/20 bg-green-500/5'
                        : r.compatible === false
                        ? 'border-red-500/20 bg-red-500/5'
                        : 'border-yellow-500/20 bg-yellow-500/5'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      {r.compatible === true ? (
                        <CheckCircle className="mt-0.5 h-5 w-5 shrink-0 text-green-400" />
                      ) : r.compatible === false ? (
                        <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
                      ) : (
                        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-yellow-400" />
                      )}
                      <div className="min-w-0">
                        <p className="font-medium text-white text-sm">
                          {r.catA} ↔ {r.catB} — {r.label}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {r.nameA} + {r.nameB}
                        </p>
                        <p
                          className={cn(
                            'mt-1 text-xs',
                            r.compatible === true
                              ? 'text-green-300'
                              : r.compatible === false
                              ? 'text-red-300'
                              : 'text-yellow-300'
                          )}
                        >
                          {r.reason}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {issues.length === 0 && compatible.length > 0 && (
                <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-4 text-center">
                  <p className="font-semibold text-green-300">
                    All checked pairs are compatible!
                  </p>
                  <Link href="/catalog" className="mt-2 inline-block text-xs text-gray-400 hover:text-white transition">
                    Find more parts →
                  </Link>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
