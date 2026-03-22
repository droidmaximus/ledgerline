import '@/styles/globals.css'
import { Metadata } from 'next'
import { Providers } from '@/app/providers'
import { IBM_Plex_Mono, IBM_Plex_Sans } from 'next/font/google'

const plexSans = IBM_Plex_Sans({
  subsets: ['latin'],
  variable: '--font-sans',
  weight: ['400', '500', '600', '700'],
})

const plexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  weight: ['400', '500', '600'],
})

export const metadata: Metadata = {
  title: 'Ledgerline — Financial document intelligence',
  description:
    'Ledgerline: vectorless RAG and tree-based reasoning for financial documents—no vector DB required.',
  keywords: ['RAG', 'LLM', 'Financial Analysis', 'Document Intelligence'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body
        className={`${plexSans.variable} ${plexMono.variable} font-sans antialiased`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
