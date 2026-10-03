import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy forwards /api + /health to FastAPI, so the SPA works
// without CORS in local dev. Production serves dist/ anywhere and
// points VITE_API_BASE_URL at the backend (CORS enabled there).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
