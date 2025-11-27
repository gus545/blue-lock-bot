import discord
from discord import app_commands
from discord.ext import commands
import os
from utils.formatting import create_game_embed


API_URL = os.getenv("API_URL", "http://localhost:8000")
try:
    DEFAULT_TEAM_ID = int(os.getenv("TEAM_ID", "329"))
except ValueError:
    print("❌ Error: TEAM_ID in .env is not a number. Defaulting to 329.")
    DEFAULT_TEAM_ID = 329


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="latest", description="Get the latest scraped games")
    async def latest_games(self, interaction: discord.Interaction, team_id: int = DEFAULT_TEAM_ID):
        await interaction.response.defer()

        games_data = await self.bot.api.get_latest_games(team_id=team_id)

        if not games_data:
            await interaction.followup.send("No games found", ephemeral=True)
            return

        embed = create_game_embed(games_data, title=f"Latest Games (Team ID: {team_id})")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Games(bot))