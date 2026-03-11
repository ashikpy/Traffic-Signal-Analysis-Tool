import os
from pathlib import Path
import geopandas as gpd
from rich import print
from utils.tabulate_dir import tabulate_files
from utils.rich_tabulate import rich_tablulate
from utils.constants import csv_dir, geojson_dir
from utils.rich_components import bold_color_print, bold_input


def convert_geojson_to_csv(geojson_path, csv_dir):
    # Load GeoJSON data
    gdf = gpd.read_file(geojson_path)

    # Use pathlib for clean filename extraction
    file_path = Path(geojson_path)
    file_name = file_path.stem

    # Extract longitude and latitude
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    # Export to CSV
    output_path = Path(csv_dir) / f"{file_name}.csv"
    gdf[["lat", "lon"]].to_csv(output_path, index=False)

    return f"Conversion complete: {geojson_path} to {output_path}"


def main():

    target_ext = csv_dir
    # Check if these directories exist
    try:
        os.makedirs(geojson_dir, exist_ok=True)
        os.makedirs(target_ext, exist_ok=True)
    except Exception as e:
        print(f"Error creating directories: {e}")
        return

    # Tabulate the files in the directory
    orignal_list = tabulate_files(geojson_dir, "geojson")[0]

    if not orignal_list:
        bold_color_print("No GeoJSON files found in the directory.", "red")
        return
    else:
        rich_tablulate(orignal_list)

    try:
        index = int(bold_input(
            "Enter the index of the GeoJSON file to convert (N to cancel)"))
        if index < 0 or index >= len(orignal_list):
            raise IndexError("Index out of range.")
        geojson_path = orignal_list[index]
        bold_color_print(f"Selected file: {geojson_path}", "blue")
        file_name = Path(geojson_path).stem
        verification = bold_input(
            f"Your CSV will be saved as [italic]{file_name}.csv[/italic]. Proceed? (Y/N)", color="magenta"
        ).strip().upper()
        if verification != 'Y':
            bold_color_print("Conversion cancelled.", "red")
            return
        else:
            result = convert_geojson_to_csv(geojson_path, target_ext)
            bold_color_print(result, "green")
    except (ValueError, IndexError) as e:
        bold_color_print(f"Invalid input: {e}", "red")
        return


if __name__ == "__main__":
    main()
