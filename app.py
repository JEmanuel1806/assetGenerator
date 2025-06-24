import customtkinter
from customtkinter import filedialog
import os

import asset_creator
from PIL import Image


class AssetGeneratorApp:

    def __init__(self):
        self.app = customtkinter.CTk()
        self.app.title("TPF2 Asset Generator")
        self.app.geometry("720x480")
        self.folder = None

        self.init_button()
        self.app.mainloop()

    def init_button(self):
        button = customtkinter.CTkButton(self.app, text="Choose folder", command=self.button_folder_select)
        button.grid(row=0, column=0, padx=300, pady=20)

    def show_mod_preview(self, folder):
        try:
            mod_preview = Image.open(os.path.join(folder, "image_00.tga"))
            width, height = mod_preview.size
            preview_size = (width, height)

        except FileNotFoundError:
            print("Preview image not found!")
            return

        ctk_img = customtkinter.CTkImage(mod_preview, size=preview_size)
        label = customtkinter.CTkLabel(self.app, image=ctk_img, text="")
        label.grid(row=2, column=0, padx=300, pady=20)
        label.image = ctk_img

        # show all mdl
        scroll_frame = customtkinter.CTkScrollableFrame(self.app, width=300, height=200)
        scroll_frame.grid(row=0, column=0, padx=20, pady=0, sticky="nsew")

        # config for resizing
        self.app.grid_rowconfigure(0, weight=1)
        self.app.grid_columnconfigure(0, weight=1)

        mdl_files = asset_creator.get_files_from_directory(folder)[1]
        checkbox_value_pairs = {}

        for index, filename in enumerate(mdl_files):
            checkbox_boolean = customtkinter.BooleanVar(value=False)
            cb = customtkinter.CTkCheckBox(scroll_frame, text=filename, variable=checkbox_boolean)
            cb.grid(row=index, column=0, sticky="w", padx=5, pady=2)
            checkbox_value_pairs[filename] = checkbox_boolean

        # display_more_options()
        button = customtkinter.CTkButton(self.app, text="Create assets!",
                                         command=lambda: asset_creator.generate_assets(folder, checkbox_value_pairs))
        button.grid(row=0, column=0, padx=300, pady=10)

        button_reselect = customtkinter.CTkButton(self.app, text="Reselect", command=self.button_folder_select)
        button_reselect.grid(row=1, column=0, padx=300, pady=10)

    # responsible for selection obv
    def button_folder_select(self):
        folder = filedialog.askdirectory()
        if not folder:
            print("No folder selected!")
        print("Selected folder:", folder)
        if asset_creator.validate_vehicle_type(folder):
            self.show_mod_preview(folder)
