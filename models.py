from pydantic import BaseModel
import datetime
from typing import Optional
from pydantic import Field, ConfigDict


class ScrapedGame(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    home_team: str = Field(alias="homeTeam")
    away_team: str = Field(alias="awayTeam")
    home_score: Optional[int] = Field(alias="homeScore")
    away_score: Optional[int] = Field(alias="awayScore")
    home_team_primary_color: str = Field(alias="homeTeamPrimaryColor")
    home_team_secondary_color: str = Field(alias="homeTeamSecondaryColor")
    away_team_primary_color: str = Field(alias="awayTeamPrimaryColor")
    away_team_secondary_color: str = Field(alias="awayTeamSecondaryColor")
    field_name: str = Field(alias="fieldName")
    field_num: int = Field(alias="fieldNum")
    game_time: str = Field(alias="gameTime")
    info: Optional[str]

class TeamModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    primary_color: str = Field(alias="primaryColor")
    secondary_color: str = Field(alias="secondaryColor")
    div: int