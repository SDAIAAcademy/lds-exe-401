# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""The portfolio committee's calculator, from the course root:

    uv run labs/portfolio/portfolio_calc.py labs/files/portfolio/my_decisions.csv
    uv run labs/portfolio/portfolio_calc.py labs/files/portfolio/my_decisions.csv --envelope 3782

It reads the twelve use cases in labs/files/portfolio/usecases.csv and your decisions file (the columns
of decisions_template.csv): for each case the filter it fails (data_rule, no_owner, kill_met,
no_outcome_measure, or empty), the value per successful outcome you accept as traceable to the accounts
(empty = the owner's claim), and your decision (fund, stop, return, defer, or empty).
It applies the formulas of gate_rules.md and adds up the first-year cost of the cases you fund against
the envelope. It does not decide for you: the filters and the accepted value are your judgement.
Standard library only; nothing is written to disk.
"""
import argparse
import csv
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]
PORTFOLIO = LABS / 'files' / 'portfolio'
FILTERS = {'', 'data_rule', 'no_owner', 'kill_met', 'no_outcome_measure'}
DECISIONS = {'', 'fund', 'stop', 'return', 'defer'}
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass


def read_csv(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser(description='The portfolio committee calculator.')
    ap.add_argument('decisions')
    ap.add_argument('--envelope', type=int, default=4450, help='thousand SAR (default 4450)')
    a = ap.parse_args()
    path = Path(a.decisions)
    if not path.exists():
        print(f'No file {path.name}. Copy decisions_template.csv to it first.')
        return 2
    cases = read_csv(PORTFOLIO / 'usecases.csv')
    mine = {r.get('id', '').strip(): r for r in read_csv(path)}
    problems = []
    rows = []
    for u in cases:
        d = mine.get(u['id'], {})
        filt = (d.get('filter') or '').strip()
        dec = (d.get('decision') or '').strip()
        acc = (d.get('accepted_value_per_success_sar') or '').strip()
        if filt not in FILTERS:
            problems.append(f"{u['id']}: unknown filter '{filt}' (use one of {', '.join(sorted(FILTERS - {''}))} or leave empty)")
        if dec not in DECISIONS:
            problems.append(f"{u['id']}: unknown decision '{dec}' (use fund, stop, return, defer or leave empty)")
        if filt and dec == 'fund':
            problems.append(f"{u['id']}: funded although it fails the filter {filt}")
        try:
            vps = float(acc) if acc else float(u['value_per_success_sar_claimed'])
        except ValueError:
            problems.append(f"{u['id']}: accepted value '{acc}' is not a number")
            vps = 0.0
        build, run = int(u['build_k']), int(u['run_k_per_year'])
        annual = run + build / 3
        succ = int(u['outcomes_per_year']) * float(u['success_rate'])
        value = succ * vps / 1000
        net = value - annual
        y1 = build + run
        rows.append({'id': u['id'], 'filter': filt or '-', 'cpso': annual * 1000 / succ if succ else None,
                     'value': value, 'net': net, 'y1': y1, 'ratio': net / y1 if y1 else 0, 'decision': dec or '-',
                     'claimed': not acc})

    print(f"{'case':<6}{'filter':<20}{'cost/success':>13}{'value k':>9}{'net k':>8}{'year-1 k':>9}{'net/yr1':>8}  decision")
    for r in rows:
        cp = f"{r['cpso']:.2f}" if r['cpso'] is not None else 'n/a'
        mark = '' if not r['claimed'] else ' (claimed)'
        print(f"{r['id']:<6}{r['filter']:<20}{cp:>13}{r['value']:>9.0f}{r['net']:>8.0f}{r['y1']:>9}{r['ratio']:>8.2f}  {r['decision']}{mark}")
    funded = [r for r in rows if r['decision'] == 'fund']
    spent = sum(r['y1'] for r in funded)
    print()
    print(f"funded: {', '.join(r['id'] for r in funded) or 'none'} ({len(funded)} cases); year-1 cost {spent:,} of {a.envelope:,}")
    if len(funded) > 5:
        problems.append('more than five cases funded')
    if spent > a.envelope:
        problems.append(f'over the envelope by {spent - a.envelope:,}')
    for p in problems:
        print('problem: ' + p)
    if not problems:
        print('No rule broken. The committee paper still has to say why.')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
