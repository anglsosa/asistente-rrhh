import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// El proxy manda /api al backend, así no se necesita CORS en FastAPI
export default defineConfig({
	plugins: [react(), tailwindcss()],
	server: { proxy: { "/api": "http://localhost:8000" } },
});
