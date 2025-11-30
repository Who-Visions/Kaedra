
import os

def summarize_file(filepath):
    """
    Summarizes the content of a file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Placeholder for summarization logic
        summary = content[:400]
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        result = summarize_file(filepath)
        print(result)
    else:
        print({"success": False, "error": "No filepath provided."})
