
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.tools.notion import update_page_content
from rich.console import Console

console = Console()

LORE_CONTENT = """
### [EXTENDED LORE]

**Origin**
Forged in the silence of the Void before the first stars ignited, the Shadow Blade is not made of metal, but of solidified absence. It drinks the light around it, leaving a trail of dimness in its wake.

**Capabilities**
The blade phases through conventional matter, cutting directly at the spiritual essence or 'animus' of a target. It is one of the few weapons capable of harming a fully manifested Voidborn.

**Curse**
The wielder slowly loses their color vision, eventually seeing the world only in shades of grey and static, a condition known as 'Veil-Blindness'.
"""

console.print("[bold cyan]>> [DEMO] Kaedra is writing to Notion...[/]")
try:
    res = update_page_content("The Shadow Blade", LORE_CONTENT)
    console.print(res)
except Exception as e:
    console.print(f"[red]Error: {e}[/]")
