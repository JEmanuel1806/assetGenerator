import customtkinter
import os
from customtkinter import filedialog
import re

import shutil

from PIL import Image

global current_vehicle_type  # global for now


def filter_asset_file(asset_file):
    with open(asset_file, "r") as af:
        asset_file_content = af.read()

    # Throw out metadata
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
        print("No metadata block found.")
        return

    with open(asset_file, "w") as af:
        af.write(asset_file_content)

    print("Threw out metadata for " + asset_file)


def copy_asset_files(folder):
    asset_folder = os.path.join(folder, "res", "models", "model", "asset")
    vehicle_folder = os.path.join(folder, "res", "models", "model", "vehicle")
    ignore_names = ["menu", "beladen", "fake", "gedreht", "zusatz"]

    file_paths = []
    asset_files = []

    print("Generating assets...")
    os.makedirs(asset_folder, exist_ok=True)
    for root, dirs, files in os.walk(vehicle_folder):
        for file in files:
            # make sure to ignore files and folders with name "fake", "beladen" , .. etc.
            if file.endswith(".mdl") and all(term not in root and term not in file for term in ignore_names):
                file_paths.append(os.path.join(root, file))
                shutil.copy(os.path.join(root, file), asset_folder)
    for root, dirs, files in os.walk(asset_folder):
        for file in files:
            if file.endswith(".mdl"):
                filter_asset_file(os.path.join(root, file))
                asset_files.append(file)

    return asset_files, file_paths


def create_con(folder, asset_files, mdl_paths):
    con_folder = os.path.join(folder, "res", "construction")
    con_name = f"{con_folder.split('/')[-1].split('_')[-2]}_asset.con"

    # asset file paths for con (asset/x.mdl)
    asset_file_path = []
    icon_path = []

    for asset_file_name in asset_files:
        asset_file_path.append("asset/" + asset_file_name)

    for mdl_path in mdl_paths:
        parts = os.path.normpath(mdl_path).split(os.sep)
        vehicle_index = parts.index("vehicle")
        relative_parts = parts[vehicle_index + 1:]  # only need part after "vehicle"
        relative_path = "ui/models_small/vehicle/" + "/".join(relative_parts)  # con requires forward slashes
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

    # replace the content of the template
    con_file = con_template
    con_file = con_file.replace("#model_icons", icon_block)
    con_file = con_file.replace("#model_values", asset_block)
    con_file = con_file.replace("#year_from_wagon", "1950")

    if current_vehicle_type in ["Waggon", "Train"]:
        con_file = con_file.replace("#height_params", train_wagon_block)
        con_file = con_file.replace("#get_params", "local trax = positionx.getValue(params)")
        con_file = con_file.replace("#rail_height", "if params.position == 1 then height = 1.05 end")
        con_file = con_file.replace("#asset_type", '"ASSET_TRACK"')
        con_file = con_file.replace("#categories", f'"{current_vehicle_type}"')
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


def add_script(folder):
    script_path = os.path.join(folder, "res", "scripts")
    os.makedirs(script_path, exist_ok=True)

    shutil.copy("template/parambuilder_v1_1.lua", script_path)


def generate_assets(folder):
    asset_files, mdl_paths = copy_asset_files(folder)
    con_name = create_con(folder, asset_files, mdl_paths)
    create_menu_icon(folder, con_name)
    add_script(folder)


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


def show_mod_preview(folder):
    try:
        mod_preview = Image.open(os.path.join(folder, "image_00.tga"))
        preview_size = mod_preview.size * 3
    except FileNotFoundError:
        print("Preview image not found!")
        return

    ctk_img = customtkinter.CTkImage(mod_preview, size=preview_size)
    label = customtkinter.CTkLabel(app, image=ctk_img, text="")
    label.grid(row=2, column=0, padx=300, pady=20)
    label.image = ctk_img

    # show all mdl

    scroll_frame = customtkinter.CTkScrollableFrame(app, width=300, height=200)
    scroll_frame.grid(row=0, column=0, padx=20, pady=0, sticky="nsew")

    # Konfiguration für resizing
    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)

    mdl_files = [folder]
    checkbox_vars = {}

    for i, filename in enumerate(mdl_files):
        var = customtkinter.BooleanVar(value=False)
        cb = customtkinter.CTkCheckBox(scroll_frame, text=filename, variable=var)
        cb.grid(row=i, column=0, sticky="w", padx=5, pady=2)
        checkbox_vars[filename] = var

    # display_more_options()
    button = customtkinter.CTkButton(app, text="Create assets!", command=lambda: generate_assets(folder))
    button.grid(row=0, column=0, padx=300, pady=10)

    button_reselect = customtkinter.CTkButton(app, text="Reselect", command=button_folder_select)
    button_reselect.grid(row=1, column=0, padx=300, pady=10)


def button_folder_select():
    folder = filedialog.askdirectory()
    if not folder:
        print("No folder selected!")
    print("Selected folder:", folder)
    if validate_vehicle_type(folder):
        show_mod_preview(folder)


def create_ui(app):
    app.title("TPF2 Asset Generator")
    app.geometry("720x480")
    button = customtkinter.CTkButton(app, text="Choose folder", command=button_folder_select,
                                     font=("Segoe UI", 14, "bold"))
    button.grid(row=0, column=0, padx=300, pady=20)


# MAIN
app = customtkinter.CTk()
create_ui(app)
app.mainloop()
