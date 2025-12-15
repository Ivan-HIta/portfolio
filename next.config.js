/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Habilita el directorio app (routing basado en archivos) que se utiliza en
  // esta plantilla. Si agregas más directorios o aliases, ajusta tsconfig.json
  experimental: {
    appDir: true
  }
};

module.exports = nextConfig;