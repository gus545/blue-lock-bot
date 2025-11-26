from pydantic import BaseModel
import datetime
from typing import Optional

class ScrapedGame(BaseModel):
    homeTeam: str
    awayTeam: str
    homeScore: Optional[int]
    awayScore: Optional[int]
    homeTeamPrimaryColor: str
    homeTeamSecondaryColor: str
    awayTeamPrimaryColor: str
    awayTeamSecondaryColor: str
    fieldName: str
    fieldNum: int
    gameTime: str
    info: Optional[str]

class TeamModel(BaseModel):
    name: str
    primaryColor: str
    secondaryColor: str
    div: int