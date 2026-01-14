/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  env: {
    COSMOS_DB_ENDPOINT: process.env.COSMOS_DB_ENDPOINT,
    COSMOS_DB_KEY: process.env.COSMOS_DB_KEY,
    COSMOS_DB_DATABASE_NAME: process.env.COSMOS_DB_DATABASE_NAME,
    COSMOS_DB_CONTAINER_NAME: process.env.COSMOS_DB_CONTAINER_NAME,
  },
}

module.exports = nextConfig
