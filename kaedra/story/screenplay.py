"""
Screenplay Formatter - SJSU Format Compliant
Converts AI narrative responses to proper scriptwriting notation.
"""
import re
from typing import List, Optional
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.console import Group


class ScreenplayFormatter:
    """Converts narrative text to proper screenplay format (SJSU standard)."""
    
    def __init__(self, console=None):
        self.console = console
        self.current_scene = 1
        self.current_act = 1
    
    def format_scene_header(self, int_ext: str = "INT", location: str = "UNKNOWN", 
                           time: str = "DAY") -> Text:
        """Format scene header: INT./EXT. LOCATION - TIME"""
        header = f"{int_ext.upper()}. {location.upper()} - {time.upper()}"
        return Text(header, style="bold underline")
    
    def format_character_name(self, name: str) -> Text:
        """Format character name: ALL CAPS, centered."""
        return Text(name.upper(), style="bold", justify="center")
    
    def format_stage_direction(self, direction: str) -> Text:
        """Format stage direction: (parenthetical, dim italic, indented)"""
        # Indent 2.5 inches equivalent (~25 chars)
        indented = "                         " + f"({direction})"
        return Text(indented, style="dim italic")
    
    def format_dialogue(self, text: str) -> Text:
        """Format dialogue: runs full width."""
        return Text(text, style="none")
    
    def format_act_scene(self) -> Text:
        """Format act/scene designation."""
        designation = f"ACT {self._roman(self.current_act)}\nScene {self.current_scene}"
        return Text(designation, style="bold underline", justify="center")
    
    def _roman(self, num: int) -> str:
        """Convert integer to Roman numeral."""
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        roman_num = ''
        for i, v in enumerate(val):
            while num >= v:
                roman_num += syms[i]
                num -= v
        return roman_num
    
    def parse_and_format(self, text: str, characters: Optional[List[str]] = None) -> str:
        """
        Parse narrative text and convert to screenplay format.
        
        Detects:
        - Character names (CAPS followed by colon or dialogue)
        - Stage directions (text in parentheses)
        - Scene transitions (FADE IN, CUT TO, etc.)
        - Dialogue blocks
        """
        if characters is None:
            characters = []
        
        lines = text.split('\n')
        formatted_lines = []
        
        # Common screenplay transitions
        transitions = ['FADE IN', 'FADE OUT', 'CUT TO', 'DISSOLVE TO', 'SMASH CUT', 'MATCH CUT']
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                formatted_lines.append("")
                continue
            
            # Scene headers (INT./EXT.)
            if stripped.startswith(('INT.', 'EXT.', 'INT/EXT.')):
                formatted_lines.append(f"[bold underline]{stripped}[/]")
                continue
            
            # Transitions
            if any(stripped.upper().startswith(t) for t in transitions):
                formatted_lines.append(f"[dim]{stripped.upper()}[/]")
                continue
            
            # Stage directions (full line in parentheses)
            if stripped.startswith('(') and stripped.endswith(')'):
                formatted_lines.append(f"[dim italic]                         {stripped}[/]")
                continue
            
            # Character name detection (ALL CAPS at start, possibly with (V.O.) or (O.S.))
            char_match = re.match(r'^([A-Z][A-Z\s]+)(?:\s*\([^)]+\))?$', stripped)
            if char_match and len(stripped) < 40:
                # This looks like a character name
                formatted_lines.append(f"[bold]                    {stripped}[/]")
                continue
            
            # Check if line starts with known character name followed by colon
            char_dialogue = re.match(r'^([A-Z][A-Z\s]+):\s*(.+)$', stripped)
            if char_dialogue:
                char_name = char_dialogue.group(1)
                dialogue = char_dialogue.group(2)
                formatted_lines.append(f"[bold]                    {char_name}[/]")
                formatted_lines.append(dialogue)
                continue
            
            # Inline stage directions within dialogue
            if '(' in stripped and ')' in stripped:
                # Replace inline directions with italics
                processed = re.sub(r'\(([^)]+)\)', r'[dim italic](\1)[/]', stripped)
                formatted_lines.append(processed)
                continue
            
            # Default: treat as dialogue or action
            formatted_lines.append(stripped)
        
        return '\n'.join(formatted_lines)
    
    def render_panel(self, formatted_text: str, scene_info: str = "") -> Panel:
        """Wrap formatted screenplay in a Rich Panel."""
        return Panel(
            formatted_text,
            title=f"[bold yellow]📜 SCREENPLAY[/]",
            subtitle=f"[dim]{scene_info}[/]" if scene_info else None,
            border_style="yellow",
            padding=(1, 2)
        )


# Convenience function for direct use
def to_screenplay(text: str, characters: List[str] = None) -> str:
    """Convert text to screenplay format."""
    formatter = ScreenplayFormatter()
    return formatter.parse_and_format(text, characters)
