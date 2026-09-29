import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Local dev convenience: the frontend calls relative /documents,
      // /tasks, etc. and Vite forwards them to the FastAPI backend, so the
      // browser never needs to know the backend's port. Production nginx
      // config (frontend/nginx.conf) does the equivalent proxying.
      "/documents": "http://localhost:8000",
      "/tasks": "http://localhost:8000",
      "/golden": "http://localhost:8000",
      "/taxonomy": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
