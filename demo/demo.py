"""Narrated terminal demo: Disease surveillance on Samyama.

Record with asciinema:
    asciinema rec -c "python -m demo.demo" demo/surveillance.cast

Loads real WHO Global Health Observatory (GHO) surveillance data — countries,
WHO regions, notifiable diseases, annual disease reports and childhood vaccine
coverage — into a Samyama graph, then walks through the questions an outbreak /
surveillance team asks: where is disease burden concentrated, and where are the
immunity gaps that let it spread?

To keep the demo snappy the reporting window is scoped to 2016-2019; every
record is real WHO GHO data (no synthetic values).
"""

from __future__ import annotations

import time

from rich.console import Console
from rich.panel import Panel
from samyama import SamyamaClient

from etl.helpers import Registry
from etl.who_loader import load_who_data

console = Console()
G = "surveillance"
YEARS = {2016, 2017, 2018, 2019}


def pause(s: float = 1.4) -> None:
    time.sleep(s)


def step(title: str) -> None:
    console.print()
    console.rule(f"[bold cyan]{title}")
    pause(0.6)


def run(client, q, label):
    console.print(f"  [dim]cypher>[/dim] [yellow]{q}[/yellow]")
    rows = client.query(q, G).records
    one = len(rows) == 1 and len(rows[0]) == 1
    console.print(f"  [green]→[/green] {label}: [bold]{rows[0][0] if one else rows}[/bold]")
    pause()
    return rows


def main() -> None:
    console.print(Panel.fit(
        "[bold]Samyama · Disease Surveillance Knowledge Graph[/bold]\n"
        "\"Where is disease burden concentrated — and where are the immunity gaps?\"\n"
        "[dim]data: WHO Global Health Observatory (GHO) · public indicators[/dim]",
        border_style="cyan",
    ))
    pause(1.2)

    step("1 · Load WHO GHO surveillance data into Samyama")
    console.print("  [dim]countries · WHO regions · diseases · disease reports · vaccine coverage (2016-2019)…[/dim]")
    stats = load_who_data(client := SamyamaClient.embedded(), "data", Registry(), G, years=YEARS)
    total_nodes = sum(v for k, v in stats.items() if k.endswith("nodes"))
    total_edges = sum(v for k, v in stats.items() if k.endswith("edges"))
    console.print(f"  [green]loaded[/green] {total_nodes} nodes, {total_edges} edges")
    run(client, "MATCH (c:Country) RETURN count(c) AS countries", "countries tracked")
    run(client, "MATCH (d:Disease) RETURN count(d) AS diseases", "notifiable diseases monitored")

    step("2 · Which diseases generate the most surveillance reporting?")
    run(
        client,
        "MATCH (d:Disease)<-[:REPORT_OF]-(r:DiseaseReport) "
        "RETURN d.name AS disease, count(r) AS reports "
        "ORDER BY reports DESC LIMIT 5",
        "most-reported indicators",
    )

    step("3 · Where is cholera burden concentrated? (outbreak hotspots)")
    run(
        client,
        "MATCH (c:Country)-[:REPORTED]->(r:DiseaseReport)-[:REPORT_OF]->(d:Disease) "
        'WHERE d.name = "Number of reported cases of cholera" '
        "RETURN c.name AS country, sum(r.value) AS cases "
        "ORDER BY cases DESC LIMIT 5",
        "countries with most reported cholera cases",
    )

    step("4 · Where are the immunity gaps? (DTP3 coverage below 50%)")
    console.print("  [dim]low childhood vaccine coverage = the populations an outbreak spreads through…[/dim]")
    pause()
    run(
        client,
        "MATCH (c:Country)-[:HAS_COVERAGE]->(v:VaccineCoverage) "
        'WHERE v.antigen = "DTP3 immunization coverage (%)" AND v.coverage_pct < 50.0 '
        "RETURN c.name AS country, min(v.coverage_pct) AS lowest_dtp3_pct "
        "ORDER BY lowest_dtp3_pct ASC LIMIT 5",
        "most under-vaccinated populations",
    )

    console.print()
    console.print(Panel.fit(
        "[bold green]One Country.iso_code joins this to health-systems-kg & "
        "health-determinants-kg[/bold green] — outbreak signal, response capacity,\n"
        "and social drivers answered on a single engine, one Cypher query.",
        border_style="green",
    ))
    pause(1.5)


if __name__ == "__main__":
    main()
