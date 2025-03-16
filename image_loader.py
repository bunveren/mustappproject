# image_loader.py
import tkinter as tk
from PIL import Image, ImageTk
import requests
import io
import concurrent.futures
import time  # Import time for timing

MAX_IMAGE_WIDTH = 75   # Reduced MAX_IMAGE_WIDTH to 75 (thumbnails)
MAX_IMAGE_HEIGHT = 125  # Reduced MAX_IMAGE_HEIGHT to 125 (thumbnails)
image_loading_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)  # Reduced thread pool size to 4
image_frames_global = [] # To be populated from main.py
NUM_COLUMNS = 4 # Define the number of columns for the grid layout

def load_and_display_image(movie, frame, root):
    """Loads movie poster image and displays it in the given frame with detailed logging."""
    image_url = movie['poster_url']
    start_time = time.time()
    print(f"Image loading started for: {movie['title']}, URL: {image_url}")  # Log start

    try:
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()
        download_time = time.time() - start_time
        print(f"Image downloaded successfully for: {movie['title']}, URL: {image_url}, Status Code: {response.status_code}, Download Time: {download_time:.2f}s") # Log download success

        image_data = io.BytesIO(response.content)
        img = Image.open(image_data)
        image_open_time = time.time() - (start_time + download_time) # Time to open image after download
        print(f"Image opened with PIL for: {movie['title']}, URL: {image_url}, Open Time: {image_open_time:.2f}s") # Log image open time

        img.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT), Image.LANCZOS) # Using the REDUCED MAX_IMAGE_WIDTH/HEIGHT
        thumbnail_time = time.time() - (start_time + download_time + image_open_time) # Time for thumbnailing
        print(f"Thumbnail created for: {movie['title']}, URL: {image_url}, Thumbnail Time: {thumbnail_time:.2f}s, Size: {img.size}") # Log thumbnail time and size

        photo = ImageTk.PhotoImage(img)
        photo_create_time = time.time() - (start_time + download_time + image_open_time + thumbnail_time) # Time to create PhotoImage
        print(f"PhotoImage created for: {movie['title']}, URL: {image_url}, PhotoImage Time: {photo_create_time:.2f}s, Size: {(photo.width(), photo.height())}") # Log PhotoImage time and size

        root.after(0, lambda: _display_image_in_frame(frame, photo))
        total_processing_time = time.time() - start_time
        print(f"Image display scheduled for: {movie['title']}, URL: {image_url}, Total Processing Time: {total_processing_time:.2f}s") # Log total time

    except requests.exceptions.RequestException as e:
        error_time = time.time() - start_time
        root.after(0, lambda: _display_error_image_in_frame(frame, f"Error loading image: {e}"))
        print(f"Request Exception for image: {image_url}, Error: {e}, Time: {error_time:.2f}s, Movie: {movie['title']}") # Log RequestException
    except Exception as e:
        error_time = time.time() - start_time
        root.after(0, lambda: _display_error_image_in_frame(frame, f"Error: {e}"))
        print(f"General Error loading image: {image_url}, Error: {e}, Time: {error_time:.2f}s, Movie: {movie['title']}") # Log general Exception
    finally:
        end_time = time.time()
        total_time = end_time - start_time
        print(f"Image loading finished for: {movie['title']}, URL: {image_url}, Total Time: {total_time:.2f}s") # Log finish time

def _display_image_in_frame(frame, photo):
    """Displays the image in the given frame."""
    label_image = tk.Label(frame, image=photo)
    label_image.image = photo
    label_image.pack()

def _display_error_image_in_frame(frame, error_message):
    """Displays an error message in place of the image."""
    label_image = tk.Label(frame, text=error_message, wraplength=MAX_IMAGE_WIDTH)
    label_image.pack()

def add_movie_to_display(movie, index, parent_frame, root):
    """Creates a frame for a movie and adds it to the display using grid layout."""
    frame = tk.Frame(parent_frame, borderwidth=2, relief=tk.GROOVE)
    image_frames_global.append(frame) # Use the global list

    if not movie or not isinstance(movie, dict) or 'title' not in movie:
        print(f"Skipping display of invalid movie data: {movie}")
        error_label = tk.Label(frame, text="Error: Invalid movie data")
        error_label.pack()
        return

    label_title = tk.Label(frame, text=movie['title'], font=("Arial", 12), wraplength=MAX_IMAGE_WIDTH * 2) # Increased wraplength for potentially wider titles in grid
    label_title.pack()

    print(f"Adding movie to display (with image loading) in grid: {movie['title']}, index: {index}") # Debug print
    image_loading_thread_pool.submit(load_and_display_image, movie, frame, root)

    col_index = index % NUM_COLUMNS
    row_index = index // NUM_COLUMNS
    frame.grid(row=row_index, column=col_index, padx=5, pady=5, sticky="nsew") # Use grid layout
