import requests
import json
import os
import time
import logging
import feedparser
import ssl
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    filename='letterboxd_trakt_sync.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class LetterboxdToTraktSync:
    def __init__(self):
        # Trakt API credentials from environment variables
        self.CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
        self.CLIENT_SECRET = os.getenv("TRAKT_CLIENT_SECRET")
        self.REDIRECT_URI = os.getenv("TRAKT_REDIRECT_URI")

        # API endpoints
        self.TRAKT_API_URL = "https://api.trakt.tv"
        self.TRAKT_TOKEN_URL = f"{self.TRAKT_API_URL}/oauth/token"

        # Letterboxd username from environment variable
        self.LETTERBOXD_USERNAME = os.getenv("LETTERBOXD_USERNAME")

        # Token storage
        self.token_file = "trakt_token.json"

        # Initialize logging
        logging.info("Starting Letterboxd to Trakt weekly sync")

        # Validate that required environment variables are set
        if not all([self.CLIENT_ID, self.CLIENT_SECRET, self.REDIRECT_URI, self.LETTERBOXD_USERNAME]):
            logging.error("Missing required environment variables. Check your .env file.")
            raise ValueError("Missing required environment variables")

    def run(self):
        """Main sync function"""
        logging.info("Starting weekly sync process")

        # Authenticate with Trakt
        access_token = self.authenticate_trakt()
        if not access_token:
            logging.error("Authentication failed")
            return False

        # Get Letterboxd data from the past week
        movies = self.get_letterboxd_data()
        if not movies:
            logging.info("No movies watched in the past week")
            return False

        # Sync to Trakt
        success = self.sync_to_trakt(access_token, movies)
        if success:
            logging.info("Weekly sync completed successfully")
        else:
            logging.error("Weekly sync failed")

        return success

    def authenticate_trakt(self):
        """Handle Trakt authentication using OAuth"""
        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
                access_token = token_data.get('access_token')
                refresh_token = token_data.get('refresh_token')
                expires_at = token_data.get('expires_at', 0)

                # Check if token is expired
                if time.time() > expires_at:
                    logging.info("Token expired, refreshing...")
                    return self.refresh_access_token(refresh_token)
                else:
                    logging.info("Using existing token")
                    return access_token
        else:
            logging.error("No token file found. Please run the initial authentication manually.")
            return None

    def refresh_access_token(self, refresh_token):
        """Refresh the access token using the refresh token"""
        data = {
            "refresh_token": refresh_token,
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "redirect_uri": self.REDIRECT_URI,
            "grant_type": "refresh_token"
        }

        try:
            response = requests.post(self.TRAKT_TOKEN_URL, json=data)
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                refresh_token = token_data["refresh_token"]

                # Calculate expiration time
                expires_at = time.time() + token_data["expires_in"]
                token_data["expires_at"] = expires_at

                # Save token data to file
                with open(self.token_file, 'w') as f:
                    json.dump(token_data, f)

                logging.info("Token refreshed successfully")
                return access_token
            else:
                logging.error(f"Token refresh failed: {response.text}")
                return None
        except Exception as e:
            logging.error(f"Error refreshing token: {str(e)}")
            return None

    def get_trakt_headers(self, access_token):
        """Get headers for Trakt API requests"""
        return {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": self.CLIENT_ID,
            "Authorization": f"Bearer {access_token}"
        }

    def get_letterboxd_data(self):
        """Get data from Letterboxd using their RSS feed, filtering for movies watched in the past week"""
        try:
            # Use feedparser to parse the RSS feed
            feed_url = f"https://letterboxd.com/{self.LETTERBOXD_USERNAME}/rss/"
            logging.info(f"Fetching Letterboxd RSS feed from: {feed_url}")

            if hasattr(ssl, '_create_unverified_context'):
                ssl._create_default_https_context = ssl._create_unverified_context

            feed = feedparser.parse(feed_url)

            if not feed.entries:
                logging.warning(
                    f"No entries found in the RSS feed. Feed status: {feed.status if hasattr(feed, 'status') else 'unknown'}")
                logging.debug(f"Feed bozo: {feed.bozo if hasattr(feed, 'bozo') else 'unknown'}")
                logging.debug(f"Feed headers: {feed.headers if hasattr(feed, 'headers') else 'unknown'}")
                return None

            # Calculate the date one week ago
            one_week_ago = datetime.now() - timedelta(days=7)

            # Extract watched movies from the past week
            watched_movies = []

            for entry in feed.entries:
                # Check if this entry has the necessary letterboxd metadata
                if not hasattr(entry, 'letterboxd_watcheddate'):
                    continue

                # Parse the watched date
                try:
                    watched_date = datetime.strptime(entry.letterboxd_watcheddate, "%Y-%m-%d")
                except (ValueError, TypeError):
                    continue

                # Skip movies watched more than a week ago
                if watched_date < one_week_ago:
                    continue

                # Extract movie information directly from the letterboxd metadata
                title = entry.letterboxd_filmtitle if hasattr(entry, 'letterboxd_filmtitle') else None
                year = entry.letterboxd_filmyear if hasattr(entry, 'letterboxd_filmyear') else None

                # Format the watched date to ISO 8601 format with time and explicit UTC timezone
                # This ensures Trakt interprets the time correctly
                watched_at = f"{entry.letterboxd_watcheddate}T12:00:00.000Z"

                # Extract rating if present
                rating = None
                if hasattr(entry, 'letterboxd_memberrating') and entry.letterboxd_memberrating:
                    try:
                        # Convert Letterboxd rating (0.5-5) to Trakt rating (1-10)
                        rating_value = float(entry.letterboxd_memberrating)
                        rating = int(rating_value * 2)
                    except (ValueError, TypeError):
                        pass

                # Only add movies with valid title and watched date
                if title and watched_at:
                    movie = {
                        "title": title,
                        "year": year,
                        "watched_at": watched_at,
                        "rating": rating
                    }

                    watched_movies.append(movie)
                    logging.debug(f"Added movie: {title} ({year}) watched on {watched_at}")

            logging.info(f"Retrieved {len(watched_movies)} movies watched in the past week")
            return watched_movies

        except Exception as e:
            logging.error(f"Error getting Letterboxd data: {str(e)}")
            return None

    def sync_to_trakt(self, access_token, movies):
        """Sync watched movies to Trakt"""
        if not movies:
            logging.info("No movies to sync")
            return False

        # Prepare data for Trakt API
        movies_data = {"movies": []}

        for movie in movies:
            movie_data = {
                "title": movie["title"]
            }

            # Only add year if it's a valid integer
            if movie.get("year") and str(movie["year"]).isdigit():
                movie_data["year"] = int(movie["year"])

            # Add watched date if available
            if movie.get("watched_at"):
                movie_data["watched_at"] = movie["watched_at"]

            movies_data["movies"].append(movie_data)

        # Send request to Trakt API
        url = f"{self.TRAKT_API_URL}/sync/history"
        headers = self.get_trakt_headers(access_token)

        try:
            response = requests.post(url, headers=headers, json=movies_data)

            # Add a sleep to respect rate limits
            time.sleep(2)

            if response.status_code == 201:
                result = response.json()
                logging.info(f"Synced {result.get('added', {}).get('movies', 0)} movies to Trakt")
                logging.info(f"Already on Trakt: {result.get('existing', {}).get('movies', 0)} movies")
                logging.info(f"Not found: {result.get('not_found', {}).get('movies', 0)} movies")

                # If we have ratings, sync those too
                self.sync_ratings_to_trakt(access_token, movies)
                return True
            else:
                logging.error(f"Failed to sync to Trakt: {response.text}")
                return False

        except Exception as e:
            logging.error(f"Error syncing to Trakt: {str(e)}")
            return False

    def sync_ratings_to_trakt(self, access_token, movies):
        """Sync movie ratings to Trakt"""
        # Filter movies that have ratings
        movies_with_ratings = [movie for movie in movies if movie.get("rating")]

        if not movies_with_ratings:
            logging.info("No ratings to sync")
            return

        # Prepare data for Trakt API
        ratings_data = {"movies": []}

        for movie in movies_with_ratings:
            movie_data = {
                "title": movie["title"],
                "rating": movie["rating"]
            }

            # Only add year if it's a valid integer
            if movie.get("year") and str(movie["year"]).isdigit():
                movie_data["year"] = int(movie["year"])

            ratings_data["movies"].append(movie_data)

        # Send request to Trakt API
        url = f"{self.TRAKT_API_URL}/sync/ratings"
        headers = self.get_trakt_headers(access_token)

        try:
            response = requests.post(url, headers=headers, json=ratings_data)
            # Add a sleep to respect rate limits
            time.sleep(2)

            if response.status_code == 201:
                result = response.json()
                logging.info(f"Synced {result.get('added', {}).get('movies', 0)} movie ratings to Trakt")
                logging.info(f"Updated {result.get('updated', {}).get('movies', 0)} movie ratings")
                logging.info(f"Not found: {result.get('not_found', {}).get('movies', 0)} movies for ratings")
                return True
            else:
                logging.error(f"Failed to sync ratings to Trakt: {response.text}")
                return False

        except Exception as e:
            logging.error(f"Error syncing ratings to Trakt: {str(e)}")
            return False


if __name__ == "__main__":
    syncer = LetterboxdToTraktSync()
    syncer.run()