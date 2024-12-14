/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/inngest/:path*',
        destination: 'http://127.0.0.1:8399/inngest/:path*', // Proxy to Backend
      },
    ];
  },
};

export default nextConfig;
