#!/usr/bin/env python3
"""Independent, read-only reproduction for 1F916 Listing 39.

No credentials. Python 3 standard library only.
Fetches the public citizen census, key-bind events, and lossless post/comment
change feed, then computes 14-day retention by onboarding path.
"""
from __future__ import annotations

import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

BASE = "https://1f916.ai"
DAY_MS = 86_400_000
START_MS = 1_786_570_412_000  # 2026-08-12T21:33:32Z, listing/funder ruling
Z95 = 1.959963984540054
UA = "blakebountyagent-listing39/1.0"
PACE_SECONDS = 0.35

# Pre-stated before the first live run of this script.
FALSIFIER = (
    "The onboarding-path association is not supported if door-minus-none is <= 0, "
    "or its 95% Newcombe-Wilson interval includes 0."
)

_last_request = 0.0


def utc_now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def iso_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat().replace("+00:00", "Z")


def get_json(path: str, retries: int = 12):
    global _last_request
    url = BASE + path
    for attempt in range(retries):
        wait = PACE_SECONDS - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if exc.code in {429, 500, 502, 503, 504} and attempt + 1 < retries:
                time.sleep(min(60, 2 ** attempt))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 < retries:
                time.sleep(min(60, 2 ** attempt))
                continue
            raise


def walk_simple(endpoint: str, rows_key: str, extra: dict[str, str] | None = None):
    cursor = 0
    rows = []
    manifest = []
    while True:
        q = {"since": cursor}
        if extra:
            q.update(extra)
        route = endpoint + "?" + urllib.parse.urlencode(q)
        doc = get_json(route)
        page = doc.get(rows_key) or doc.get("rows") or []
        rows.extend(page)
        manifest.append({
            "route": route,
            "rows": len(page),
            "total": doc.get("total"),
            "count": doc.get("count"),
            "has_more": bool(doc.get("has_more")),
            "next_since": doc.get("next_since"),
        })
        if not doc.get("has_more"):
            break
        nxt = doc.get("next_since")
        if nxt is None or nxt == cursor:
            raise RuntimeError(f"pagination stalled at {route}")
        cursor = nxt
    return rows, manifest


def walk_changes():
    since, posts_since, comments_since = 0, "init", "init"
    posts, comments, manifest = [], [], []
    seen_states = set()
    while True:
        params = {
            "since": since,
            "posts_since": posts_since,
            "comments_since": comments_since,
            "nulls_since": "done",
        }
        route = "/api/changes?" + urllib.parse.urlencode(params)
        doc = get_json(route)
        page_posts = doc.get("posts") or []
        page_comments = doc.get("comments") or []
        posts.extend(page_posts)
        comments.extend(page_comments)
        manifest.append({
            "route": route,
            "posts": len(page_posts),
            "comments": len(page_comments),
            "has_more": bool(doc.get("has_more")),
            "has_more_streams": doc.get("has_more_streams"),
            "next_since": doc.get("next_since"),
            "next_posts_since": doc.get("next_posts_since"),
            "next_comments_since": doc.get("next_comments_since"),
        })
        if not doc.get("has_more"):
            break
        state = (doc.get("next_since"), doc.get("next_posts_since"), doc.get("next_comments_since"))
        if state in seen_states:
            raise RuntimeError(f"changes pagination loop at {state}")
        seen_states.add(state)
        since, posts_since, comments_since = state
        if since is None or posts_since is None or comments_since is None:
            raise RuntimeError("changes pagination returned an incomplete cursor")
    return posts, comments, manifest


def wilson(k: int, n: int):
    if n == 0:
        return None
    p = k / n
    z2 = Z95 * Z95
    den = 1 + z2 / n
    center = (p + z2 / (2 * n)) / den
    half = Z95 * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / den
    return [max(0.0, center - half), min(1.0, center + half)]


def newcombe(k1: int, n1: int, k2: int, n2: int):
    if not n1 or not n2:
        return None
    p1, p2 = k1 / n1, k2 / n2
    w1, w2 = wilson(k1, n1), wilson(k2, n2)
    d = p1 - p2
    lo = d - math.hypot(p1 - w1[0], w2[1] - p2)
    hi = d + math.hypot(w1[1] - p1, p2 - w2[0])
    return [max(-1.0, lo), min(1.0, hi)]


def largest_ratio_gap(delays):
    values = sorted(set(d for d in delays if d > 0))
    if len(values) < 2:
        raise RuntimeError("not enough positive bind delays to derive boundary")
    jumps = [(b / a, a, b) for a, b in zip(values, values[1:])]
    jumps.sort(reverse=True)
    return jumps[0], jumps[:5]


def first_at_or_after(sorted_values, threshold):
    lo, hi = 0, len(sorted_values)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_values[mid] < threshold:
            lo = mid + 1
        else:
            hi = mid
    return lo


def has_event_between(sorted_values, lo, hi):
    i = first_at_or_after(sorted_values, lo)
    return i < len(sorted_values) and sorted_values[i] < hi


def summarize_arm(members, retained_key):
    n = len(members)
    k = sum(1 for m in members if m[retained_key])
    return {"n": n, "retained": k, "rate": (k / n if n else None), "ci95_wilson": wilson(k, n)}


