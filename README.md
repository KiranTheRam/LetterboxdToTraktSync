# Letterboxd → Trakt.tv Sync CLI

A simple, configurable command‑line tool to sync your Letterboxd watch history (and ratings) into your Trakt.tv account.

---

## Features

- Fetches your watched movies from your Letterboxd RSS feed  
- Filters by “start date” so you can catch up only from a given day onward  
- Syncs **history** (`/sync/history`) and **ratings** (`/sync/ratings`) in separate, retry‑aware steps  
- Converts Letterboxd’s 0.5–5 star scale into Trakt’s 1–10 rating system  
- Handles Trakt rate‑limits (HTTP 429) with automatic retries  
- Detailed logging (`letterboxd_trakt_sync.log`) for troubleshooting  

---

## Requirements

- Python 3.7+  
- A public Letterboxd account  
- A Trakt.tv account with an API application (Client ID & Client Secret)  
- The following Python packages:
  ```bash
  pip install requests feedparser python-dotenv
  ```

---

## Installation

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/letterboxd-to-trakt-cli.git
   cd letterboxd-to-trakt-cli
   ```

2. **Create a `.env`**  
   In the project root, create `.env` with your credentials:
   ```dotenv
   # Trakt API credentials
   TRAKT_CLIENT_ID=YOUR_TRAKT_CLIENT_ID
   TRAKT_CLIENT_SECRET=YOUR_TRAKT_CLIENT_SECRET
   TRAKT_REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob

   # Letterboxd username
   LETTERBOXD_USERNAME=your_letterboxd_username
   ```

3. **Obtain a Trakt access token**  
   The first time you run the script, it will look for `trakt_token.json`.  
   You can generate this by exchanging your OAuth credentials manually or via a helper script:
   ```bash
   python trakt_auth.py
   ```
   *(See [Authentication](#authentication) below.)*

---

## Usage

```bash
python main.py
```

- Will sync your entire Letterboxd history.

```bash
python main.py [-s START_DATE]
```

- `-s, --start-date`  
  - **Format:** `MM-DD-YYYY`  
  - **Example:** `-s 04-09-2025`  
 
```bash
python main.py [-d DAYS_AS_NUMBER]
```

- `-d, --days`  
  - **Format:** `number`  
  - **Example:** `-d 30`  

**Examples**

- Sync everything:
  ```bash
  python main.py
  ```
- Sync from April 9, 2025 onward:
  ```bash
  python main.py -s 04-09-2025
  ```

- Sync from 30 days ago onward:
  ```bash
  python main.py -d 30
  ```
---

## Authentication

1. Register a **“Script”** application on [Trakt.tv’s API dashboard](https://trakt.tv/oauth/applications).  
2. Fill in your **Client ID**, **Client Secret**, and use `urn:ietf:wg:oauth:2.0:oob` as the redirect URI.  
3. Run:
   ```bash
   python trakt_auth.py
   ```
   This should open a link in your browser. Authorize the app and paste the code back into the prompt.  
4. A `trakt_token.json` file will be created automatically.

---

## Logging & Troubleshooting

- All HTTP errors, rate‑limit warnings, and parsing issues are logged to `letterboxd_trakt_sync.log`.  
- If you see **“Auth failed.”**, ensure your `.env` is correct and that `trakt_token.json` exists and is valid.  
- If **“No movies to sync.”** appears, double‑check your Letterboxd RSS feed (must be public) and date filter.

---

## Contributing

1. Fork the repo  
2. Create a feature branch (`git checkout -b feature-name`)  
3. Commit your changes (`git commit -m "Add feature"`)  
4. Push and open a Pull Request  

---

## License

This project is released under the [MIT License](LICENSE).  
