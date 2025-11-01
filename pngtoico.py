import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk # Make sure Pillow is installed: pip install Pillow
import os
import sys
import threading
import webbrowser
import time
# Try importing ttkthemes, handle if not found
try:
    from ttkthemes import ThemedTk
    ttk_themes_available = True
except ImportError:
    ttk_themes_available = False
    ThemedTk = tk.Tk # Fallback to standard Tk

# --- Configuration ---
DEFAULT_ICON_SIZE = "32x32"
ICON_SIZES = ["16x16", "24x24", "32x32", "48x48", "64x64", "128x128", "256x256"]
DOWNLOADS_FOLDER = os.path.join(os.path.expanduser('~'), 'Downloads')
MONITOR_INTERVAL_SECONDS = 2

# --- Application Class ---
class PngToIcoConverter(ThemedTk):

    def __init__(self):
        # Initialize with theme if available
        if ttk_themes_available:
            super().__init__(theme="awbreezedark") # Or choose another theme
        else:
            super().__init__()
            print("ttkthemes not found, using default Tkinter style.")

        self.title("PNG to ICO Converter")
        self.resizable(False, False)
        try:
            # When packaged by PyInstaller with --onefile, data files are
            # extracted to a temporary folder available as sys._MEIPASS.
            # Use that path when present so the runtime can load bundled
            # resources like 'icon.ico'. If not found, fall back to
            # the working directory.
            base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
            icon_path = os.path.join(base_path, 'icon.ico')
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                # If the developer also passed --icon to PyInstaller,
                # the executable will still have an icon in Explorer.
                print('Info: icon.ico not found at runtime, skipping iconbitmap.')
        except tk.TclError as e:
            print(f"Warning: failed to set window icon: {e}")
            self.update_status("Warning: Application icon not loaded.")

        self.current_file_path = None       # Path of the originally loaded file (for naming output)
        self.loaded_pil_image = None        # <<< Store the actual PIL Image object here
        self.current_image_preview = None   # Reference to PhotoImage for display

        # --- Style ---
        self.style = ttk.Style()
        # Apply some padding/font styles even without ttkthemes
        self.style.configure('TButton', padding=6, font=('Segoe UI', 9)) # Example font
        self.style.configure('TLabel', padding=5, font=('Segoe UI', 9))
        self.style.configure('Bold.TLabel', font=('Segoe UI', 12, 'bold'))
        self.style.configure('TCombobox', padding=5, font=('Segoe UI', 9))
        self.style.configure('TCheckbutton', font=('Segoe UI', 9))
        self.style.configure('Status.TLabel', padding=3, font=('Segoe UI', 8))


        # --- UI Elements ---
        self.configure(padx=15, pady=15)

        # Title
        title_label = ttk.Label(self, text="PNG to ICO Converter", style='Bold.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="ew")

        # Preview Frame & Label
        preview_frame = ttk.Frame(self, borderwidth=1, relief=tk.SUNKEN, width=210, height=210)
        preview_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        preview_frame.grid_propagate(False)

        self.preview_label = ttk.Label(preview_frame, text="No Image Selected", anchor=tk.CENTER, compound=tk.CENTER)
        self.preview_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Select Button
        self.select_button = ttk.Button(self, text="Select PNG Image", command=self.select_image)
        self.select_button.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")

        # Size Selection
        size_label = ttk.Label(self, text="ICO Size:")
        size_label.grid(row=3, column=0, pady=5, sticky="w")

        self.size_var = tk.StringVar(value=DEFAULT_ICON_SIZE)
        # Make combobox slightly wider if needed
        self.size_dropdown = ttk.Combobox(self, textvariable=self.size_var, values=ICON_SIZES, state="readonly", width=15)
        self.size_dropdown.grid(row=3, column=1, pady=5, sticky="ew")

        # Multi-size ICO Option
        self.generate_all_sizes_var = tk.BooleanVar(value=False)
        self.generate_all_sizes_check = ttk.Checkbutton(
            self,
            text="Generate all common sizes (16x16 to 256x256)",
            variable=self.generate_all_sizes_var,
            command=self._toggle_size_dropdown_state, # New method to enable/disable dropdown
            style='TCheckbutton'
        )
        self.generate_all_sizes_check.grid(row=4, column=0, columnspan=2, pady=(5, 10), sticky="w")

        # Convert Button
        self.convert_button = ttk.Button(self, text="Convert to ICO", command=self.convert_png_to_ico, state=tk.DISABLED)
        self.convert_button.grid(row=5, column=0, columnspan=2, pady=5, sticky="ew")

        # Output Folder Selection
        output_frame = ttk.LabelFrame(self, text="Output Folder", padding=(10, 5))
        output_frame.grid(row=6, column=0, columnspan=2, pady=(10, 5), sticky="ew")

        self.output_folder_var = tk.StringVar(value=DOWNLOADS_FOLDER)
        self.output_folder_label = ttk.Label(output_frame, textvariable=self.output_folder_var, wraplength=250, anchor=tk.W)
        self.output_folder_label.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.browse_output_button = ttk.Button(output_frame, text="Browse", command=self.browse_output_folder)
        self.browse_output_button.grid(row=0, column=1, sticky="e")
        output_frame.grid_columnconfigure(0, weight=1) # Allow label to expand

        # Flaticon Button
        self.browser_button = ttk.Button(self, text="Find Icons (Flaticon)", command=self.open_browser)
        self.browser_button.grid(row=7, column=0, columnspan=2, pady=5, sticky="ew")

        # Buy Me a Coffee Button
        self.coffee_button = ttk.Button(self, text="☕ Buy Me a Coffee", command=self.open_coffee_link, style='Accent.TButton')
        self.coffee_button.grid(row=8, column=0, columnspan=2, pady=5, sticky="ew")

        # Auto-Delete Option
        self.auto_delete_var = tk.BooleanVar(value=True)
        self.auto_delete_check = ttk.Checkbutton(
            self,
            text="Delete original PNG from Downloads after loading?",
            variable=self.auto_delete_var,
            style='TCheckbutton' # Apply style if needed
        )
        self.auto_delete_check.grid(row=9, column=0, columnspan=2, pady=(10, 0), sticky="w")

        # Status Bar
        self.status_var = tk.StringVar(value="Ready.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, style='Status.TLabel')
        status_bar.grid(row=10, column=0, columnspan=2, pady=(15, 0), sticky="ew")

        # --- Start Download Monitoring ---
        # Check if downloads folder exists before starting thread
        if os.path.isdir(DOWNLOADS_FOLDER):
            self.monitor_thread = threading.Thread(target=self.monitor_downloads, daemon=True)
            self.monitor_thread.start()
        else:
            msg = f"Downloads folder not found:\n{DOWNLOADS_FOLDER}\nAutomatic loading disabled."
            self.update_status("Error: Downloads folder missing.")
            messagebox.showwarning("Setup Warning", msg)


    def update_status(self, message):
        """Safely updates the status bar text from any thread."""
        # Schedule the update on the main Tkinter thread
        self.after(0, self.status_var.set, message)
        # self.update_idletasks() # Generally not needed when using .after()

    def browse_output_folder(self):
        """Opens a directory dialog to select the output folder."""
        selected_folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self.output_folder_var.get() # Start in current selected folder
        )
        if selected_folder:
            self.output_folder_var.set(selected_folder)
            self.update_status(f"Output folder set to: {os.path.basename(selected_folder)}")
        else:
            self.update_status("Output folder selection cancelled.")

    def _toggle_size_dropdown_state(self):
        """Enables or disables the size dropdown based on the 'generate all sizes' checkbox."""
        if self.generate_all_sizes_var.get():
            self.size_dropdown.config(state=tk.DISABLED)
        else:
            self.size_dropdown.config(state="readonly")

    def select_image(self):
        """Opens a file dialog to select a PNG image."""
        file_path = filedialog.askopenfilename(
            title="Select PNG Image",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_path:
            self.process_image(file_path, source="selection") # Indicate source
        else:
            self.update_status("Image selection cancelled.")

    def process_image(self, file_path, source="manual"): # Default source
        """Loads, validates, stores, and displays the PNG image."""
        self.update_status(f"Processing {os.path.basename(file_path)}...")
        try:
            if not os.path.exists(file_path):
                 # Handle case where file disappears between detection and processing
                 raise FileNotFoundError(f"File not found during processing: {file_path}")

            # Open the image using Pillow
            image = Image.open(file_path)

            # Ensure it's actually a PNG
            if image.format != 'PNG':
                 image.close() # Close the file handle
                 raise ValueError("Selected file is not a valid PNG.")

            # --- Key Change: Store the PIL Image object ---
            # Make a copy to ensure we have our own version
            self.loaded_pil_image = image.copy()
            image.close() # Close the original file handle opened by Image.open()

            # Store the original path for output naming
            self.current_file_path = file_path

            # Create preview thumbnail *from the stored PIL image*
            preview_image = self.loaded_pil_image.copy() # Work on a copy for thumbnailing
            preview_image.thumbnail((200, 200), Image.Resampling.LANCZOS)
            self.current_image_preview = ImageTk.PhotoImage(preview_image)

            # Update UI
            self.preview_label.config(image=self.current_image_preview, text="")
            self.convert_button['state'] = tk.NORMAL
            self.update_status(f"Loaded: {os.path.basename(file_path)}")

            # --- Auto-delete logic (can now happen immediately) ---
            if source == "download" and self.auto_delete_var.get():
                # We have the image data in self.loaded_pil_image, so deleting
                # the original file now is safe for conversion.
                self.delete_downloaded_file(file_path)

        except FileNotFoundError as fnf_err:
             error_msg = f"Error: {fnf_err}"
             print(error_msg)
             self.update_status(error_msg)
             messagebox.showerror("Error", f"The file\n{file_path}\ncould not be found. It might have been moved or deleted before processing.")
             self.reset_ui() # Reset state
        except ValueError as ve:
            error_msg = f"Invalid File: {ve}"
            print(error_msg)
            self.update_status(f"Error: {ve}")
            messagebox.showerror("Invalid File", str(ve))
            self.reset_ui()
        except Exception as e:
            error_msg = f"Could not load or process the image:\n{e}"
            print(f"Image processing error: {e}")
            self.update_status(f"Error loading image: {e}")
            messagebox.showerror("Image Error", error_msg)
            self.reset_ui()


    def reset_ui(self):
        """Resets the UI and internal state when no image is loaded or an error occurs."""
        self.preview_label.config(image='', text="No Image Selected")
        self.current_image_preview = None
        self.current_file_path = None
        self.loaded_pil_image = None # <<< Clear the stored PIL image
        self.convert_button['state'] = tk.DISABLED
        self.update_status("Ready.") # Optionally reset status

    def delete_downloaded_file(self, file_path):
        """Attempts to delete the specified file from Downloads."""
        if not file_path or not file_path.startswith(DOWNLOADS_FOLDER):
             print(f"Skipping deletion for file outside Downloads: {file_path}")
             return # Safety check

        try:
            print(f"Attempting to delete: {file_path}")
            os.remove(file_path)
            self.update_status(f"Deleted original: {os.path.basename(file_path)}")
            print(f"Successfully deleted: {file_path}")
        except OSError as e:
            error_msg = f"Could not delete {os.path.basename(file_path)}:\n{e}\nCheck file permissions or if it's in use."
            self.update_status(f"Error deleting file: {e}")
            print(error_msg)
            messagebox.showwarning("Deletion Error", error_msg)
        except Exception as e:
             error_msg = f"An unexpected error occurred during deletion:\n{e}"
             self.update_status(f"Error deleting file: {e}")
             print(error_msg)
             messagebox.showwarning("Deletion Error", error_msg)

    def convert_png_to_ico(self):
        """Converts the in-memory PNG image to an ICO file."""
        # --- Key Change: Check for the loaded PIL image ---
        if not self.loaded_pil_image:
            messagebox.showwarning("No Image Data", "Please load a PNG image first.")
            self.update_status("Conversion failed: No image loaded.")
            return
        # We still need the original path for naming the output
        if not self.current_file_path:
             messagebox.showerror("Internal Error", "Cannot determine output filename.")
             self.update_status("Conversion failed: Missing original path.")
             return

        try:
            self.update_status("Converting...")
            # --- Key Change: Use the stored PIL image directly ---
            img_to_convert = self.loaded_pil_image # No need to reopen file

            # Determine sizes for ICO
            ico_sizes = []
            base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
            output_dir = self.output_folder_var.get() # Use the selected output folder
            ico_filename = ""

            if self.generate_all_sizes_var.get():
                # Generate all common sizes
                for size_str in ICON_SIZES:
                    width, height = map(int, size_str.split('x'))
                    ico_sizes.append((width, height))
                ico_filename = f"{base_name}_all_sizes.ico"
            else:
                # Generate single selected size
                size_str = self.size_var.get()
                if 'x' not in size_str:
                    raise ValueError("Invalid size format selected.")

                try:
                    width, height = map(int, size_str.split('x'))
                    if not (0 < width <= 512 and 0 < height <= 512): # Basic sanity check
                        raise ValueError("Invalid dimensions")
                except ValueError:
                    raise ValueError(f"Invalid size specified: {size_str}")
                ico_sizes.append((width, height))
                ico_filename = f"{base_name}_{width}x{height}.ico"

            ico_path = os.path.join(output_dir, ico_filename)

            # Pillow's save handles ICO creation.
            img_to_convert.save(ico_path, format='ICO', sizes=ico_sizes)

            success_msg = f"Saved: {ico_filename}"
            self.update_status(success_msg)
            messagebox.showinfo("Success", f"Image successfully converted!\nSaved as:\n{ico_path}")

        except ValueError as ve:
            error_msg = f"Conversion Error: {ve}"
            print(error_msg)
            self.update_status(error_msg)
            messagebox.showerror("Conversion Error", str(ve))
        except Exception as e:
            error_msg = f"Could not convert or save the ICO file:\n{e}"
            print(f"Conversion/Save error: {e}")
            self.update_status(f"Conversion Error: {e}")
            messagebox.showerror("Conversion Error", error_msg)


    def open_browser(self):
        """Opens Flaticon in the default web browser."""
        self.update_status("Opening Flaticon...")
        try:
            webbrowser.open("https://www.flaticon.com/")
            # Don't reset status immediately, let user see it opened
            # self.after(1500, self.update_status, "Ready.") # Optional delayed reset
        except Exception as e:
            error_msg = f"Could not open the web browser:\n{e}"
            self.update_status(f"Error opening browser: {e}")
            print(error_msg)
            messagebox.showerror("Browser Error", error_msg)

    def open_coffee_link(self):
        """Opens Buy Me a Coffee page in the default web browser."""
        self.update_status("Opening Buy Me a Coffee...")
        try:
            webbrowser.open("https://buymeacoffee.com/bariselcii")
        except Exception as e:
            error_msg = f"Could not open the web browser:\n{e}"
            self.update_status(f"Error opening browser: {e}")
            print(error_msg)
            messagebox.showerror("Browser Error", error_msg)

    # --- Download Monitoring ---
    def monitor_downloads(self):
        """Monitors the Downloads folder for new PNG files."""
        print(f"Starting download monitor for: {DOWNLOADS_FOLDER}")
        initial_scan_done = False
        existing_files = set() # Initialize empty

        while True:
            try:
                # Scan directory content
                current_content = os.listdir(DOWNLOADS_FOLDER)
                current_pngs = set(f for f in current_content if f.lower().endswith('.png') and os.path.isfile(os.path.join(DOWNLOADS_FOLDER, f)))

                if not initial_scan_done:
                    # On first run, just populate the existing files set
                    existing_files = current_pngs
                    initial_scan_done = True
                    print("Initial download scan complete.")
                else:
                    # Find newly added files
                    new_files = current_pngs - existing_files
                    if new_files:
                        # Process the first new file found alphabetically
                        # Could use modification time for 'newest' if needed, but more complex
                        newest_file_name = sorted(list(new_files))[0]
                        file_path = os.path.join(DOWNLOADS_FOLDER, newest_file_name)
                        print(f"Detected new PNG: {newest_file_name}")

                        # Schedule UI update and processing on main thread
                        # Pass source="download" to enable potential deletion
                        self.after(0, self.process_image, file_path, "download")

                        # Update the set of known files *after* scheduling processing
                        existing_files.add(newest_file_name)

                    # Optional: Check for deleted files if needed, though not required here
                    # deleted_files = existing_files - current_pngs
                    # if deleted_files:
                    #     existing_files = current_pngs # Update known files

                # Update the set for the next iteration (handles additions)
                existing_files.update(current_pngs) # Make sure known set doesn't shrink unexpectedly

            except FileNotFoundError:
                err_msg = f"Downloads folder {DOWNLOADS_FOLDER} not found or inaccessible."
                print(err_msg)
                self.update_status(f"Error: {err_msg}")
                break # Stop monitoring if folder vanishes
            except OSError as e:
                 # Permissions error, etc.
                 print(f"Error scanning Downloads folder: {e}")
                 self.update_status(f"Warning: Error scanning Downloads ({e})")
                 # Continue monitoring, might be temporary
            except Exception as e:
                print(f"Unexpected error in monitoring thread: {e}")
                # Depending on severity, might want to break or log more details
                # self.update_status("Error: Unexpected issue in monitor.")

            # Wait before checking again
            time.sleep(MONITOR_INTERVAL_SECONDS)


# --- Main Execution ---
if __name__ == "__main__":
    # Check ttkthemes availability and choose Tk class
    RootClass = ThemedTk if ttk_themes_available else tk.Tk
    app = PngToIcoConverter()
    app.mainloop()