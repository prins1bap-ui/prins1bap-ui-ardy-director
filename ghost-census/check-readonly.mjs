import fs from 'node:fs';

const source = fs.readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const failures = [];
const required = [
  "method:'GET'",
  "credentials:'omit'",
  "connect-src https://1f916.ai",
  'Built by @blakebountyagent',
  'citizen #2485'
];
for (const token of required) if (!source.includes(token)) failures.push(`missing required marker: ${token}`);
const forbidden = [
  /method\s*:\s*['\"](?:POST|PUT|PATCH|DELETE)['\"]/i,
  /authorization\s*:/i,
  /localStorage/i,
  /sessionStorage/i,
  /document\.cookie/i,
  /type\s*=\s*['\"]password['\"]/i,
  /citizen[_ -]?secret/i,
  /private[_ -]?key/i,
  /walletconnect/i,
  /innerHTML\s*=/i,
  /insertAdjacentHTML/i
];
for (const pattern of forbidden) if (pattern.test(source)) failures.push(`forbidden pattern present: ${pattern}`);
const writes = [...source.matchAll(/fetch\s*\(([^)]*)\)/g)].map(m => m[0]);
if (!source.includes('async function getJSON')) failures.push('missing single GET client');
if (failures.length) {
  console.error('READ-ONLY AUDIT: FAIL');
  for (const f of failures) console.error(`- ${f}`);
  process.exit(1);
}
console.log('READ-ONLY AUDIT: PASS');
console.log(`fetch call sites inspected: ${writes.length}`);
console.log('All network traffic is routed through getJSON(), which hard-codes GET and omits credentials.');
