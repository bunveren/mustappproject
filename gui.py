# gui.py
import tkinter as tk
from tkinter import ttk, messagebox

search_button = None # Define search_button as global in gui.py

def display_error_message(parent, message):
    """Displays an error message in a messagebox."""
    messagebox.showerror("Error", message, parent=parent)

def display_info_message(parent, message):
    """Displays an info message in a messagebox."""
    messagebox.showinfo("Info", message, parent=parent)

def setup_gui(root, handle_search_button_click_callback):
    """Sets up the main GUI elements and returns necessary widgets."""
    root.title("Movie Scraper")
    root.geometry("1000x700")

    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=0)
    root.rowconfigure(1, weight=0)
    root.rowconfigure(2, weight=0) # Added row for radio buttons
    root.rowconfigure(3, weight=1)
    root.rowconfigure(4, weight=0)


    label_username = tk.Label(root, text="Enter Username:", font=("Arial", 12))
    label_username.grid(row=0, column=0, padx=10, pady=10, sticky="e")

    entry_username = tk.Entry(root, width=40, font=("Arial", 12))
    entry_username.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    # Radio buttons for list type selection
    list_type_var = tk.StringVar(value="want") # Default to "Want to Watch"
    radio_want_to_watch = tk.Radiobutton(root, text="Want to Watch", variable=list_type_var, value="want", font=("Arial", 10))
    radio_want_to_watch.grid(row=2, column=0, pady=5, sticky="e")
    radio_watched = tk.Radiobutton(root, text="Watched", variable=list_type_var, value="watched", font=("Arial", 10))
    radio_watched.grid(row=2, column=1, pady=5, sticky="w")


    global search_button # Use the global search_button
    search_button = tk.Button(root, text="Search", command=lambda: handle_search_button_click_callback( # Placeholder command - will be reassigned in main.py
        entry_username, status_var, progress_bar, image_inner_frame, root, search_button, list_type_var), # Pass list_type_var
        font=("Arial", 12), bg="#4CAF50", fg="white", activebackground="#367C39", relief=tk.RAISED)
    search_button.grid(row=1, column=0, columnspan=1, pady=10, sticky="e") # Grid it here initially as well


    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="indeterminate")
    progress_bar.grid(row=1, column=1, sticky="w", padx=10)

    image_frame = tk.Frame(root)
    image_frame.grid(row=3, column=0, columnspan=2, sticky="nsew") # Row number adjusted

    canvas = tk.Canvas(image_frame)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar_vertical = ttk.Scrollbar(image_frame, orient="vertical", command=canvas.yview)
    scrollbar_vertical.pack(side="right", fill="y")
    style = ttk.Style()
    style.configure("Vertical.TScrollbar", sliderthickness=20)

    canvas.configure(yscrollcommand=scrollbar_vertical.set)

    image_inner_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=image_inner_frame, anchor="nw")
    image_inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    status_var = tk.StringVar()
    status_bar = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_bar.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=5) # Row number adjusted
    status_var.set("Ready")

    return entry_username, search_button, progress_bar, image_inner_frame, status_var, root, list_type_var # Return list_type_var

def clear_movie_frames(image_frames_list):
    """Clears all displayed movie frames."""
    for frame in image_frames_list:
        frame.destroy()
    image_frames_list.clear()