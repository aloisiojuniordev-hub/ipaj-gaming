/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  build: {
    outDir: "dist",
    // O chunk do Three.js (~690 kB, ~177 kB gzip) só é baixado via import() dinâmico na Home.
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      // Three.js fica em um chunk separado para não pesar o carregamento inicial.
      output: { manualChunks: { three: ["three"] } },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false,
  },
});
