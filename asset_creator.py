import os
import re

import shutil

global current_vehicle_type


# throw out the metadata and other unnecessary garbage
# first we throw out the metdata block
# then we filter out blocks inside the children that contain lights or other objects
# that are not supposed to exist with assets (lights, end lights or other stuff)
def filter_asset_file(asset_file):
    with open(asset_file, "r") as af:
        asset_file_content = af.read()

    # throw out metadata
    pattern = re.compile(r'metadata\s*=\s*\{', re.DOTALL)
    match = pattern.search(asset_file_content)

    start_index = match.end()
    stack = 1
    end_index = start_index

    # to properly remove parenthisisisisis from the mdl .. uagh
    while stack > 0 and end_index < len(asset_file_content):
        if asset_file_content[end_index] == '{':
            stack += 1
        elif asset_file_content[end_index] == '}':
            stack -= 1
        end_index += 1

    metadata_content = asset_file_content[start_index:end_index - 1].strip()

    if metadata_content:
        asset_file_content = asset_file_content.replace(metadata_content, "")
    if not match:
        return

    # filter out ligths etc..
    # basic idea is to reconstruct the file by just leaving out blocks inside the children blocks,
    # which contain stuff like lights, zugschluss, etc. that shouldnt appear with assets
    # the user can specify the things he would like to ignore or filter out
    # some default values are already locked in
    lines = asset_file_content.splitlines(keepends=True)
    result_content = []
    forbidden_terms = ["zugschluss", "panto_up", "zugschlussleuchte", "licht_rot", "licht_weiss"]

    in_block = False
    nesting_level = 0
    in_subblock = False
    sub_nesting = 0
    block_lines = []

    for line in lines:
        line_s = line.strip()

        if not in_block and line_s.startswith("children"):
            in_block = True
            nesting_level = line_s.count("{") - line_s.count("}")
            result_content.append(line)
            continue

        if in_block:
            nesting_level += line_s.count("{") - line_s.count("}")

            if not in_subblock and "{" in line_s:
                in_subblock = True
                block_lines = []
                sub_nesting = 0

            if in_subblock:
                sub_nesting += line_s.count("{")
                sub_nesting -= line_s.count("}")
                block_lines.append(line)

                if sub_nesting == 0:
                    in_subblock = False
                    full_block = ''.join(block_lines).lower()

                    if any(term in full_block for term in forbidden_terms):
                        pass

                    else:
                        result_content.extend(block_lines)
                    block_lines = []

            if nesting_level == 0:
                result_content.append(
                    line)  # not 100% why this is needed, but otherwise the last parenthesis goes missing
                in_block = False

        else:
            result_content.append(line)

    with open(asset_file, "w", encoding="utf-8") as af:
        af.write(''.join(result_content))

    print("Threw out metadata for " + asset_file)


def get_files_from_directory(folder):
    vehicle_folder = os.path.join(folder, "res", "models", "model", "vehicle")
    ignore_terms = ["menu", "menue", "menu", "beladen", "fake", "gedreht", "zusatz", "group", "deko", "tafel", "load"]

    full_path_vehicle_files = []
    vehicle_files = []

    for root, dirs, files in os.walk(vehicle_folder):
        for file in files:

            if file.endswith(".mdl") and all(
                    term.lower() not in root.lower() and term.lower() not in file.lower() for term in ignore_terms):
                full_path_vehicle_files.append(os.path.join(root, file))
                vehicle_files.append(file)

    number_of_files = len(vehicle_files)
    print(f"Found {number_of_files} models.")

    return vehicle_files, full_path_vehicle_files


def copy_asset_files(folder, selected_files):
    asset_folder = os.path.join(folder, "res", "models", "model", "asset")

    file_paths = []
    asset_files = []

    print("Generating assets...")

    os.makedirs(asset_folder, exist_ok=True)
    for file in selected_files:
        shutil.copy(file, asset_folder)
        file_paths.append(file)

    for root, dirs, files in os.walk(asset_folder):
        for file in files:
            if file.endswith(".mdl"):
                filter_asset_file(os.path.join(root, file))
                asset_files.append(file)

    return asset_files, file_paths


