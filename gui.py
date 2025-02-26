import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import time
import threading
from tkinter import ttk  # For Progress Bar
from PIL import Image, ImageTk  # For image display
import io
import requests
from queue import Queue
import main as m

MAX_IMAGE_WIDTH = 150  # Reduce image size further
MAX_IMAGE_HEIGHT = 200

def on_search_button_click():
    """Handles the search button click event in a separate thread to prevent UI freezing."""
    username = entry_username.get()
    if not username:
        messagebox.showwarning("Input Error", "Please enter a username!")
        return

    # Disable the button while searching
    search_button.config(state=tk.DISABLED)
    text_result.delete(1.0, tk.END)  # Clear previous results
    clear_image_frames() # clear previous posters
    progress_bar.start()  # Start the progress bar
    status_var.set("Searching...") # Update status bar
    num_movies_found = 0 # initialize number of movies
    # Start the search in a separate thread
    movie_queue = Queue() # thread safe queue to pass movies
    threading.Thread(target=perform_search, args=(username, movie_queue), daemon=True).start()

    # Start consumer thread to add movies to the display
    threading.Thread(target=process_movie_queue, args=(movie_queue,), daemon=True).start()

def perform_search(username, movie_queue):
    """Performs the actual search and puts movies in the queue."""
    start_time = time.time()

    try:
        movies = m.get_user_want_to_watch_movies_from_webpage(username)
        if not movies:
            root.after(0, lambda: messagebox.showinfo("No Movies Found", "No movies found or there was an error!"))  # use root.after for thread safety
            root.after(0, lambda: status_var.set("No movies found.")) # update status bar
        else:
            global num_movies_found
            num_movies_found = len(movies)
            for movie in movies:
                 if movie and isinstance(movie, dict) and 'title' in movie:
                     movie_queue.put(movie) # put movie data in the queue
                 else:
                     print(f"Skipping invalid movie data: {movie}")

            movie_queue.put(None) # signal end of movies
            root.after(0, lambda: status_var.set(f"Found {len(movies)} movies.  Displaying...")) # Update status bar

    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}")) # use root.after for thread safety
        root.after(0, lambda: status_var.set(f"Error: {e}")) #Update status bar
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        root.after(0, lambda: root.title(f"Movie Scraper (Search time: {elapsed_time:.2f} seconds)")) # use root.after for thread safety
        root.after(0, lambda: progress_bar.stop())  # Stop the progress bar
        root.after(0, lambda: search_button.config(state=tk.NORMAL))  # Re-enable the button

def process_movie_queue(movie_queue):
    """Gets movies from the queue and adds them to the display."""
    index = 0
    while True:
        movie = movie_queue.get()
        if movie is None:
            break # end of queue
        root.after(0, lambda: add_movie_display(movie, index)) # add movie using main thread
        index += 1
    root.after(0, lambda: status_var.set(f"Display complete. {num_movies_found} movies displayed."))

def add_movie_display(movie, index):
    """Adds the movie title and poster image to the UI."""
    frame = tk.Frame(image_frame, borderwidth=2, relief=tk.GROOVE) # each movie gets its own frame
    frame.pack(side=tk.LEFT, padx=5, pady=5) # arrange movies horizontally

    # Check if the movie data is valid
    if not movie or not isinstance(movie, dict) or 'title' not in movie:
        print(f"Skipping display of invalid movie data: {movie}")
        error_label = tk.Label(frame, text="Error: Invalid movie data")
        error_label.pack()
        return

    label_title = tk.Label(frame, text=movie['title'], font=("Arial", 12), wraplength=MAX_IMAGE_WIDTH)
    label_title.pack()

    try:
        image_url = movie['poster_url']
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        image_data = io.BytesIO(response.content)
        img = Image.open(image_data)

        # Resize the image
        img.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT), Image.LANCZOS)  # Use thumbnail for better performance
        photo = ImageTk.PhotoImage(img)
        label_image = tk.Label(frame, image=photo)
        label_image.image = photo # keep a reference!
        label_image.pack()

    except requests.exceptions.RequestException as e:  # more specific exception handling
        label_image = tk.Label(frame, text=f"Error loading image: {e}", wraplength=MAX_IMAGE_WIDTH)
        label_image.pack()

    except Exception as e:
        label_image = tk.Label(frame, text=f"Error: {e}", wraplength=MAX_IMAGE_WIDTH)
        label_image.pack()
    image_frames.append(frame)  # Add the frame to the list

def clear_image_frames():
    """Clears all the image frames from the UI."""
    for frame in image_frames:
        frame.destroy()
    image_frames.clear()

root = tk.Tk()
root.title("Movie Scraper")
root.geometry("1000x700") # increased size for better layout

# Configure grid layout - more organized and flexible
root.columnconfigure(0, weight=1)  # Username label/entry column
root.columnconfigure(1, weight=1)  # Search button and empty space
root.rowconfigure(0, weight=0)      # Username label/entry row
root.rowconfigure(1, weight=0)      # Search button row
root.rowconfigure(2, weight=1)      # Results area row
root.rowconfigure(3, weight=0) # status bar
root.rowconfigure(4, weight=1) # text area

# Username Label and Entry
label_username = tk.Label(root, text="Enter Username:", font=("Arial", 12))
label_username.grid(row=0, column=0, padx=10, pady=10, sticky="e") # aligned to the right

entry_username = tk.Entry(root, width=40, font=("Arial", 12))
entry_username.grid(row=0, column=1, padx=10, pady=10, sticky="w") # aligned to the left

# Search Button
search_button = tk.Button(root, text="Search", command=on_search_button_click, font=("Arial", 12), bg="#4CAF50", fg="white", activebackground="#367C39", relief=tk.RAISED)  # Style the button
search_button.grid(row=1, column=0, columnspan=1, pady=10, sticky="e") # position to the left

# Progress Bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="indeterminate")
progress_bar.grid(row=1, column=1, sticky="w", padx=10)

# Frame to hold images
image_frame = tk.Frame(root)
image_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

# Create a Canvas to hold the images
canvas = tk.Canvas(image_frame)
canvas.pack(side="left", fill="both", expand=True)

# Add a scrollbar to the Canvas
scrollbar = ttk.Scrollbar(image_frame, orient="horizontal", command=canvas.xview)
scrollbar.pack(side="bottom", fill="x")

canvas.configure(xscrollcommand=scrollbar.set)

image_inner_frame = tk.Frame(canvas)  # Frame *inside* the canvas to hold image frames

canvas.create_window((0, 0), window=image_inner_frame, anchor="nw")

image_inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

image_frame = image_inner_frame # Now image_frame is what add_movie_display uses

image_frames = []  # List to keep track of image frames

# Status bar
status_var = tk.StringVar()
status_bar = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_bar.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
status_var.set("Ready") #Initial status

# text_result should be defined here because it is used on the main thread:
text_result = ScrolledText(root, wrap=tk.WORD, width=80, height=10, font=("Courier New", 10))
# Move the position of the text_result to upper part.
text_result.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

root.mainloop()