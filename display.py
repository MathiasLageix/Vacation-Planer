"""Affichage CLI des résultats et insights avec Rich."""
from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from models import InsightReport, NormalizedCar, NormalizedFlight, NormalizedHotel

console = Console()


# ---------------------------------------------------------------------------
# Vols
# ---------------------------------------------------------------------------

def print_flights(flights: list[NormalizedFlight], criteria_summary: str = "") -> None:
    if criteria_summary:
        console.print(f"\n[bold cyan]Vols :[/bold cyan] {criteria_summary}\n")

    if not flights:
        console.print("[yellow]Aucun vol trouvé pour ces critères.[/yellow]")
        return

    table = Table(title=f"{len(flights)} vol(s)", box=box.ROUNDED, show_lines=True)
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
        h, m = divmod(f.total_duration_minutes, 60)
        table.add_row(
            str(i),
            f"{f.total_price:.2f} {f.currency}",
            ", ".join(f.carrier_codes),
            "Direct" if f.stops == 0 else f"{f.stops} escale(s)",
            first_seg.departure_at.strftime("%d %b %H:%M"),
            last_seg.arrival_at.strftime("%d %b %H:%M"),
            f"{h}h{m:02d}",
            f.deep_link,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Hôtels
# ---------------------------------------------------------------------------

def print_hotels(hotels: list[NormalizedHotel], criteria_summary: str = "") -> None:
    if criteria_summary:
        console.print(f"\n[bold cyan]Hébergements :[/bold cyan] {criteria_summary}\n")

    if not hotels:
        console.print("[yellow]Aucun hébergement trouvé pour ces critères.[/yellow]")
        return

    table = Table(title=f"{len(hotels)} hébergement(s)", box=box.ROUNDED, show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Hôtel")
    table.add_column("Étoiles", justify="center")
    table.add_column("Prix/nuit", justify="right", style="bold green")
    table.add_column("Total", justify="right")
    table.add_column("Nuits", justify="center")
    table.add_column("Adresse")
    table.add_column("Lien", style="blue")

    for i, h in enumerate(hotels, 1):
        stars = ("★" * h.stars) if h.stars else "—"
        table.add_row(
            str(i),
            h.name,
            stars,
            f"{h.price_per_night:.2f} {h.currency}",
            f"{h.total_price:.2f} {h.currency}",
            str(h.nights),
            h.address or "—",
            h.deep_link,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Autos
# ---------------------------------------------------------------------------

def print_cars(cars: list[NormalizedCar], stub_message: str = "") -> None:
    console.print("\n[bold cyan]Location d'autos[/bold cyan]\n")

    if stub_message:
        console.print(f"[yellow]{stub_message}[/yellow]")
        return

    if not cars:
        console.print("[yellow]Aucune auto trouvée.[/yellow]")
        return

    table = Table(title=f"{len(cars)} option(s)", box=box.ROUNDED, show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Catégorie")
    table.add_column("Compagnie")
    table.add_column("Prix/jour", justify="right", style="bold green")
    table.add_column("Total", justify="right")
    table.add_column("Prise en charge")
    table.add_column("Lien", style="blue")

    for i, c in enumerate(cars, 1):
        table.add_row(
            str(i),
            c.category,
            c.company,
            f"{c.price_per_day:.2f} {c.currency}",
            f"{c.total_price:.2f} {c.currency}",
            c.pickup_location,
            c.deep_link,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

def print_insights(report: InsightReport) -> None:
    if not report.has_insights:
        return

    type_label = {"flight": "vols", "hotel": "hébergements", "car": "autos"}.get(
        report.search_type, report.search_type
    )
    old_fmt = report.snapshot_old_at.strftime("%d %b %H:%M")
    new_fmt = report.snapshot_new_at.strftime("%d %b %H:%M")
    console.print(
        f"\n[bold magenta]Insights {type_label}[/bold magenta] "
        f"[dim]({old_fmt} → {new_fmt})[/dim]\n"
    )

    for p in report.price_changes:
        arrow = "[green]↓[/green]" if p.delta < 0 else "[red]↑[/red]"
        console.print(
            f"  {arrow} [bold]{p.label}[/bold] : "
            f"{p.old_price:.2f} → {p.new_price:.2f} {p.currency} "
            f"([{'green' if p.delta < 0 else 'red'}]{p.pct_change:+.1f}%[/])"
        )

    for a in report.availability:
        if a.event == "disappeared":
            console.print(
                f"  [red]✗ Disparu[/red] : [bold]{a.label}[/bold] "
                f"(était {a.price:.2f} {a.currency})"
            )
        else:
            console.print(
                f"  [green]✓ Nouveau[/green] : [bold]{a.label}[/bold] "
                f"à {a.price:.2f} {a.currency}"
            )

    console.print()
