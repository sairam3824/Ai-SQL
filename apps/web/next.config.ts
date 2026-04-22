import path from 'path';
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  typedRoutes: true,
  outputFileTracingRoot: path.join(process.cwd(), '../../'),
  output: 'standalone',
};

export default nextConfig;
