import subprocess
import time
import os

def run_test(i):
    print(f"\n--- Run {i+1}/30 ---")
    start = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        ["python", "tests/test_notion_search_quality.py"],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    end = time.time()
    duration = end - start
    out = result.stdout or ""
    err = result.stderr or ""
    print(out)
    if err:
        print("STDERR:", err)
    print(f"Duration: {duration:.2f}s")
    return "✅ Match!" in out

if __name__ == "__main__":
    successes = 0
    total = 30
    for i in range(total):
        if run_test(i):
            successes += 1
    print(f"\nFinal Result: {successes}/{total} successes")
