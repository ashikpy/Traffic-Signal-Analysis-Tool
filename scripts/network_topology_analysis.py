import pandas as pd
import geopandas as gpd
import networkx as nx
import numpy as np
from scipy.spatial import KDTree
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from utils.csv_region_selector import csv_region_selector
from utils.rich_components import bold_color_print
from rich.prompt import IntPrompt

console = Console()

def analyze_network(df, region_name, threshold_m):
    # 1. Coordinate Projection for distance
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
    utm_crs = gdf.estimate_utm_crs()
    gdf_utm = gdf.to_crs(utm_crs)
    
    coords = np.array(list(zip(gdf_utm.geometry.x, gdf_utm.geometry.y)))
    tree = KDTree(coords)
    
    # 2. Build Graph
    G = nx.Graph()
    # Add all nodes first
    for i in range(len(df)):
        G.add_node(i, pos=(df.iloc[i]['lon'], df.iloc[i]['lat']))
    
    # Find neighbors within threshold
    adj_list = tree.query_ball_tree(tree, r=threshold_m)
    for i, neighbors in enumerate(adj_list):
        for j in neighbors:
            if i < j:
                # Calculate exact distance for edge weight
                dist = np.linalg.norm(coords[i] - coords[j])
                G.add_edge(i, j, weight=dist)

    # 3. Network Statistics
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    
    # Connected Components (isolated vs connected grids)
    components = list(nx.connected_components(G))
    num_components = len(components)
    largest_cc = max(components, key=len) if components else set()
    size_largest_cc = len(largest_cc)
    
    # Hub Analysis (Degree Centrality)
    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 0
    hubs = [i for i, d in degrees.items() if d == max_degree]
    
    # Corridors (Path Analysis)
    # A "Strict Corridor" is a part of the graph that is a path (degree <= 2)
    corridor_nodes = [n for n, d in degrees.items() if d == 2]
    junction_nodes = [n for n, d in degrees.items() if d > 2]
    
    # Average Clustering (how much it forms triangles/grids)
    avg_clustering = nx.average_clustering(G)

    # 4. Results Display
    stats_table = Table(title=f"Network Topology Analysis: {region_name} (@{threshold_m}m)", show_lines=True)
    stats_table.add_column("Network Property", style="cyan")
    stats_table.add_column("Value", style="yellow")

    stats_table.add_row("Total Potential Hubs (Nodes)", str(num_nodes))
    stats_table.add_row("Total Connections (Edges)", str(num_edges))
    stats_table.add_row("Independent Grids (Components)", str(num_components))
    stats_table.add_row("Largest Synchronized Group", f"{size_largest_cc} signals")
    stats_table.add_row("Max Connections per Signal", str(max_degree))
    stats_table.add_row("Complex Junctions (Deg > 2)", str(len(junction_nodes)))
    stats_table.add_row("Linear Corridor Segments", str(len(corridor_nodes)))
    stats_table.add_row("Grid Density Coefficient", f"{avg_clustering:.4f}")

    console.print("\n")
    console.print(stats_table)

    # Engineering Insight using Topology
    if avg_clustering > 0.1:
        insight = "High Grid Connectivity: The signal network forms dense clusters. Ideal for 'Area Traffic Control Systems' (ATCS) where entire zones are synchronized together."
        color = "green"
    elif size_largest_cc / num_nodes > 0.5:
        insight = "Strong Backbone: More than half the city signals are connected. Focus on a single 'Master Controller' for the main city corridors."
        color = "blue"
    else:
        insight = "Fragmented Network: Signals are mostly in small, isolated groups. Suggests traffic management should be handled at the 'Sub-division' level rather than centrally."
        color = "magenta"

    console.print(Panel(f"[bold {color}]Topology Insight:[/bold {color}]\n{insight}", expand=False))

def main():
    try:
        input_file, region_name = csv_region_selector(purpose="to Analyze Network Topology")
    except Exception:
        return

    df = pd.read_csv(input_file)
    if len(df) < 2:
        bold_color_print("Error: Need at least 2 points for network analysis.", "red")
        return

    threshold = IntPrompt.ask("Enter connection threshold for topology (meters)", default=300)

    with console.status("[bold green]Analyzing graph topology...[/bold green]"):
        analyze_network(df, region_name, threshold)

if __name__ == "__main__":
    main()
