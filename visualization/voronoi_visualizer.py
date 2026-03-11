import pandas as pd
import geopandas as gpd
from shapely.ops import voronoi_diagram
from shapely.geometry import MultiPoint, box
import plotly.express as px
import plotly.graph_objects as go
from utils.csv_region_selector import csv_region_selector
from utils.zoom_center_plotly import zoom_center
from rich.console import Console
import numpy as np

console = Console()

def main():
    input_file, region_name = csv_region_selector(purpose="to Visualize Catchment Areas (Voronoi)")
    
    df = pd.read_csv(input_file)
    if len(df) < 3:
        console.print("[red]Error: Need at least 3 points to generate a Voronoi diagram.[/red]")
        return

    with console.status("[bold green]Generating Voronoi Catchment Areas...[/bold green]"):
        # 1. Prepare points
        points = MultiPoint(list(zip(df['lon'], df['lat'])))
        
        # 2. Generate Voronoi
        # We need a slightly larger bounding box to avoid clipping issues
        mask = box(*points.bounds).buffer(0.1)
        regions = voronoi_diagram(points, envelope=mask)
        
        # 3. Create a GeoDataFrame for the regions
        voronoi_polygons = []
        for poly in regions.geoms:
            voronoi_polygons.append(poly)
            
        gdf_voronoi = gpd.GeoDataFrame(geometry=voronoi_polygons, crs="EPSG:4326")
        
        # 4. Clip to Bounding Box of points for cleaner look
        bbox = box(*points.bounds)
        gdf_voronoi = gdf_voronoi.clip(bbox)
        
        # 5. Spatial Join to associate each polygon with its signal ID (if exists)
        points_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
        gdf_voronoi = gpd.sjoin(gdf_voronoi, points_gdf, how="left", predicate="contains")
        
        # 6. Calculate Area (in km2) for color-coding
        # Projection to UTM for accurate area
        utm_crs = gdf_voronoi.estimate_utm_crs()
        gdf_voronoi['area_km2'] = gdf_voronoi.to_crs(utm_crs).area / 1_000_000
        
        # Create a "Density Score" (Inverse of area - smaller area = higher density)
        gdf_voronoi['density_score'] = 1 / (gdf_voronoi['area_km2'] + 1e-9)
        gdf_voronoi['log_density'] = np.log10(gdf_voronoi['density_score'])

    zoom, center = zoom_center(df['lon'].tolist(), df['lat'].tolist())

    fig = px.choropleth_map(
        gdf_voronoi,
        geojson=gdf_voronoi.__geo_interface__,
        locations=gdf_voronoi.index,
        color='log_density',
        color_continuous_scale="Viridis",
        opacity=0.5,
        center=center,
        zoom=zoom,
        map_style="open-street-map",
        title=f"Signal Catchment Areas: {region_name} (Color by Density)",
        hover_data=['area_km2']
    )

    # Add the points on top
    fig.add_trace(go.Scattermap(
        lat=df['lat'],
        lon=df['lon'],
        mode='markers',
        marker=dict(size=4, color='white', opacity=0.8),
        name='Traffic Signals',
        text=df['id'] if 'id' in df.columns else None
    ))

    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        coloraxis_colorbar=dict(
            title="Density Log",
            ticksuffix="",
            showticklabels=True
        )
    )

    fig.show()

if __name__ == "__main__":
    main()
