from pathlib import Path
from utils.tabulate_dir import tabulate_files
from utils.rich_tabulate import rich_tablulate
from utils.constants import csv_dir

# NEEDED


def main():
    output_dir = Path("data/traffic_csv")
    output_dir.mkdir(parents=True, exist_ok=True)

    file_paths = []

    original_data = tabulate_files(csv_dir, target_ext="csv")[0]
    rich_tablulate(original_data)

    list_of_inputs = input(
        "Enter the indices of the files to merge (comma separated): ")

    indices = list_of_inputs.split(',')
    indices = [int(idx.strip()) for idx in indices if idx.strip().isdigit()]
    file_paths = [original_data[i]
                  for i in indices if 0 <= i < len(original_data)]

    if not file_paths:
        print("No valid files selected.")
        return

    # check if all the csvs have the same columns
    first_file_columns = None
    for file_path in file_paths:
        with open(file_path, 'r') as f:
            columns = f.readline().strip().split(',')
            if first_file_columns is None:
                first_file_columns = columns
            elif first_file_columns != columns:
                print(
                    f"File {file_path} has different columns than the first file.")
                return

    print("All files have the same columns.")
    print("Selected file paths:")
    for file_path in file_paths:
        print(file_path)

    # Merge the CSV files

    merged_data = []
    for idx, file_path in enumerate(file_paths):
        with open(file_path, 'r') as f:
            lines = f.readlines()
            if idx == 0:
                merged_data.extend(line.strip() for line in lines)
            else:
                merged_data.extend(line.strip() for line in lines[1:])

    city_names = [Path(fp).stem.split('_')[0].capitalize() for fp in file_paths]
    merged_file_name = "_".join(city_names)
    output_file = output_dir / f"{merged_file_name}_traffic_signals.csv"
    with open(output_file, 'w') as f:
        for line in merged_data:
            f.write(line + '\n')

    print(
        f"Merged CSV file created at: {output_file}")


if __name__ == "__main__":
    main()
