import json
import os
from datetime import datetime
import logging
import feedparser
import ssl
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
LETTERBOXD_USERNAME = os.getenv("LETTERBOXD_USERNAME")

def get_letterboxd_data():
    """Get data from Letterboxd using their RSS feed with feedparser"""
    try:
        # Use feedparser to parse the RSS feed
        feed_url = f"https://letterboxd.com/{LETTERBOXD_USERNAME}/rss/"
        logging.info(f"Fetching Letterboxd RSS feed from: {feed_url}")

        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context
        feed = feedparser.parse(feed_url)
        print(json.dumps(feed, indent=4))

        # Testing
        # for movie in feed.entries:
        #     print(json.dumps(movie, indent=4))

        if not feed.entries:
            logging.warning(
                f"No entries found in the RSS feed. Feed status: {feed.status if hasattr(feed, 'status') else 'unknown'}")
            # Debug the feed content
            print(f"Feed bozo: {feed.bozo if hasattr(feed, 'bozo') else 'unknown'}")
            print(f"Feed headers: {feed.headers if hasattr(feed, 'headers') else 'unknown'}")
            return None

        # Extract diary entries (watched movies)
        watched_movies = []
        for entry in feed.entries:
            # Debug entry information
            print(f"Processing entry: {entry.title if hasattr(entry, 'title') else 'No title'}")

            # Check if this is a diary entry (watched movie)
            if hasattr(entry, 'title') and 'watched' in entry.title.lower():
                # Extract movie information
                title_parts = entry.title.split(' watched ')
                if len(title_parts) > 1:
                    movie_title_with_year = title_parts[1]
                    # Extract year if present
                    if '(' in movie_title_with_year and ')' in movie_title_with_year:
                        title = movie_title_with_year.split(' (')[0].strip()
                        year_part = movie_title_with_year.split(' (')[1]
                        year = year_part.split(')')[0].strip() if ')' in year_part else None
                    else:
                        title = movie_title_with_year.strip()
                        year = None

                    # Get watched date from published date if available
                    watched_at = None
                    if hasattr(entry, 'published_parsed'):
                        watched_date = datetime(*entry.published_parsed[:6])
                        watched_at = watched_date.strftime("%Y-%m-%d")

                    # Extract rating if present in the description
                    rating = None
                    if hasattr(entry, 'description'):
                        if 'rated it' in entry.description.lower():
                            rating_text = entry.description.lower().split('rated it')[1].split('stars')[0].strip()
                            try:
                                # Convert Letterboxd rating (0.5-5) to Trakt rating (1-10)
                                rating_value = float(rating_text)
                                rating = rating_value * 2
                            except ValueError:
                                pass

                    movie = {
                        "title": title,
                        "year": year,
                        "watched_at": watched_at,
                        "rating": rating
                    }
                    watched_movies.append(movie)
                    print(f"Added movie: {title} ({year}) watched on {watched_at}")

        logging.info(f"Retrieved {len(watched_movies)} movies from Letterboxd")
        return watched_movies
    except Exception as e:
        logging.error(f"Error getting Letterboxd data: {str(e)}")
        return None

if __name__ == "__main__":
    get_letterboxd_data()