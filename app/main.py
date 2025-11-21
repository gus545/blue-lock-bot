from fastapi import FastAPI
from prisma import Prisma
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional
from models import GameModel, TeamModel
from prisma.enums import GameStatus



db = Prisma()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles database connection on startup and disconnection on shutdown.
    """
    print("Connecting to database...")
    await db.connect()
    print("Connected!")
    yield
    print("Disconnecting from database...")
    await db.disconnect()
    print("Disconnected.")


app = FastAPI(lifespan=lifespan)


@app.post("/teams")
async def create_team(team_data: TeamModel):
    """
    Creates a new team in the database.
    """
  
    new_team = await db.team.create(data=team_data.model_dump())
    return new_team

@app.get("/teams")
async def get_teams():
    """
    Retrieves all teams from the database.
    """
    return await db.team.find_many()

@app.post("/games")
async def create_game(game_data: GameModel):
    
    existing_game = await db.game.find_first(
        where={
            "gameTime": game_data.gameTime,
            "location": f"{game_data.fieldName} - Field {game_data.fieldNum}",
        }
    )

    if existing_game:
        return {"message": "Game already exists", "game": existing_game}

    home_team = await db.team.upsert(
        where={
            "name": game_data.homeTeam
        },
        data={
            "create": {
                "name": game_data.homeTeam,
                "primaryColor": game_data.homeTeamPrimaryColor,
                "secondaryColor": game_data.homeTeamSecondaryColor,
                "div": 1
            },
            "update": {
                "primaryColor": game_data.homeTeamPrimaryColor,
                "secondaryColor": game_data.homeTeamSecondaryColor,
            }
        }
    )

    away_team = await db.team.upsert(
        where={
            "name": game_data.awayTeam
        },
        data={
            "create": {
                "name": game_data.awayTeam,
                "primaryColor": game_data.awayTeamPrimaryColor,
                "secondaryColor": game_data.awayTeamSecondaryColor,
                "div": 0
            },
            "update": {
                "primaryColor": game_data.awayTeamPrimaryColor,
                "secondaryColor": game_data.awayTeamSecondaryColor,
            }
        }
    )


    current_status = GameStatus.SCHEDULED

    if game_data.homeScore is not None and game_data.awayScore is not None:
        current_status = GameStatus.FINISHED

    new_game = await db.game.create(data={
        "gameTime": game_data.gameTime,
        "location": f"{game_data.fieldName} - Field {game_data.fieldNum}",
        "homeScore": game_data.homeScore,
        "awayScore": game_data.awayScore,
        "homeTeamId": home_team.id,
        "awayTeamId": away_team.id,
        "status": current_status
    })

    return new_game
@app.get("/games")
async def get_games():
    """
    Retrieves all games from the database.
    """
    return await db.game.find_many()
