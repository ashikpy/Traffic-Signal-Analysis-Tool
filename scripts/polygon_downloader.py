import overpy
import osmnx as ox
import json
import os
from utils.constants import geojson_outline_dir
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()


def get_states(country_name):
    api = overpy.Overpass()
    query = f"""
    area["name:en"="{country_name}"]["admin_level"="2"]->.country;
    relation(area.country)["admin_level"="4"]["boundary"="administrative"];
    out body;
    """
    result = api.query(query)
    states = [(rel.tags.get("name", "Unknown"), rel.id)
              for rel in result.relations]
    return states


def download_state_polygon(country_name):
    console.rule(
        f"[bold blue]Fetching States for [green]{country_name}[/green][/bold blue]")
    states = get_states(country_name)
    if not states:
        console.print("No states found.")
        return

    table = Table(title="Available States")
    table.add_column("Index", style="cyan", justify="right")
    table.add_column("State Name", style="magenta")

    for i, (name, _) in enumerate(states):
        table.add_row(str(i), name)
    console.print(table)

    state_names = [name for name, _ in states]
    input_str = Prompt.ask(
        "\n[bold yellow]Enter index or state name to download[/bold yellow]"
    )

    # Try to parse as index
    try:
        index = int(input_str)
        if index < 0 or index >= len(states):
            console.print("[red]Invalid state index.[/red]")
            return
    except ValueError:
        # Try matching by name
        normalized_input = input_str.strip().lower()
        matched_states = [
            i for i, (name, _) in enumerate(states)
            if name.strip().lower() == normalized_input
        ]
        if not matched_states:
            console.print("[red]Invalid state name.[/red]")
            return
        index = matched_states[0]

    state_name = states[index][0]

    # Use osmnx to download GeoJSON
    gdf = ox.geocode_to_gdf(f"{state_name}, {country_name}")
    geojson = gdf.__geo_interface__

    # Save to file
    os.makedirs(os.path.join(geojson_outline_dir, country_name), exist_ok=True)
    filename = os.path.join(
        geojson_outline_dir,
        country_name,
        f"{state_name.replace(' ', '_')}.geojson"
    )
    with open(filename, "w") as f:
        json.dump(geojson, f)
    console.print(f"\n[green]Saved:[/green] {filename}")
    return filename


def main():
    country_name = input("Enter the country name: ").strip()
    if not country_name:
        console.print("Country name cannot be empty.")
        return
    download_state_polygon(country_name)


if __name__ == "__main__":
    main()
