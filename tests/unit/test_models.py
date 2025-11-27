import pytest
from prisma.models import Game
from backend.main import calculate_stats


@pytest.fixture
def sample_games_data():
    """
    Fixture to provide sample game data for testing calculate_stats.
    """

    return [
        Game(
            id = 1,
            gameTime="2025-10-10T10:00:00Z",
            location="Field A",
            homeScore=0,
            awayScore=0,
            homeTeamId=1,
            awayTeamId=2,
            status="FINISHED"
        ),
        Game(
            id=2,
            gameTime="2025-10-10T10:00:00Z",
            location="Field A",
            homeScore=1,
            awayScore=0,
            homeTeamId=1,
            awayTeamId=2,
            status="FINISHED"
        ),
        Game(
            id=3,
            gameTime="2025-10-10T10:00:00Z",
            location="Field A",
            homeScore=3,
            awayScore=0,
            homeTeamId=2,
            awayTeamId=1,
            status="FINISHED"
        )
    ]

def test_calculate_stats(sample_games_data):

    stats = calculate_stats(sample_games_data, 1)

    assert stats["gf"] == 1
    assert stats["ga"] == 3
    assert stats["gd"] == -2
    assert stats["w"] == 1
    assert stats["l"] == 1
    assert stats["d"] == 1
    assert stats["points"] == 4
    assert stats["gamesPlayed"] == 3

def test_calculate_stats_empty_list():

    stats = calculate_stats([], 1)

    assert stats["gf"] == 0
    assert stats["ga"] == 0
    assert stats["gd"] == 0
    assert stats["w"] == 0
    assert stats["l"] == 0
    assert stats["d"] == 0
    assert stats["points"] == 0
    assert stats["gamesPlayed"] == 0

def test_calculate_stats_single_game(sample_games_data):
    stats = calculate_stats([sample_games_data[1]], 1)

    assert stats["gf"] == 1
    assert stats["ga"] == 0
    assert stats["gd"] == 1
    assert stats["w"] == 1
    assert stats["l"] == 0
    assert stats["d"] == 0
    assert stats["points"] == 3
    assert stats["gamesPlayed"] == 1

