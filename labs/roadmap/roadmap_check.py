# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Checks a roadmap (and, with --budget, prices it against the group's yearly caps), from the course root:

    uv run labs/roadmap/roadmap_check.py labs/files/roadmap/my_roadmap.csv
    uv run labs/roadmap/roadmap_check.py labs/files/roadmap/my_roadmap.csv --budget labs/files/roadmap/my_budget.csv

The roadmap file has the columns of labs/files/roadmap/roadmap_template.csv: id, horizon_1_2_3 (1, 2, 3,
or a dash for an initiative you drop), go_live_month (1 to 36), milestone, depends_on, reason.
The budget file is optional and has build_y1_k, build_y2_k, build_y3_k per initiative: leave a row empty
to keep the build costs of initiatives.csv, or write all three numbers to move build money between years.
Run costs, retirement costs and the old chatbot's licence are computed from the go-live months, by the
rules of budget_envelope.md. Standard library only; nothing is written to disk.
"""
import argparse
import csv
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]
ROADMAP = LABS / 'files' / 'roadmap'
CAPS = [6200, 7800, 5600]
LEGACY_PER_YEAR = 180
RETIRES_LEGACY = 'I08'
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass


def read_csv(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def months_in_year(go_live, year):
    start, end = (year - 1) * 12, year * 12
    return min(12, max(0, end - max(start, go_live)))


def as_int(text):
    try:
        return int(str(text).strip())
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description='Checks a roadmap and prices it against the yearly caps.')
    ap.add_argument('roadmap')
    ap.add_argument('--budget')
    a = ap.parse_args()
    init = {r['id']: r for r in read_csv(ROADMAP / 'initiatives.csv')}
    path = Path(a.roadmap)
    if not path.exists():
        print(f'No file {path.name}. Copy roadmap_template.csv to it first.')
        return 2
    rows = {r['id']: r for r in read_csv(path)}
    problems, notes = [], []

    plan = {}
    for iid in init:
        r = rows.get(iid)
        if r is None:
            problems.append(f'{iid}: missing from the roadmap')
            continue
        h = (r.get('horizon_1_2_3') or '').strip()
        if h in ('-', '—'):
            plan[iid] = None
            continue
        m = as_int(r.get('go_live_month', ''))
        if h not in ('1', '2', '3') or m is None:
            problems.append(f'{iid}: write a horizon (1, 2, 3 or -) and a go-live month')
            continue
        if not 1 <= m <= 36:
            problems.append(f'{iid}: go-live month {m} is outside 1 to 36')
            continue
        if (m - 1) // 12 + 1 != int(h):
            problems.append(f'{iid}: go-live month {m} is not in horizon {h} (horizon 1 = months 1-12, 2 = 13-24, 3 = 25-36)')
        plan[iid] = m
    if problems:
        print('The roadmap is not complete yet:')
        for p in problems:
            print('  ' + p)
        return 1

    for iid, m in plan.items():
        for dep in init[iid]['depends_on'].split():
            if m is None:
                continue
            if plan.get(dep) is None:
                problems.append(f'{iid} depends on {dep}, which you dropped')
            elif plan[dep] > m:
                problems.append(f'{iid} goes live in month {m}, before {dep} (month {plan[dep]}) on which it depends')
    dropped = [k for k, v in plan.items() if v is None]
    if dropped:
        notes.append('dropped: ' + ', '.join(dropped))
    print(f'Roadmap: {len(plan)} initiatives, {len(dropped)} dropped; dependencies ' + ('respected.' if not problems else 'NOT respected:'))
    for p in problems:
        print('  ' + p)

    if not a.budget:
        return 1 if problems else 0

    bpath = Path(a.budget)
    build_over = {}
    if bpath.exists():
        for r in read_csv(bpath):
            vals = [as_int(r.get(f'build_y{y}_k', '')) for y in (1, 2, 3)]
            if all(v is not None for v in vals):
                build_over[r['id']] = vals
                default = sum(int(init[r['id']][f'build_y{y}_k']) for y in (1, 2, 3))
                if sum(vals) != default:
                    notes.append(f"{r['id']}: build total {sum(vals)} differs from initiatives.csv ({default})")
            elif any(v is not None for v in vals):
                print(f"{r['id']}: write all three build numbers or none")
                return 1
    else:
        print(f'No file {bpath.name}: using the build costs of initiatives.csv.')

    lines = {'build': [0, 0, 0], 'run': [0, 0, 0], 'retire': [0, 0, 0], 'legacy': [0, 0, 0]}
    for iid, m in plan.items():
        if m is None:
            continue
        r = init[iid]
        build = build_over.get(iid, [int(r[f'build_y{y}_k']) for y in (1, 2, 3)])
        for k, y in enumerate((1, 2, 3)):
            lines['build'][k] += build[k]
            lines['run'][k] += round(int(r['run_per_year_k']) * months_in_year(m, y) / 12)
            if (m - 1) // 12 + 1 == y:
                lines['retire'][k] += int(r['retire_cost_k'])
    end = plan.get(RETIRES_LEGACY) or 36  # the licence is paid up to and including the retirement month
    for k, y in enumerate((1, 2, 3)):
        lines['legacy'][k] = round(LEGACY_PER_YEAR * min(12, max(0, min(end, y * 12) - (y - 1) * 12)) / 12)
    totals = [sum(lines[n][k] for n in lines) for k in range(3)]

    print()
    print(f"{'thousand SAR':<14}{'year 1':>9}{'year 2':>9}{'year 3':>9}")
    for n in ('build', 'run', 'retire', 'legacy'):
        print(f'{n:<14}' + ''.join(f'{v:>9,}' for v in lines[n]))
    print(f"{'total':<14}" + ''.join(f'{v:>9,}' for v in totals))
    print(f"{'cap':<14}" + ''.join(f'{v:>9,}' for v in CAPS))
    print(f"{'headroom':<14}" + ''.join(f'{c - t:>9,}' for c, t in zip(CAPS, totals)))
    share = lines['run'][2] / totals[2] if totals[2] else 0
    print(f'run share of year 3: {share:.0%}')
    for n in notes:
        print('note: ' + n)
    over = [k + 1 for k in range(3) if totals[k] > CAPS[k]]
    if over:
        print('Over the cap in year ' + ', '.join(map(str, over)) + '.')
    else:
        print('Within the cap in all three years.')
    return 1 if (problems or over) else 0


if __name__ == '__main__':
    sys.exit(main())
