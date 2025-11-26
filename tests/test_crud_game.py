import pytest

@pytest.mark.asyncio
async def test_crud_game(db_integration, client_integration):

    # Create game

    new_game = {
        "homeTeam": "Home Team",
        "awayTeam": "Away Team",
        "homeScore": 1,
        "awayScore": 0,
        "homeTeamPrimaryColor": "Red",
        "homeTeamSecondaryColor": "Black",
        "awayTeamPrimaryColor": "Red",
        "awayTeamSecondaryColor": "Black",
        "fieldName": "Park",
        "fieldNum": 1,
        "gameTime": "2025-01-01T12:00:00Z",
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
        "homeTeam": "Updated game",
        "awayTeam": "Updated game",
        "homeScore": 2,
        "awayScore": 1,
        "homeTeamPrimaryColor": "Blue",
        "homeTeamSecondaryColor": "White",
        "awayTeamPrimaryColor": "Blue",
        "awayTeamSecondaryColor": "White",
        "fieldName": "Park",
        "fieldNum": 1,
        "gameTime": "2025-01-01T12:00:00Z",
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
    assert await db_integration.game.find_many() == []