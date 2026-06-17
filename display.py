"""Affichage CLI des résultats avec Rich."""
from rich.console import Console
from rich.table import Table
from rich import box

from models import NormalizedFlight

console = Console()


def print_results(flights: list[NormalizedFlight], criteria_summary: str = "") -> None:
    if criteria_summary:
        console.print(f"\n[bold cyan]Recherche :[/bold cyan] {criteria_summary}\n")

    if not flights:
        console.print("[yellow]Aucun vol trouvé pour ces critères.[/yellow]")
        return

    table = Table(
        title=f"{len(flights)} vol(s) trouvé(s)",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Prix", style="bold green", justify="right")
    table.add_column("Compagnie(s)")
    table.add_column("Escales", justify="center")
    table.add_column("Départ")
    table.add_column("Arrivée")
    table.add_column("Durée", justify="right")
    table.add_column("Lien", style="blue")

    for i, f in enumerate(flights, 1):
        first_seg = f.segments[0]
        last_seg = f.segments[-1]
        carriers = ", ".join(f.carrier_codes)
        stops_label = "Direct" if f.stops == 0 else f"{f.stops} escale(s)"
        duration_h, duration_m = divmod(f.total_duration_minutes, 60)
        table.add_row(
            str(i),
            f"{f.total_price:.2f} {f.currency}",
            carriers,
            stops_label,
            first_seg.departure_at.strftime("%d %b %H:%M"),
            last_seg.arrival_at.strftime("%d %b %H:%M"),
            f"{duration_h}h{duration_m:02d}",
            f.deep_link,
        )

    console.print(table)
    console.print("\n[dim]Cliquez sur un lien pour accéder directement à la page de réservation.[/dim]\n")
