# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Checks the reference solutions of LDS-EXE-401 against the answer key, from the course root:

    uv run labs/solutions/check.py all          # or: agent, roadmap, portfolio, policy, incident

agent: runs the two reference workflows with the scripted stand-in and checks the numbers the
debrief slides quote. roadmap, portfolio, incident: recompute the reference numbers from the case
files in labs/files/ (not from the generator) and compare them with labs/solutions/reference.json.
policy: checks that the reference resolution of the eight scenarios is consistent with the
reference permission matrix. Prints PASS or the first difference; exits 1 on a difference.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]
FILES = LABS / 'files'
SOL = LABS / 'solutions'
REF = json.loads((SOL / 'reference.json').read_text(encoding='utf-8'))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass


def read_csv(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def expect(name, got, want):
    if got != want:
        print(f'FAIL {name}: got {got!r}, expected {want!r}')
        sys.exit(1)


def check_agent():
    expected = {'run1': (11, 48, 5071.45, {'policy_not_applied': 3, 'wrong_amount': 3, 'steps_exhausted': 2, 'followed_customer_instruction': 1}),
                'run2': (17, 60, 329.0, {'steps_exhausted': 2, 'followed_customer_instruction': 1})}
    for label, (succ, calls, over, fails) in expected.items():
        tag = f'ref-{label}'
        subprocess.run([sys.executable, str(LABS / 'agent' / 'run_agent.py'), str(SOL / 'agent' / f'workflow_{label}.json'),
                        '--label', tag, '--stand-in'], check=True, capture_output=True)
        s = json.loads((LABS / 'agent' / 'runs' / tag / 'summary.json').read_text(encoding='utf-8'))
        expect(f'{label} successes', s['successes'], succ)
        expect(f'{label} calls', s['calls_used'], calls)
        expect(f'{label} overpaid', s['overpaid_sar'], over)
        expect(f'{label} failures', s['failures'], fails)
        print(f'agent {label}: {succ}/20, {calls} calls, cost per success {s["cost_per_success_sar"]} SAR, overpaid {over} SAR')
    print('PASS agent')


def months_in_year(go_live, year):
    start, end = (year - 1) * 12, year * 12
    return min(12, max(0, end - max(start, go_live)))


def check_roadmap():
    rows = read_csv(FILES / 'roadmap' / 'initiatives.csv')
    build = [sum(int(r[f'build_y{y}_k']) for r in rows) for y in (1, 2, 3)]
    run = [sum(round(int(r['run_per_year_k']) * months_in_year(int(r['go_live_month']), y) / 12) for r in rows) for y in (1, 2, 3)]
    retire = [sum(int(r['retire_cost_k']) for r in rows if (int(r['go_live_month']) - 1) // 12 + 1 == y) for y in (1, 2, 3)]
    legacy = [180, 45, 0]
    totals = [build[k] + run[k] + retire[k] + legacy[k] for k in range(3)]
    r = REF['roadmap']
    expect('build', build, r['build'])
    expect('run', run, r['run'])
    expect('totals', totals, r['totals'])
    profile = read_csv(FILES / 'roadmap' / 'maturity_profile.csv')
    expect('components', len(profile), 7)
    ref_profile = read_csv(SOL / 'roadmap' / 'maturity_reference.csv')
    expect('evidence scores', [int(p['evidence_score_0_4']) for p in ref_profile], [2, 1, 1, 2, 1, 2, 0])
    tool = LABS / 'roadmap' / 'roadmap_check.py'
    for road, budget, want_code, want_total in (('roadmap_after_lab_3_1.csv', None, 1, '6,628    7,720    5,255'),
                                                ('roadmap_after_lab_4_1.csv', 'budget_after_lab_4_1.csv', 0, '6,200    7,780    5,255')):
        cmd = [sys.executable, str(tool), str(SOL / 'roadmap' / road)] + (['--budget', str(SOL / 'roadmap' / budget)] if budget else ['--budget', str(FILES / 'roadmap' / 'budget_template.csv')])
        p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        expect(f'{road} exit code', p.returncode, want_code)
        expect(f'{road} totals', want_total in p.stdout, True)
        expect(f'{road} dependencies', 'dependencies respected' in p.stdout, True)
    print('roadmap: lab 3.1 reference respects dependencies and is 428 over in year 1; lab 4.1 reference fits the caps')
    print(f'roadmap: totals {totals} against caps {r["caps"]}; year 1 over by {r["over_cap"][0]}; run share in year 3 {r["run_share_y3"]}')
    print('PASS roadmap')


def check_portfolio():
    rows = read_csv(FILES / 'portfolio' / 'usecases.csv')
    accounts = {(a['company'], a['account_line']) for a in read_csv(FILES / 'portfolio' / 'accounts.csv')}
    traceable_vps = {'UC03': 9}  # the fuel part only: the hiring line is not in the accounts (value_notes.md)
    out = {}
    for u in rows:
        uid = u['id']
        filt = None
        if u['method'] == 'توليدي' and u['data_class'] != 'عام':
            filt = 'data_rule'
        elif not u['owner_role']:
            filt = 'no_owner'
        elif u['kill_criterion_met'] == 'نعم':
            filt = 'kill_met'
        elif int(u['outcomes_per_year']) == 0:
            filt = 'no_outcome_measure'
        annual = int(u['run_k_per_year']) + int(u['build_k']) / 3
        succ = int(u['outcomes_per_year']) * float(u['success_rate'])
        vps = traceable_vps.get(uid, int(u['value_per_success_sar_claimed']))
        line = u['account_line'].split(': ', 1)[-1]
        in_accounts = (u['company'], line) in accounts
        trace = round(succ * vps / 1000) if in_accounts else 0
        out[uid] = dict(filter=filt, net=round(trace - annual), y1=int(u['build_k']) + int(u['run_k_per_year']), cpso=round(annual * 1000 / succ, 2) if succ else None)
    for k, v in out.items():
        expect(f'{k} filter', v['filter'], REF['portfolio']['cases'][k]['filter'])
        expect(f'{k} net', v['net'], REF['portfolio']['cases'][k]['net_k'])
        expect(f'{k} cost per success', v['cpso'], REF['portfolio']['cases'][k]['cpso_sar'])
    p = REF['portfolio']
    tool = LABS / 'portfolio' / 'portfolio_calc.py'
    for name, env, funded, spent in (('decisions_reference.csv', p['envelope_k'], p['funded'], p['spent_k']),
                                     ('decisions_after_cut.csv', p['envelope_after_cut_k'], p['funded_after_cut'], p['spent_after_cut_k'])):
        r = subprocess.run([sys.executable, str(tool), str(SOL / 'portfolio' / name), '--envelope', str(env)], capture_output=True, text=True, encoding='utf-8')
        expect(f'{name} exit code', r.returncode, 0)
        line = f"funded: {', '.join(sorted(funded))} ({len(funded)} cases); year-1 cost {spent:,} of {env:,}"
        expect(f'{name} funded line', line in r.stdout, True)
    print(f'portfolio: fund {p["funded"]} ({p["spent_k"]} of {p["envelope_k"]}), stop {p["stop"]}; after the 15% cut: {p["funded_after_cut"]}')
    print('PASS portfolio')


def check_policy():
    key = json.loads((SOL / 'policy' / 'policy_key.json').read_text(encoding='utf-8'))
    matrix = {(r['agent'], r['action']): r for r in read_csv(SOL / 'policy' / 'permission_matrix_reference.csv')}
    for s in key['scenarios']:
        if 'matrix' in s:
            agent, action, level = s['matrix']
            got = matrix[(agent, action)]['level_p0_p4']
            expect(f"{s['id']} level", got, level)
    for (agent, action), r in matrix.items():
        if r['level_p0_p4'] in ('ص2', 'ص3') and not r['approver_role']:
            print(f'FAIL {agent} {action}: an acting level without an approver')
            sys.exit(1)
        if r['approver_role'] and r['approver_role'] == key['owners'].get(agent):
            print(f'FAIL {agent} {action}: the owner approves its own agent')
            sys.exit(1)
    r = subprocess.run([sys.executable, str(LABS / 'policy' / 'matrix_check.py'), str(SOL / 'policy' / 'permission_matrix_reference.csv')],
                       capture_output=True, text=True, encoding='utf-8')
    expect('matrix_check on the reference', (r.returncode, 'no fixed rule broken' in r.stdout), (0, True))
    for fb, ref in (('policy_after_lab_6_1.md', 'policy_after_lab_6_1.md'), ('policy_after_lab_7_1.md', 'policy_after_lab_7_1.md'),
                    ('permission_matrix_after_lab_7_1.csv', 'permission_matrix_reference.csv')):
        expect(f'fallback {fb} matches the reference', (FILES / 'policy' / 'fallback' / fb).read_bytes(), (SOL / 'policy' / ref).read_bytes())
    expect('tool requests resolved', sorted(key['tool_requests']), [f'TR{i:02d}' for i in range(1, 11)])
    print(f"policy: {len(key['scenarios'])} scenarios consistent with {len(matrix)} matrix rows; fallbacks match")
    print('PASS policy')


def check_incident():
    rows = read_csv(FILES / 'incident' / 'shifts.csv')
    flags = {r['driver']: r['flagged_days'].split() for r in read_csv(FILES / 'incident' / 'tool_flags.csv')}

    def per_day(buggy):
        per = {}
        for r in rows:
            d, day, start, hours = r['driver'], int(r['day_of_month']), int(r['start_hour']), int(r['hours'])
            per.setdefault(d, {}).setdefault(day, 0)
            per[d][day] += min(hours, 24 - start)
            if start + hours > 24:
                per[d].setdefault(day + 1, 0)
                per[d][day + 1] += hours if buggy else start + hours - 24
        return {d: sorted(day for day, h in days.items() if h > 12) for d, days in per.items() if any(h > 12 for h in days.values())}

    tool, true = per_day(True), per_day(False)
    expect('tool reproduces its flags', {d: [str(x) for x in v] for d, v in tool.items()}, flags)
    i = REF['incident']
    expect('true flag days', sum(len(v) for v in true.values()), i['true_flag_days'])
    expect('false flag drivers', sorted(d for d in tool if d not in true), i['false_flag_drivers'])
    print(f"incident: {i['tool_flag_days']} flag-days from the tool, {i['true_flag_days']} real; {len(i['false_flag_drivers'])} drivers flagged only by the bug; wrong warnings {i['wrong_warnings']}")
    print('PASS incident')


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    checks = {'agent': check_agent, 'roadmap': check_roadmap, 'portfolio': check_portfolio, 'policy': check_policy, 'incident': check_incident}
    for name, fn in checks.items():
        if what in ('all', name):
            fn()
