import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5199 },
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: { output: { manualChunks: (id) => (id.includes("/src/data/") ? "data" : id.includes("node_modules") ? "vendor" : undefined) } },
  },
});
