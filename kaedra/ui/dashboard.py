from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.layout import Layout
from rich import box
import time

class KaedraDashboard:
    def __init__(self):
        self.console = Console()
        self.status = "INITIALIZING"
        self.mic_status = "OFF"
        self.active_lights = []
        self.last_tokens = 0
        self.total_cost = 0.0
        self.history = []  # List of (role, message, color)
        self.stream_buffer = []
        self.polygraph_active = False

    def set_status(self, status: str, color: str = "white"):
        self.status = f"[{color}]{status}[/{color}]"

    def set_mic(self, status: str):
        self.mic_status = status

    def set_lights(self, lights: list):
        self.active_lights = lights

    def update_stats(self, latency: float, tokens: int, cost: float):
        self.last_tokens = tokens
        self.total_cost += cost

    def set_polygraph(self, active: bool):
        self.polygraph_active = active

    def start_stream(self, role: str, color: str = "magenta"):
        self.stream_buffer = [f"[{color}]{role}: [/{color}]"]

    def print_stream(self, text: str, color: str = "magenta"):
        self.stream_buffer.append(text)

    def end_stream(self):
        full_text = "".join(self.stream_buffer)
        pass

    def update_history(self, role: str, message: str, color: str = "white"):
        self.history.append((role, message, color))
        if len(self.history) > 8:
            self.history.pop(0)

    def generate_view(self):
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )

        poly_status = "[bold yellow]![/bold yellow]" if self.polygraph_active else ""
        
        header_table = Table.grid(expand=True)
        header_table.add_column(justify="left", ratio=1)
        header_table.add_column(justify="center", ratio=1)
        header_table.add_column(justify="right", ratio=1)
        header_table.add_row(
            f"Status: {self.status}",
            f"[bold magenta]KAEDRA MODULAR ENGINE[/bold magenta] {poly_status}",
            f"Mic: {'[green]ON[/green]' if self.mic_status!='OFF' else '[red]OFF[/red]'}"
        )
        
        layout["header"].update(Panel(header_table, style="cyan", box=box.ROUNDED))

        history_table = Table(show_header=False, box=None, expand=True)
        history_table.add_column(style="bold", width=12)
        history_table.add_column()
        
        for role, msg, color in self.history:
            history_table.add_row(f"[{color}]{role}:[/{color}]", msg)
            
        layout["main"].update(Panel(history_table, title="Neural Stream", border_style="magenta", box=box.ROUNDED))

        stats = f"Tokens: {self.last_tokens:,} | Total Cost: ${self.total_cost:.4f} | Lights: {', '.join(self.active_lights) if self.active_lights else 'None'}"
        layout["footer"].update(Panel(Align.center(stats), style="blue", box=box.ROUNDED, title="Kaedra Status"))
        
        return layout
