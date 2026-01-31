import type { NextConfig } from "next";
import { config } from "dotenv";
import path from "path";

// Load .env.local from project root (parent directory)
// process.cwd() is the frontend directory when Next.js runs, so go up one level
config({ path: path.resolve(process.cwd(), "..", ".env.local") });

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
