import pytest

@pytest.mark.asyncio
async def test_crud_team(db_integration, client_integration):

    # Create team

    new_team = {
        "name": "New Team",
        "primary_color": "Red",
        "secondary_color": "Black",
        "div": 1
    }

    response = await client_integration.post("/teams", json=new_team)

    assert response.status_code == 200
    
    db_entry = await db_integration.team.find_unique(where={"id": response.json()["id"]})

    assert db_entry.name == "New Team"
    assert db_entry.div == 1
    assert db_entry.primaryColor == "Red"
    assert db_entry.secondaryColor == "Black"

    # Get team

    fetched_team = await client_integration.get(f"/teams/{response.json()['id']}")
    assert fetched_team.status_code == 200
    assert fetched_team.json()["name"] == "New Team"
    assert fetched_team.json()["div"] == 1
    assert fetched_team.json()["primaryColor"] == "Red"  # The database schema uses camelCase
    assert fetched_team.json()["secondaryColor"] == "Black"

    # Update team

    updated_team = {
        "name": "Updated Team",
        "primary_color": "Blue",
        "secondary_color": "White",
        "div": 2
    }

    response = await client_integration.put(f"/teams/{response.json()['id']}", json=updated_team)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Team"
    assert response.json()["div"] == 2
    assert response.json()["primaryColor"] == "Blue"
    assert response.json()["secondaryColor"] == "White"

    # Delete team
    response = await client_integration.delete(f"/teams/{response.json()['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Team"
    assert await db_integration.team.find_unique(where={"id": response.json()["id"]}) is None