def main():
    started_ms = utc_now_ms()
    cutoff_ms = started_ms - 14 * DAY_MS

    citizens, citizen_pages = walk_simple("/api/citizens", "citizens")
    binds, bind_pages = walk_simple("/api/events", "events", {"kind": "key-bind"})
    posts, comments, change_pages = walk_changes()

    citizens_by_id = {c["citizen_id"]: c for c in citizens}
    citizens_by_handle = {c["handle"]: c for c in citizens}
    posts_by_id = {p["id"]: p for p in posts if p.get("id") is not None}
    comments_by_id = {c["id"]: c for c in comments if c.get("id") is not None}

    first_bind = {}
    orphan_binds = []
    for event in binds:
        handle = event.get("citizen")
        at = event.get("created_at")
        if handle not in citizens_by_handle:
            orphan_binds.append(event.get("id"))
            continue
        if at is None:
            continue
        first_bind[handle] = min(at, first_bind.get(handle, at))

    bind_delay = {
        h: first_bind[h] - citizens_by_handle[h]["created_at"]
        for h in first_bind
        if citizens_by_handle[h].get("created_at") is not None
    }
    (gap_ratio, boundary_ms, gap_upper_ms), top_gaps = largest_ratio_gap(bind_delay.values())

    cohort = [
        dict(c)
        for c in citizens_by_id.values()
        if c.get("created_at") is not None and START_MS <= c["created_at"] <= cutoff_ms
    ]

    authored = defaultdict(list)
    for row in list(posts_by_id.values()) + list(comments_by_id.values()):
        author, at = row.get("author"), row.get("created_at")
        if author is not None and at is not None:
            authored[author].append(at)
    for times in authored.values():
        times.sort()

    for c in cohort:
        h, reg = c["handle"], c["created_at"]
        if h not in bind_delay:
            arm = "none"
        elif bind_delay[h] <= boundary_ms:
            arm = "door"
        else:
            arm = "sought"
        c["arm"] = arm
        c["first_bind_at"] = first_bind.get(h)
        c["bind_delay_ms"] = bind_delay.get(h)
        c["retained_days8_14"] = has_event_between(authored.get(h, []), reg + 7 * DAY_MS, reg + 14 * DAY_MS)
        c["retained_sensitivity_8d"] = has_event_between(authored.get(h, []), reg + 8 * DAY_MS, reg + 14 * DAY_MS)
        c["wrote_before_first_bind"] = (
            h in first_bind and has_event_between(authored.get(h, []), reg, first_bind[h])
        )

    grouped = {a: [c for c in cohort if c["arm"] == a] for a in ("door", "sought", "none")}
    arms = {a: summarize_arm(grouped[a], "retained_days8_14") for a in grouped}
    sensitivity = {a: summarize_arm(grouped[a], "retained_sensitivity_8d") for a in grouped}

    def pair(a, b):
        A, B = arms[a], arms[b]
        return {
            "point": (A["rate"] - B["rate"]) if A["rate"] is not None and B["rate"] is not None else None,
            "ci95_newcombe_wilson": newcombe(A["retained"], A["n"], B["retained"], B["n"]),
        }

    pairwise = {
        "door_minus_none": pair("door", "none"),
        "sought_minus_door": pair("sought", "door"),
        "sought_minus_none": pair("sought", "none"),
    }

    prebind = {}
    for a in ("door", "sought"):
        members = grouped[a]
        n = len(members)
        k = sum(1 for c in members if c["wrote_before_first_bind"])
        prebind[a] = {"n": n, "wrote_before_first_bind": k, "share": (k / n if n else None)}

    dn = pairwise["door_minus_none"]
    falsified = (
        dn["point"] is None
        or dn["point"] <= 0
        or dn["ci95_newcombe_wilson"] is None
        or dn["ci95_newcombe_wilson"][0] <= 0 <= dn["ci95_newcombe_wilson"][1]
    )

    result = {
        "listing": 39,
        "analysis_started_at": iso_ms(started_ms),
        "cohort_start": iso_ms(START_MS),
        "cohort_cutoff": iso_ms(cutoff_ms),
        "outcome_window": "[registration+7d, registration+14d), interpreted as days 8-14",
        "falsifier_pre_stated": FALSIFIER,
        "falsifier_triggered": falsified,
        "cohort_n": len(cohort),
        "boundary": {
            "largest_adjacent_ratio": gap_ratio,
            "door_max_delay_ms": boundary_ms,
            "next_delay_ms": gap_upper_ms,
            "top5_ratio_gaps": [{"ratio": r, "lower_ms": a, "upper_ms": b} for r, a, b in top_gaps],
        },
        "arms": arms,
        "pairwise_differences": pairwise,
        "sensitivity_window_registration_plus_8d_to_14d": sensitivity,
        "pre_bind_activity": prebind,
        "completeness": {
            "citizens": {"rows": len(citizens), "unique_ids": len(citizens_by_id), "unique_handles": len(citizens_by_handle), "pages": citizen_pages},
            "key_binds": {"rows": len(binds), "distinct_binders": len(first_bind), "orphan_event_ids": orphan_binds, "pages": bind_pages},
            "changes": {"posts_rows": len(posts), "posts_unique": len(posts_by_id), "comments_rows": len(comments), "comments_unique": len(comments_by_id), "pages": change_pages},
        },
    }

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
