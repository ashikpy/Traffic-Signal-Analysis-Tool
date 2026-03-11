import os
import pandas as pd
import geopandas as gpd
import osmnx as ox
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from utils.csv_region_selector import csv_region_selector
from utils.rich_components import bold_color_print
import plotly.express as px

console = Console()

def main():
    input_file, region_name = csv_region_selector(purpose="to Analyze Road Context")
    
    df = pd.read_csv(input_file)
    if len(df) == 0:
        bold_color_print("No data found in CSV.", "red")
        return

    # To avoid crashing on state-wide huge data, we limit the analysis area
    # by taking the bounding box of the signals
    min_lon, max_lon = df['lon'].min(), df['lon'].max()
    min_lat, max_lat = df['lat'].min(), df['lat'].max()
    
    # Check if area is too large (heuristic: > 0.5 degrees is often a whole state)
    if (max_lon - min_lon) > 0.5 or (max_lat - min_lat) > 0.5:
        bold_color_print("Warning: Dataset area is very large. Downloading road networks might take time.", "yellow")

    try:
        with console.status(f"[bold green]Fetching Road Network for {region_name} from OSM...[/bold green]"):
            # Download the graph for the area
            # Handle different OSMnx versions for graph_from_bbox
            north, south = max_lat + 0.01, min_lat - 0.01
            east, west = max_lon + 0.01, min_lon - 0.01
            
            try:
                # Newer OSMnx versions (v2.0+)
                G = ox.graph_from_bbox(bbox=(north, south, east, west), network_type='drive')
            except TypeError:
                # Older OSMnx versions
                G = ox.graph_from_bbox(north, south, east, west, network_type='drive')
            
            # Convert graph edges to a GeoDataFrame
            nodes, edges = ox.graph_to_gdfs(G)
            
        with console.status("[bold blue]Matching Signals to Road Classes...[/bold blue]"):
            # Find the nearest edge (road) for each signal
            # ox.nearest_edges is efficient
            nearest_edges = ox.nearest_edges(G, df['lon'], df['lat'])
            
            road_types = []
            importance_scores = []
            
            # Map road types to importance (1-10)
            importance_map = {
                'motorway': 10, 'trunk': 9, 'primary': 8, 
                'secondary': 6, 'tertiary': 4, 'residential': 2, 
                'living_street': 1, 'unclassified': 2
            }

            for u, v, k in nearest_edges:
                edge_data = edges.loc[(u, v, k)]
                # highway tag contains road type (can be a list)
                h_type = edge_data['highway']
                if isinstance(h_type, list):
                    h_type = h_type[0]
                
                road_types.append(h_type)
                importance_scores.append(importance_map.get(str(h_type), 2))

            df['road_type'] = road_types
            df['criticality_score'] = importance_scores

    except Exception as e:
        bold_color_print(f"Error fetching road data: {e}", "red")
        return

    # 📊 Results Table
    table = Table(title=f"Urban Context Analysis: {region_name}")
    table.add_column("Road Class", style="cyan")
    table.add_column("Signal Count", style="magenta")
    table.add_column("Criticality", style="yellow")
    
    counts = df['road_type'].value_counts()
    for road, count in counts.items():
        score = df[df['road_type'] == road]['criticality_score'].iloc[0]
        criticality = "HIGH" if score >= 8 else "MED" if score >= 5 else "LOW"
        table.add_row(str(road).capitalize(), str(count), criticality)
    
    console.print("\n")
    console.print(table)

    # 🗺️ Visualization
    bold_color_print("Generating Contextual Map (Color coded by Road Importance)...", "cyan")
    
    fig = px.scatter_map(
        df,
        lat="lat", lon="lon",
        color="criticality_score",
        size="criticality_score",
        hover_name="road_type",
        color_continuous_scale="Reds",
        title=f"Strategic Signal Criticality: {region_name}",
        map_style="open-street-map",
        zoom=12
    )
    
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    fig.show()

if __name__ == "__main__":
    main()
