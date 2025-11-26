from fastapi import FastAPI
from prisma import Prisma
from prisma.models import Game
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import List, Optional
from models import ScrapedGame, TeamModel
from prisma.enums import GameStatus
from datetime import datetime



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
    
    team = await db.team.upsert(
        where={
            "name": team_data.name
            }
            ,
        data={
            "create": {
                "name": team_data.name,
                "primaryColor": team_data.primaryColor,
                "secondaryColor": team_data.secondaryColor,
                "div": team_data.div
            },
            "update": {
                "primaryColor": team_data.primaryColor,
                "secondaryColor": team_data.secondaryColor,
                "div": team_data.div
            }
        }
    )

    return team

@app.get("/teams")
async def get_teams(limit: Optional[int] = None, time_gt: Optional[datetime] = None):
    """
    Retrieves all teams from the database.
    """
    return await db.team.find_many()

@app.get("/teams/{team_id}")
async def get_team(team_id: int):
    """
    Retrieves a specific team by ID from the database.
    """
    return await db.team.find_unique(where={"id": team_id})

@app.put("/teams/{team_id}")
async def update_team(team_id: int, team_data: TeamModel):
    """
    Updates an existing team in the database.
    """
    updated_team = await db.team.update(
        where={"id": team_id},
        data={
            "name": team_data.name,
            "primaryColor": team_data.primaryColor,
            "secondaryColor": team_data.secondaryColor,
            "div": team_data.div
        }
    )
    return updated_team

@app.delete("/teams/{team_id}")
async def delete_team(team_id: int):
    """
    Deletes a team from the database.
    """
    deleted_team = await db.team.delete(where={"id": team_id})
    return deleted_team




@app.post("/games")
async def create_game(game_data: ScrapedGame):
    
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
        "status": current_status,
        "info": game_data.info
    })

    await refresh_stats(home_team.id)
    await refresh_stats(away_team.id)
    return new_game
@app.get("/games")
async def get_games(game_time_gt: Optional[str] = None, limit: Optional[int] = 100, sort_by: Optional[str] = None, team_id: Optional[int] = None):
    """
    Retrieves all games from the database.
    """

    sort_by_clause = {}
    if sort_by:
        sort_by_clause = {
            sort_by: "asc"
        }

    where_clause={}
    if game_time_gt:
        game_time_gt = datetime.fromisoformat(game_time_gt.replace('Z', '+00:00'))

        where_clause = {
            "gameTime": {
                "gt": game_time_gt
            },
            "OR": [
                {"homeTeamId": team_id},
                {"awayTeamId": team_id}
            ]
        }



    games = await db.game.find_many(
        where=where_clause,
        take=limit,
        order=sort_by_clause
    )

    return games


@app.get("/games/{game_id}")
async def get_game(game_id: int):
    """
    Retrieves a specific game by ID from the database.
    """
    return await db.game.find_unique(where={"id": game_id})

@app.put("/games/{game_id}")
async def update_game(game_id: int, game_data: ScrapedGame):
    """
    Updates an existing game in the database.
    """
    existing_game = await db.game.find_unique(where={"id": game_id})

    old_home_team_id = existing_game.homeTeamId
    old_away_team_id = existing_game.awayTeamId

    if not existing_game:
        return {"message": "Game not found"}

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
                "div": 1
            },
            "update": {
                "primaryColor": game_data.awayTeamPrimaryColor,
                "secondaryColor": game_data.awayTeamSecondaryColor
            }
        }
    )  

    updated_game = await db.game.update(
        where={"id": game_id},
        data={
            "gameTime": game_data.gameTime,
            "location": f"{game_data.fieldName} - Field {game_data.fieldNum}",
            "homeScore": game_data.homeScore,
            "awayScore": game_data.awayScore,
            "homeTeamId": home_team.id,
            "awayTeamId": away_team.id,
            "info": game_data.info
        }
    )
    await refresh_stats(old_home_team_id)
    await refresh_stats(old_away_team_id)
    await refresh_stats(home_team.id)
    await refresh_stats(away_team.id)
    return updated_game

@app.delete("/games/{game_id}")
async def delete_game(game_id: int):
    """
    Deletes a game from the database.
    """
    deleted_game = await db.game.delete(where={"id": game_id})
    return deleted_game





async def refresh_stats(team_id: int):

    stats = calculate_stats(await db.game.find_many(where={"AND": [{"status": GameStatus.FINISHED}, {"OR": [{"homeTeamId": team_id}, {"awayTeamId": team_id}]}]}), team_id)
    await db.team.update_many(where={"id": team_id}, data=stats)
    return stats


@app.post("/clear")
async def clear_games():
    """
    Clears all games and teams from the database.
    """
   
    await db.game.delete_many()
    await db.team.delete_many()

    return {"message": "Games and teams cleared"}

def calculate_stats(games : List[Game], team_id: int):

    gf = 0
    ga = 0
    gd = 0
    w = 0
    l = 0
    d = 0
    points = 0
    gp = 0

    for game in games:
        gp += 1
        if game.homeTeamId == team_id:
            gf += game.homeScore
            ga += game.awayScore
            if game.homeScore > game.awayScore:
                w += 1
                points += 3
            elif game.homeScore < game.awayScore:
                l += 1
            else:
                d += 1
                points += 1
        else: 
            gf += game.awayScore
            ga += game.homeScore
            if game.awayScore > game.homeScore:
                w += 1
                points += 3
            elif game.awayScore < game.homeScore:
                l += 1
            else:
                d += 1
                points += 1
    gd = gf - ga
    
    stats = {
        "gf": gf,
        "ga": ga,
        "gd": gd,
        "w": w,
        "l": l,
        "d": d,
        "points": points,
        "gamesPlayed": gp
    }

    return stats
