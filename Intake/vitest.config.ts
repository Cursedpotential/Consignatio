import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // Nested applications own their tests and runtime configuration.
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
  },
});
