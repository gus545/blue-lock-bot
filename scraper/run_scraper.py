import requests
import time
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from dotenv import load_dotenv
import os
from parser import LeagueParser
import requests_cache


# --- Constants ---
CRAWL_DELAY = 15 # seconds
UNKNOWN_STR = "Unknown"
ERROR_INT = -1
STATE_FILE = "scraper_state.json"

# Load .env
load_dotenv()

requests_cache.install_cache('http_cache', expire_after=3600)

default_headers = {
    "User-Agent": "BlueLockBot/1.0 (contact: angusmdev@gmail.com)"
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_page(session: requests.Session, url: str) -> Optional[str]:

    try:
        print(f"Fetching {url}...")
        response = session.get(url)

        if response.from_cache:
            print("Loaded from cache.")
        else:
            print("Fetched.")
            time.sleep(CRAWL_DELAY)

        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def load_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def main():

    # Check if scraped_data directory exists
    if not os.path.exists("scraped_data"):
        os.makedirs("scraped_data")

    # Check if pages have been pulled recently
    state = load_state()
    last_run = state.get("last_run")
    if not last_run or (datetime.now() - datetime.fromisoformat(last_run)).days > 0 or True:
        session = requests.Session()
        session.headers.update(headers)
        
        league_url = os.getenv("LEAGUE_URL") + os.getenv("LEAGUE_ID")
        schedule_url = os.getenv("SCHEDULE_URL") + os.getenv("LEAGUE_ID")
        results_url = os.getenv("RESULTS_URL") + os.getenv("LEAGUE_ID")

        # Fetch pages from the web and save them
        league_html = fetch_page(session, league_url)
        schedule_html = fetch_page(session, schedule_url)
        results_html = fetch_page(session, results_url) 

        # Update state
        state["last_run"] = datetime.now().isoformat()
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
    else:
        print(f"Scraper last ran at {last_run}")
        return
            
    print(schedule_html)
    league_table = LeagueParser.parse_league_table_page(league_html)
    schedule = LeagueParser.parse_schedule_page(schedule_html)
    results = LeagueParser.parse_results_page(results_html)

    print("Sending game data...") 
    for team in league_table:
        print(requests.post('http://127.0.0.1:8000/teams', json.dumps(team)).content)
        
    for r in results:
        print(requests.post('http://127.0.0.1:8000/games', json.dumps(r)).content)
    
    for s in schedule:
        print(requests.post('http://127.0.0.1:8000/games', json.dumps(s)).content)








if __name__ == "__main__":
    main()