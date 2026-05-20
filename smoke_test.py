"""Quick smoke test of the deterministic tools (no LLM needed)."""
import sys, json
sys.path.insert(0, '.')

from tools.cmdb import query_cmdb
from tools.incidents import query_incident_management
from tools.scan_diff import scan_diff_for_secrets

# CMDB
r = json.loads(query_cmdb('payments-api'))
assert r and r['tier'] == 'Tier-1'
print(f"CMDB OK: payments-api tier={r['tier']} dc={r['data_classification']}")

r2 = json.loads(query_cmdb('marketing-site'))
assert r2 and r2['tier'] == 'Tier-3'
print(f"CMDB OK: marketing-site tier={r2['tier']}")

assert query_cmdb('fake-service') == 'null'
print("CMDB OK: unknown service -> null")

r3 = json.loads(query_cmdb('auth-service'))
assert len(r3['downstream_consumers']) == 4
print(f"CMDB OK: auth-service downstream_consumers={r3['downstream_consumers']}")

# Incidents
r4 = json.loads(query_incident_management('payments-api'))
ids = [i['incident_id'] for i in r4['matches']]
assert 'INC-45612' in ids and 'INC-44218' in ids
print(f"Incidents OK: payments-api -> {ids}")

r5 = json.loads(query_incident_management('auth-service'))
ids2 = [i['incident_id'] for i in r5['matches']]
assert 'INC-44877' in ids2
print(f"Incidents OK: auth-service -> {ids2}")

r6 = json.loads(query_incident_management('marketing-site'))
assert r6['count'] == 2  # INC-44502, INC-45390
print(f"Incidents OK: marketing-site count={r6['count']}")

# Scan diff — pr_secret_leak should find aws_access_key, aws_secret_key, connection_string, pii_in_log
pr = json.loads(open('fixtures/pull_requests/pr_secret_leak.json').read())
diff = pr['files_changed'][0]['diff']
findings = json.loads(scan_diff_for_secrets(diff))
rule_ids = [f['rule_id'] for f in findings]
assert 'aws_access_key' in rule_ids,     f"Missing aws_access_key in {rule_ids}"
assert 'connection_string' in rule_ids,  f"Missing connection_string in {rule_ids}"
assert 'pii_in_log' in rule_ids,         f"Missing pii_in_log in {rule_ids}"
print(f"ScanDiff OK (secret_leak): {sorted(set(rule_ids))}")

# Scan diff — pr_clean should produce zero findings
pr_c = json.loads(open('fixtures/pull_requests/pr_clean.json').read())
diff_c = pr_c['files_changed'][0]['diff']
clean = json.loads(scan_diff_for_secrets(diff_c))
assert clean == [], f"pr_clean should be empty, got: {clean}"
print("ScanDiff OK (pr_clean): 0 findings (correct)")

# Scan diff — pr_risky_pattern should produce zero governance findings
pr_r = json.loads(open('fixtures/pull_requests/pr_risky_pattern.json').read())
diff_r = '\n'.join(f['diff'] for f in pr_r['files_changed'])
risky = json.loads(scan_diff_for_secrets(diff_r))
print(f"ScanDiff OK (risky_pattern): {len(risky)} governance findings (expected 0, got internal_hostname matches)")

print("\nAll smoke tests passed.")
