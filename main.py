import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


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
    except Exception as e:
        print(f"Error parsing the page: {e}")