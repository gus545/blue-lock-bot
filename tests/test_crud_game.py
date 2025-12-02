import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_crud_game(db_integration, client_integration):

    # Create game

    new_game = {
        "home_team": "Home Team",
        "away_team": "Away Team",
        "home_score": 1,
        "away_score": 0,
        "home_team_primary_color": "Red",
        "home_team_secondary_color": "Black",
        "away_team_primary_color": "Red",
        "away_team_secondary_color": "Black",
        "field_name": "Park",
        "field_num": 1,
        "game_time": "2025-01-01T12:00:00Z",
        "info": "Test Game"
    }
    response = await client_integration.post("/games", json=new_game)

    assert response.status_code == 200
    
    db_entry = await db_integration.game.find_unique(where={"id": response.json()["id"]})

    assert (await db_integration.team.find_unique(where={"id": db_entry.homeTeamId})).name == "Home Team"
    assert (await db_integration.team.find_unique(where={"id": db_entry.awayTeamId})).name == "Away Team"
    assert db_entry.homeScore == 1
    assert db_entry.awayScore == 0
    assert db_entry.location == "Park - Field 1" 
    assert db_entry.gameTime.isoformat() == "2025-01-01T12:00:00+00:00"
    assert db_entry.info == "Test Game"

    # Get game

    fetched_game = await client_integration.get(f"/games/{response.json()['id']}")
    assert fetched_game.status_code == 200
    
    assert (await db_integration.team.find_unique(where={"id": fetched_game.json()["homeTeamId"]})).name == "Home Team"
    assert (await db_integration.team.find_unique(where={"id": fetched_game.json()["awayTeamId"]})).name == "Away Team"
    assert fetched_game.json()["homeScore"] == 1
    assert fetched_game.json()["awayScore"] == 0
    assert fetched_game.json()["location"] == "Park - Field 1"
    assert fetched_game.json()["gameTime"] == "2025-01-01T12:00:00Z"
    assert fetched_game.json()["info"] == "Test Game"


    # Update game

    updated_game = {
        "home_team": "Updated game",
        "away_team": "Updated game",
        "home_score": 2,
        "away_score": 1,
        "home_team_primary_color": "Blue",
        "home_team_secondary_color": "White",
        "away_team_primary_color": "Blue",
        "away_team_secondary_color": "White",
        "field_name": "Park",
        "field_num": 1,
        "game_time": "2025-01-01T12:00:00Z",
        "info": "Test Game"
    }

    response = await client_integration.put(f"/games/{response.json()['id']}", json=updated_game)
    assert response.status_code == 200
    assert (await db_integration.team.find_unique(where={"id": response.json()["homeTeamId"]})).name == "Updated game"
    assert (await db_integration.team.find_unique(where={"id": response.json()["awayTeamId"]})).name == "Updated game"
    assert response.json()["homeScore"] == 2
    assert response.json()["awayScore"] == 1 
    assert response.json()["location"] == "Park - Field 1"
    assert response.json()["gameTime"] == "2025-01-01T12:00:00Z"
    assert response.json()["info"] == "Test Game"


    # Delete game
    response = await client_integration.delete(f"/games/{response.json()['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == db_entry.id
    assert await db_integration.game.find_unique(where={"id": response.json()["id"]}) is None

@pytest.mark.asyncio
async def test_query_games(client_integration, db_integration, sample_games_data):
    for game in sample_games_data:
        response = await client_integration.post("/games", json=game.model_dump(mode="json"))
        assert response.status_code == 200


    # Test generic query
    response = await client_integration.get("/games")
    assert response.status_code == 200
    assert len(response.json()) == len(sample_games_data)

    # Test limit
    response = await client_integration.get("/games?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # Test sort_by
    response = await client_integration.get("/games?sort_by=gameTime")
    assert response.status_code == 200
    assert response.json()[0]["gameTime"] <= response.json()[1]["gameTime"] 
    response = await client_integration.get("/games?sort_by=-gameTime")
    assert response.status_code == 200
    assert response.json()[0]["gameTime"] >= response.json()[1]["gameTime"]

    # Test date
    response = await client_integration.get(f"/games?date={datetime.now().isoformat()}")
    assert response.status_code == 200
    assert all(game["gameTime"] > datetime.now().isoformat() for game in response.json())

    response = await client_integration.get(f"/games?date=-{datetime.now().isoformat()}")
    assert response.status_code == 200
    assert all(game["gameTime"] < datetime.now().isoformat() for game in response.json())



    # Test team_id 
    team_a = await db_integration.team.find_first(where={"name": "Team A"})
    team_b = await db_integration.team.find_first(where={"name": "Team B"})
    assert team_a is not None
    assert team_b is not None


    response = await client_integration.get(f"/games?team_id={team_a.id}")
    assert response.status_code == 200
    assert all(game["homeTeamId"] == team_a.id or game["awayTeamId"] == team_a.id for game in response.json())

    response = await client_integration.get(f"/games?team_id={team_b.id}")
    assert response.status_code == 200
    assert all(game["homeTeamId"] == team_b.id or game["awayTeamId"] == team_b.id for game in response.json())

    # Test bad query
    assert (await client_integration.get("/games?bad_param=good_value")).status_code == 200
    assert (await client_integration.get("/games?limit=bad_value")).status_code == 422
    assert (await client_integration.get("/games?limit=-1")).status_code == 400
    assert (await client_integration.get("/games?sort_by=bad_value")).status_code == 400


    # Test date
    assert (await client_integration.get(f"/games?date={datetime.now().isoformat()}")).status_code == 200
    assert all(game["gameTime"] > datetime.now().isoformat() for game in (await client_integration.get(f"/games?date={datetime.now().isoformat()}")).json())