# replace the content of the template con file with the acquired info
# ui preview
# mdl files
# and some smaller parameter
def create_con(folder, asset_files, mdl_paths):
    con_folder = os.path.join(folder, "res", "construction")
    con_name = f"{con_folder.split('/')[-1].split('_')[-2]}_asset.con"

    asset_file_path = []
    icon_path = []

    for asset_file_name in asset_files:
        asset_file_path.append("asset/" + asset_file_name)

    for mdl_path in mdl_paths:
        parts = os.path.normpath(mdl_path).split(os.sep)
        vehicle_index = parts.index("vehicle")
        relative_parts = parts[vehicle_index + 1:]  # get relative path of mdl file (waggon/..)
        relative_path = "ui/models_small/vehicle/" + "/".join(relative_parts)
        relative_path = relative_path.replace(".mdl", "@2x.tga")
        icon_path.append(relative_path)

    os.makedirs(con_folder, exist_ok=True)

    icon_block = '\n\t"' + '",\n\t"'.join(icon_path) + '"\n'
    asset_block = '\n\t"' + '",\n\t"'.join(asset_file_path) + '"\n'

    with open("template/conTemplate.lua", "r") as ct:
        con_template = ct.read()

    train_wagon_block = """\
                    {
                    key = "position",
                    name = _("height"),
                    uiType = "BUTTON",
                    values = { _("ground"), _("rail") },
                    tooltip = _("height_tooltip"),
                    defaultIndex = 1,
                    },
                    positionx.params,
                    assetmodel.params,
                    """

    con_file = con_template
    con_file = con_file.replace("#model_icons", icon_block)
    con_file = con_file.replace("#model_values", asset_block)
    con_file = con_file.replace("#year_from_wagon", "1950")

    # for waggons and trains we want 2 height options (track, ground)
    if current_vehicle_type in ["Waggon", "Train"]:
        con_file = con_file.replace("#height_params", train_wagon_block)
        con_file = con_file.replace("#get_params", "local trax = positionx.getValue(params)")
        con_file = con_file.replace("#rail_height", "if params.position == 1 then height = 1.05 end")
        con_file = con_file.replace("#asset_type", '"ASSET_TRACK"')
        con_file = con_file.replace("#categories", f'"{current_vehicle_type}"')
    # for the rest we dont need that
    else:
        con_file = con_file.replace("#height_params", "assetmodel.params,")
        con_file = con_file.replace("#get_params", "local trax = 0")
        con_file = con_file.replace("#rail_height", "")
        con_file = con_file.replace("#asset_type", '"ASSET_DEFAULT"')
        con_file = con_file.replace("#categories", f'"{current_vehicle_type}"')

    with open(os.path.join(con_folder, con_name), 'w') as con:
        con.write(con_file)

    return con_name


def create_menu_icon(folder, con_name):
    asset_ui_path = os.path.join(folder, "res", "textures", "ui", "construction")
    os.makedirs(asset_ui_path, exist_ok=True)

    con_name = con_name.replace(".con", "")

    mod_name = os.path.basename(folder)
    shutil.copy(os.path.join(folder, "image_00.tga"), os.path.join(asset_ui_path, f"{con_name}.tga"))


# responsible for copying the mandatory script into every folder we need
# without this we will generously crash
def add_script(folder):
    script_path = os.path.join(folder, "res", "scripts")
    os.makedirs(script_path, exist_ok=True)

    shutil.copy("template/parambuilder_v1_1.lua", script_path)


def generate_assets(folder, checkbox_value_pairs):
    selected_files = []

    # only consider checked mdl files please
    for file, boolean_val in checkbox_value_pairs.items():
        if boolean_val.get():
            selected_files.append(file)

    asset_files, mdl_paths = copy_asset_files(folder, selected_files)
    con_name = create_con(folder, asset_files, mdl_paths)
    create_menu_icon(folder, con_name)
    add_script(folder)


# detect the type of vehicle thats being processed
# important for later processing and distinction
# if no vehicle is found, what are folder are you even using?
def validate_vehicle_type(folder):
    required_file = "mod.lua"
    vehicle_paths = {
        "Waggon": os.path.join("res", "models", "model", "vehicle", "waggon"),
        "Train": os.path.join("res", "models", "model", "vehicle", "train"),
        "Truck": os.path.join("res", "models", "model", "vehicle", "truck"),
        "Bus": os.path.join("res", "models", "model", "vehicle", "bus"),
        "Car": os.path.join("res", "models", "model", "vehicle", "car"),
        "Ship": os.path.join("res", "models", "model", "vehicle", "ship"),
        "Plane": os.path.join("res", "models", "model", "vehicle", "plane"),
    }

    if not os.path.isfile(os.path.join(folder, required_file)):
        print("No mod.lua found. Correct folder?")
        return False

    for vehicle_type, vehicle_path in vehicle_paths.items():
        full_path = os.path.join(folder, vehicle_path)
        if os.path.isdir(full_path):
            print("Vehicle type:", vehicle_type)
            global current_vehicle_type
            current_vehicle_type = vehicle_type
            return True

    print("Not a supported mod type.")
    return False
