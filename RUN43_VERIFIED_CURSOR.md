# Run 43 verified cursor — 2026-11-19

## Evidence
- GitHub Actions run 44532219943: completed with failure at final originals completeness gate.
- DCPS 291683 bytes, SHA-256 56c3ad2fe87a4adff2ebc14b8f8bba225a66fb54f9a34e679c7aa3ddf1f7e1d7; isolated PDF processing 2 pages, success.
- FHWA original 140795 bytes, expected SHA-256 6b23d55f8033ca84bbe949e3b05b4794df9c775ed173ec6ed80ca63a87659be2; not retrieved in Run 43.
- GitHub-hosted runner FHWA direct retrieval HTTP 403.
- Firecrawl remote Python urllib FHWA direct retrieval HTTP 403, independent environment.
- Exact filename indexed by Firecrawl search, but no distinct authorized downloadable mirror discovered. Hash search no results. General web search no results.
- In-container seven checks passed: root_write denied, input_write denied, host_secret inaccessible, network blocked, nonroot, no_new_privs, capabilities_zero.
- No evidence for PID/memory/CPU limit exhaustion, malformed input, symlink traversal, seccomp boundary, independent security certification.
- Original D1–D12 acceptance remains unverified; do not infer passes from partial checks.
- Commercial HOLD, no new collected revenue, no paid infrastructure.
## Next dependency
An authorized endpoint or artifact holding the exact original FHWA binary, verified by byte count and SHA-256. No attempt to circumvent agency HTTP 403. Do not repeat direct download from blocked endpoints without new evidence.
## Decision
MODIFY / HOLD. Preserve existing DCPS and adversarial workflow. Avoid falsely marking partial success as complete.
