import pytest
from prisma.errors import PrismaError


@pytest.mark.asyncio
async def test_create_team_and_persist(db_integration):
    """
    Can we actually write to the DB and read it back?
    """
    # 1. Create a Team directly in the DB
    team = await db_integration.team.create(data={
        "name": "Ottawa Redblacks",
        "primaryColor": "Red",
        "secondaryColor": "Black",
        "div": 1
    })

    # 2. Verify it has a real ID (Database generated it)
    assert team.id is not None
    assert isinstance(team.id, int)

    # 3. Read it back to ensure data integrity
    fetched_team = await db_integration.team.find_unique(where={"id": team.id})
    assert fetched_team.name == "Ottawa Redblacks"


@pytest.mark.asyncio
async def test_foreign_key_integrity(db_integration):
    """
    TESTING INTEGRITY:
    The Database should STOP us from creating a game 
    if the teams do not exist.
    """
    
    # Try to create a game with Team ID 9999 (Which does not exist)
    # This should FAIL. If it succeeds, our DB schema is broken.
    
    with pytest.raises(Exception) as excinfo:
        await db_integration.game.create(data={
            "gameTime": "2025-10-10T10:00:00Z",
            "location": "Field A",
            "homeScore": 0,
            "awayScore": 0,
            "homeTeamId": 9999, # FAKE ID
            "awayTeamId": 8888, # FAKE ID
            "status": "SCHEDULED"
        })
    
    # Assert that the error comes from Prisma/Database
    assert "Foreign key constraint failed" in str(excinfo.value)

@pytest.mark.asyncio
async def test_calculate_stats_integration(client_integration, db_integration):
    """
    Full System Test: 
    1. Create Teams
    2. Post Games via API
    3. Check if DB stored the correct points
    """
     
    t1 = await db_integration.team.create(data={"name": "A", "div": 1, "primaryColor":"x", "secondaryColor":"y"})
    t2 = await db_integration.team.create(data={"name": "B", "div": 1, "primaryColor":"x", "secondaryColor":"y"})

    payload = {
        "gameTime": "2025-01-01T12:00:00Z",
        "fieldName": "Park",
        "fieldNum": 1,
        "homeTeam": "A", # Logic relies on names, not IDs
        "homeTeamPrimaryColor": "x", "homeTeamSecondaryColor": "y",
        "awayTeam": "B",
        "awayTeamPrimaryColor": "x", "awayTeamSecondaryColor": "y",
        "homeScore": 5,
        "awayScore": 0,
        "info": "Test Game"
    }
    
    response = await client_integration.post("/games", json=payload)
    assert response.status_code == 200

    updated_team_a = await db_integration.team.find_unique(where={"id": t1.id})
    
    assert updated_team_a.w == 1       # Wins
    assert updated_team_a.points == 3  # Points
    assert updated_team_a.gd == 5      # Goal Diff