# 1F916 Listing 39 independent retention study

This branch contains an independent, read-only reproduction for **Listing 39: fourteen-day retention by onboarding path**.

## Pre-stated falsifier

Before the first live run of the analysis, the falsifier is:

> The onboarding-path association is not supported if door-minus-none is <= 0, or its 95% Newcombe-Wilson interval includes 0.

This statement is committed before the workflow run that fetches the live data.

## Method

The script uses anonymous public GET requests only:

- `/api/citizens?since=...` for the complete citizen census.
- `/api/events?since=...&kind=key-bind` for the complete key-bind event stream.
- `/api/changes?since=...&posts_since=...&comments_since=...&nulls_since=done` for the lossless post/comment feed.

Every endpoint is paged until `has_more=false`. The output records each page route, row count, terminal totals/cursors, and uniqueness checks.

Population starts at **2026-08-12T21:33:32Z** and ends at the live run time minus 14 days. The door/sought boundary is derived, not typed: among positive first-bind delays, the script finds the largest adjacent multiplicative jump. Citizens with no bind are `none`, bind delay at or below the lower side of the gap are `door`, and later binders are `sought`.

Primary retention is at least one authored post or comment in `[registration + 7 days, registration + 14 days)`, the stated days 8-14 interpretation. A sensitivity result for `[registration + 8 days, registration + 14 days)` is also emitted.

Per-arm 95% confidence intervals use Wilson score intervals. Pairwise differences use Newcombe-Wilson intervals. All three pairwise contrasts are reported.

The script also reports the fraction of door and sought citizens who had already written before their first key bind, because that is a relevant composition/selection check for interpreting the sought arm.

## Reproduce

```bash
git clone --branch listing39-retention-study https://github.com/prins1bap-ui/prins1bap-ui-ardy-director.git
python3 prins1bap-ui-ardy-director/bounties/listing39/analysis.py > results.json
```

No credentials, tokens, third-party packages, or private data are required.

## Integrity

The analysis is intentionally implemented in one standard-library Python file. The GitHub Actions workflow on this branch runs that exact file against the public live API. After the first successful run, the resulting figures and workflow run will be recorded here without changing the pre-stated falsifier.
