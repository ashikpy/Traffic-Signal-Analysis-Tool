import pandas as pd
import geopandas as gpd
from scipy.spatial import Voronoi
from shapely.geometry import Point, MultiPoint, Polygon
import numpy as np
import plotly.graph_objects as go
from utils.csv_region_selector import csv_region_selector
from utils.zoom_center_plotly import zoom_center
from utils.rich_components import bold_color_print
from rich.console import Console
from rich.table import Table

console = Console()

def main():
    input_file, region_name = csv_region_selector(purpose="to find Coverage Gaps")
    
    df = pd.read_csv(input_file)
    if len(df) < 4:
        console.print("[red]Error: Need at least 4 points for gap analysis.[/red]")
        return

    with console.status("[bold green]Calculating urban coverage gaps...[/bold green]"):
        # 1. Coordinate Prep
        points_coords = df[['lon', 'lat']].values
        
        # 2. Generate Voronoi
        vor = Voronoi(points_coords)
        
        # 3. Create a boundary (Convex Hull) of existing signals
        multipoint = MultiPoint(points_coords)
        boundary = multipoint.convex_hull
        
        # 4. Filter Voronoi vertices that are INSIDE the city boundary
        # A Voronoi vertex is the center of a circle passing through 3+ nodes.
        # It's the point furthest from its nearest signals.
        gap_candidates = []
        for vertex in vor.vertices:
            pt = Point(vertex)
            if boundary.contains(pt):
                # Calculate distance to nearest existing signal (in degrees, converted to km approx)
                # For more accuracy, we'd project, but for ranking degrees is fine
                min_dist = min([pt.distance(Point(p)) for p in points_coords])
                gap_candidates.append({
                    'lon': vertex[0],
                    'lat': vertex[1],
                    'gap_size_deg': min_dist
                })

        # 5. Get Top Gaps
        gaps_df = pd.DataFrame(gap_candidates).sort_values(by='gap_size_deg', ascending=False)
        top_gaps = gaps_df.head(5).copy()

        # Convert gap size to meters (rough approx at equator: 1 deg ~ 111km)
        top_gaps['gap_size_m'] = top_gaps['gap_size_deg'] * 111139

    # 6. Display Table
    table = Table(title=f"Placement Recommendations: {region_name} (Estimated Gaps)")
    table.add_column("Rank", style="cyan")
    table.add_column("Coordinates (Lon, Lat)", style="magenta")
    table.add_column("Nearest Signal Distance", style="yellow")
    
    for i, row in enumerate(top_gaps.itertuples(), 1):
        table.add_row(str(i), f"{row.lon:.5f}, {row.lat:.5f}", f"{row.gap_size_m:.0f} meters")
    
    console.print("\n")
    console.print(table)
    bold_color_print("Visualizing recommended signal placements on map...", "cyan")

    # 7. Visualization
    zoom, center = zoom_center(df['lon'].tolist(), df['lat'].tolist())
    fig = go.Figure()

    # Existing Signals
    fig.add_trace(go.Scattermap(
        lat=df['lat'], lon=df['lon'],
        mode='markers',
        marker=dict(size=6, color='blue', opacity=0.5),
        name='Existing Signals'
    ))

    # Recommended Gaps
    fig.add_trace(go.Scattermap(
        lat=top_gaps['lat'], lon=top_gaps['lon'],
        mode='markers+text',
        marker=dict(size=15, color='red', symbol='marker'),
        text=[f"REC {i}" for i in range(1, 6)],
        textposition="top center",
        name='Recommended Placements'
    ))

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(center=center, zoom=zoom),
        title=f"Signal Coverage Gap Discovery: {region_name}",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )
    
    fig.show()

if __name__ == "__main__":
    main()
