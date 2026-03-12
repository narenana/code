'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Zap } from 'lucide-react'

const NAV_LINKS = [
  { href: '/catalog', label: 'Catalog' },
  { href: '/compatibility', label: 'Compatibility Checker' },
]

export default function Navbar() {
  const pathname = usePathname()

  return (
    <nav className="sticky top-0 z-50 border-b border-white/10 bg-[#0a0a0f]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2 text-white">
          <Zap className="h-6 w-6 text-[#e94560]" fill="currentColor" />
          <span className="text-xl font-bold tracking-tight">
            nare<span className="text-[#e94560]">nana</span>
          </span>
        </Link>

        <div className="flex items-center gap-6">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                'text-sm font-medium transition-colors hover:text-[#e94560]',
                pathname === link.href ? 'text-[#e94560]' : 'text-gray-400'
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}
