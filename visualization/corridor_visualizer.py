import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from scipy.spatial import KDTree
import numpy as np
import plotly.graph_objects as go
from utils.csv_region_selector import csv_region_selector
from utils.zoom_center_plotly import zoom_center
from rich.console import Console
from rich.prompt import IntPrompt

console = Console()

def main():
    input_file, region_name = csv_region_selector(purpose="to Visualize Connectivity Corridors")
    
    df = pd.read_csv(input_file)
    if len(df) < 2:
        console.print("[red]Error: Need at least 2 points for connectivity analysis.[/red]")
        return

    threshold = IntPrompt.ask("Enter connectivity threshold (meters)", default=300)

    with console.status(f"[bold green]Generating Corridors (Threshold: {threshold}m)...[/bold green]"):
        # 1. Prepare points in UTM for accurate distance
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
        utm_crs = gdf.estimate_utm_crs()
        gdf_utm = gdf.to_crs(utm_crs)
        
        coords = np.array(list(zip(gdf_utm.geometry.x, gdf_utm.geometry.y)))
        tree = KDTree(coords)
        
        # 2. Find neighbors within threshold
        # query_ball_tree returns indices of neighbors
        adj_list = tree.query_ball_tree(tree, r=threshold)
        
        lines_lon = []
        lines_lat = []
        
        edges_count = 0
        for i, neighbors in enumerate(adj_list):
            for j in neighbors:
                if i < j:  # Only add each edge once
                    p1 = df.iloc[i]
                    p2 = df.iloc[j]
                    
                    # For Plotly Scattermapbox lines/paths, we use [lon1, lon2, None] pattern
                    lines_lon.extend([p1['lon'], p2['lon'], None])
                    lines_lat.extend([p1['lat'], p2['lat'], None])
                    edges_count += 1

    zoom, center = zoom_center(df['lon'].tolist(), df['lat'].tolist())

    fig = go.Figure()

    # Add the corridors (lines)
    if edges_count > 0:
        fig.add_trace(go.Scattermap(
            lon=lines_lon,
            lat=lines_lat,
            mode='lines',
            line=dict(width=2, color='orange'),
            name=f'Corridors (<{threshold}m)',
            opacity=0.6
        ))

    # Add the signal markers
    fig.add_trace(go.Scattermap(
        lat=df['lat'],
        lon=df['lon'],
        mode='markers',
        marker=dict(size=6, color='cyan', opacity=0.9),
        name='Traffic Signals',
        text=df['id'] if 'id' in df.columns else None
    ))

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(center=center, zoom=zoom),
        title=f"Traffic Signal Connectivity: {region_name} ({edges_count} links found)",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        showlegend=True
    )

    fig.show()

if __name__ == "__main__":
    main()
