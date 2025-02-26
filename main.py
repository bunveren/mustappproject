import requests
from bs4 import BeautifulSoup
import json

def get_user_want_to_watch_movies_from_webpage(username):
    """
    Scrapes the Mustapp "want" page to extract movie titles.
    """
    url = f"https://mustapp.com/@{username}/want"
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        movie_elements = soup.find_all('a', class_='poster js_item')
        movies = []

        for movie_element in movie_elements:
            title_element = movie_element.find('div', class_='poster__title')
            poster_art_element = movie_element.find('div', class_='poster__art')

            if title_element and poster_art_element:
                title = title_element.text.strip()
                # background-image stilini çek ve URL'i ayıkla
                style = poster_art_element['style']
                poster_url = style.split('url("')[1].split('");')[0]

                movies.append({'title': title, 'poster_url': poster_url})

        # Çekilen filmleri yazdırma
        if movies:
            print("Çekilen Filmler:")
            for movie in movies:
                print(f"  - {movie['title']}")
                print(f"    Poster URL: {movie['poster_url']}")
        else:
            print("Film bulunamadı.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return []
    except Exception as e:
        print(f"Error parsing the page: {e}")
        return []


def main():
    username = input("Enter the username: ")

    want_to_watch_movies = get_user_want_to_watch_movies_from_webpage(username)

    print(f"\nWant To Watch Movies for user @{username}:")
    if want_to_watch_movies:
        for title in want_to_watch_movies:
            print(title)
    else:
        print("No 'want to watch' movies found (or error scraping the page).")


if __name__ == "__main__":
    main()