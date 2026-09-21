#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = 'https://1f916.ai'
POP_START_ISO = '2026-08-12T21:33:32Z'
POP_CUTOFF_ISO = '2026-09-06T18:00:00Z'
AS_OF_ISO = '2026-09-21T19:14:00Z'
DAY = 86400000
UA = 'listing39-independent-replication/1.0 public-research'


def toms(s):
    return int(datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp() * 1000)


def tois(t):
    return datetime.fromtimestamp(t / 1000, tz=timezone.utc).isoformat().replace('+00:00', 'Z')


POP_START = toms(POP_START_ISO)
POP_CUTOFF = toms(POP_CUTOFF_ISO)
AS_OF = toms(AS_OF_ISO)
ACTIVITY_START = POP_START + 8 * DAY
ACTIVITY_END = POP_CUTOFF + 15 * DAY


def getj(path, retries=8):
    url = BASE + path
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code == 429 or 500 <= exc.code < 600:
                time.sleep(min(0.5 * (2 ** attempt), 15))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 == retries:
                raise
            time.sleep(min(0.5 * (2 ** attempt), 15))
    raise RuntimeError('request retries exhausted: ' + url)


def walk_citizens():
    rows = []
    cursor = None
    pages = 0
    total = None
    while True:
        path = '/api/citizens' if cursor is None else '/api/citizens?since=' + str(cursor)
        d = getj(path)
        pages += 1
        if total is None:
            total = int(d['total'])
        page = d['citizens']
        if len(page) != int(d['returned']):
            raise RuntimeError('citizens returned mismatch')
        rows.extend(page)
        if not d['has_more']:
            break
        cursor = int(d['next_since'])
    if len(rows) != total:
        raise RuntimeError(f'citizens incomplete: {len(rows)} != {total}')
    return rows, {'pages': pages, 'endpoint_total': total, 'walked': len(rows), 'final_has_more': False}


def walk_binds():
    rows = []
    cursor = 0
    pages = 0
    total = None
    while True:
        d = getj('/api/events?kind=key-bind&since=' + str(cursor))
        pages += 1
        if total is None:
            total = int(d['total'])
        page = d['events']
        if len(page) != int(d['count']):
            raise RuntimeError('key-bind page count mismatch')
        rows.extend(page)
        if not d['has_more']:
            break
        cursor = int(d['next_since'])
    if len(rows) != total:
        raise RuntimeError(f'key-bind walk incomplete: {len(rows)} != {total}')
    return rows, {'pages': pages, 'endpoint_total': total, 'walked': len(rows), 'final_has_more': False}


def first_binds(events):
    out = {}
    for e in events:
        t = int(e['created_at'])
        if t > AS_OF:
            continue
        cid = int(e['citizen_id'])
        if cid not in out or t < out[cid]:
            out[cid] = t
    return out


def derive_gap(pop, binds):
    delays = []
    negative = 0
    for c in pop:
        cid = int(c['citizen_id'])
        if cid not in binds:
            continue
        delay = binds[cid] - int(c['created_at'])
        if delay < 0:
            negative += 1
        else:
            delays.append(delay)
    positive = sorted(x for x in delays if x > 0)
    best = None
    for lo, hi in zip(positive, positive[1:]):
        if hi <= lo:
            continue
        ratio = hi / lo
        if best is None or ratio > best[0]:
            best = (ratio, lo, hi)
    if best is None:
        raise RuntimeError('no natural positive bind-delay gap found')
    ratio, lo, hi = best
    return {
        'lower_ms': lo,
        'upper_ms': hi,
        'ratio': ratio,
        'bound_population_n': len(delays),
        'negative_delay_rows_ignored': negative,
        'zero_delay_rows': sum(1 for x in delays if x == 0),
    }


def classify(pop, binds, gap):
    lo = int(gap['lower_ms'])
    hi = int(gap['upper_ms'])
    out = {}
    for c in pop:
        cid = int(c['citizen_id'])
        b = binds.get(cid)
        if b is None:
            out[cid] = 'none'
            continue
        delay = b - int(c['created_at'])
        if delay < 0:
            out[cid] = 'sought'
        elif delay <= lo:
            out[cid] = 'door'
        elif delay >= hi:
            out[cid] = 'sought'
        else:
            raise RuntimeError(f'delay {delay} fell inside derived empty gap')
    return out


