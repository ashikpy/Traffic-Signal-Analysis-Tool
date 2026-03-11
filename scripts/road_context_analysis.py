import os
import pandas as pd
import geopandas as gpd
import osmnx as ox
from shapely.geometry import Point
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

    # Calculate Area
    min_lon, max_lon = df['lon'].min(), df['lon'].max()
    min_lat, max_lat = df['lat'].min(), df['lat'].max()
    
    # Calculate span
    lon_span = max_lon - min_lon
    lat_span = max_lat - min_lat

    # 1. Download Road Network
    try:
        with console.status(f"[bold green]Analysis area: {lon_span:.2f} x {lat_span:.2f} degrees. Fetching OSM roads...[/bold green]"):
            # If area is too large, it will take hours. We limit it to a 10km radius from center if it's too big.
            if lon_span > 0.2 or lat_span > 0.2:
                bold_color_print("\nArea too large for full download. Focusing on the city center (10km radius)...", "yellow")
                center_lat, center_lon = df['lat'].mean(), df['lon'].mean()
                G = ox.graph_from_point((center_lat, center_lon), dist=10000, network_type='drive')
            else:
                # Defensive call for different OSMnx versions
                north, south = max_lat + 0.005, min_lat - 0.005
                east, west = max_lon + 0.005, min_lon - 0.005
                
                # We use positional args first as it's most compatible across many versions
                try:
                    # Newest versions (bbox as first positional or keyword)
                    G = ox.graph_from_bbox(bbox=(north, south, east, west), network_type='drive')
                except Exception:
                    try:
                        # Versions that want a tuple but no keyword
                        G = ox.graph_from_bbox((north, south, east, west), network_type='drive')
                    except Exception:
                        # Old versions that want north, south, east, west
                        G = ox.graph_from_bbox(north, south, east, west, network_type='drive')
            
            # Convert graph edges to a GeoDataFrame and project for distance
            nodes, edges = ox.graph_to_gdfs(G)
            edges_utm = edges.to_crs(edges.estimate_utm_crs())
            
        with console.status("[bold blue]Matching Signals to Road Classes...[/bold blue]"):
            # Find the nearest edge (road) for each signal
            nearest_edges = ox.nearest_edges(G, df['lon'], df['lat'])
            
            road_types = []
            importance_scores = []
            valid_indices = []
            filtered_count = 0
            
            # Map road types to importance (1-10)
            importance_map = {
                'motorway': 10, 'trunk': 9, 'primary': 8, 
                'secondary': 6, 'tertiary': 4, 'residential': 2, 
                'living_street': 1, 'unclassified': 2
            }
            
            # Distance threshold (meters) - Road signals should be within 20m of a road edge
            DIST_THRESHOLD = 20

            for i, edge_info in enumerate(nearest_edges):
                try:
                    edge_data_utm = edges_utm.loc[edge_info]
                    edge_data = edges.loc[edge_info]
                except (KeyError, TypeError):
                    edge_data_utm = edges_utm.iloc[edge_info]
                    edge_data = edges.iloc[edge_info]
                
                # Calculate Distance to the edge (in meters)
                sig_geom = Point(df.iloc[i]['lon'], df.iloc[i]['lat'])
                road_geom_utm = edge_data_utm['geometry']
                
                # Project signal point to the same UTM CRS
                sig_point_utm = gpd.GeoSeries([sig_geom], crs="EPSG:4326").to_crs(edges_utm.crs).iloc[0]
                dist = sig_point_utm.distance(road_geom_utm)
                
                if dist > DIST_THRESHOLD:
                    filtered_count += 1
                    continue
                
                # highway tag contains road type (can be a list)
                h_type = edge_data['highway']
                if isinstance(h_type, list):
                    h_type = h_type[0]
                
                road_types.append(h_type)
                importance_scores.append(importance_map.get(str(h_type), 2))
                valid_indices.append(i)

            # Rebuild dataframe with only valid road-aligned signals
            df = df.iloc[valid_indices].copy()
            df['road_type'] = road_types
            df['criticality_score'] = importance_scores
            
            bold_color_print(f"Filtered out {filtered_count} signals that were too far from road infrastructure (likely railway/outliers).", "yellow")
            
            # Save the enriched data back to the CSV
            df.to_csv(input_file, index=False)
            console.print(f"[bold green]Data saved successfully to {input_file}[/bold green]")

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
