import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Ajusta a base para produção (container único serve em /dashboard/)
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/dashboard/" : "/",
  plugins: [react()],
  server: {
    port: 5002,
    open: false,
    proxy: {
      "/api/v1": {
        target: "http://127.0.0.1:8010",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1/, ""),
      },
    },
  },
}));