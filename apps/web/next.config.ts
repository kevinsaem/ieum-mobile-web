import type { NextConfig } from "next";

const isGitHubPages = process.env.GITHUB_PAGES === "true";
const repositoryPath = "/ieum-mobile-web";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "export",
  trailingSlash: true,
  basePath: isGitHubPages ? repositoryPath : undefined,
  assetPrefix: isGitHubPages ? repositoryPath : undefined,
};

export default nextConfig;
