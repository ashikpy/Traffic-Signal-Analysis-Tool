# Traffic Signal Location Analysis

This project analyzes the locations of traffic signals across various regions in India using CSV and GeoJSON data. It provides tools for clustering, visualization, and data transformation to support urban planning and traffic management.

## Features

- **Data Sources:**
  - CSV and GeoJSON files for multiple Indian states and cities
- **Scripts:**
  - Clustering with DBSCAN
  - GeoJSON to CSV conversion
  - Region-based CSV selection
  - Merging CSVs
  - Polygon downloader
- **Visualization:**
  - Heatmaps
  - Cluster visualizations
  - Bounding box and lon/lat visualizers
  - State-wise visualizations
- **Utilities:**
  - Rich text and tabulation components
  - Plotly zoom center

## Directory Structure

```
main.py
requirements.txt
cache/
data/
  traffic_csv/
  traffic_geojson/
scripts/
utils/
visualization/
```

## Getting Started

1. **Install dependencies:**
   ```fish
   pip install -r requirements.txt
   ```
2. **Run main analysis:**
   ```fish
   python main.py
   ```
3. **Use scripts for data processing:**
   - Example: Convert GeoJSON to CSV
     ```fish
     python scripts/geojson_to_csv.py
     ```

## Data

- Located in `data/traffic_csv/` and `data/traffic_geojson/`
- Includes traffic signal locations for major Indian states and cities

## Visualization

- Visual outputs are generated in the `visualization/` directory
- Use provided scripts to create heatmaps, clusters, and more

## Contributing

Pull requests and suggestions are welcome. Please open an issue for major changes.

## License

MIT License
