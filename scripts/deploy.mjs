// Deploy the built static site to a web server folder.
//
//   npm run deploy        # builds, checks links, then copies dist/ -> DEPLOY_DEST
//
// DEPLOY_DEST comes from the environment or from local-paths.json at the repo
// root (not committed). The script empties its destination before copying, and a
// web root usually holds other sites: a mistyped DEPLOY_DEST would wipe one of
// them. So it refuses to clear a folder unless it is empty or already holds this
// book, recognised by the sections.json every build of it publishes.
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { basename, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { BASE } from '../src/lib/site.mjs';

const LOCAL = fileURLToPath(new URL('../local-paths.json', import.meta.url));
const local = existsSync(LOCAL) ? JSON.parse(readFileSync(LOCAL, 'utf-8')) : {};
const DEST = process.env.DEPLOY_DEST || local.DEPLOY_DEST;
const SRC = fileURLToPath(new URL('../dist', import.meta.url));

if (!DEST) {
  console.error('DEPLOY_DEST is not set: set the environment variable or add it to local-paths.json.');
  process.exit(1);
}
if (!existsSync(join(SRC, 'sections.json'))) {
  console.error(`No build found at ${SRC}. Run "npm run build" first.`);
  process.exit(1);
}
// The folder name is the URL path on the web server; they must agree.
if (basename(DEST) !== BASE.replace(/^\//, '')) {
  console.error(`DEPLOY_DEST ${DEST} would be served at /${basename(DEST)}/, but the site is built for ${BASE}/.`);
  process.exit(1);
}

mkdirSync(DEST, { recursive: true });
const existing = readdirSync(DEST);
if (existing.length > 0 && !existing.includes('sections.json')) {
  console.error(`Refusing to clear ${DEST}: it is not empty and does not hold a previous deploy of this book `
    + `(no sections.json). Contents: ${existing.slice(0, 8).join(', ')}`);
  process.exit(1);
}

// Clear the contents (not the folder) so stale content-hashed assets from
// earlier deploys do not accumulate.
for (const entry of existing) rmSync(join(DEST, entry), { recursive: true, force: true });
cpSync(SRC, DEST, { recursive: true });

console.log(`Deployed ${SRC} -> ${DEST} (${readdirSync(DEST).length} top-level entries).`);
if (local.DEPLOY_URL) console.log(`Served at ${local.DEPLOY_URL} . HTML revalidates via its meta tag; assets are content-hashed.`);
