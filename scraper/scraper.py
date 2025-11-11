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


# --- Constants ---
CRAWL_DELAY = 15 # seconds
UNKNOWN_STR = "Unknown"
ERROR_INT = -1

# Load .env
load_dotenv()

def send_to_api(data: Dict[str, Any], endpoint: str):
    api_url = os.getenv("API_URL")
    api_key = os.getenv("API_KEY")

    try:
        response = requests.post(
            f"{api_url}/{endpoint}", 
            json=json.dumps(data), 
            headers={"Content-Type": "application/json", "x-api-key": api_key})
        
        response.raise_for_status()

        if response.status_code == 201:
            print(f"    > Successfully added data to endpoint {endpoint}: {data}")
            return True
        else:
            print(f"    > Error adding data to endpoint {endpoint}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"    > Error sending data to endpoint {endpoint}: {e}")
        return False



# --- Main Parsing Functions ---

def fetch_page(session: requests.Session, url: str) -> Optional[str]:

    try:
        print(f"Fetching {url}...")
        response = session.get(url)
        response.raise_for_status()

        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_results_page(html_content: str) -> List[Dict[str, Any]]:
    """
    Parses the "Results" page HTML for completed game scores.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    week_results_tables = soup.find_all("table", class_="generalDataTable")

    if not week_results_tables:
        print("No 'generalDataTable' tables found on results page.")
        return []

    results = []

    for table in week_results_tables:
        
        date_span = table.find("span", class_="ui-column-title")
        if not date_span:
            print("Skipping table: No date title span found.")
            continue
        
        table_date_str = date_span.text.strip()
        table_date_object: Optional[datetime] = None
        try:
            table_date_object = datetime.strptime(table_date_str, "%A %d %B %Y")
        except ValueError as e:
            print(f"Skipping table: Could not parse date '{table_date_str}'. Error: {e}")
            continue

        # --- Check if date is in the future ---
        if table_date_object > datetime.now():
            print(f"Skipping table: Date '{table_date_str}' is in the future.")
            continue

        # --- Safely find rows ---
        rows = table.find_all("tr", class_="ui-widget-content")
        if not rows:
            print(f"Skipping table for {table_date_str}: No 'ui-widget-content' rows found.")
            continue

        for row in rows:
            team_rows = row.find_all("tr")

            if len(team_rows) < 2:
                print("Skipping row: Expected 2 <tr> tags for teams, found less.")
                continue

            home_team_td = team_rows[0].find("td", class_="teamNames")
            away_team_td = team_rows[1].find("td", class_="teamNames")
            
            # If we can't find the core team name, skip it
            if not home_team_td or not away_team_td:
                print("Skipping row: Could not find home or away team <td>.")
                continue

            home_team_name, extra_info = extract_team_name(home_team_td)
            away_team_name, _ = extract_team_name(away_team_td)

            home_team_score = extract_team_score(team_rows[0])
            away_team_score = extract_team_score(team_rows[1])

            # Your check is good.
            if home_team_score == ERROR_INT or away_team_score == ERROR_INT:
                print(f"Skipping game: Final score not posted for {home_team_name} vs {away_team_name}.")
                continue

            location, field = extract_location(row)
            time_str = extract_time_text(row)

            results.append({
                "home_team_name": home_team_name,
                "away_team_name": away_team_name,
                "home_team_score": home_team_score,
                "away_team_score": away_team_score,
                "location": location,
                "field": field,
                "time": time_str,
                "date": table_date_str,
                "extra_info": extra_info
            })

    return results

def parse_schedule_page(html_content: str) -> List[Dict[str, Any]]:
    """
    Parses the "Schedule" page HTML.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    fixture_rows = soup.find_all("tr", class_="ui-widget-content")
    
    if not fixture_rows:
        print("No 'ui-widget-content' rows found on schedule page.")
        return []

    fixtures = []
    
    for row in fixture_rows:
        
        # --- Extract date ---
        date_text = UNKNOWN_STR
        parent_table = row.find_parent("table", class_="generalDataTable")
        if parent_table:
            date_span = parent_table.find("span", class_="ui-column-title")
            if date_span:
                date_text = date_span.text.strip()

        # --- Extract team names ---
        team_name_tds = row.find_all("td", class_="teamNames")
        
        if len(team_name_tds) < 2:
            print("Skipping row: Expected 2 'teamNames' <td>s, found less.")
            continue
            
        home_team_name, extra_info = extract_team_name(team_name_tds[0])
        away_team_name, _ = extract_team_name(team_name_tds[1])

        if (home_team_name == "TBD" or away_team_name == "TBD"):
            print(f"Skipping row: Teams are TBD.")
            continue

        # --- Extract team colours ---
        team_logo_tds = row.find_all("td", class_="teamLogos")
        
        home_team_color_1, home_team_color_2 = (UNKNOWN_STR, UNKNOWN_STR)
        away_team_color_1, away_team_color_2 = (UNKNOWN_STR, UNKNOWN_STR)

        if len(team_logo_tds) >= 2:
            home_team_color_1, home_team_color_2 = extract_team_colors(team_logo_tds[0])
            away_team_color_1, away_team_color_2 = extract_team_colors(team_logo_tds[1])

        # --- Extract location and time ---
        field_name, field_number_str = extract_location(row)
        time_text = extract_time_text(row)

        fixtures.append({
            "home_team_name": home_team_name,
            "home_team_color_1": home_team_color_1,
            "home_team_color_2": home_team_color_2,
            "away_team_name": away_team_name,
            "away_team_color_1": away_team_color_1,
            "away_team_color_2": away_team_color_2,
            "extra_info": extra_info,
            "field_name": field_name,
            "field_number": field_number_str,
            "time": time_text,
            "date": date_text
        })

    return fixtures

def parse_league_table_page(html_content: str) -> List[Dict[str, Any]]:
    """
    Parses the "League Table" (standings) page HTML.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    div_containers = soup.find_all("div", class_="section")

    if not div_containers:
        print("No 'section' divs found on league table page.")
        return []

    league_table = []

    for div in div_containers:
        div_division_h3 = div.find("h3")
        div_division = div_division_h3.text.strip() if div_division_h3 else UNKNOWN_STR

        table_body = div.find("tbody", class_="ui-datatable-data")
        if not table_body:
            print(f"Skipping division '{div_division}': No table body found.")
            continue
            
        table_rows = table_body.find_all("tr")
        if not table_rows:
            print(f"Skipping division '{div_division}': Table body has no rows.")
            continue

        for row in table_rows:
            cells = row.find_all("td")

            if len(cells) < 10:
                print(f"Skipping row in '{div_division}': Expected 10 cells, found {len(cells)}.")
                continue

            def safe_get_text(cell: Tag) -> str:
                return cell.text.strip()
            
            def safe_get_int(cell: Tag) -> int:
                try:
                    return int(cell.text.strip())
                except ValueError:
                    return ERROR_INT

            league_table.append({
                "name": safe_get_text(cells[1]),
                "gp": safe_get_int(cells[2]),
                "w": safe_get_int(cells[3]),
                "l": safe_get_int(cells[4]),
                "d": safe_get_int(cells[5]),
                "gf": safe_get_int(cells[6]),
                "ga": safe_get_int(cells[7]),
                "gd": safe_get_int(cells[8]),
                "pts": safe_get_int(cells[9]),
                "division": div_division
            })

    return league_table


def extract_team_score(element: Tag) -> int:
    """
    Safely extracts the score from a team's row.
    """
    if not element:
        return ERROR_INT
        
    team_score_span = element.find("td", class_="teamScores")

    if team_score_span:
        team_score_text = team_score_span.text.strip()
        
        match = re.search(r"\d+", team_score_text)
        if match:
            try:
                return int(match.group())
            except ValueError:
                return ERROR_INT
    
    return ERROR_INT

def extract_team_colors(element: Tag) -> Tuple[str, str]:
    """
    Safely extracts shirt colors from a team's logo <td>.
    """
    if not element:
        return (UNKNOWN_STR, UNKNOWN_STR)
        
    shirt_span = element.find("span")
    
    if not shirt_span:
        return (UNKNOWN_STR, UNKNOWN_STR)
        
    color_1_regex = re.compile(r"--shirt-colour-1: ([^;]+)")
    color_2_regex = re.compile(r"--shirt-colour-2: ([^;]+)")

    style_string = shirt_span.get('style', '')
      
    color_1_match = color_1_regex.search(style_string)
    color_1 = color_1_match.group(1).strip() if color_1_match else UNKNOWN_STR
        
    color_2_match = color_2_regex.search(style_string)
    color_2 = color_2_match.group(1).strip() if color_2_match else UNKNOWN_STR

    return color_1, color_2

def extract_team_name(element: Tag) -> Tuple[str, Optional[str]]:
    """
    Safely extracts team name and extra info (e.g., "3rd Place Match")
    from a team name <td>.
    """
    if not element:
        return (UNKNOWN_STR, None)
        
    span_tag = element.find("span")
    
    if span_tag and span_tag.get_text(strip=True):
        try:
            full_text = element.get_text(strip=True)
            text_parts = full_text.split("-", 1) # Split only on the first "-"
            
            if len(text_parts) == 2:
                extra_info = text_parts[0].strip()
                team_name = text_parts[1].strip()
                return team_name, extra_info
            else:
                return text_parts[0].strip(), None
        except Exception as e:
            print(f"Error splitting team name: {e}")
            return (element.get_text(strip=True), None)
    else:
        return element.get_text(strip=True), None

def extract_location(element: Tag) -> Tuple[str, str]:
    """
    Safely extracts the field name and number from a fixture row <tr>.
    """
    if not element:
        return (UNKNOWN_STR, UNKNOWN_STR)
        
    location_element = element.find("a", class_="ui-link ui-widget generalLink facilityLink")
    
    if location_element:
        location_text = location_element.text.strip()
        pattern = re.compile(r"^(.+)\s+\((\d+)\)$")
        match = pattern.search(location_text)
        
        if match:
            field_name = match.group(1)
            field_number_str = match.group(2)
            return field_name, field_number_str
        else:
            return location_text, UNKNOWN_STR
            
    return (UNKNOWN_STR, UNKNOWN_STR)

def extract_time_text(element: Tag) -> str:
    """
    Safely extracts the game time from a fixture row <tr>.
    """
    if not element:
        return UNKNOWN_STR
        
    time_regex = re.compile(r"\d{1,2}:\d{2}\s*(?:am|pm)", re.IGNORECASE)
    
    div_text = element.get_text()
    match = time_regex.search(div_text)
    
    if match:
        # match.group(0) gets the *entire* matched string
        return match.group(0).strip()
    
    return UNKNOWN_STR

# --- Main Scraper Execution ---

def main():
    session = requests.Session()

    session.headers.update({
        "User-Agent": "BlueLockBot/1.0 (contact: angusmdev@gmail.com)"
    })

    league_url = os.getenv("LEAGUE_URL")
    schedule_url = os.getenv("SCHEDULE_URL")
    results_url = os.getenv("RESULTS_URL")

    league_html = fetch_page(session, league_url)
    time.sleep(CRAWL_DELAY)
    schedule_html = fetch_page(session, schedule_url)
    time.sleep(CRAWL_DELAY)
    results_html = fetch_page(session, results_url) 
    time.sleep(CRAWL_DELAY)

    league_table = parse_league_table_page(league_html)
    fixtures = parse_schedule_page(schedule_html)
    results = parse_results_page(results_html)

    
    






if __name__ == "__main__":
    main()