import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',  // Generate static HTML export
  images: {
    unoptimized: true  // Required for static export
  }
};

export default nextConfig;
