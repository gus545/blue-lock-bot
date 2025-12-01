# conftest.py
import pytest
import pytest_asyncio
import subprocess
import os
from prisma import Prisma
from backend.main import app
from unittest.mock import patch
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport 
from models import ScrapedGame
from datetime import datetime, timedelta
import pytz


from datetime import datetime, timedelta, timezone

# ✅ Define them as proper Timezone-Aware Datetime Objects
PAST_DATE = (datetime.now(timezone.utc) - timedelta(days=5)).astimezone(pytz.timezone('US/Eastern')).isoformat()
FUTURE_DATE = (datetime.now(timezone.utc) + timedelta(days=5)).astimezone(pytz.timezone('US/Eastern')).isoformat()



# 1. Configuration
TEST_DB_URL = os.getenv("TEST_DB_URL")

# 2. DATABASE SETUP (Runs ONCE per session)
# This just pushes the schema. It does NOT return a connection.
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    print("\n--- 1. Pushing Schema to Test DB ---")
    # We set the environment variable specifically for this command
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DB_URL
    env["DB_VOLUME"] = ""
    
    # Inside your test setup
    subprocess.run(["docker-compose", "--profile", "test", "up", "-d"])
    print("--- Docker Compose Started ---")

    subprocess.run(
        ["prisma", "db", "push", "--skip-generate"], 
        env=env,
        check=True
    )

    print("--- Schema Push Complete ---")

    yield

    subprocess.run(["docker-compose", "down"], env=env, check=True)

# 3. DATABASE CONNECTION (Runs PER TEST)
# We changed scope to "function" (default) to match the test loop.
@pytest_asyncio.fixture
async def db_integration():
    print("\n--- 2. Connecting to DB ---")
    client = Prisma(datasource={'url': TEST_DB_URL})
    await client.connect()
    
    # CLEANUP: Wipe the DB clean before giving it to the test
    # Order matters: delete children (Game) before parents (Team)
    await client.game.delete_many()
    await client.team.delete_many()

    # Patch the global 'db' in main.py with this new client
    with patch("backend.main.db", client):
        yield client

    # Teardown
    print("\n--- 3. Disconnecting ---")
    await client.disconnect()

@pytest_asyncio.fixture
async def client_integration():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_games_data():
    return [
        ScrapedGame(
            home_team="Team A",
            away_team="Team B",
            home_score=2,
            away_score=1,
            home_team_primary_color="#FF0000",
            home_team_secondary_color="#00FF00",
            away_team_primary_color="#0000FF",
            away_team_secondary_color="#FFFF00",
            field_name="Stadium",
            game_time=PAST_DATE,
            field_num=1,
            info="Test Info"
        ),
        ScrapedGame(
            home_team="Team C",
            away_team="Team D",
            home_score=3,
            away_score=0,
            home_team_primary_color="#00FFFF",
            home_team_secondary_color="#FF00FF",
            away_team_primary_color="#FF0000",
            away_team_secondary_color="#00FF00",
            field_name="Stadium",
            field_num=2,
            game_time=PAST_DATE,
            info="Test Info"
        ),
        ScrapedGame(
            home_team="Team E",
            away_team="Team F",
            home_score=1,
            away_score=2,
            home_team_primary_color="#FF00FF",
            home_team_secondary_color="#00FFFF",
            away_team_primary_color="#000000",
            away_team_secondary_color="#FFFFFF",
            field_name="Stadium",
            field_num=3,
            game_time=PAST_DATE,
            info="Test Info"
        ),
        ScrapedGame(
            home_team="Team C",
            away_team="Team A",
            home_score=2,
            away_score=1,
            home_team_primary_color="#00FFFF",
            home_team_secondary_color="#FF00FF",
            away_team_primary_color="#0000FF",
            away_team_secondary_color="#FFFF00",
            field_name="Stadium",
            field_num=2,
            game_time=FUTURE_DATE,
            info="Test Info"
        ),
        ScrapedGame(
            home_team="Team D",
            away_team="Team B",
            home_score=1,
            away_score=2,
            home_team_primary_color="#FF0000",
            home_team_secondary_color="#00FF00",
            away_team_primary_color="#0000FF",
            away_team_secondary_color="#FF0000",
            field_name="Stadium",
            field_num=1,
            game_time=FUTURE_DATE,
            info="Test Info"
        ),
        ScrapedGame(
            home_team="Team F",
            away_team="Team E",
            home_score=3,
            away_score=0,
            home_team_primary_color="#FF00FF",
            home_team_secondary_color="#00FFFF",
            away_team_primary_color="#000000",
            away_team_secondary_color="#FFFFFF",
            field_name="Stadium",
            field_num=3,
            game_time=FUTURE_DATE,
            info="Test Info"
        )
    ]

    