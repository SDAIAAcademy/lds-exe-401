# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Checks an agent permission matrix against the two fixed rules of permission_levels.md, from the course root:

    uv run labs/policy/matrix_check.py labs/files/policy/my_matrix.csv

The matrix has the columns of labs/files/policy/permission_matrix_template.csv. Levels are written
ص0 to ص4 (P0 to P4 is accepted too). The checker does not judge whether a level is right for an action:
that is the policy's work. It checks what the policy says can never happen:
  - ص4 is not granted under this policy;
  - an acting level (ص2, ص3) has an approver, and ص3 has a written limit;
  - nobody approves the actions of an agent they own (segregation of duties);
  - an acting level has an evaluation owner and a written evaluation minimum.
Standard library only; nothing is written to disk.
"""
import csv
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]
POLICY = LABS / 'files' / 'policy'
LEVELS = {'ص0', 'ص1', 'ص2', 'ص3', 'ص4'}
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass


def read_csv(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def level_of(text):
    t = (text or '').strip().upper().replace('P', 'ص')
    return t


def main():
    if len(sys.argv) != 2:
        print('usage: uv run labs/policy/matrix_check.py <matrix.csv>')
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f'No file {path.name}. Copy permission_matrix_template.csv to it first.')
        return 2
    owners = {a['agent']: a['owner_role'] for a in read_csv(POLICY / 'agents.csv')}
    template = [(r['agent'], r['action']) for r in read_csv(POLICY / 'permission_matrix_template.csv')]
    rows = read_csv(path)
    have = {(r.get('agent', '').strip(), r.get('action', '').strip()): r for r in rows}
    problems, empty = [], []
    for key in template:
        if key not in have:
            problems.append(f'{key[0]} {key[1]}: row missing')
    for (agent, action), r in have.items():
        lv = level_of(r.get('level_p0_p4'))
        name = f'{agent} {action}'
        if not lv:
            empty.append(name)
            continue
        if lv not in LEVELS:
            problems.append(f'{name}: unknown level {lv}')
            continue
        approver = (r.get('approver_role') or '').strip()
        if lv == 'ص4':
            problems.append(f'{name}: ص4 is not granted under this policy')
        if lv in ('ص2', 'ص3') and not approver:
            problems.append(f'{name}: {lv} acts on the world but has no approver')
        if lv == 'ص3' and not (r.get('limit') or '').strip():
            problems.append(f'{name}: ص3 needs a written limit')
        if approver and owners.get(agent) and approver == owners[agent]:
            problems.append(f'{name}: the approver is the agent\'s owner ({approver}); segregation of duties')
        if lv in ('ص2', 'ص3') and not ((r.get('evaluation_owner_role') or '').strip() and (r.get('evaluation_minimum') or '').strip()):
            problems.append(f'{name}: an acting level needs an evaluation owner and a written minimum')
    if empty:
        print(f'{len(empty)} rows have no level yet: ' + '; '.join(empty))
    for p in problems:
        print('problem: ' + p)
    filled = len(have) - len(empty)
    print(f'{filled} of {len(template)} rows filled; ' + ('no fixed rule broken.' if not problems else f'{len(problems)} problems.'))
    return 1 if problems or empty else 0


if __name__ == '__main__':
    sys.exit(main())
