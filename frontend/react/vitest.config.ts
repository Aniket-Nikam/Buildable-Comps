import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    pool: "forks",
    maxWorkers: 1,
    setupFiles: ["./src/test/setup.ts"],
  },
});
