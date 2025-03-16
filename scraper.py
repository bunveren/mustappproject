import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By

DEBUG_SAVE_PAGE_SOURCE = True  # Flag to enable saving page source for debug

def fetch_movie_data(username, list_type="want"):
    """
    Fetches movie data from the webpage for the given username and list type.
    Saves page source for debugging if DEBUG_SAVE_PAGE_SOURCE is True.
    """
    if list_type not in ["want", "watched"]:
        raise ValueError("list_type must be 'want' or 'watched'")

    base_url = f"https://mustapp.com/@{username}"
    url = f"https://mustapp.com/@{username}/{list_type}"

    try:
        print(f"Fetching URL: {url} (Initial URL)")
        response = requests.get(url)
        response.raise_for_status()

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(base_url)

        if DEBUG_SAVE_PAGE_SOURCE: # Save page source *before* trying to click
            page_source = driver.page_source
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("Page source saved to debug_page_source.html")

        if list_type == "watched":
            print("Switching to 'Watched' tab using Selenium...")
            watched_tab_element = driver.find_element(By.XPATH, "//div[contains(@class, 'profile__list_menu_item') and contains(@class, 'm_active') and text()='Watched']")
            watched_tab_element.click()
            time.sleep(2)
            print("'Watched' tab clicked and waiting for content to load.")


        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 10
        while scroll_count < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            new_height = driver.execute_script("return document.body.scrollHeight")
            print(f"Scroll attempt {scroll_count+1}: Last Height = {last_height}, New Height = {new_height}")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_count += 1

        html = driver.page_source
        driver.quit()
        soup = BeautifulSoup(html, 'html.parser')
        movie_elements = soup.find_all('a', class_='poster js_item')
        print(f"Number of movie_elements found by BeautifulSoup (list_type: {list_type}): {len(movie_elements)}")
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
        print(f"Number of movies after deduplication (list_type: {list_type}): {len(movies)}")
        return movies

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page for list_type '{list_type}': {e}")
        return None
    except Exception as e:
        print(f"Error parsing the page for list_type '{list_type}': {e}")
        return None