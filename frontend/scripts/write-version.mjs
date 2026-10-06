// Post-build: stamp dist/version.json with the hashed entry bundle id so the
// inline self-heal script in index.html can detect a stale in-memory bundle
// and force one reload. Runs as part of `npm run build`.
import { readFileSync, writeFileSync } from 'node:fs';

const html = readFileSync('dist/index.html', 'utf8');
const m = html.match(/assets\/index-([A-Za-z0-9_-]+)\.js/);
if (!m) {
  console.error('write-version: could not find hashed entry asset in dist/index.html');
  process.exit(1);
}
writeFileSync('dist/version.json', JSON.stringify({ build: m[1], t: Date.now() }) + '\n');
console.log(`write-version: build=${m[1]}`);
