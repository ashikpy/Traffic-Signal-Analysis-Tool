from scripts.polygon_downloader import download_state_polygon
from utils.constants import geojson_outline_dir
from utils.csv_region_selector import csv_region_selector

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import plotly.express as px
import os

# NEEDED


def main():
    input_file, region_name = csv_region_selector(
        purpose="to Visualize for a State")
    print(f"Selected: {region_name.title()}")

    polygon_path = download_state_polygon(region_name.title())
    if not polygon_path or not os.path.exists(polygon_path):
        print(f"[ERROR] Could not find or download polygon for {region_name}")
        return
    polygon_gdf = gpd.read_file(polygon_path)

    df = pd.read_csv(input_file)
    gdf_points = gpd.GeoDataFrame(
        df, geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])], crs="EPSG:4326")

    points_in_poly = gdf_points[gdf_points.geometry.within(
        polygon_gdf.union_all())]

    # Create the scatter plot
    fig = px.scatter_map(
        points_in_poly,
        lat=points_in_poly.geometry.y,
        lon=points_in_poly.geometry.x,
        zoom=6,
        title=f"Points within {region_name}"
    )

    # Project polygon to Web Mercator, get centroids, and back to WGS84
    projected_gdf = polygon_gdf.to_crs(epsg=3857)
    centroids = projected_gdf.geometry.centroid.to_crs(epsg=4326)

    # Add the polygon border to the figure
    fig.add_trace(
        px.line_map(
            polygon_gdf,
            lat=centroids.y,
            lon=centroids.x,
        ).data[0]
    )

    # Update the layout to use open street map and set the line properties
    fig.update_layout(
        map_style="open-street-map",
        map=dict(
            layers=[{
                "source": polygon_gdf.__geo_interface__,
                "type": "line",
                "color": "red",
                "line": {"width": 2}
            }]
        )
    )

    fig.show()


if __name__ == "__main__":
    main()
