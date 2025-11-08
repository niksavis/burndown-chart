"""Show RI Operational Tasks with recent deployments."""

import json
from datetime import datetime, timedelta, timezone

# Load JIRA cache
with open("jira_cache.json", "r") as f:
    cache_data = json.load(f)

# Extract issues from cache structure
issues = cache_data.get("issues", []) if isinstance(cache_data, dict) else cache_data

# Filter RI Operational Tasks
operational = [
    i
    for i in issues
    if i.get("fields", {}).get("project", {}).get("key") == "RI"
    and i.get("fields", {}).get("issuetype", {}).get("name") == "Operational Task"
]

print(f"Total RI Operational Tasks: {len(operational)}\n")

# Find deployments in last 30 days
today = datetime.now(timezone.utc)
thirty_days_ago = today - timedelta(days=30)

deployments = []

for task in operational:
    key = task.get("key")
    fixversions = task.get("fields", {}).get("fixVersions", [])

    if not fixversions:
        continue

    for fv in fixversions:
        release_date_str = fv.get("releaseDate", "")
        if not release_date_str:
            continue

        try:
            rd = datetime.fromisoformat(release_date_str)
            if rd.tzinfo is None:
                rd = rd.replace(tzinfo=timezone.utc)

            # Only past deployments in last 30 days
            if rd <= today and rd >= thirty_days_ago:
                deployments.append(
                    {
                        "key": key,
                        "fixversion": fv.get("name"),
                        "release_date": release_date_str,
                        "datetime": rd,
                    }
                )
        except Exception:
            pass

# Sort by date
deployments.sort(key=lambda x: x["datetime"])

print(f"Deployments in last 30 days (past only): {len(deployments)}\n")
print("Task ID | Fix Version | Release Date")
print("-" * 60)
for d in deployments:
    print(f"{d['key']} | {d['fixversion']} | {d['release_date']}")

# Calculate frequency
period_days = (today - thirty_days_ago).days
deployments_per_week = (len(deployments) / period_days) * 7 if period_days > 0 else 0
print(f"\nDeployment Frequency: {len(deployments)} deployments in {period_days} days")
print(f"= {deployments_per_week:.2f} deployments per week")
