
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    if (process.env.NODE_ENV === "development") {
      return [
        {
          source: '/api/inngest/:path*',
          destination: 'http://127.0.0.1:8399/inngest/:path*',
        },
        {
          source: '/api/chat/:path*',
          destination: 'http://127.0.0.1:8399/chat/:path*',
        },
      ];
    } else {
      return [];
    }
  },
};

export default nextConfig;
