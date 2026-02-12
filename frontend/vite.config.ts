import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { visualizer } from 'rollup-plugin-visualizer';

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on mode (loaded but may not be directly used)
  loadEnv(mode, process.cwd(), '');

  const isProduction = mode === 'production';

  return {
    plugins: [
      react(),
      visualizer({
        filename: 'dist/stats.html',
        open: false,
        gzipSize: true,
        template: 'treemap',
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      strictPort: false,
      open: true,
      headers: {
        'X-DNS-Prefetch-Control': 'off',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
      },
    },
    preview: {
      port: 4173,
      headers: {
        'X-DNS-Prefetch-Control': 'off',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: isProduction ? 'hidden' : false,
      minify: isProduction ? 'terser' : 'esbuild',
      terserOptions: isProduction ? {
        compress: {
          drop_console: false,
          drop_debugger: true,
          pure_funcs: [],
        },
        format: {
          comments: false,
        },
      } : undefined,
      cssCodeSplit: true,
      rollupOptions: {
        output: {
          manualChunks: {
            react: ['react', 'react-dom', 'react-router-dom'],
            query: ['@tanstack/react-query'],
            ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
            forms: ['react-hook-form', 'zod'],
            state: ['zustand'],
          },
          chunkFileNames: 'js/[name]-[hash].js',
          entryFileNames: 'js/[name]-[hash].js',
          assetFileNames: '[ext]/[name]-[hash].[ext]',
          // Optimize chunk names for caching
          compact: true,
        },
        // Externalize dependencies that shouldn't be bundled
        external: [],
        // Define globals for external dependencies
        globals: {},
      },
      chunkSizeWarningLimit: 500,
      // Generate report for CI
      reportCompressedSize: isProduction,
    },
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        '@tanstack/react-query',
        'zustand',
        'axios',
      ],
      // Exclude problematic packages from optimization
      exclude: [],
    },
    // CSS configuration
    css: {
      postcss: './postcss.config.js',
    },
    // Define global constants
    define: {
      // Replace process.env with actual values
      __DEV__: !isProduction,
      'process.env.NODE_ENV': JSON.stringify(mode),
    },
  };
});
