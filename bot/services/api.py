import aiohttp
from typing import List, Optional, Dict, Any
import datetime

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
            print(f"💥 Connection Error: {e}")
            return None

    async def get_latest_games(self, team_id: int, limit: int = 5) -> List[Dict]:
        params = {
            "team_id": team_id,
            "limit": limit,
            "sort_by": "-gameTime",
            "date": "-"+ datetime.datetime.now().isoformat()
        }


        games = await self._get("/games", params=params)
        team = await self.get_team_from_id(team_id=team_id)

        return {
            "team": team,
            "games": games
        }
    
    async def get_upcoming_games(self, team_id: int, limit: int = 3) -> List[Dict]:
        
        params = {
            "team_id": team_id,
            "limit": 3,
            "sort_by": "gameTime",
            "date": datetime.datetime.now().isoformat()
        }

        
        team = await self.get_team_from_id(team_id=team_id)
        if not team:
            return None
        
        games = await self._get("/games", params=params)

        return {
            "team": team,
            "games": games
        }
    
    async def get_team_from_id(self, team_id: int):
        if not team_id:
            return None
        
        return await self._get(f"/teams/{team_id}")
        
