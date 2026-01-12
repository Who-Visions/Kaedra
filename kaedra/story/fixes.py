"""
Hotfixes and Diagnostic extensions for StoryEngine v7.15.
"""
from .ui import console

def add_diagnostics_command(engine):
    """
    Returns a callable that displays system diagnostics.
    """
    def show_diag():
        console.print("\n[bold cyan]🩺 System Diagnostics (v7.15)[/]")

        # 1. Context Budget
        try:
            budget = engine.context.get_budget_status()
            color = "green" if budget['usage_percent'] < 80 else "yellow" if budget['usage_percent'] < 95 else "red"
            console.print(f"Context Budget: [{color}]{budget['usage_percent']:.1f}%[/] ({budget['current']:,} / {budget['capacity']:,} tokens)")
        except Exception as e:
            console.print(f"[red]Context Status: Error ({e})[/]")

        # 2. Circuit Breaker
        if hasattr(engine, 'retry_policy'):
            if engine.retry_policy._circuit_open:
                console.print("[bold red]Circuit Breaker: OPEN (Fleet Review Suspended)[/]")
            else:
                console.print(f"[green]Circuit Breaker: CLOSED (Stable) | Failures: {engine.retry_policy._successive_failures}[/]")
        else:
            console.print("[dim]Circuit Breaker: Not Initialized[/]")

        # 3. Memory
        import psutil
        import os
        process = psutil.Process(os.getpid())
        mem = process.memory_info().rss / 1024 / 1024
        console.print(f"Memory Usage: {mem:.1f} MB")

        console.print("[dim]Diagnostics Complete.[/]\n")

    return show_diag
