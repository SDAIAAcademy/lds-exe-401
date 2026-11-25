# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Recounts the overtime flags from the shift log, from the course root:

    uv run labs/incident/recount.py              # hours split at midnight, as the rule means
    uv run labs/incident/recount.py --as-tool    # the way overtime_tool.md says the tool counts

A flag is a driver with more than 12 hours of work in one calendar day; a written warning follows
two flags or more in the month (overtime_tool.md). The script reads labs/files/incident/shifts.csv and
compares its flags with the tool's own list in tool_flags.csv. Standard library only; nothing is written.
"""
import argparse
import csv
import sys
from pathlib import Path

INCIDENT = Path(__file__).resolve().parents[1] / 'files' / 'incident'
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass


def read_csv(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def flags(rows, as_tool):
    per = {}
    for r in rows:
        d, day, start, hours = r['driver'], int(r['day_of_month']), int(r['start_hour']), int(r['hours'])
        per.setdefault(d, {}).setdefault(day, 0)
        per[d][day] += min(hours, 24 - start)
        if start + hours > 24:
            per[d].setdefault(day + 1, 0)
            # the tool "also counts the shift on the next day so no hour is lost": the whole shift again
            per[d][day + 1] += hours if as_tool else start + hours - 24
    return {d: sorted(day for day, h in days.items() if h > 12) for d, days in per.items() if any(h > 12 for h in days.values())}


def main():
    ap = argparse.ArgumentParser(description='Recounts the overtime flags from the shift log.')
    ap.add_argument('--as-tool', action='store_true', help='count the way the tool does')
    a = ap.parse_args()
    rows = read_csv(INCIDENT / 'shifts.csv')
    tool_list = {r['driver']: [int(x) for x in r['flagged_days'].split()] for r in read_csv(INCIDENT / 'tool_flags.csv')}
    mine = flags(rows, a.as_tool)
    crossing = sum(1 for r in rows if int(r['start_hour']) + int(r['hours']) > 24)
    mode = 'as the tool counts' if a.as_tool else 'split at midnight'
    print(f'{len(rows)} shifts, {len({r["driver"] for r in rows})} drivers, {crossing} shifts cross midnight')
    print(f'{mode}: {sum(len(v) for v in mine.values())} flag-days for {len(mine)} drivers')
    warned = sorted(d for d, v in mine.items() if len(v) >= 2)
    print(f'drivers with two flags or more (a written warning): {", ".join(warned) or "none"}')
    tool_warned = sorted(d for d, v in tool_list.items() if len(v) >= 2)
    only_tool = sorted(d for d in tool_list if d not in mine)
    print(f'the tool list: {sum(len(v) for v in tool_list.values())} flag-days for {len(tool_list)} drivers; warnings: {", ".join(tool_warned) or "none"}')
    print(f'drivers flagged by the tool and not here: {", ".join(only_tool) or "none"}')
    same = {d: v for d, v in tool_list.items()} == mine
    print('this count reproduces the tool list exactly.' if same else 'this count differs from the tool list.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
