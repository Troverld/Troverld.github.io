// Refresh checked-in browser dependencies without adding a build-time npm step.
// node scripts/vendor-libraries.mjs /absolute/path/to/node_modules
import { copyFile, mkdir, readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
if (!process.argv[2]) throw new Error('Pass the node_modules directory containing mathjax@3.2.2 and mermaid@11.12.0');
const modules = path.resolve(process.argv[2]);
async function copy(source, target) {
  await mkdir(path.dirname(target), { recursive: true });
  await copyFile(source, target);
}
for (const [name, version] of [['mathjax', '3.2.2'], ['mermaid', '11.12.0']]) {
  const source = path.join(modules, name);
  const pkg = JSON.parse(await readFile(path.join(source, 'package.json'), 'utf8'));
  if (pkg.version !== version) throw new Error(`Expected ${name}@${version}, got ${pkg.version}`);
  const target = path.join(root, 'static/vendor', name, version);
  await copy(path.join(source, 'LICENSE'), path.join(target, 'LICENSE.txt'));
  if (name === 'mathjax') {
    await copy(path.join(source, 'es5/tex-svg-full.js'), path.join(target, 'tex-svg-full.js'));
    const extensions = 'input/tex/extensions';
    for (const file of await readdir(path.join(source, 'es5', extensions))) {
      if (file.endsWith('.js')) await copy(path.join(source, 'es5', extensions, file), path.join(target, extensions, file));
    }
  } else {
    await copy(path.join(source, 'dist/mermaid.esm.min.mjs'), path.join(target, 'mermaid.esm.min.mjs'));
    const chunks = 'chunks/mermaid.esm.min';
    for (const file of await readdir(path.join(source, 'dist', chunks))) {
      if (file.endsWith('.mjs')) await copy(path.join(source, 'dist', chunks, file), path.join(target, chunks, file));
    }
  }
  console.log(`Copied ${name}@${version} runtime and license.`);
}
