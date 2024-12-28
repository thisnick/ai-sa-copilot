
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/inngest/:path*',
        destination:
          process.env.NODE_ENV === "development" ?
         'http://127.0.0.1:8399/inngest/:path*':
         `${process.env.API_BASE_URL}/inngest/:path*`
      },
      {
        source: '/api/chat/:path*',
        destination:
          process.env.NODE_ENV === "development" ?
         'http://127.0.0.1:8399/chat/:path*':
         `${process.env.API_BASE_URL}/chat/:path*`
      },
    ];
  },
};

export default nextConfig;
