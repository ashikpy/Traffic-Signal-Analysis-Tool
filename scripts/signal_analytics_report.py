import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
from scipy.spatial import KDTree
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import plotly.express as px
from utils.csv_region_selector import csv_region_selector
from utils.rich_components import bold_color_print

console = Console()

def calculate_analytics(df, region_name):
    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])], 
        crs="EPSG:4326"
    )

    # Estimate UTM CRS for accurate distance calculations in meters
    try:
        utm_crs = gdf.estimate_utm_crs()
        gdf_utm = gdf.to_crs(utm_crs)
    except Exception:
        # Fallback to a generic metric projection if UTM estimation fails
        gdf_utm = gdf.to_crs("EPSG:3857")
        bold_color_print("Warning: Could not estimate UTM CRS. Using Web Mercator (less accurate).", "yellow")

    coords = np.array(list(zip(gdf_utm.geometry.x, gdf_utm.geometry.y)))
    
    # Use KDTree for efficient nearest neighbor search
    tree = KDTree(coords)
    # k=2 because the nearest neighbor to a point is itself (distance 0)
    distances, _ = tree.query(coords, k=2)
    nn_distances = distances[:, 1]  # Take the second column (nearest neighbor)

    # Calculate Stats
    total_signals = len(df)
    avg_spacing = np.mean(nn_distances)
    median_spacing = np.median(nn_distances)
    min_spacing = np.min(nn_distances)
    max_spacing = np.max(nn_distances)
    std_dev = np.std(nn_distances)

    # Estimate Area (Bounding Box method)
    min_x, min_y, max_x, max_y = gdf_utm.total_bounds
    area_km2 = ((max_x - min_x) * (max_y - min_y)) / 1_000_000
    density = total_signals / area_km2 if area_km2 > 0 else 0

    # Create Results Table
    stats_table = Table(title=f"Traffic Signal Analytics: {region_name}", show_lines=True)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="yellow")

    stats_table.add_row("Total Signals", f"{total_signals:,}")
    stats_table.add_row("Average Spacing", f"{avg_spacing:.2f} meters")
    stats_table.add_row("Median Spacing", f"{median_spacing:.2f} meters")
    stats_table.add_row("Min Spacing", f"{min_spacing:.2f} meters")
    stats_table.add_row("Max Spacing", f"{max_spacing:.2f} meters")
    stats_table.add_row("Spacing Std Dev", f"{std_dev:.2f} meters")
    stats_table.add_row("Estimated Region Area", f"{area_km2:.2f} km²")
    stats_table.add_row("Signal Density", f"{density:.2f} signals/km²")

    console.print("\n")
    console.print(stats_table)
    
    # Interpretation Panel
    if avg_spacing < 200:
        insight = "High density layout. Ideal for urban grid systems but may require synchronized signal timing (Green Waves) to prevent gridlock."
        color = "green"
    elif 200 <= avg_spacing < 600:
        insight = "Moderate spacing. Typical for suburban arterials. Focus should be on intersection safety and throughput."
        color = "blue"
    else:
        insight = "Low density/Isolated signals. Priority should be on high-visibility signage and advanced warning for high-speed approaches."
        color = "magenta"

    console.print(Panel(f"[bold {color}]Engineer's Insight:[/bold {color}]\n{insight}", expand=False))

    # Add Visualization for the report
    fig = px.histogram(
        nn_distances, 
        nbins=30, 
        title=f"Signal Spacing Distribution: {region_name}",
        labels={'value': 'Spacing (meters)', 'count': 'Frequency'},
        color_discrete_sequence=['#3366CC']
    )
    fig.add_vline(x=avg_spacing, line_dash="dash", line_color="red", annotation_text="Avg")
    fig.update_layout(showlegend=False)
    
    bold_color_print("\nOpening Spacing Distribution Chart...", "cyan")
    fig.show()

def main():
    try:
        input_file, region_name = csv_region_selector(purpose="to Generate Analytics Report")
    except Exception:
        return

    df = pd.read_csv(input_file)
    
    if len(df) < 2:
        bold_color_print("Error: Need at least 2 points for spacing analytics.", "red")
        return

    with console.status("[bold green]Calculating spatial analytics...[/bold green]"):
        calculate_analytics(df, region_name)

if __name__ == "__main__":
    main()
