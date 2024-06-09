import os
import re
import tkinter as tk
from tkinter.filedialog import askdirectory
from collections import defaultdict


def load_files(origin_path):
    origin_path_waggon = os.path.join(origin_path, "res/models/model/vehicle/waggon/")
    final_path = os.path.join(origin_path, "res/models/model/asset/")
    con_path = os.path.join(origin_path, "res/construction/")

    roots = defaultdict(list)

    ignore_names = ["menu", "beladen", "fake", "gedreht", "zusatz"]

    # Create directories for assets and construction
    os.makedirs(final_path, exist_ok=True)
    os.makedirs(con_path, exist_ok=True)

    # Function to check if a file name contains any word from ignore_names
    def should_ignore(file_name, ignore_list):
        return any(word in file_name for word in ignore_list)

    # Iterate over all directories in waggon
    for root, dirs, files in os.walk(origin_path_waggon):
        for file in files:
            if not should_ignore(file, ignore_names):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding="utf-8", errors="ignore") as current_file:
                    content = current_file.read()
                    processed_content = process_files(content)

                # if metadata is empty, file is prob. not a waggon
                if processed_content is None:
                    continue

                target_file_path = os.path.join(final_path, file)
                with open(target_file_path, 'w', encoding="utf-8") as target_file:
                    target_file.write(processed_content)
                    roots[root].append(file)

    # Create Con file
    con_file_name = f"{origin_path.split('/')[-1].split('_')[-2]}_asset.con"
    con_file_path = os.path.join(con_path, con_file_name)
    with open(con_file_path, 'w', encoding="utf-8") as con_file:
        con_file.write(create_con(origin_path_waggon, roots))


def process_files(content):
    pattern = re.compile(r'metadata\s*=\s*\{', re.DOTALL)
    match = pattern.search(content)

    if not match:
        print("No matches found.")
        return content

    start_index = match.end()
    stack = 1
    end_index = start_index

    while stack > 0 and end_index < len(content):
        if content[end_index] == '{':
            stack += 1
        elif content[end_index] == '}':
            stack -= 1
        end_index += 1

    metadata_content = content[start_index:end_index - 1].strip()

    if metadata_content:
        processed_content = content.replace(metadata_content, "")
        return processed_content
    else:
        print("No content found within metadata. Skipping to the next file.")
        return None


def filter_zugschluss(content):
    beginning = """
        {
            materials = { "vehicle/waggon/modwerkstatt_basis/zugschlussSNCF90s.mtl", },
            mesh = "vehicle/waggon/modwerkstatt_basis/zugschluss/zugschlussSNCF90s_lod0.msh",
            name = "zugschluss_sncf",
            transf = { 0.99999928474426, -1.3430874332698e-06, -0, 0, 1.3430692433758e-06, 0.99998581409454, 0.005235958378762, 0, -7.0323533662986e-09, -0.0052359574474394, 0.99998563528061, 0, -6.8299999237061, 0.83999997377396, 1.210000038147, 1, },
        },
        {
            materials = { "vehicle/waggon/modwerkstatt_basis/zugschlussSNCF90sLicht.mtl", },
            mesh = "vehicle/waggon/modwerkstatt_basis/zugschluss/zugschlussSNCFLicht90s_lod0.msh",
            name = "zugschluss_sncf_licht",
            transf = { 0.99999928474426, -1.3430874332698e-06, -0, 0, 1.3430692433758e-06, 0.99998581409454, 0.005235958378762, 0, -7.0323533662986e-09, -0.0052359574474394, 0.99998563528061, 0, -6.8299999237061, -0.83999997377396, 1.210000038147, 1, },
        },
    """

    return content.replace(beginning, "")


def create_con(path, roots):
    with open("conTemplate.con", 'r') as con_template:
        content = con_template.read()

    icon_names = []
    model_names = []

    for root_path, filenames in roots.items():
        if isinstance(root_path, str) and isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    # Create icon path
                    relative_path = os.path.relpath(root_path, path)
                    icon_path = os.path.join("ui/models_20/vehicle/waggon", relative_path,
                                             filename.replace(".mdl", "") + "@2x.tga")
                    # Replace backslashes with forward slashes
                    icon_path = icon_path.replace("\\", "/")

                    # Create model path
                    model_path = os.path.join("asset", filename)
                    model_path = model_path.replace("\\", "/")

                    # Append paths to lists
                    icon_names.append(f"\"{icon_path}\",\n\t\t\t\t\t\t")
                    model_names.append(f"\"{model_path}\",\n\t\t\t\t\t\t")
                else:
                    print(f"Skipping non-string filename: {filename}")
        else:
            print(f"Skipping non-string root_path or non-list filenames: {root_path}, {filenames}")

    if icon_names and model_names:
        content = content.replace("#model_icons", "".join(icon_names))
        content = content.replace("#model_values", "".join(model_names))

    content = content.replace("#year_from_wagon,", "1970,")

    return content


if __name__ == '__main__':
    # Hide the main Tkinter window
    root = tk.Tk()
    root.withdraw()

    # Choose mod directory
    given_path = askdirectory(title="Select the directory containing the original mdl files")
    if given_path.split("/")[-2] != "staging_area":
        print("Select a valid path in staging area.")
        print(given_path)
    elif given_path:
        try:
            load_files(given_path)
            print("Processing complete.")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("No directory selected.")