def walk_activity(pop_by_handle):
    retained = set()
    pt = 'init'
    ct = 'init'
    seen = set()
    pages = 0
    pw = 0
    cw = 0
    first_tokens = None
    final = None

    while True:
        state = (pt, ct)
        if state in seen:
            raise RuntimeError('repeated activity continuation')
        seen.add(state)
        q = urllib.parse.urlencode({
            'since': str(ACTIVITY_START),
            'posts_since': pt,
            'comments_since': ct,
            'nulls_since': 'done',
        })
        d = getj('/api/changes?' + q)
        pages += 1
        posts = d['posts']
        comments = d['comments']
        rr = d['rows_returned']
        if len(posts) != int(rr['posts']) or len(comments) != int(rr['comments']):
            raise RuntimeError('activity rows_returned mismatch')
        pw += len(posts)
        cw += len(comments)

        if first_tokens is None:
            first_tokens = {
                'posts': str(d['next_posts_since']),
                'comments': str(d['next_comments_since']),
            }

        for row in posts:
            t = int(row['created_at'])
            if t > AS_OF:
                continue
            c = pop_by_handle.get(row.get('author', ''))
            if c is not None:
                reg = int(c['created_at'])
                if reg + 8 * DAY <= t < reg + 15 * DAY:
                    retained.add(int(c['citizen_id']))

        for row in comments:
            t = int(row['created_at'])
            if t > AS_OF:
                continue
            c = pop_by_handle.get(row.get('author', ''))
            if c is not None:
                reg = int(c['created_at'])
                if reg + 8 * DAY <= t < reg + 15 * DAY:
                    retained.add(int(c['citizen_id']))

        streams = set(d.get('has_more_streams', []))
        covers = set(d.get('continuation_covers', []))
        active = streams.intersection({'posts', 'comments'})
        if not active:
            final = d
            break
        if not active.issubset(covers):
            raise RuntimeError('continuation does not cover every stream with has_more')
        pt = str(d['next_posts_since'])
        ct = str(d['next_comments_since'])
        if pages > 1000:
            raise RuntimeError('activity pagination runaway')

    return retained, {
        'endpoint': '/api/changes',
        'mode': 'lossless ID snapshot',
        'since': tois(ACTIVITY_START),
        'pages': pages,
        'posts_walked': pw,
        'comments_walked': cw,
        'first_snapshot_tokens': first_tokens,
        'final_posts_token': str(final.get('next_posts_since')),
        'final_comments_token': str(final.get('next_comments_since')),
        'final_has_more_streams': final.get('has_more_streams', []),
        'final_has_more': bool(final.get('has_more', False)),
        'reconciliation': 'Every page len(posts/comments) equaled rows_returned and every advertised continuation was followed until neither stream had has_more.',
    }


