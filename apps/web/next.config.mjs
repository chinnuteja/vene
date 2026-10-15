import path from 'node:path';
import { fileURLToPath } from 'node:url';
const workspaceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
/** @type {import('next').NextConfig} */
const config = {
  distDir: process.env.NEXT_DIST_DIR ?? '.next',
  outputFileTracingRoot: workspaceRoot,
  reactStrictMode: true,
  poweredByHeader: false,
  devIndicators: false,
};
export default config;

