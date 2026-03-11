from pathlib import Path
from utils.rich_tabulate import rich_tablulate
from utils.tabulate_dir import tabulate_files
from rich.console import Console
from rich.prompt import IntPrompt
from utils.constants import csv_dir

console = Console()


def csv_region_selector(file_dir=csv_dir, tar="csv", purpose=""):
    original_file = tabulate_files(file_dir, tar)[0]
    rich_tablulate(original_file)

    try:
        input_index = IntPrompt.ask(
            f"Select the index of the file {purpose}")
    except (ValueError, KeyboardInterrupt):
        console.print(
            "[bold red]No input provided or invalid input. Exiting...[/bold red]")
        return
    if input_index is None:
        console.print("[bold red]No input received. Exiting...[/bold red]")
        return
    input_file = original_file[input_index]

    # Use pathlib for clean name extraction
    file_path = Path(input_file)
    # Get the part before the first underscore and capitalize
    region_name = file_path.stem.split("_")[0].capitalize()

    return input_file, region_name


if __name__ == "__main__":
    csv_region_selector()
