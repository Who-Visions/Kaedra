"""
Harvest Fleet script.
Fetches git logs from multiple repositories and aggregates them into a timeline.
"""
import subprocess
import datetime
from typing import List, Dict

# Constants
WORKSPACE = "c:/Users/super/Watchtower/Kaedra_Local"
REPOS = {
    "unk": "https://github.com/Who-Visions/unk-app-ai.git",
    "kam": "https://github.com/Who-Visions/Kam-ai.git",
    "visions": "https://github.com/Who-Visions/Visions-ai.git",
    "iris": "https://github.com/Who-Visions/Iris-Ai.git",
    "yuki": "https://github.com/Who-Visions/Yuki-Ai.git",
    "tester": "https://github.com/Who-Visions/who-visions-tester.git",
    "rhea": "https://github.com/Who-Visions/Rhea-Noir.git",
    "dav1d": "https://github.com/Who-Visions/Dav1d.git",
    "kaedra_remote": "https://github.com/Who-Visions/Kaedra.git"
}


def run_git(args: List[str], cwd: str = WORKSPACE) -> str:
    """Run a git command and return the output."""
    try:
        # pylint: disable=subprocess-run-check
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout.strip()
    except OSError as err:
        return str(err)
    except Exception as err: # pylint: disable=broad-exception-caught
        return str(err)


def main():
    """Main execution function."""
    timeline: List[Dict[str, str]] = []
    print("Starting Fleet Harvest for 2026 (Jan 1 - Present)...")

    for name, url in REPOS.items():
        print(f"Processing {name}...")
        remote_name = f"fleet_{name}"

        # 1. Add Remote (ignore error if exists)
        run_git(["remote", "add", remote_name, url])

        # 2. Fetch
        print(f"  Fetching {url}...")
        run_git(["fetch", remote_name])

        # 3. Log
        log_cmd = [
            "log",
            f"{remote_name}/main",
            "--since=2026-01-01",
            "--format=%ad__%s__%h",
            "--date=iso"
        ]
        # Try main first, fallback to master if empty
        logs = run_git(log_cmd)
        if not logs:
            log_cmd[1] = f"{remote_name}/master"
            logs = run_git(log_cmd)

        if logs:
            for line in logs.split('\n'):
                if "__" in line:
                    parts = line.split("__", 2)
                    if len(parts) == 3:
                        date_str, msg, commit_hash = parts
                        timeline.append({
                            "date": date_str,
                            "repo": name.upper(),
                            "msg": msg,
                            "hash": commit_hash
                        })
            print(f"  Found {len(logs.splitlines())} commits.")
        else:
            print("  No commits in range.")

    # Sort chronologically (reverse for latest first)
    timeline.sort(key=lambda x: x['date'], reverse=True)

    with open("fleet_timeline_2026.md", "w", encoding="utf-8") as f:
        f.write("### 2026 - The Year of Agency\n\n")
        for event in timeline:
            dt = datetime.datetime.fromisoformat(event['date']).strftime('%Y-%m-%d')
            f.write(f"- **{dt}**: [{event['repo']}] {event['msg']} ({event['hash']})\n")

    print("Timeline written to fleet_timeline_2026.md")


if __name__ == "__main__":
    main()
