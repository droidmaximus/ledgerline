/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_GATEWAY_URL: process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8083',
    NEXT_PUBLIC_CACHE_SERVICE_URL: process.env.NEXT_PUBLIC_CACHE_SERVICE_URL || 'http://localhost:8082',
  },
  async rewrites() {
    const gateway =
      (process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8083').replace(
        /\/$/,
        ''
      )
    return {
      // afterFiles: resolve _next/static and pages first; only then proxy /api/* to the gateway
      afterFiles: [
        {
          source: '/api/:path*',
          destination: `${gateway}/:path*`,
        },
      ],
    }
  },
  typescript: {
    tsconfigPath: './tsconfig.json',
  },
}

module.exports = nextConfig
