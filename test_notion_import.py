import sys
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from kaedra.services.notion import NotionService
print("Import success")
notion = NotionService()
print("Init success")
