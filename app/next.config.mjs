
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/inngest/:path*',
        destination:
          process.env.NODE_ENV === "development" ?
         'http://127.0.0.1:8399/api/inngest/:path*':
         `${process.env.API_BASE_URL}/api/inngest/:path*`
      },
      {
        source: '/api/chat/:path*',
        destination:
          process.env.NODE_ENV === "development" ?
         'http://127.0.0.1:8399/api/chat/:path*':
         `${process.env.API_BASE_URL}/api/chat/:path*`
      },
    ];
  },
};

export default nextConfig;
