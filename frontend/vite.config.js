import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
// import AutoImport from 'unplugin-auto-import/vite' // Removed
// import Components from 'unplugin-vue-components/vite' // Removed
// import { ElementPlusResolver } from 'unplugin-vue-components/resolvers' // Removed
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue(),
    // AutoImport({ // Removed
    //   resolvers: [ElementPlusResolver()],
    // }),
    // Components({ // Removed
    //   resolvers: [ElementPlusResolver()],
    // }),
  ],
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: true,
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  }
})
