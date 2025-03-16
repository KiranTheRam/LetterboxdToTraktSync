# Letterboxd to Trakt Sync

A Python tool that syncs your watched movies and ratings from Letterboxd to Trakt.tv automatically.

## Overview

This tool fetches your recently watched movies from your Letterboxd RSS feed and syncs them to your Trakt.tv account, including watch dates and ratings. It handles the conversion between Letterboxd's 5-star rating system and Trakt's 10-point scale.

## Features

- Automatically syncs watched movies from Letterboxd to Trakt.tv
- Preserves watch dates for accurate history tracking
- Converts Letterboxd ratings (0.5-5 stars) to Trakt ratings (1-10)
- Handles rate limiting with built-in delays
- Detailed logging for troubleshooting

## Prerequisites

- Python 3.6+
- A Letterboxd account with public activity
- A Trakt.tv account with API access

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/letterboxd-to-trakt-sync.git
cd letterboxd-to-trakt-sync
```

2. Install the required dependencies:
```
pip install requests feedparser python-dotenv
```

3. Create a `.env` file with your credentials:
```
# Trakt API credentials
TRAKT_CLIENT_ID=your_client_id_here
TRAKT_CLIENT_SECRET=your_client_secret_here
TRAKT_REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob

# Letterboxd username
LETTERBOXD_USERNAME=your_letterboxd_username
```

## Usage

1. First, you need to authenticate with Trakt.tv to generate a token file:
```
python trakt_auth.py
```

2. Once authenticated, run the sync script:
```
python main.py
```

3. (Optional) Set up a cron job or scheduled task to run the script periodically.

## How It Works

1. The script fetches your Letterboxd RSS feed to get your recently watched movies
2. It extracts movie titles, years, watch dates, and ratings
3. It formats the data for Trakt's API, including converting dates to ISO 8601 format
4. It sends the data to Trakt's `/sync/history` and `/sync/ratings` endpoints
5. It respects Trakt's rate limits by adding delays between requests

## Troubleshooting

If you encounter issues:

- Check the `letterboxd_trakt_sync.log` file for detailed error messages
- Ensure your Letterboxd profile is public
- Verify your Trakt API credentials are correct
- Make sure your token file hasn't expired

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
