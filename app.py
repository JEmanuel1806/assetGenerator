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

        self.app.iconbitmap(os.path.join("res", "images", "asset_generator.ico"))  # Icon setzen

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

        for widget in self.app.winfo_children():
            widget.destroy()

        # scroll frame containing all found models
        scroll_frame = customtkinter.CTkScrollableFrame(self.app, width=400, height=300)
        scroll_frame.grid(row=1, column=0, padx=20, pady=20, sticky="n")

        ctk_img = customtkinter.CTkImage(mod_preview, size=preview_size)
        preview_label = customtkinter.CTkLabel(self.app, image=ctk_img, text="")
        preview_label.grid(row=1, column=1, padx=20, pady=20, sticky="ns")
        preview_label.image = ctk_img

        mdl_files = asset_creator.get_files_from_directory(folder)[1]
        checkbox_value_pairs = {}

        for i, filename in enumerate(mdl_files):
            checkbox_var = customtkinter.BooleanVar(value=False)
            short_name = os.path.basename(filename)
            cb = customtkinter.CTkCheckBox(scroll_frame, text=short_name, variable=checkbox_var)
            cb.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            checkbox_value_pairs[filename] = checkbox_var

        scroll_label_amount = customtkinter.CTkLabel(self.app,
                                                     text=f"Found {len(mdl_files)} models of type "
                                                          f"{asset_creator.current_vehicle_type}.",
                                                     font=("Segoe UI", 14, "bold"))
        scroll_label_amount.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")

        create_btn = customtkinter.CTkButton(
            self.app,
            text="Create assets!",
            font=("Calibri", 14, "bold"),
            command=lambda: asset_creator.generate_assets(folder, checkbox_value_pairs)
        )
        create_btn.grid(row=2, column=1, padx=20, pady=10, sticky="e")

        reselect_btn = customtkinter.CTkButton(
            self.app,
            text="Reselect",
            font=("Calibri", 14, "bold"),
            command=self.button_folder_select
        )
        reselect_btn.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        self.app.grid_columnconfigure(0, weight=1)
        self.app.grid_columnconfigure(1, weight=1)

    # responsible for selection obv
    def button_folder_select(self):
        folder = filedialog.askdirectory()
        if not folder:
            print("No folder selected!")
        print("Selected folder:", folder)
        if asset_creator.validate_vehicle_type(folder):
            self.show_mod_preview(folder)
