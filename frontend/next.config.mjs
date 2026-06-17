/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // API_URL : "http://localhost:8000" en dev, URL Railway backend en prod
    const apiUrl = process.env.API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
