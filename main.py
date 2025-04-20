#!/usr/bin/env python3
import os
import time
import json
import ssl
import argparse
import datetime
import logging
from typing import List, Dict, Optional

import requests
import feedparser
from dotenv import load_dotenv

# Load environment variables
env_loaded = load_dotenv()

# Logging setup
logging.basicConfig(
    filename='letterboxd_trakt_sync.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LetterboxdToTraktSync:
    RETRY_LIMIT = 3
    RATE_LIMIT_STATUS = 429

    def __init__(self):
        self.session = requests.Session()
        self.CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
        self.CLIENT_SECRET = os.getenv("TRAKT_CLIENT_SECRET")
        self.REDIRECT_URI = os.getenv("TRAKT_REDIRECT_URI")
        self.USERNAME = os.getenv("LETTERBOXD_USERNAME")
        self.token_path = 'trakt_token.json'
        self.api_url = 'https://api.trakt.tv'

        missing = [k for k in ("TRAKT_CLIENT_ID","TRAKT_CLIENT_SECRET","TRAKT_REDIRECT_URI","LETTERBOXD_USERNAME")
                   if not os.getenv(k)]
        if missing:
            msg = f"Missing env vars: {', '.join(missing)}"
            logging.error(msg)
            raise EnvironmentError(msg)

        # Allow unverified SSL if needed
        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context

    def run(self, start_date: Optional[datetime.date] = None) -> bool:
        print("Starting sync...")
        token = self._get_access_token()
        if not token:
            print("Auth failed.")
            return False

        movies = self._fetch_and_filter(start_date)
        if not movies:
            print("No movies to sync.")
            return False

        print("Syncing movies:")
        for m in movies:
            print(f" - {m['title']} ({m['year'] or 'N/A'}) @ {m['watched_at']}")

        history_ok = self._post_sync('history', movies)
        ratings_ok = self._post_sync('ratings', [m for m in movies if m.get('rating')], key='rating')

        success = history_ok and (ratings_ok or True)
        print("Done." if success else "Completed with errors.")
        return success

    def _get_access_token(self) -> Optional[str]:
        if os.path.exists(self.token_path):
            with open(self.token_path) as f:
                data = json.load(f)
            if time.time() > data.get('expires_at', 0):
                return self._refresh_token(data['refresh_token'])
            return data['access_token']
        logging.error("No token file.")
        return None

    def _refresh_token(self, refresh_token: str) -> Optional[str]:
        payload = {
            'refresh_token': refresh_token,
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'redirect_uri': self.REDIRECT_URI,
            'grant_type': 'refresh_token'
        }
        resp = self.session.post(f"{self.api_url}/oauth/token", json=payload)
        resp.raise_for_status()
        data = resp.json()
        data['expires_at'] = time.time() + data.get('expires_in', 0)
        with open(self.token_path, 'w') as f:
            json.dump(data, f)
        return data['access_token']

    def _headers(self, token: str) -> Dict[str, str]:
        return {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': self.CLIENT_ID,
            'Authorization': f"Bearer {token}"
        }

    def _fetch_and_filter(self, start_date: Optional[datetime.date]) -> List[Dict]:
        feed = feedparser.parse(f"https://letterboxd.com/{self.USERNAME}/rss/")
        entries = getattr(feed, 'entries', [])

        movies = []
        for e in entries:
            date_str = getattr(e, 'letterboxd_watcheddate', None)
            if not date_str:
                continue
            watched = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            if start_date and watched < start_date:
                continue
            movie = {
                'title': getattr(e, 'letterboxd_filmtitle', ''),
                'year': int(getattr(e, 'letterboxd_filmyear', 0) or 0),
                'watched_at': f"{date_str}T12:00:00.000Z",
                'rating': int(float(getattr(e, 'letterboxd_memberrating', 0)) * 2) if getattr(e, 'letterboxd_memberrating', None) else None
            }
            if movie['title']:
                movies.append(movie)
        logging.info(f"Filtered {len(movies)} movies")
        return movies

    def _post_sync(self, endpoint: str, data_list: List[Dict], key: str = None) -> bool:
        if not data_list:
            return True
        payload = {'movies': []}
        for m in data_list:
            item = {'title': m['title']}
            if m.get('year'):
                item['year'] = m['year']
            if endpoint == 'history':
                item['watched_at'] = m['watched_at']
            elif key and m.get(key) is not None:
                item[key] = m[key]
            payload['movies'].append(item)

        url = f"{self.api_url}/sync/{endpoint}"
        headers = self._headers(self._get_access_token())
        for attempt in range(self.RETRY_LIMIT):
            resp = self.session.post(url, headers=headers, json=payload)
            if resp.status_code == self.RATE_LIMIT_STATUS:
                retry = int(resp.headers.get('Retry-After', 1))
                logging.warning(f"Rate limited, retry in {retry}s")
                time.sleep(retry)
                continue
            try:
                resp.raise_for_status()
                added = resp.json().get('added', {}).get('movies', 0)
                print(f"{endpoint.capitalize()} synced: {added}")
                return True
            except Exception as e:
                logging.error(f"Failed {endpoint}: {e}")
                return False
        logging.error(f"{endpoint} sync failed after retries")
        return False

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Sync Letterboxd to Trakt')
    group = p.add_mutually_exclusive_group()
    group.add_argument('-s', '--start-date',
                       help="Start date in MM-DD-YYYY format")
    group.add_argument('-d', '--days', type=int,
                       help="Number of days back to sync")

    args = p.parse_args()

    # Determine start_date
    if args.days is not None:
        start = datetime.date.today() - datetime.timedelta(days=args.days)
    elif args.start_date:
        start = datetime.datetime.strptime(args.start_date, '%m-%d-%Y').date()
    else:
        start = None  # 'all' behavior
    LetterboxdToTraktSync().run(start)
