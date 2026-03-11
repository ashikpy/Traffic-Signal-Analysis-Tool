from rich.console import Console
from rich.prompt import IntPrompt
from scripts import (
    get_traffic_geojson_by_name,
    geojson_to_csv,
    merge_csvs,
    signal_analytics_report,
    network_topology_analysis,
    signal_gap_analysis,
)

from utils.rich_components import bold_color_print, numbered_list_panel, print_panel, line_title, box_text
from visualization import (
    lon_lat_visualizer,
    dbscan_cluster_visualizer,
    heatmap_maker,
    visualize_states,
    voronoi_visualizer,
    corridor_visualizer
)


available_scripts = [
    ("Get GeoJSON by name", get_traffic_geojson_by_name.main),
    ("Convert GeoJSON to CSV", geojson_to_csv.main),
    ("Merge CSVs", merge_csvs.main),
    ("Signal Analytics Report", signal_analytics_report.main),
    ("Network Topology Analysis", network_topology_analysis.main),
    ("Signal Placement Suggestion (Gap Analysis)", signal_gap_analysis.main),
]


available_visualizations = [
    ("Visualize Scatter Plot", lon_lat_visualizer.main),
    ("Visualize Heatmap", heatmap_maker.main),
    ("Visualize Clusters with DBSCAN",
     dbscan_cluster_visualizer.main),
    ("Visualize States", visualize_states.main),
    ("Visualize Influence Map (Voronoi)", voronoi_visualizer.main),
    ("Visualize Signal Corridors", corridor_visualizer.main),
]


console = Console()


def main():
    try:
        while True:
            print_panel("Welcome to Traffic Data Analysis Tool")

            # Display Available Scripts
            script_list_text = numbered_list_panel(available_scripts, "green")
            box_text(script_list_text, "Available Scripts", "green")

            # Display Available Visualizations
            offset = len(available_scripts)
            viz_list_text = numbered_list_panel(
                available_visualizations, "cyan", start=offset + 1)
            box_text(viz_list_text, "Available Visualizations", "cyan")

            # Combine all into a single list for easier lookup
            all_actions = available_scripts + available_visualizations
            total_options = len(all_actions)

            # Prompt for User Input
            bold_color_print(
                f"Enter 1-{total_options} to run an action, or 0/any other key to exit.", "magenta")
            
            try:
                choice = IntPrompt.ask("[bold yellow]Select an option[/bold yellow]", default=0)
            except Exception:
                choice = 0

            if choice == 0 or choice > total_options:
                bold_color_print("Exiting...\n", "red")
                break

            # Execute selection
            name, func = all_actions[choice - 1]
            action_type = "Script" if choice <= offset else "Visualization"
            
            print("")
            line_title(f"Running {action_type}: {name}")
            print("")
            
            try:
                func()
            except Exception as e:
                bold_color_print(f"Error running {name}: {e}", "red")
            
            print("") # Spacer
            
    except KeyboardInterrupt:
        bold_color_print("\nInterrupted. Exiting", "red")


if __name__ == "__main__":
    main()
