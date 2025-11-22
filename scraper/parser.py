from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import re
import pytz

# --- Constants ---
UNKNOWN_STR = "Unknown"
ERROR_INT = -1
TIMEZONE = pytz.timezone("US/Eastern")

# --- Parsing Functions ---

class LeagueParser:

    @staticmethod
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

                 # --- Extract team colours ---
                team_logo_tds = row.find_all("td", class_="teamLogos")
                
                home_team_color_1, home_team_color_2 = (UNKNOWN_STR, UNKNOWN_STR)
                away_team_color_1, away_team_color_2 = (UNKNOWN_STR, UNKNOWN_STR)

                if len(team_logo_tds) >= 2:
                    home_team_color_1, home_team_color_2 = LeagueParser.extract_team_colors(team_logo_tds[0])
                    away_team_color_1, away_team_color_2 = LeagueParser.extract_team_colors(team_logo_tds[1])
                
                # If we can't find the core team name, skip it
                if not home_team_td or not away_team_td:
                    print("Skipping row: Could not find home or away team <td>.")
                    continue

                home_team_name, extra_info = LeagueParser.extract_team_name(home_team_td)
                away_team_name, _ = LeagueParser.extract_team_name(away_team_td)

                home_team_score = LeagueParser.extract_team_score(team_rows[0])
                away_team_score = LeagueParser.extract_team_score(team_rows[1])

                # Your check is good.
                if home_team_score == ERROR_INT or away_team_score == ERROR_INT:
                    print(f"Skipping game: Final score not posted for {home_team_name} vs {away_team_name}.")
                    continue

                location, field = LeagueParser.extract_location(row)
                time_text = LeagueParser.extract_time_text(row)

                gameDate = LeagueParser.date_and_time_to_iso(table_date_str, time_text)

                results.append({
                    "homeTeam": home_team_name,
                    "homeTeamPrimaryColor": home_team_color_1,
                    "homeTeamSecondaryColor": home_team_color_2,
                    "homeScore": home_team_score,
                    "awayTeam": away_team_name,
                    "awayTeamPrimaryColor": away_team_color_1,
                    "awayTeamSecondaryColor": away_team_color_2,
                    "awayScore": away_team_score,
                    "fieldName": location,
                    "fieldNum": int(field),
                    "gameTime": gameDate,
                    "info": extra_info
                })

        return results

    @staticmethod
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
                
            home_team_name, extra_info = LeagueParser.extract_team_name(team_name_tds[0])
            away_team_name, _ = LeagueParser.extract_team_name(team_name_tds[1])

            if (home_team_name == "TBD" or away_team_name == "TBD"):
                print(f"Skipping row: Teams are TBD.")
                continue

            # --- Extract team colours ---
            team_logo_tds = row.find_all("td", class_="teamLogos")
            
            home_team_color_1, home_team_color_2 = (UNKNOWN_STR, UNKNOWN_STR)
            away_team_color_1, away_team_color_2 = (UNKNOWN_STR, UNKNOWN_STR)

            if len(team_logo_tds) >= 2:
                home_team_color_1, home_team_color_2 = LeagueParser.extract_team_colors(team_logo_tds[0])
                away_team_color_1, away_team_color_2 = LeagueParser.extract_team_colors(team_logo_tds[1])

            # --- Extract location and time ---
            field_name, field_number_str = LeagueParser.extract_location(row)
            time_text = LeagueParser.extract_time_text(row)

            gameDate = LeagueParser.date_and_time_to_iso(date_text, time_text)

            fixtures.append({
                "homeTeam": home_team_name,
                "homeTeamPrimaryColor": home_team_color_1,
                "homeTeamSecondaryColor": home_team_color_2,
                "homeScore": None,
                "awayScore": None,
                "awayTeam": away_team_name,
                "awayTeamPrimaryColor": away_team_color_1,
                "awayTeamSecondaryColor": away_team_color_2,
                "info": extra_info,
                "fieldName": field_name,
                "fieldNum": field_number_str,
                "gameTime": gameDate
            })

        return fixtures

    @staticmethod
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
            div_division = int(re.search(r'\d+', div_division).group()) if re.search(r'\d+', div_division) else ERROR_INT
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
                
                # Extract team color
                primary_color, secondary_color = LeagueParser.extract_team_colors(cells[0])


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
                    "div": div_division,
                    "primaryColor": primary_color,
                    "secondaryColor": secondary_color
                })

        return league_table

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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
                text_parts = full_text.split("-", 1)
                
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

    @staticmethod
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
                
                return field_name, int(field_number_str.strip())
            else:
                return location_text, UNKNOWN_STR
                
        return (UNKNOWN_STR, UNKNOWN_STR)

    @staticmethod
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
            return match.group(0).strip()
        
        return UNKNOWN_STR
    
    @staticmethod 
    def date_and_time_to_iso(date_str: str, time_str: str):

        full_string = f"{date_str} {time_str}" 

        dt_object = datetime.strptime(full_string, "%A %d %B %Y %I:%M%p")
        dt_object = dt_object.astimezone(TIMEZONE)
        return dt_object.isoformat()