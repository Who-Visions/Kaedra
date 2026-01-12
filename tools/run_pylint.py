import sys
import subprocess
import re
import time
from pathlib import Path
from collections import Counter

try:
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.syntax import Syntax
    from rich import box
except ImportError:
    print("Please install rich: pip install rich")
    sys.exit(1)

console = Console()

def parse_pylint_line(line):
    # Default format: path:line:col: msg_id: msg
    # We want to extract: path, line, type (E,W,R,C), msg
    pattern = r"^(.*?):(\d+):(\d+): ([A-Z]\d+): (.*)$"
    match = re.match(pattern, line.strip())
    if match:
        return {
            "path": match.group(1),
            "line": match.group(2),
            "col": match.group(3),
            "code": match.group(4),
            "msg": match.group(5),
            "type": match.group(4)[0] # E, W, R, C, F
        }
    return None

def get_type_color(code_type):
    if code_type == 'E': return "red"     # Error
    if code_type == 'F': return "red bold" # Fatal
    if code_type == 'W': return "yellow"  # Warning
    if code_type == 'C': return "blue"    # Convention
    if code_type == 'R': return "magenta" # Refactor
    return "white"

def make_layout():
    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=5)
    )
    layout["main"].split_row(
        Layout(name="issues", ratio=2),
        Layout(name="stats", ratio=1)
    )
    return layout

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "kaedra"
    
    # Pre-count Python files
    py_files = list(Path(target_dir).rglob("*.py"))
    total_files = len(py_files)
    
    layout = make_layout()
    
    # Statistics
    stats = Counter()
    recent_issues = [] # List of tuples (path, line, code, msg)
    
    with Live(layout, refresh_per_second=4, screen=True) as live:
        
        # Header
        layout["header"].update(
            Panel(f"[bold cyan]KAEDRA PYLINT AUDIT[/] | Target: [yellow]{target_dir}[/] | Files: [green]{total_files}[/]", 
                  style="white on black")
        )
        
        # Run Pylint
        process = subprocess.Popen(
            ["pylint", target_dir, "--output-format=text", "--msg-template={path}:{line}:{column}: {msg_id}: {msg}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        score_line = None
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if not line:
                continue
                
            # Check for score
            if "Your code has been rated at" in line:
                score_line = line.strip()
                continue
                
            parsed = parse_pylint_line(line)
            
            if parsed:
                stats[parsed['type']] += 1
                short_path = Path(parsed['path']).name
                # Add to recent issues (keep last 15)
                recent_issues.append(parsed)
                if len(recent_issues) > 20:
                    recent_issues.pop(0)

            # Save to detailed log
            with open("pylint_issues.txt", "a", encoding="utf-8") as detailed_log:
                detailed_log.write(line)
            
            # --- Update UI ---
            
            # Issues Table
            table = Table(box=box.SIMPLE, expand=True)
            table.add_column("File", style="cyan")
            table.add_column("Line", style="magenta", width=6)
            table.add_column("Code", width=8)
            table.add_column("Message")
            
            for i in recent_issues:
                color = get_type_color(i['type'])
                table.add_row(
                    Path(i['path']).name,
                    str(i['line']),
                    f"[{color}]{i['code']}[/]",
                    i['msg']
                )
            
            layout["issues"].update(Panel(table, title="Live Issues Feed", border_style="cyan"))
            
            # Stats Table
            stats_table = Table(box=box.ROUNDED, expand=True)
            stats_table.add_column("Type", style="bold")
            stats_table.add_column("Count", justify="right")
            
            stats_table.add_row("[red bold]Fatal (F)", str(stats['F']))
            stats_table.add_row("[red]Errors (E)", str(stats['E']))
            stats_table.add_row("[yellow]Warnings (W)", str(stats['W']))
            stats_table.add_row("[blue]Conventions (C)", str(stats['C']))
            stats_table.add_row("[magenta]Refactors (R)", str(stats['R']))
            
            layout["stats"].update(Panel(stats_table, title="Issue Statistics", border_style="yellow"))
            
            # Footer (Spinner)
            layout["footer"].update(Panel(f"[bold white]Scanning...[/] {line.strip()[:100]}", style="dim"))
            
    # Final Output
    console.clear()
    console.print(Panel(f"[bold green]AUDIT COMPLETE[/]\n\n{score_line or 'Score not found.'}", style="green"))
    
    # Print Summary Table
    final_table = Table(title="Final Statistics")
    final_table.add_column("Category")
    final_table.add_column("Count")
    for k, v in stats.items():
        final_table.add_row(str(k), str(v))
    console.print(final_table)
    
    # Report File
    with open("pylint_report_rich.txt", "w") as f:
        f.write(f"Final Score: {score_line}\n")
        f.write(f"Stats: {stats}\n")

if __name__ == "__main__":
    main()
