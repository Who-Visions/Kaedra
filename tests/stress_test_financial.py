import asyncio
import time
import os
import logging
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from kaedra.services.invoices import InvoiceService

# Setup
load_dotenv()
console = Console()
logging.basicConfig(level=logging.ERROR)

async def run_financial_stress_test(num_turns=20):
    console.print(f"[bold magenta]💰 Kaedra Financial Ops Stress Test (n={num_turns})[/bold magenta]")
    
    # Initialize Service
    t_init = time.time()
    try:
        service = InvoiceService()
        status = service.get_status()
        console.print(f"[dim]Init Time: {time.time()-t_init:.4f}s[/dim]")
        
        console.print("\n[bold]Provider Status:[/bold]")
        if status["stripe"]["configured"]:
            console.print(f"  • Stripe: [green]Configured[/green] (Connected: {status['stripe']['connected']})")
        else:
            console.print(f"  • Stripe: [red]Not Configured[/red]")
            
        if status["square"]["configured"]:
            console.print(f"  • Square: [green]Configured[/green] (Connected: {status['square']['connected']})")
        else:
            console.print(f"  • Square: [red]Not Configured[/red]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Failed to initialize InvoiceService: {e}[/bold red]")
        return

    # Prepare Table
    table = Table(title="Transaction Log", border_style="cyan")
    table.add_column("Iter", justify="right", style="dim")
    table.add_column("Provider", style="white")
    table.add_column("Operation", style="cyan")
    table.add_column("Latency", justify="center")
    table.add_column("Result", justify="left")

    console.print("\n[bold]Starting 20-run sequence...[/bold]")
    
    metrics = []
    
    for i in range(1, num_turns + 1):
        # Alternate between Stripe/Square if both available, or just use what we have
        use_stripe = status["stripe"]["configured"]
        use_square = status["square"]["configured"]
        
        # Iteration operations
        ops = []
        if use_stripe: ops.append("stripe")
        if use_square: ops.append("square")
        
        if not ops:
            console.print("[red]No providers configured to test![/red]")
            break
            
        current_provider = ops[(i-1) % len(ops)] # Round robin
        
        t_start = time.time()
        result_len = 0
        error = None
        
        try:
            # We use list_invoices as a safe read-heavy load test
            invoices = service.list_invoices(provider=current_provider, limit=5)
            result_len = len(invoices)
        except Exception as e:
            error = str(e)
            
        latency = time.time() - t_start
        metrics.append({"lat": latency, "provider": current_provider, "error": bool(error)})
        
        # Log row
        status_str = f"[green]Success ({result_len} inv)[/green]" if not error else f"[red]Error: {error}[/red]"
        table.add_row(str(i), current_provider.title(), "list_invoices(limit=5)", f"{latency:.3f}s", status_str)
        
        # Small sleep to enforce roughly user-like pacing (and avoid instant rate limits)
        # asyncio.sleep not needed since calls are synchronous currently, use time.sleep
        time.sleep(0.5) 
        
        # Progress indicator every 5
        if i % 5 == 0:
            console.print(f"Completed {i}/{num_turns}...")

    console.print(table)
    
    # Results
    if metrics:
        avg_lat = sum(m["lat"] for m in metrics) / len(metrics)
        errors = sum(1 for m in metrics if m["error"])
        
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  • Total Runs: {len(metrics)}")
        console.print(f"  • Avg Latency: [cyan]{avg_lat:.3f}s[/cyan]")
        console.print(f"  • Errors: {errors}")
        
        if errors == 0:
            console.print("[bold green]✅ FINANCIAL SKILL VERIFIED[/bold green]")
        else:
            console.print("[bold yellow]⚠️ WARNING: ERRORS DETECTED[/bold yellow]")

if __name__ == "__main__":
    asyncio.run(run_financial_stress_test(num_turns=20))
