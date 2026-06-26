import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import path from "path"
import { fileURLToPath } from "url"

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [vue()],
  base: "/admin/",
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: { port: 3000, proxy: { "/api": { target: "http://localhost:8000", changeOrigin: true } } },
  build: {
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ["vue", "vue-router", "pinia"],
          elementPlus: ["element-plus"],
          utils: ["axios"],
        },
      },
    },
    minify: "terser",
    terserOptions: {
      compress: {
        drop_console: true,
      },
    },
  },
})