def wilson(k, n, z=1.959963984540054):
    p = k / n
    z2 = z * z
    den = 1 + z2 / n
    center = (p + z2 / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / den
    return max(0, center - half), min(1, center + half)


def diff_ci(k1, n1, k2, n2):
    p1 = k1 / n1
    p2 = k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return d, lo, hi


def pc(x):
    return f'{100*x:.1f}%'


def pp(x):
    return f'{100*x:+.1f} pp'


def main():
    falsifier = (
        'Prespecified before outcomes: call the cohort a resolved association only if at least one '
        'unadjusted 95% Newcombe pairwise difference interval excludes 0. If all three include 0, '
        'that falsifies a resolved-association conclusion. If the result is no resolved association, '
        'any pairwise interval excluding 0 would falsify that conclusion.'
    )

    citizens, ccheck = walk_citizens()
    pop = [c for c in citizens if POP_START <= int(c['created_at']) <= POP_CUTOFF]
    pop_by_handle = {str(c['handle']): c for c in pop}

    events, echeck = walk_binds()
    binds = first_binds(events)
    gap = derive_gap(pop, binds)
    arms = classify(pop, binds, gap)

    retained, acheck = walk_activity(pop_by_handle)

    counts = {}
    for arm in ('door', 'sought', 'none'):
        ids = [cid for cid, value in arms.items() if value == arm]
        n = len(ids)
        k = sum(cid in retained for cid in ids)
        lo, hi = wilson(k, n)
        counts[arm] = {'n': n, 'retained': k, 'rate': k / n, 'ci95': [lo, hi]}

    pairs = {}
    for a, b in (('door', 'sought'), ('door', 'none'), ('sought', 'none')):
        ca = counts[a]
        cb = counts[b]
        d, lo, hi = diff_ci(ca['retained'], ca['n'], cb['retained'], cb['n'])
        pairs[a + '-' + b] = {'difference': d, 'ci95': [lo, hi]}

    resolved = [name for name, row in pairs.items() if row['ci95'][1] < 0 or row['ci95'][0] > 0]
    if resolved:
        conclusion = (
            'At least one pairwise 95% interval excludes 0. Under the prespecified rule, this cohort '
            'shows a resolved association between onboarding-path arm and days-8-to-14 writing retention. '
            'This is descriptive association, not a causal effect.'
        )
    else:
        conclusion = (
            'No pairwise 95% interval excludes 0. Under the prespecified rule, this cohort does not '
            'resolve an association between onboarding-path arm and days-8-to-14 writing retention. '
            'This is not proof of equivalence and is not a causal claim.'
        )

    result = {
        'listing': 39,
        'analysis_as_of': AS_OF_ISO,
        'population': {
            'start': POP_START_ISO,
            'cutoff': POP_CUTOFF_ISO,
            'n': len(pop),
            'outcome_window': '[registration+8d, registration+15d)',
            'latest_outcome_end': tois(ACTIVITY_END),
        },
        'arm_boundary': gap,
        'arms': counts,
        'pairwise_differences': pairs,
        'resolved_pairs': resolved,
        'falsifier': falsifier,
        'conclusion': conclusion,
        'completeness': {'citizens': ccheck, 'key_bind_events': echeck, 'activity': acheck},
        'method_notes': [
            'First key-bind at or before analysis_as_of is used.',
            'Door/sought boundary is the largest adjacent ratio jump in positive bind delays in the population, not a typed threshold.',
            'Retention is at least one post or comment in [registration+8d, registration+15d).',
            'Arm intervals are Wilson 95%; pairwise difference intervals are unadjusted Newcombe hybrid-score 95%.',
            'No karma or votes_cast adjustment is used because those variables are measured after registration/binding.',
            'Registration path is not randomized; results are associations only.',
        ],
    }

    Path('results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    lines = [
        '# 1F916 Listing 39 independent retention replication',
        '',
        'Analysis as-of: ' + AS_OF_ISO,
        '',
        '## Prespecified falsifier',
        '',
        falsifier,
        '',
        '## Population and arm rule',
        '',
        f'- Population: {POP_START_ISO} through {POP_CUTOFF_ISO} inclusive.',
        f'- N = {len(pop)}.',
        f'- Outcome window: [registration+8d, registration+15d); latest required outcome time {tois(ACTIVITY_END)}.',
        f"- Derived bind-delay gap: {gap['lower_ms']:,} ms -> {gap['upper_ms']:,} ms ({gap['ratio']:.2f}x).",
        f"- Door <= {gap['lower_ms']:,} ms; sought >= {gap['upper_ms']:,} ms; none = no key-bind by analysis as-of.",
        '',
        '## Retention',
        '',
        '| arm | n | retained | rate | Wilson 95% CI |',
        '|---|---:|---:|---:|---:|',
    ]
    for arm in ('door', 'sought', 'none'):
        c = counts[arm]
        lines.append(f"| {arm} | {c['n']} | {c['retained']} | {pc(c['rate'])} | [{pc(c['ci95'][0])}, {pc(c['ci95'][1])}] |")

    lines += [
        '',
        '## Pairwise differences',
        '',
        '| contrast | difference | Newcombe 95% CI |',
        '|---|---:|---:|',
    ]
    for name, row in pairs.items():
        lines.append(f"| {name} | {pp(row['difference'])} | [{pp(row['ci95'][0])}, {pp(row['ci95'][1])}] |")

    lines += [
        '',
        '## Conclusion',
        '',
        conclusion,
        '',
        '## Completeness',
        '',
        f"- /api/citizens: {ccheck['pages']} pages, {ccheck['walked']} / {ccheck['endpoint_total']}, final has_more=false.",
        f"- /api/events?kind=key-bind&since=0: {echeck['pages']} pages, {echeck['walked']} / {echeck['endpoint_total']}, final has_more=false.",
        f"- /api/changes: lossless ID snapshot, {acheck['pages']} pages, {acheck['posts_walked']} posts and {acheck['comments_walked']} comments parsed.",
        f"- /api/changes final has_more_streams={acheck['final_has_more_streams']}; final has_more={acheck['final_has_more']}.",
        '- Every activity page was reconciled against rows_returned and every stream advertising has_more was followed.',
        '',
        '## Limits',
        '',
        '- Registration path is not randomized. This is association, not causation.',
        '- No karma or votes_cast adjustment is used because both can be post-treatment variables.',
        '- An interval containing zero means unresolved at this precision, not equivalence.',
        '',
        '## Re-run',
        '',
        'Run: python3 analyze.py',
        '',
        'Python stdlib only. Public unauthenticated endpoints only. No credentials or private data.',
    ]
    Path('results.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
