import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // pdf-build/ holds the print pipeline's node helpers (plain .mjs, because
    // render-sections.mjs runs under plain node). They are covered here so that
    // `npm run test` stays the one command, as in the Vacuum book.
    include: ['src/**/*.test.ts', 'scripts/**/*.test.mjs', 'pdf-build/**/*.test.mjs'],
    environment: 'node',
  },
});
