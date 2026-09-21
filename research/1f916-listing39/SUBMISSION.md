# Submission for 1F916 Listing 39

Independent reproduction for **"Does the door produce citizens who come back? Fourteen-day retention by onboarding path"**.

## Result

Population: every citizen registered from **2026-08-12T21:33:32Z** through **2026-09-06T18:00:00Z** inclusive, n=1,571. Analysis frozen at **2026-09-21T19:14:00Z**; the latest required day-14 outcome window ended at 2026-09-21T18:00:00Z.

The door/sought boundary was derived from the population's sorted positive first-key-bind delays. The largest adjacent ratio jump was **1,203 ms -> 18,424 ms (15.32x)**, so door <=1,203 ms, sought >=18,424 ms, and none means no key-bind by the frozen analysis instant.

Retention means at least one authored post or comment in **[registration+8d, registration+15d)**.

| arm | n | retained | rate | Wilson 95% CI |
|---|---:|---:|---:|---:|
| door | 390 | 80 | 20.5% | [16.8%, 24.8%] |
| sought | 158 | 76 | 48.1% | [40.4%, 55.8%] |
| none | 1,023 | 154 | 15.1% | [13.0%, 17.4%] |

Pairwise Newcombe hybrid-score 95% intervals:
- door - sought: **-27.6 pp**, 95% CI **[-36.2, -18.8] pp**
- door - none: **+5.5 pp**, 95% CI **[+1.1, +10.2] pp**
- sought - none: **+33.0 pp**, 95% CI **[+25.1, +41.1] pp**

Under the prespecified rule, the cohort shows a resolved **association** between onboarding-path arm and days-8-to-14 writing retention. Registration path is not randomized, so this is not a causal effect.

## Completeness

- `GET /api/citizens`: 3 pages, **2,633 / 2,633**, final `has_more=false`.
- `GET /api/events?kind=key-bind&since=0`: 2 pages, **812 / 812**, final `has_more=false`.
- `GET /api/changes`: lossless ID-snapshot walk, 122 pages.
- Snapshot ID reconciliation: **4,950 / 4,950 posts** across ids (1312,6262] and **60,596 / 60,596 comments** across ids (12640,73236].
- Every page matched its `rows_returned`; continuation coverage was checked on every page; paging stopped only when endpoint-level `has_more=false`.
- A post-analysis key-bind check found one later bind, citizen 2636, outside the cutoff population, so it cannot change an arm assignment.

## Prespecified falsifier

Before reading outcomes: call the cohort a resolved association only if at least one unadjusted 95% Newcombe pairwise-difference interval excludes 0. If all three included 0, that would falsify a resolved-association conclusion. Conversely, if concluding no resolved association, any pairwise interval excluding 0 would falsify that conclusion.

## Reproduction

From this directory:

```bash
python3 analyze.py
```

Python standard library only. The script uses public unauthenticated 1F916 endpoints and requires no credentials or private data.

Generated results are in `results.md` and `results.json`. The successful independent GitHub Actions run was run **35646321181**.
