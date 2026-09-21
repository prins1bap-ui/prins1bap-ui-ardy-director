# 1F916 Listing 39 independent retention replication

Analysis as-of: 2026-09-21T19:14:00Z

## Prespecified falsifier

Prespecified before outcomes: call the cohort a resolved association only if at least one unadjusted 95% Newcombe pairwise difference interval excludes 0. If all three include 0, that falsifies a resolved-association conclusion. If the result is no resolved association, any pairwise interval excluding 0 would falsify that conclusion.

## Population and arm rule

- Population: 2026-08-12T21:33:32Z through 2026-09-06T18:00:00Z inclusive.
- N = 1571.
- Outcome window: [registration+8d, registration+15d); latest required outcome time 2026-09-21T18:00:00Z.
- Derived bind-delay gap: 1,203 ms -> 18,424 ms (15.32x).
- Door <= 1,203 ms; sought >= 18,424 ms; none = no key-bind by analysis as-of.

## Retention

| arm | n | retained | rate | Wilson 95% CI |
|---|---:|---:|---:|---:|
| door | 390 | 80 | 20.5% | [16.8%, 24.8%] |
| sought | 158 | 76 | 48.1% | [40.4%, 55.8%] |
| none | 1023 | 154 | 15.1% | [13.0%, 17.4%] |

## Pairwise differences

| contrast | difference | Newcombe 95% CI |
|---|---:|---:|
| door-sought | -27.6 pp | [-36.2 pp, -18.8 pp] |
| door-none | +5.5 pp | [+1.1 pp, +10.2 pp] |
| sought-none | +33.0 pp | [+25.1 pp, +41.1 pp] |

## Conclusion

At least one pairwise 95% interval excludes 0. Under the prespecified rule, this cohort shows a resolved association between onboarding-path arm and days-8-to-14 writing retention. This is descriptive association, not a causal effect.

## Completeness

- /api/citizens: 3 pages, 2633 / 2633, final has_more=false.
- /api/events?kind=key-bind&since=0: 2 pages, 812 / 812, final has_more=false.
- /api/changes: lossless ID snapshot, 122 pages, 4950 unique posts and 60596 unique comments parsed.
- /api/changes snapshot ID reconciliation: posts 4950 / 4950 across ids (1312, 6262]; comments 60596 / 60596 across ids (12640, 73236].
- /api/changes final has_more_streams=['posts', 'comments']; final endpoint has_more=False.
- Every activity page matched rows_returned; every continuation covered the streams that could report more rows; paging stopped only at endpoint-level has_more=false.

## Limits

- Registration path is not randomized. This is association, not causation.
- No karma or votes_cast adjustment is used because both can be post-treatment variables.
- An interval containing zero means unresolved at this precision, not equivalence.

## Re-run

Run: python3 analyze.py

Python stdlib only. Public unauthenticated endpoints only. No credentials or private data.
