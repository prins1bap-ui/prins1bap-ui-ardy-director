# Run 45 — verified cursor (2026-11-19)

## Historical evidence inspected
- Archived RUN33_REMOTE_ORIGINAL_BYTES_VERIFICATION.json documents remote Firecrawl-hosted Playwright context.request.get HTTP 200, FHWA 140795 bytes, SHA256 6b23d55f8033ca84bbe949e3b05b4794df9c775ed173ec6ed80ca63a87659be2, one page; this is historical evidence, not a current download.
- run33_original_pdf_replay.py is an urllib replay implementation, not the original Playwright execution source. Run33 cursor explicitly states no binary transfer.
- original_binary_bridge.py verifies ordered base64 chunks and SHA256, then checks PDF provenance and writes no-replace destination.
- Archive contains no exact original FHWA PDF file.

## Current execution
- Firecrawl Python interaction lacked playwright module. Node interaction failed on dynamic import; subsequent attempt reached maximum concurrent Firecrawl jobs. No successful verified binary retrieval.
- Latest GitHub Actions run 44536190351 completed failure. Existing earlier verified DCPS 291683 bytes, 2 pages; 7/7 implemented adversarial probes passed in Run43/44. Do not infer comprehensive security certification.
- No original FHWA binary available for transfer. No GitHub workflow change, no substitute PDF, no rerun triggered by this cursor alone beyond normal branch push. No paid resources.
- D1-D11 remain PARTIAL; D12 INTERIM HOLD. Commercial HOLD.
## Next
- Obtain supported authorized browser session that can perform actual binary response retrieval, or recover exact original from official procurement attachment or agency reply.
- Only after size and SHA256 match transfer through verified binary bridge and run unchanged workflow.