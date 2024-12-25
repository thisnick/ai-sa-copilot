import nextMdx from '@next/mdx'
import remarkGfm from 'remark-gfm';

const withMdx = nextMdx({
  options: {
    remarkPlugins: [remarkGfm],
  },
});

/** @type {import('next').NextConfig} */
const unWrappedNextConfig = {
  // Add this line:
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

/** @type {import('next').NextConfig} */
const nextConfig = withMdx(unWrappedNextConfig);

export default nextConfig;
