import aiohttp
from typing import List, Optional, Dict, Any
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

TEAM_NAME = os.getenv("TEAM_NAME")

class LeagueClient:
    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        self.session = session
        self.base_url = base_url

    async def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    print(f"⚠️ 404 Not Found: {url}")
                    return None
                else:
                    print(f"❌ API Error {resp.status}: {await resp.text()}")
                    return None
        except Exception as e:
            print(f"💥 Connection Error: {e}, for {url} with params {params}")
            return None

    async def get_latest_games(self, team_id: int, limit: int = 5) -> List[Dict]:
        

        team = await self.get_team_from_id(team_id=team_id)
        if not team:
            return None
        
        params = {
            "team_id": team["id"],
            "limit": limit,
            "sort_by": "-gameTime",
            "date": "-"+ datetime.datetime.now().isoformat()
        }

        games = await self._get("/games", params=params)

        return {
            "team": team,
            "games": games
        }
    
    async def get_upcoming_games(self, team_id: int, limit: int = 3) -> List[Dict]:
        
        team = await self.get_team_from_id(team_id=team_id)
        if not team:
            return None
        params = {
            "team_id": team["id"],
            "limit": limit,
            "sort_by": "gameTime",
            "date": datetime.datetime.now().isoformat()
        }

        
        
        games = await self._get("/games", params=params)

        return {
            "team": team,
            "games": games
        }
    
    async def get_team_from_id(self, team_id: int):
        if not team_id:
            return await self._get("/teams", params={"name": TEAM_NAME})
        
        
        return await self._get(f"/teams", params={"id": team_id})
        
