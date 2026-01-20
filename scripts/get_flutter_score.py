import os
import subprocess
import re

def get_dart_pylint_standard_score():
    """
    Standardizes flutter analyze output to a 0-10 score.
    Score = 10.0 - (Issues / (Lines of Code / 100))
    """
    try:
        # 1. Run flutter analyze
        print("Running flutter analyze...")
        # Use full path for reliability on this system
        flutter_path = r'C:\Users\super\Downloads\flutter_windows_3.38.6-stable\flutter\bin\flutter.bat'
        result = subprocess.run(
            [flutter_path, 'analyze'],
            capture_output=True,
            text=True,
            check=False,
            cwd='kaedra_mobile'
        )
        output = result.stdout + result.stderr
        
        # 2. Extract issue count
        match = re.search(r'(\d+) issues? found', output)
        issue_count = int(match.group(1)) if match else 0
        
        # 3. Estimate Lines of Code (Dart files in lib/)
        loc = 0
        for root, dirs, files in os.walk('kaedra_mobile/lib'):
            for file in files:
                if file.endswith('.dart'):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                            loc += len(f.readlines())
                    except:
                        pass
        
        # 4. Calculate Score
        if loc == 0: return 10.0, 0, 0
        
        # 1 issue per 100 LOC = -1.0 penalty.
        penalty_factor = (issue_count / (loc / 100))
        score = max(0.0, 10.0 - penalty_factor)
        
        print(f"Total Lines of Code: {loc}")
        print(f"Total Issues: {issue_count}")
        print(f"Standardized Score: {score:.2f}/10")
        
        return score, issue_count, loc
    except Exception as e:
        print(f"Error calculating score: {e}")
        return 0.0, 0, 0

if __name__ == "__main__":
    get_dart_pylint_standard_score()
