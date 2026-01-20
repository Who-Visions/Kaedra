import nbformat
import sys
from pathlib import Path

def extract_code_from_ipynb(ipynb_path: str, output_py_path: str):
    path = Path(ipynb_path)
    if not path.exists():
        print(f"Error: {path} does not exist.")
        return
    
    try:
        nb = nbformat.read(str(path), as_version=4)
        code_cells = [cell.get('source', '') for cell in nb.cells if cell.cell_type == 'code']
        
        with open(output_py_path, 'w', encoding='utf-8') as f:
            f.write(f'"""Extracted from {path.name}"""\n\n')
            f.write('\n\n# ' + ('=' * 40) + '\n# NEW CELL\n# ' + ('=' * 40) + '\n\n'.join(code_cells))
        print(f"Successfully extracted to {output_py_path}")
    except Exception as e:
        print(f"Error processing {path.name}: {e}")

if __name__ == "__main__":
    # Examples to extract
    targets = [
        ('C:/Users/super/Watchtower/gemini-cookbook/examples/Story_Writing_with_Prompt_Chaining.ipynb', 'C:/Users/super/Watchtower/gemini-cookbook/examples/story_chaining_extracted.py'),
        ('C:/Users/super/Watchtower/gemini-cookbook/quickstarts/Get_started_thinking.ipynb', 'C:/Users/super/Watchtower/gemini-cookbook/quickstarts/thinking_extracted.py'),
        ('C:/Users/super/Watchtower/gemini-cookbook/quickstarts/Caching.ipynb', 'C:/Users/super/Watchtower/gemini-cookbook/quickstarts/caching_extracted.py'),
        ('C:/Users/super/Watchtower/gemini-cookbook/quickstarts/Function_calling.ipynb', 'C:/Users/super/Watchtower/gemini-cookbook/quickstarts/function_calling_extracted.py')
    ]
    
    for ipynb, py in targets:
        extract_code_from_ipynb(ipynb, py)
