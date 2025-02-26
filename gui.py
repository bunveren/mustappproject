import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from main import get_user_want_to_watch_movies_from_webpage
import time


def on_search_button_click():
    start = time.localtime()
    username = entry_username.get()
    if not username:
        messagebox.showwarning("Input Error", "Please enter a username!")
        return

    text_result.delete(1.0, tk.END)
    movies = get_user_want_to_watch_movies_from_webpage(username)
    if not movies:
        messagebox.showinfo("No Movies Found", "No movies found or there was an error!")
    else:
        for movie in movies:
            text_result.insert(tk.END, f"Title: {movie['title']}\nPoster URL: {movie['poster_url']}\n\n")
    root.title(f"{time.localtime()-start} seconds elapsed")

root = tk.Tk()
root.title("Movie Scraper")
root.geometry("600x400")

label_username = tk.Label(root, text="Enter Username:")
label_username.pack(pady=10)

entry_username = tk.Entry(root, width=40)
entry_username.pack(pady=5)

search_button = tk.Button(root, text="Search", command=on_search_button_click)
search_button.pack(pady=10)

text_result = ScrolledText(root, wrap=tk.WORD, width=70, height=15)
text_result.pack(pady=10)

root.mainloop()
