// vite.config.js
import { defineConfig } from "file:///home/abdulrahman/frappe-bench/apps/lms/frontend/node_modules/vite/dist/node/index.js";
import vue from "file:///home/abdulrahman/frappe-bench/apps/lms/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import path from "path";
import frappeui from "file:///home/abdulrahman/frappe-bench/apps/lms/frontend/node_modules/frappe-ui/vite/index.js";
import { VitePWA } from "file:///home/abdulrahman/frappe-bench/apps/lms/frontend/node_modules/vite-plugin-pwa/dist/index.js";
var __vite_injected_original_dirname = "/home/abdulrahman/frappe-bench/apps/lms/frontend";
var vite_config_default = defineConfig(({ mode }) => ({
  plugins: [
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      frappeTypes: {
        input: {}
      },
      buildConfig: {
        indexHtmlPath: "../lms/www/lms.html"
      }
    }),
    vue({
      script: {
        defineModel: true,
        propsDestructure: true
      }
    }),
    VitePWA({
      registerType: "autoUpdate",
      devOptions: {
        enabled: true
      },
      workbox: {
        cleanupOutdatedCaches: true,
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
        globDirectory: "/assets/lms/frontend",
        globPatterns: ["**/*.{js,ts,css,html,png,svg}"],
        runtimeCaching: [
          {
            urlPattern: ({ request }) => request.destination === "document",
            handler: "NetworkFirst",
            options: {
              cacheName: "html-cache"
            }
          }
        ]
      },
      manifest: false
    })
  ],
  server: {
    host: "0.0.0.0",
    // Accept connections from any network interface
    allowedHosts: ["ps", "fs", "home"]
    // Explicitly allow this host
  },
  resolve: {
    alias: {
      "@": path.resolve(__vite_injected_original_dirname, "src")
    }
  },
  optimizeDeps: {
    include: [
      "feather-icons",
      "engine.io-client",
      "interactjs",
      "highlight.js",
      "plyr"
    ],
    exclude: mode === "production" ? [] : ["frappe-ui"]
  }
}));
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvaG9tZS9hYmR1bHJhaG1hbi9mcmFwcGUtYmVuY2gvYXBwcy9sbXMvZnJvbnRlbmRcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIi9ob21lL2FiZHVscmFobWFuL2ZyYXBwZS1iZW5jaC9hcHBzL2xtcy9mcm9udGVuZC92aXRlLmNvbmZpZy5qc1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vaG9tZS9hYmR1bHJhaG1hbi9mcmFwcGUtYmVuY2gvYXBwcy9sbXMvZnJvbnRlbmQvdml0ZS5jb25maWcuanNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xuaW1wb3J0IHZ1ZSBmcm9tICdAdml0ZWpzL3BsdWdpbi12dWUnXG5pbXBvcnQgcGF0aCBmcm9tICdwYXRoJ1xuaW1wb3J0IGZyYXBwZXVpIGZyb20gJ2ZyYXBwZS11aS92aXRlJ1xuaW1wb3J0IHsgVml0ZVBXQSB9IGZyb20gJ3ZpdGUtcGx1Z2luLXB3YSdcblxuLy8gaHR0cHM6Ly92aXRlanMuZGV2L2NvbmZpZy9cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZygoeyBtb2RlIH0pID0+ICh7XG5cdHBsdWdpbnM6IFtcblx0XHRmcmFwcGV1aSh7XG5cdFx0XHRmcmFwcGVQcm94eTogdHJ1ZSxcblx0XHRcdGx1Y2lkZUljb25zOiB0cnVlLFxuXHRcdFx0amluamFCb290RGF0YTogdHJ1ZSxcblx0XHRcdGZyYXBwZVR5cGVzOiB7XG5cdFx0XHRcdGlucHV0OiB7fSxcblx0XHRcdH0sXG5cdFx0XHRidWlsZENvbmZpZzoge1xuXHRcdFx0XHRpbmRleEh0bWxQYXRoOiAnLi4vbG1zL3d3dy9sbXMuaHRtbCcsXG5cdFx0XHR9LFxuXHRcdH0pLFxuXHRcdHZ1ZSh7XG5cdFx0XHRzY3JpcHQ6IHtcblx0XHRcdFx0ZGVmaW5lTW9kZWw6IHRydWUsXG5cdFx0XHRcdHByb3BzRGVzdHJ1Y3R1cmU6IHRydWUsXG5cdFx0XHR9LFxuXHRcdH0pLFxuXHRcdFZpdGVQV0Eoe1xuXHRcdFx0cmVnaXN0ZXJUeXBlOiAnYXV0b1VwZGF0ZScsXG5cdFx0XHRkZXZPcHRpb25zOiB7XG5cdFx0XHRcdGVuYWJsZWQ6IHRydWUsXG5cdFx0XHR9LFxuXHRcdFx0d29ya2JveDoge1xuXHRcdFx0XHRjbGVhbnVwT3V0ZGF0ZWRDYWNoZXM6IHRydWUsXG5cdFx0XHRcdG1heGltdW1GaWxlU2l6ZVRvQ2FjaGVJbkJ5dGVzOiA1ICogMTAyNCAqIDEwMjQsXG5cdFx0XHRcdGdsb2JEaXJlY3Rvcnk6ICcvYXNzZXRzL2xtcy9mcm9udGVuZCcsXG5cdFx0XHRcdGdsb2JQYXR0ZXJuczogWycqKi8qLntqcyx0cyxjc3MsaHRtbCxwbmcsc3ZnfSddLFxuXHRcdFx0XHRydW50aW1lQ2FjaGluZzogW1xuXHRcdFx0XHRcdHtcblx0XHRcdFx0XHRcdHVybFBhdHRlcm46ICh7IHJlcXVlc3QgfSkgPT5cblx0XHRcdFx0XHRcdFx0cmVxdWVzdC5kZXN0aW5hdGlvbiA9PT0gJ2RvY3VtZW50Jyxcblx0XHRcdFx0XHRcdGhhbmRsZXI6ICdOZXR3b3JrRmlyc3QnLFxuXHRcdFx0XHRcdFx0b3B0aW9uczoge1xuXHRcdFx0XHRcdFx0XHRjYWNoZU5hbWU6ICdodG1sLWNhY2hlJyxcblx0XHRcdFx0XHRcdH0sXG5cdFx0XHRcdFx0fSxcblx0XHRcdFx0XSxcblx0XHRcdH0sXG5cdFx0XHRtYW5pZmVzdDogZmFsc2UsXG5cdFx0fSksXG5cdF0sXG5cdHNlcnZlcjoge1xuXHRcdGhvc3Q6ICcwLjAuMC4wJywgLy8gQWNjZXB0IGNvbm5lY3Rpb25zIGZyb20gYW55IG5ldHdvcmsgaW50ZXJmYWNlXG5cdFx0YWxsb3dlZEhvc3RzOiBbJ3BzJywgJ2ZzJywgJ2hvbWUnXSwgLy8gRXhwbGljaXRseSBhbGxvdyB0aGlzIGhvc3Rcblx0fSxcblx0cmVzb2x2ZToge1xuXHRcdGFsaWFzOiB7XG5cdFx0XHQnQCc6IHBhdGgucmVzb2x2ZShfX2Rpcm5hbWUsICdzcmMnKSxcblx0XHR9LFxuXHR9LFxuXHRvcHRpbWl6ZURlcHM6IHtcblx0XHRpbmNsdWRlOiBbXG5cdFx0XHQnZmVhdGhlci1pY29ucycsXG5cdFx0XHQnZW5naW5lLmlvLWNsaWVudCcsXG5cdFx0XHQnaW50ZXJhY3RqcycsXG5cdFx0XHQnaGlnaGxpZ2h0LmpzJyxcblx0XHRcdCdwbHlyJyxcblx0XHRdLFxuXHRcdGV4Y2x1ZGU6IG1vZGUgPT09ICdwcm9kdWN0aW9uJyA/IFtdIDogWydmcmFwcGUtdWknXSxcblx0fSxcbn0pKVxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUFrVSxTQUFTLG9CQUFvQjtBQUMvVixPQUFPLFNBQVM7QUFDaEIsT0FBTyxVQUFVO0FBQ2pCLE9BQU8sY0FBYztBQUNyQixTQUFTLGVBQWU7QUFKeEIsSUFBTSxtQ0FBbUM7QUFPekMsSUFBTyxzQkFBUSxhQUFhLENBQUMsRUFBRSxLQUFLLE9BQU87QUFBQSxFQUMxQyxTQUFTO0FBQUEsSUFDUixTQUFTO0FBQUEsTUFDUixhQUFhO0FBQUEsTUFDYixhQUFhO0FBQUEsTUFDYixlQUFlO0FBQUEsTUFDZixhQUFhO0FBQUEsUUFDWixPQUFPLENBQUM7QUFBQSxNQUNUO0FBQUEsTUFDQSxhQUFhO0FBQUEsUUFDWixlQUFlO0FBQUEsTUFDaEI7QUFBQSxJQUNELENBQUM7QUFBQSxJQUNELElBQUk7QUFBQSxNQUNILFFBQVE7QUFBQSxRQUNQLGFBQWE7QUFBQSxRQUNiLGtCQUFrQjtBQUFBLE1BQ25CO0FBQUEsSUFDRCxDQUFDO0FBQUEsSUFDRCxRQUFRO0FBQUEsTUFDUCxjQUFjO0FBQUEsTUFDZCxZQUFZO0FBQUEsUUFDWCxTQUFTO0FBQUEsTUFDVjtBQUFBLE1BQ0EsU0FBUztBQUFBLFFBQ1IsdUJBQXVCO0FBQUEsUUFDdkIsK0JBQStCLElBQUksT0FBTztBQUFBLFFBQzFDLGVBQWU7QUFBQSxRQUNmLGNBQWMsQ0FBQywrQkFBK0I7QUFBQSxRQUM5QyxnQkFBZ0I7QUFBQSxVQUNmO0FBQUEsWUFDQyxZQUFZLENBQUMsRUFBRSxRQUFRLE1BQ3RCLFFBQVEsZ0JBQWdCO0FBQUEsWUFDekIsU0FBUztBQUFBLFlBQ1QsU0FBUztBQUFBLGNBQ1IsV0FBVztBQUFBLFlBQ1o7QUFBQSxVQUNEO0FBQUEsUUFDRDtBQUFBLE1BQ0Q7QUFBQSxNQUNBLFVBQVU7QUFBQSxJQUNYLENBQUM7QUFBQSxFQUNGO0FBQUEsRUFDQSxRQUFRO0FBQUEsSUFDUCxNQUFNO0FBQUE7QUFBQSxJQUNOLGNBQWMsQ0FBQyxNQUFNLE1BQU0sTUFBTTtBQUFBO0FBQUEsRUFDbEM7QUFBQSxFQUNBLFNBQVM7QUFBQSxJQUNSLE9BQU87QUFBQSxNQUNOLEtBQUssS0FBSyxRQUFRLGtDQUFXLEtBQUs7QUFBQSxJQUNuQztBQUFBLEVBQ0Q7QUFBQSxFQUNBLGNBQWM7QUFBQSxJQUNiLFNBQVM7QUFBQSxNQUNSO0FBQUEsTUFDQTtBQUFBLE1BQ0E7QUFBQSxNQUNBO0FBQUEsTUFDQTtBQUFBLElBQ0Q7QUFBQSxJQUNBLFNBQVMsU0FBUyxlQUFlLENBQUMsSUFBSSxDQUFDLFdBQVc7QUFBQSxFQUNuRDtBQUNELEVBQUU7IiwKICAibmFtZXMiOiBbXQp9Cg==
