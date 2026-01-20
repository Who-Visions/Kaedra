import os
import subprocess
import re

def get_pylint_score(filepath):
    try:
        result = subprocess.run(
            ['pylint', filepath],
            capture_output=True,
            text=True,
            check=False
        )
        output = result.stdout
        # Search for "Your code has been rated at 9.75/10"
        match = re.search(r'Your code has been rated at ([-?\d.]+)/10', output)
        if match:
            return float(match.group(1))
        return 0.0
    except Exception as e:
        print(f"Error linting {filepath}: {e}")
        return 0.0

def main():
    root_dir = os.getcwd()
    python_files = []
    
    exclude_dirs = {'.git', '.agent', '.claude', 'venv', '__pycache__', 'cache', 'sessions', 'temp_hacker_movies', 'memory', 'data'}
    
    for root, dirs, files in os.walk(root_dir):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files.")
    
    scores = []
    for filepath in python_files:
        rel_path = os.path.relpath(filepath, root_dir)
        score = get_pylint_score(filepath)
        scores.append((rel_path, score))
        print(f"{rel_path}: {score}")
    
    # Sort by score ascending
    scores.sort(key=lambda x: x[1])
    
    with open('pylint_scores_summary.txt', 'w') as f:
        for path, score in scores:
            f.write(f"{score:>6.2f} | {path}\n")

if __name__ == "__main__":
    main()
