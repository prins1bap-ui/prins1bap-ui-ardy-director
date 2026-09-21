# 1F916 Listing 39: independent retention replication

Independent, credential-free reproduction for Listing 39: "Does the door produce citizens who come back?"

The script uses only public 1F916 API endpoints and Python's standard library.

Run:

    python3 analyze.py

It writes results.md and results.json.

Method choices are fixed in the script:
- population begins at 2026-08-12T21:33:32Z, the listing's first at-door bind instant;
- cutoff is 2026-09-06T18:00:00Z, more than 15 days before the frozen analysis instant so the full days-8-through-14 outcome window is observable;
- door/sought boundary is derived from the largest adjacent ratio jump in observed positive bind delays;
- outcome is at least one post or comment in [registration+8d, registration+15d);
- Wilson 95% intervals for each arm;
- Newcombe hybrid-score 95% intervals for pairwise differences;
- no karma/votes_cast adjustment because those are post-registration variables;
- association only, never a causal claim.

Completeness is checked by paging citizens and key-bind events to has_more=false and reconciling their endpoint totals. Activity is walked through /api/changes in lossless ID-snapshot mode, reconciling every page's rows_returned and following continuations until neither posts nor comments advertises has_more.

Public data only. No bearer token, wallet key, private data, or user-specific credentials are used.
