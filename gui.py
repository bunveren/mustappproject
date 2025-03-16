import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import requests
import io
from queue import Queue
import threading
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import concurrent.futures

MAX_IMAGE_WIDTH = 300
MAX_IMAGE_HEIGHT = 500
num_movies_found = 0
image_frames = []
image_loading_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=12)

def get_user_want_to_watch_movies_from_webpage(username):
    url = f"https://mustapp.com/@{username}/want"
    try:
        response = requests.get(url)
        response.raise_for_status()

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        html = driver.page_source
        driver.quit()
        soup = BeautifulSoup(html, 'html.parser')
        movie_elements = soup.find_all('a', class_='poster js_item')
        movies = []
        seen_movies = set()
        for movie_element in movie_elements:
            title_element = movie_element.find('div', class_='poster__title')
            poster_art_element = movie_element.find('div', class_='poster__art')

            if title_element and poster_art_element:
                title = title_element.text.strip()
                style = poster_art_element['style']
                poster_url = style.split('url("')[1].split('");')[0]
                movie_id = f"{title}_{poster_url}"
                if movie_id not in seen_movies:
                    movies.append({'title': title, 'poster_url': poster_url})
                seen_movies.add(movie_id)
        return movies

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the page: {e}")
        return None

def on_search_button_click():
    username = entry_username.get()
    if not username:
        messagebox.showwarning("Input Error", "Please enter a username!")
        return

    search_button.config(state=tk.DISABLED)
    clear_image_frames()
    progress_bar.start()
    status_var.set("Searching...")
    global num_movies_found
    num_movies_found = 0
    movie_queue = Queue()
    threading.Thread(target=perform_search, args=(username, movie_queue), daemon=True).start()
    threading.Thread(target=process_movie_queue, args=(movie_queue,), daemon=True).start()

def perform_search(username, movie_queue):
    start_time = time.time()

    try:
        movies = get_user_want_to_watch_movies_from_webpage(username)
        if movies is None:
            root.after(0, lambda: messagebox.showerror("Error", "Could not fetch movies. Please check console for details."))
            root.after(0, lambda: status_var.set("Search Error."))
        elif not movies:
            root.after(0, lambda: messagebox.showinfo("No Movies Found", "No movies found for this user or there was an error."))
            root.after(0, lambda: status_var.set("No movies found."))
        else:
            global num_movies_found
            num_movies_found = len(movies)
            for movie in movies:
                 if movie and isinstance(movie, dict) and 'title' in movie:
                     movie_queue.put(movie)
                 else:
                     print(f"Skipping invalid movie data: {movie}")

            movie_queue.put(None)
            root.after(0, lambda: status_var.set(f"Found {len(movies)} movies.  Displaying..."))

    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
        root.after(0, lambda: status_var.set(f"Error: {e}"))
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        root.after(0, lambda: root.title(f"Movie Scraper (Search time: {elapsed_time:.2f} seconds)"))
        root.after(0, lambda: progress_bar.stop())
        root.after(0, lambda: search_button.config(state=tk.NORMAL))

def process_movie_queue(movie_queue):
    index = 0
    while True:
        movie = movie_queue.get()
        if movie is None:
            break
        add_movie_display_threaded(movie, index)
        index += 1
    root.after(0, lambda: status_var.set(f"Display complete. {num_movies_found} movies displayed."))

def add_movie_display_threaded(movie, index):
    frame = tk.Frame(image_frame, borderwidth=2, relief=tk.GROOVE)
    frame.pack(side=tk.LEFT, padx=5, pady=5)
    image_frames.append(frame)

    if not movie or not isinstance(movie, dict) or 'title' not in movie:
        print(f"Skipping display of invalid movie data: {movie}")
        error_label = tk.Label(frame, text="Error: Invalid movie data")
        error_label.pack()
        return

    label_title = tk.Label(frame, text=movie['title'], font=("Arial", 12), wraplength=MAX_IMAGE_WIDTH)
    label_title.pack()

    image_loading_thread_pool.submit(load_image_threaded, movie, frame)

def load_image_threaded(movie, frame):
    try:
        image_url = movie['poster_url']
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()
        image_data = io.BytesIO(response.content)
        img = Image.open(image_data)
        img.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        root.after(0, lambda: display_image(frame, photo))

    except requests.exceptions.RequestException as e:
        root.after(0, lambda: display_error_image(frame, f"Error loading image: {e}"))
        print(f"Request Exception for image: {image_url}, Error: {e}")
    except Exception as e:
        root.after(0, lambda: display_error_image(frame, f"Error: {e}"))
        print(f"General Error loading image: {image_url}, Error: {e}")

def display_image(frame, photo):
    label_image = tk.Label(frame, image=photo)
    label_image.image = photo
    label_image.pack()

def display_error_image(frame, error_message):
    label_image = tk.Label(frame, text=error_message, wraplength=MAX_IMAGE_WIDTH)
    label_image.pack()

def clear_image_frames():
    global image_frames
    for frame in image_frames:
        frame.destroy()
    image_frames = []

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Movie Scraper")
    root.geometry("1000x700")

    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=0)
    root.rowconfigure(1, weight=0)
    root.rowconfigure(2, weight=1)
    root.rowconfigure(3, weight=0)

    label_username = tk.Label(root, text="Enter Username:", font=("Arial", 12))
    label_username.grid(row=0, column=0, padx=10, pady=10, sticky="e")

    entry_username = tk.Entry(root, width=40, font=("Arial", 12))
    entry_username.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    search_button = tk.Button(root, text="Search", command=on_search_button_click, font=("Arial", 12),
        bg="#4CAF50", fg="white", activebackground="#367C39", relief=tk.RAISED)
    search_button.grid(row=1, column=0, columnspan=1, pady=10, sticky="e")

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="indeterminate")
    progress_bar.grid(row=1, column=1, sticky="w", padx=10)

    image_frame = tk.Frame(root)
    image_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

    canvas = tk.Canvas(image_frame)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(image_frame, orient="horizontal", command=canvas.xview)
    scrollbar.pack(side="bottom", fill="x")
    style = ttk.Style()
    style.configure("Horizontal.TScrollbar", sliderthickness=20)

    canvas.configure(xscrollcommand=scrollbar.set)

    image_inner_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=image_inner_frame, anchor="nw")
    image_inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    image_frame = image_inner_frame

    status_var = tk.StringVar()
    status_bar = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_bar.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    status_var.set("Ready")

    root.mainloop()