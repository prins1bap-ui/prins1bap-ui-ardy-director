# Cyndra bug bounty report packet

Prepared: 2026-09-14

## Reward preference
Gift Card

## Severity
Cosmetic (UI/typo/layout)

## Bug title
API docs claim six MCP tools but document only five

## Steps to reproduce
1. Open https://www.cyndra.ai/api-docs.
2. Scroll to the MCP section.
3. Note that the section states the Cyndra MCP server exposes six read-only tools.
4. Count the tools documented immediately below that statement. Only five are listed: search_cyndra_content, get_cyndra_page, list_cyndra_pages, get_cyndra_pricing, and get_cyndra_changelog.
5. Scroll to the FAQ. The MCP answer again says the server exposes six tools and specifically says case studies can be fetched.
6. The same API documentation also publishes public case-study endpoints, but no case-study MCP tool appears in the documented MCP tool list.

## Expected behavior vs actual behavior
Expected: the MCP documentation should match the server surface. If six tools are exposed, all six should be named and described. If only five tools are exposed, the stated tool count and FAQ should say five and should not claim case-study MCP functionality.

Actual: the page states there are six read-only MCP tools but lists only five. The FAQ also references fetching case studies, creating an internally inconsistent developer reference and leaving one advertised capability undocumented.

## Evidence
Visual evidence: https://raw.githubusercontent.com/prins1bap-ui/prins1bap-ui-ardy-director/cyndra-bounty-evidence/cyndra-mcp-docs-bug-evidence.svg

Source page: https://www.cyndra.ai/api-docs

## Additional notes
This is reproducible on the public documentation without authentication, destructive testing, data modification, or access to third-party systems. I selected the conservative Cosmetic classification because this is a documentation/UI inconsistency rather than a demonstrated service failure. Cyndra can reclassify the finding if it considers the developer-integration impact Functional.
