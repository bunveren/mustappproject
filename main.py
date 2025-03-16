# main.py (modified to add GUI close event handling and movie list type selection)
import tkinter as tk
from queue import Queue
import threading
import time
import concurrent.futures

import gui
import scraper
import image_loader

num_movies_found = 0
image_frames = image_loader.image_frames_global # Use the global list from image_loader
root = None # Declare root globally so on_gui_close can access it
image_loading_thread_pool = image_loader.image_loading_thread_pool # Access the thread pool from image_loader

def handle_search_button_click(entry_username, status_var, progress_bar, image_frame_widget, root_window, search_button, list_type_var): # Added list_type_var
    """Handles the event when the search button is clicked."""
    username = entry_username.get()
    if not username:
        gui.display_info_message(root_window, "Please enter a username!")
        return

    search_button.config(state=tk.DISABLED)
    gui.clear_movie_frames(image_frames) # Pass image_frames list
    progress_bar.start()
    status_var.set("Searching...")
    global num_movies_found
    num_movies_found = 0
    movie_queue = Queue()
    list_type = list_type_var.get() # Get selected list type from GUI
    threading.Thread(target=perform_search, # Changed to perform_search for clarity
                     args=(username, movie_queue, status_var, progress_bar, search_button, root_window, list_type), # Pass list_type
                     daemon=True).start()
    threading.Thread(target=display_movie_from_queue, args=(movie_queue, image_frame_widget, status_var, root_window), daemon=True).start()


def perform_search(username, movie_queue, status_var, progress_bar, search_button, root_window, list_type): # Added list_type
    """Performs the movie search based on username and list type.""" # Renamed from process_movies_and_display to perform_search for clarity
    start_time = time.time()
    try:
        movies = scraper.fetch_movie_data(username, list_type=list_type) # Call scraper with list_type
        print(f"Fetched movies count ({list_type}): {len(movies) if movies else 0}") # Debug print with list_type

        if movies is None:
            root_window.after(0, lambda: gui.display_error_message(root_window, "Could not fetch movies. Please check console for details."))
            root_window.after(0, lambda: status_var.set("Search Error."))
        elif not movies:
            root_window.after(0, lambda: gui.display_info_message(root_window, f"No movies found for this user's '{list_type}' list or there was an error.")) # Updated message
            root_window.after(0, lambda: status_var.set("No movies found."))
        else:
            global num_movies_found
            num_movies_found = len(movies)
            movies_queued_count = 0 # Counter for movies added to queue
            for movie in movies:
                 if movie and isinstance(movie, dict) and 'title' in movie:
                     movie_queue.put(movie)
                     movies_queued_count += 1
                 else:
                     print(f"Skipping invalid movie data: {movie}")
            print(f"Movies queued count: {movies_queued_count}") # Debug print
            print(f"Queue size after enqueueing: {movie_queue.qsize()}") # Debug print

            movie_queue.put(None)
            root_window.after(0, lambda: status_var.set(f"Found {len(movies)} movies in '{list_type}' list.  Displaying...")) # Updated status message

    except Exception as e:
        root_window.after(0, lambda: gui.display_error_message(root_window, f"An error occurred: {e}"))
        root_window.after(0, lambda: status_var.set(f"Error: {e}"))
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        root_window.after(0, lambda: root_window.title(f"Movie Scraper (Search time: {elapsed_time:.2f} seconds)"))
        root_window.after(0, lambda: progress_bar.stop())
        root_window.after(0, lambda: search_button.config(state=tk.NORMAL))

def display_movie_from_queue(movie_queue, image_frame_widget, status_var, root_window):
    """Processes movies from the queue and displays them."""
    index = 0
    movies_displayed_count = 0 # Counter for movies displayed
    while True:
        movie = movie_queue.get()
        if movie is None:
            print("Queue processing finished (None received).") # Debug print
            break
        print(f"Dequeued movie: {movie['title'] if movie else None}") # Debug print
        image_loader.add_movie_to_display(movie, index, image_frame_widget, root_window) # Pass root_window
        movies_displayed_count += 1
        index += 1
    print(f"Movies displayed count: {movies_displayed_count}") # Debug print
    root.after(0, lambda: status_var.set(f"Display complete. {num_movies_found} movies displayed."))

def on_gui_close():
    """Handles GUI close event: shutdown thread pool and destroy root."""
    print("GUI close event detected. Shutting down thread pool...")
    image_loading_thread_pool.shutdown(wait=False) # Or wait=True if you want to wait for threads to finish, but wait=False is usually fine for image loading
    print("Thread pool shutdown initiated.")
    global root
    if root:
        root.destroy()
        print("GUI root window destroyed.")
    print("Application terminated.")

if __name__ == "__main__":
    root = tk.Tk()
    entry_username, search_button, progress_bar, image_inner_frame, status_var, root_window, list_type_var = gui.setup_gui(root, handle_search_button_click) # Get list_type_var
    root = root_window # Assign the root_window to the global root

    # Modify the lambda in gui.py to pass search_button and list_type_var
    gui.search_button = tk.Button(root, text="Search", command=lambda: handle_search_button_click( # Reassign gui.search_button with corrected command
        entry_username, status_var, progress_bar, image_inner_frame, root, search_button, list_type_var), # Pass list_type_var here
        font=("Arial", 12), bg="#4CAF50", fg="white", activebackground="#367C39", relief=tk.RAISED)
    gui.search_button.grid(row=1, column=0, columnspan=1, pady=10, sticky="e") # Re-grid it

    root.protocol("WM_DELETE_WINDOW", on_gui_close) # Bind close event handler

    root.mainloop()