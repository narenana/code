import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/Navbar'

export const metadata: Metadata = {
  title: 'FPVIndia — FPV Parts Catalog & Compatibility Checker',
  description: 'Compare FPV drone parts from Indian stores. Check motor, FC, ESC, frame compatibility before you buy.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0a0a0f] text-white antialiased">
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  )
}
