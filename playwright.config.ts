import { defineConfig } from '@playwright/test';
import { BASE, PORT } from './src/lib/site.mjs';

export default defineConfig({
  testDir: './e2e',
  webServer: {
    command: 'npm run build && npm run preview',
    url: `http://localhost:${PORT}${BASE}/`,
    reuseExistingServer: false,
    timeout: 120_000,
  },
  use: { baseURL: `http://localhost:${PORT}` },
});
