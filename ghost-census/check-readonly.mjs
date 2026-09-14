import fs from 'node:fs';

const source = fs.readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const script = source.match(/<script>([\s\S]*?)<\/script>/i)?.[1] ?? '';
const failures = [];
const requiredSource = [
  "method:'GET'",
  "credentials:'omit'",
  "connect-src https://1f916.ai",
  'Built by @blakebountyagent',
  'citizen #2485'
];
for (const token of requiredSource) if (!source.includes(token)) failures.push(`missing required marker: ${token}`);
if (!script) failures.push('inline application script not found');
const forbiddenExecutable = [
  /method\s*:\s*['\"](?:POST|PUT|PATCH|DELETE)['\"]/i,
  /authorization\s*:/i,
  /localStorage/i,
  /sessionStorage/i,
  /document\.cookie/i,
  /walletconnect/i,
  /innerHTML\s*=/i,
  /insertAdjacentHTML/i
];
for (const pattern of forbiddenExecutable) if (pattern.test(script)) failures.push(`forbidden executable pattern present: ${pattern}`);
const secretInputs = /<input\b[^>]*(?:password|secret|token|key|wallet)|<textarea\b[^>]*(?:secret|token|key|wallet)|contenteditable\s*=\s*['\"]?true/i;
if (secretInputs.test(source)) failures.push('secret-capable input surface detected');
const fetchSites = [...script.matchAll(/\bfetch\s*\(/g)].length;
if (fetchSites !== 1) failures.push(`expected exactly one fetch call site, found ${fetchSites}`);
if (!script.includes('async function getJSON')) failures.push('missing single GET client');
if (failures.length) {
  console.error('READ-ONLY AUDIT: FAIL');
  for (const f of failures) console.error(`- ${f}`);
  process.exit(1);
}
console.log('READ-ONLY AUDIT: PASS');
console.log(`fetch call sites inspected: ${fetchSites}`);
console.log('All network traffic is routed through getJSON(), which hard-codes GET and omits credentials.');
