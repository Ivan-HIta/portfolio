/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enable typed imports for src aliases. The corresponding path mapping is
  // defined in tsconfig.json under "paths". This makes importing modules
  // cleaner: e.g. import Navbar from "@/components/Navbar".
  experimental: {
    appDir: true
  }
};

module.exports = nextConfig;
