/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/a2a/:path*',
        destination: 'http://localhost:8000/a2a/:path*',
      },
      {
        source: '/.well-known/:path*',
        destination: 'http://localhost:8000/.well-known/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
