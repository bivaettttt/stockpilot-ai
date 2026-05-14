import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Multiple lockfiles in monorepo parent can confuse Turbopack; pin to this app directory.
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
