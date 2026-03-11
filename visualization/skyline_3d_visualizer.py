import pandas as pd
import plotly.graph_objects as go
import numpy as np
from utils.csv_region_selector import csv_region_selector
from utils.rich_components import bold_color_print
from rich.console import Console

console = Console()

def main():
    try:
        input_file, region_name = csv_region_selector(purpose="to Generate 3D Strategic Skyline")
    except Exception:
        return

    df = pd.read_csv(input_file)
    
    # Check if we have the criticality data from the Road Context Analysis
    if 'criticality_score' not in df.columns:
        bold_color_print("Missing 'criticality_score' column.", "yellow")
        console.print("[dim]Note: Please run 'Road Context & Criticality Analysis' first to enrich your CSV data.[/dim]")
        
        # Fallback: Just use density or a uniform height for now? 
        # No, let's suggest the user run the other tool, or we can use a basic '1' as height.
        # Better: let's use spacing as an inverse metric? No, let's keep it strictly for Strategic Importance.
        return

    with console.status("[bold cyan]Building 3D Strategic Skyline...[/bold cyan]"):
        fig = go.Figure()

        # 1. Add the "Base" - Points on the floor (Z=0)
        fig.add_trace(go.Scatter3d(
            x=df['lon'],
            y=df['lat'],
            z=np.zeros(len(df)),
            mode='markers',
            marker=dict(size=2, color='gray', opacity=0.3),
            name='Signal Location (Ground)',
            hoverinfo='none'
        ))

        # 2. Add the "Pillars" - We draw a line for each signal from 0 to criticality
        # For efficiency in Plotly 3D, we can combine all into one trace using None to break lines
        x_lines = []
        y_lines = []
        z_lines = []
        
        for idx, row in df.iterrows():
            x_lines.extend([row['lon'], row['lon'], None])
            y_lines.extend([row['lat'], row['lat'], None])
            z_lines.extend([0, row['criticality_score'], None])

        fig.add_trace(go.Scatter3d(
            x=x_lines,
            y=y_lines,
            z=z_lines,
            mode='lines',
            line=dict(color='red', width=4),
            name='Criticality Pillar',
            opacity=0.6,
            hoverinfo='none'
        ))

        # 3. Add the "Peaks" - Markers at the top of the pillars
        fig.add_trace(go.Scatter3d(
            x=df['lon'],
            y=df['lat'],
            z=df['criticality_score'],
            mode='markers',
            marker=dict(
                size=5,
                color=df['criticality_score'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Importance")
            ),
            text=df['road_type'] if 'road_type' in df.columns else None,
            hovertemplate="<b>Road Style:</b> %{text}<br>" +
                          "<b>Strategic Score:</b> %{z}<br>" +
                          "<extra></extra>",
            name='Strategic Peak'
        ))

        # 4. Styling
        fig.update_layout(
            title=f"3D Strategic Skyline: {region_name}",
            template="plotly_dark",
            scene=dict(
                xaxis=dict(title='Longitude', showbackground=False),
                yaxis=dict(title='Latitude', showbackground=False),
                zaxis=dict(title='Criticality (Strategic Depth)', range=[0, 12]),
                aspectmode='manual',
                aspectratio=dict(x=1, y=1, z=0.5) # Squash the height slightly for better feel
            ),
            margin=dict(r=0, l=0, b=0, t=50)
        )

    fig.show()

if __name__ == "__main__":
    main()
